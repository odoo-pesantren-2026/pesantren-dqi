# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging
import json

_logger = logging.getLogger(__name__)


class SmartBillingTransaction(models.Model):
    """
    Model untuk menyimpan semua transaksi Smart Billing.
    Mencatat VA tagihan, VA permanen top-up, dan payment link.
    """
    _name = 'smart.billing.transaction'
    _description = 'Smart Billing Transaction'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def init(self):
        super().init()
        # ---------------------------------------------------------
        # DATA MIGRATION CHECK
        # ---------------------------------------------------------
        # Fix existing Permanent VA records that are still 'pending'
        # Query SQL langsung agar lebih cepat dan bypass ORM checks
        self.env.cr.execute("""
            UPDATE smart_billing_transaction 
            SET state = 'active' 
            WHERE transaction_type = 'va_topup' AND state = 'pending'
        """)

    name = fields.Char(
        string='Order ID',
        required=True,
        default='/',
        copy=False,
        index=True,
        tracking=True
    )
    provider = fields.Selection([
        ('dummy', 'Dummy'),
        ('bsi', 'BSI'),
        ('tki', 'TKI'),
    ], string='Provider', required=True, tracking=True)

    transaction_type = fields.Selection([
        ('va_tagihan', 'Tagihan (Invoice)'),
        ('va_topup', 'Akun VA Permanen'),
        ('payment_link', 'Payment Link'),
    ], string='Tipe Transaksi', required=True, tracking=True)

    state = fields.Selection([
        ('pending', 'Menunggu Pembayaran'),  # Untuk Tagihan
        ('active', 'Aktif'),                # Untuk VA Permanen
        ('settlement', 'Lunas / Terbayar'),
        ('expired', 'Expired'),
        ('cancelled', 'Dibatalkan'),
        ('failed', 'Gagal'),
    ], string='Status', default='pending', tracking=True)

    # Related Records
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        ondelete='restrict',
        index=True
    )
    siswa_id = fields.Many2one(
        'cdn.siswa',
        string='Santri',
        compute='_compute_siswa_id',
        store=True
    )
    move_id = fields.Many2one(
        'account.move',
        string='Invoice',
        ondelete='set null',
        help='Invoice terkait (untuk VA tagihan)'
    )
    uang_saku_id = fields.Many2one(
        'cdn.uang_saku',
        string='Transaksi Uang Saku',
        ondelete='set null',
        help='Transaksi uang saku yang dibuat (untuk top-up)'
    )

    # Transaction Details
    va_number = fields.Char(string='Nomor VA', index=True)
    va_bank = fields.Char(string='Bank VA')
    payment_url = fields.Char(string='Payment URL')
    gross_amount = fields.Float(string='Nominal', digits=(16, 2))

    # Timestamps
    transaction_time = fields.Datetime(
        string='Waktu Transaksi', default=fields.Datetime.now)
    settlement_time = fields.Datetime(string='Waktu Pembayaran')
    expiry_time = fields.Datetime(string='Waktu Kadaluarsa')

    # Provider Response
    provider_transaction_id = fields.Char(string='Provider Transaction ID')
    provider_status = fields.Char(string='Provider Status')
    provider_response = fields.Text(string='Provider Response (JSON)')

    # Notification tracking
    notification_sent = fields.Boolean(
        string='Notification Sent', default=False)

    @api.depends('partner_id')
    def _compute_siswa_id(self):
        for record in self:
            siswa = self.env['cdn.siswa'].search([
                ('partner_id', '=', record.partner_id.id)
            ], limit=1)
            record.siswa_id = siswa.id if siswa else False

    @api.model
    def create(self, vals):
        """Generate sequence for order ID if not provided"""
        if not vals.get('name') or vals.get('name') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'smart.billing.transaction')
        return super().create(vals)

    def action_check_status(self):
        """Check transaction status from provider"""
        self.ensure_one()

        provider = self._get_provider()
        result = provider.check_transaction_status(self.name)

        if result.get('success'):
            new_status = result.get('status', 'pending')

            # Map provider status to our status
            status_map = {
                'pending': 'pending',
                'settlement': 'settlement',
                'capture': 'settlement',
                'expire': 'expired',
                'cancel': 'cancelled',
                'deny': 'failed',
                'failed': 'failed',
            }

            self.state = status_map.get(new_status, 'pending')
            self.provider_status = new_status

            if result.get('settlement_time'):
                self.settlement_time = result['settlement_time']

            # If settled, process the payment
            if self.state == 'settlement':
                self._on_payment_settled()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Status Checked',
                'message': f"Status: {self.state}",
                'type': 'info',
                'sticky': False,
            }
        }

    def _get_provider(self):
        """Get the provider instance for this transaction"""
        provider_map = {
            'dummy': 'smart.billing.provider.dummy',
            'bsi': 'smart.billing.provider.bsi',
            'tki': 'smart.billing.provider.tki',
        }
        model_name = provider_map.get(
            self.provider, 'smart.billing.provider.dummy')
        return self.env[model_name]

    def _process_notification(self, data):
        """
        Process notification data from webhook.
        Called by controller when webhook is received.
        """
        self.ensure_one()

        provider = self._get_provider()
        parsed = provider.parse_notification(data)

        status = parsed.get('transaction_status', '').lower()

        # Map status
        if status in ['settlement', 'capture']:
            self.state = 'settlement'
            self.settlement_time = fields.Datetime.now()
            self._on_payment_settled()
        elif status in ['expire', 'expired']:
            self.state = 'expired'
        elif status in ['cancel', 'cancelled']:
            self.state = 'cancelled'
        elif status in ['deny', 'failed']:
            self.state = 'failed'

        self.provider_status = status
        self.provider_response = json.dumps(data, indent=2)

        # Update amount if provided
        if parsed.get('gross_amount'):
            self.gross_amount = parsed['gross_amount']

        _logger.info(f"Processed notification for {self.name}: {status}")

    def _on_payment_settled(self):
        """
        Actions to perform when payment is settled.
        - For VA tagihan: reconcile invoice
        - For VA topup: add to uang saku
        """
        self.ensure_one()

        if self.transaction_type == 'va_tagihan' and self.move_id:
            self._reconcile_invoice_payment()
        elif self.transaction_type == 'va_topup':
            self._create_uang_saku_topup()

        # Send notification
        if self.env['ir.config_parameter'].sudo().get_param('smart_billing.send_notification', 'True') == 'True':
            self._send_payment_notification()

    def _reconcile_invoice_payment(self):
        """
        Reconcile the invoice with the payment.

        Handles overpayment scenario:
        - If paid amount > invoice residual, invoice is paid fully
        - Excess amount is credited to student's wallet (uang saku)
        """
        self.ensure_one()

        if not self.move_id:
            _logger.warning(f"No invoice to reconcile for {self.name}")
            return

        if self.move_id.payment_state == 'paid':
            _logger.info(f"Invoice {self.move_id.name} already paid")
            return

        try:
            invoice_residual = self.move_id.amount_residual
            paid_amount = self.gross_amount

            # Determine actual payment amount (cannot exceed invoice residual)
            payment_amount = min(paid_amount, invoice_residual)

            # Calculate overpayment (if any)
            excess_amount = paid_amount - invoice_residual
            if excess_amount < 0:
                excess_amount = 0

            _logger.info(f"[PAYMENT] Invoice: {self.move_id.name}, Residual: {invoice_residual}, "
                         f"Paid: {paid_amount}, Payment: {payment_amount}, Excess: {excess_amount}")

            # Use Odoo's payment register wizard
            payment_register = self.env['account.payment.register'].with_context(
                active_model='account.move',
                active_ids=self.move_id.ids,
            ).create({
                'amount': payment_amount,  # Use payment_amount, not gross_amount
                'payment_date': self.settlement_time or fields.Date.today(),
                'communication': f"Smart Billing: {self.name}",
            })

            payment = payment_register._create_payments()

            if payment:
                _logger.info(
                    f"Payment created for invoice {self.move_id.name}: {payment.name}")
                self.message_post(
                    body=f"Invoice {self.move_id.name} reconciled with payment {payment.name}",
                    message_type='notification'
                )

                # Refresh invoice to get updated payment_state
                self.move_id.invalidate_recordset(
                    ['payment_state', 'amount_residual'])

                # Check if invoice is fully paid or partial
                if self.move_id.payment_state == 'paid':
                    # Invoice fully paid - close this transaction
                    self.write({'state': 'settlement'})
                    _logger.info(
                        f"[PAYMENT] Invoice {self.move_id.name} FULLY PAID - transaction closed")

                    # Send bus notification
                    self._send_realtime_update_notification('invoice_paid', {
                        'invoice_id': self.move_id.id,
                        'invoice_name': self.move_id.name,
                        'partner_id': self.partner_id.id,
                        'payment_id': payment.id,
                        'amount': payment_amount,
                        'is_fully_paid': True,
                    })
                else:
                    # Invoice partially paid - keep transaction pending, update amount
                    new_residual = self.move_id.amount_residual
                    self.write({
                        'gross_amount': new_residual,  # Update to remaining amount
                        # state stays 'pending' so VA remains visible
                    })
                    _logger.info(f"[PAYMENT] Invoice {self.move_id.name} PARTIAL - "
                                 f"remaining: Rp {new_residual:,.0f}, VA stays active")

                    # Post informative message
                    remaining_formatted = f"Rp{new_residual:,.0f}".replace(
                        ',', '.')
                    self.message_post(
                        body=f"💳 <b>Pembayaran Sebagian Diterima</b><br/>"
                        f"• Dibayar: Rp{payment_amount:,.0f}<br/>"
                        f"• Sisa tagihan: {remaining_formatted}<br/>"
                        f"• VA masih aktif untuk pelunasan",
                        message_type='notification'
                    )

                    # Send bus notification for partial payment
                    self._send_realtime_update_notification('invoice_partial', {
                        'invoice_id': self.move_id.id,
                        'invoice_name': self.move_id.name,
                        'partner_id': self.partner_id.id,
                        'payment_id': payment.id,
                        'amount': payment_amount,
                        'remaining': new_residual,
                        'is_fully_paid': False,
                    })

                    # Try to update billing at BSI with new remaining amount
                    self._update_billing_after_partial_payment(new_residual)

                # Handle overpayment - credit excess to student wallet
                if excess_amount > 0:
                    self._credit_overpayment_to_wallet(excess_amount)

        except Exception as e:
            _logger.error(
                f"Error reconciling invoice {self.move_id.name}: {e}")
            self.message_post(
                body=f"Error reconciling invoice: {str(e)}",
                message_type='notification'
            )

    def _credit_overpayment_to_wallet(self, amount):
        """
        Credit overpayment amount to student's wallet (uang saku).

        This handles the case where parent pays more than the invoice amount.
        The excess is automatically credited to the student's balance.

        Note: This does NOT require the student to have a VA account.
        VA is only needed for self-service top-up, not for receiving credits.

        Args:
            amount: The excess amount to credit to wallet
        """
        self.ensure_one()

        if amount <= 0:
            return

        # Find siswa from partner
        siswa = self.siswa_id
        if not siswa:
            # Try to find siswa by partner_id
            siswa = self.env['cdn.siswa'].search([
                ('partner_id', '=', self.partner_id.id)
            ], limit=1)

        if not siswa:
            _logger.warning(f"[OVERPAYMENT] No siswa found for partner {self.partner_id.name}. "
                            f"Excess amount Rp {amount:,.0f} cannot be credited to wallet.")
            self.message_post(
                body=f"⚠️ Kelebihan pembayaran Rp {amount:,.0f} tidak dapat dikreditkan ke saldo "
                f"karena data santri tidak ditemukan.",
                message_type='notification'
            )
            return

        try:
            # Format amounts for logging/messages
            amount_formatted = f"Rp{amount:,.0f}".replace(',', '.')

            # Create uang saku entry (NO VA REQUIRED!)
            uang_saku = self.env['cdn.uang_saku'].sudo().create({
                # cdn.uang_saku uses partner_id for siswa_id field
                'siswa_id': siswa.partner_id.id,
                'jns_transaksi': 'masuk',
                'amount_in': amount,
                'keterangan': f"Kelebihan pembayaran tagihan {self.move_id.name} - {self.name}",
                'tgl_transaksi': self.settlement_time or fields.Datetime.now(),
            })

            # Confirm the transaction to update balance
            uang_saku.action_confirm()

            _logger.info(
                f"[OVERPAYMENT] Credited {amount_formatted} to {siswa.name}'s wallet")

            self.message_post(
                body=f"💰 <b>Kelebihan Pembayaran</b><br/>"
                f"Nominal lebih: {amount_formatted}<br/>"
                f"Dikreditkan ke saldo: {siswa.name}",
                message_type='notification'
            )

            # Send real-time notification for overpayment
            self._send_realtime_update_notification('overpayment_credited', {
                'invoice_id': self.move_id.id,
                'invoice_name': self.move_id.name,
                'siswa_id': siswa.id,
                'siswa_name': siswa.name,
                'partner_id': self.partner_id.id,
                'excess_amount': amount,
                'uang_saku_id': uang_saku.id,
            })

        except Exception as e:
            _logger.error(
                f"[OVERPAYMENT] Error crediting excess to wallet: {e}")
            self.message_post(
                body=f"❌ Error mengkreditkan kelebihan pembayaran ke saldo: {str(e)}",
                message_type='notification'
            )

    def _update_billing_after_partial_payment(self, new_amount):
        """
        Update billing at BSI with new remaining amount after partial payment.

        This ensures the parent can use the SAME VA number to pay the remaining
        balance without getting a new VA.

        NOTE: This is executed in a deferred manner (after commit) to avoid
        circular call timeout when webhook triggers this during payment processing.

        Args:
            new_amount: The new remaining amount to update in BSI
        """
        self.ensure_one()

        if not self.move_id:
            return

        # Skip if we're inside a webhook context to avoid circular call
        if self.env.context.get('from_webhook'):
            _logger.info(f"[PARTIAL PAYMENT] Skipping BSI update - inside webhook context. "
                         f"Local amount updated to Rp {new_amount:,.0f}")
            return

        # Schedule the update after commit to avoid blocking the webhook response
        transaction_id = self.id
        env = self.env

        def do_update():
            try:
                # Re-fetch record in new cursor context
                with env.registry.cursor() as new_cr:
                    new_env = env(cr=new_cr)
                    transaction = new_env['smart.billing.transaction'].browse(
                        transaction_id)
                    if not transaction.exists():
                        return

                    provider = transaction._get_billing_provider()
                    customer = {
                        'first_name': transaction.partner_id.name or '',
                        'email': transaction.partner_id.email or '',
                        'phone': transaction.partner_id.phone or transaction.partner_id.mobile or '',
                    }

                    result = provider.update_billing(
                        order_id=transaction.name,
                        amount=new_amount,
                        customer_details=customer
                    )

                    if result.get('success'):
                        _logger.info(
                            f"[PARTIAL PAYMENT] Billing updated at BSI: {transaction.name} -> Rp {new_amount:,.0f}")
                    else:
                        _logger.warning(
                            f"[PARTIAL PAYMENT] Failed to update billing at BSI: {result.get('message')}")

                    new_cr.commit()
            except Exception as e:
                _logger.warning(
                    f"[PARTIAL PAYMENT] Could not update billing at BSI: {e}")

        # Execute after current transaction commits
        self.env.cr.postcommit.add(do_update)

    def _get_billing_provider(self):
        """Get the currently configured billing provider"""
        provider_code = self.env['ir.config_parameter'].sudo().get_param(
            'smart_billing.provider', 'dummy'
        )

        provider_map = {
            'dummy': 'smart.billing.provider.dummy',
            'bsi': 'smart.billing.provider.bsi',
            'tki': 'smart.billing.provider.tki',
        }

        model_name = provider_map.get(
            provider_code, 'smart.billing.provider.dummy')
        return self.env[model_name]

    def _create_uang_saku_topup(self):
        """Create uang saku transaction for top-up"""
        self.ensure_one()

        if not self.siswa_id:
            _logger.warning(f"No siswa found for top-up {self.name}")
            return

        if self.uang_saku_id:
            _logger.info(f"Uang saku already created for {self.name}")
            return

        try:
            # Create uang saku transaction (kredit/masuk)
            # Field names in cdn.uang_saku: jns_transaksi ('masuk'), amount_in, tgl_transaksi
            uang_saku = self.env['cdn.uang_saku'].sudo().create({
                # cdn.uang_saku uses partner_id for siswa_id field
                'siswa_id': self.siswa_id.partner_id.id,
                'jns_transaksi': 'masuk',
                'amount_in': self.gross_amount,
                'keterangan': f"Top-up via Smart Billing ({self.provider.upper()}) - {self.name}",
                'tgl_transaksi': self.settlement_time or fields.Datetime.now(),
            })

            # Confirm the transaction to update balance
            uang_saku.action_confirm()

            self.uang_saku_id = uang_saku.id

            _logger.info(
                f"Uang saku created and confirmed for {self.siswa_id.name}: Rp {self.gross_amount:,.0f}")
            self.message_post(
                body=f"Top-up saldo berhasil dan dikonfirmasi: Rp {self.gross_amount:,.0f}",
                message_type='notification'
            )

            # Send bus notification to trigger real-time update in browser
            self._send_realtime_update_notification('topup_completed', {
                'siswa_id': self.siswa_id.id,
                'siswa_name': self.siswa_id.name,
                'partner_id': self.partner_id.id,
                'amount': self.gross_amount,
                'uang_saku_id': uang_saku.id,
            })

        except Exception as e:
            _logger.error(
                f"Error creating/confirming uang saku for {self.name}: {e}")
            self.message_post(
                body=f"Error creating uang saku: {str(e)}",
                message_type='notification'
            )

    def _send_realtime_update_notification(self, event_type, data):
        """
        Send bus notification to trigger real-time update in browser.
        This allows the form view to update automatically without manual refresh.

        Args:
            event_type: Type of event ('invoice_paid', 'topup_completed')
            data: Dictionary with event data
        """
        self.ensure_one()

        try:
            # Get all users who might be viewing related records
            users_to_notify = self.env['res.users'].sudo().search([
                ('active', '=', True),
                ('share', '=', False),  # Only internal users
            ])

            # Add record info to data
            notification_data = {
                'type': event_type,
                'model': self._name,
                'res_id': self.id,
                'transaction_name': self.name,
                **data,
            }

            # Send notification to all internal users via bus
            for user in users_to_notify:
                self.env['bus.bus']._sendone(
                    user.partner_id,
                    'smart_billing_update',
                    notification_data
                )

            # Also send a simple_notification for visual feedback
            if event_type == 'invoice_paid' and data.get('invoice_id'):
                amount_formatted = f"Rp{data.get('amount', 0):,.0f}".replace(
                    ',', '.')
                self.env['bus.bus']._sendmany([
                    (user.partner_id, 'simple_notification', {
                        'title': '💳 Pembayaran Diterima',
                        'message': f"Tagihan {data.get('invoice_name', '')} telah dibayar ({amount_formatted})",
                        'type': 'success',
                        'sticky': False,
                    }) for user in users_to_notify
                ])
            elif event_type == 'topup_completed':
                amount_formatted = f"Rp{data.get('amount', 0):,.0f}".replace(
                    ',', '.')
                self.env['bus.bus']._sendmany([
                    (user.partner_id, 'simple_notification', {
                        'title': '💰 Top-up Berhasil',
                        'message': f"Top-up saldo {data.get('siswa_name', '')} sebesar {amount_formatted}",
                        'type': 'success',
                        'sticky': False,
                    }) for user in users_to_notify
                ])
            elif event_type == 'overpayment_credited':
                amount_formatted = f"Rp{data.get('excess_amount', 0):,.0f}".replace(
                    ',', '.')
                self.env['bus.bus']._sendmany([
                    (user.partner_id, 'simple_notification', {
                        'title': '💵 Kelebihan Pembayaran',
                        'message': f"Kelebihan {amount_formatted} dikreditkan ke saldo {data.get('siswa_name', '')}",
                        'type': 'info',
                        'sticky': True,
                    }) for user in users_to_notify
                ])
            elif event_type == 'invoice_partial':
                amount_formatted = f"Rp{data.get('amount', 0):,.0f}".replace(
                    ',', '.')
                remaining_formatted = f"Rp{data.get('remaining', 0):,.0f}".replace(
                    ',', '.')
                self.env['bus.bus']._sendmany([
                    (user.partner_id, 'simple_notification', {
                        'title': '💳 Pembayaran Sebagian',
                        'message': f"Tagihan {data.get('invoice_name', '')} dibayar {amount_formatted}, sisa: {remaining_formatted}",
                        'type': 'warning',
                        'sticky': True,
                    }) for user in users_to_notify
                ])

            _logger.info(
                f"[REALTIME] Sent {event_type} notification for {self.name} to {len(users_to_notify)} users")

        except Exception as e:
            _logger.error(
                f"[REALTIME] Error sending notification for {self.name}: {e}")

    def _send_payment_notification(self):
        """Send notification to parent about successful payment"""
        self.ensure_one()

        if self.notification_sent:
            return

        try:
            # Get parent email
            email = None
            if self.siswa_id and self.siswa_id.orangtua_id:
                email = self.siswa_id.orangtua_id.partner_id.email

            if not email:
                email = self.partner_id.email

            if not email:
                _logger.warning(f"No email found for notification {self.name}")
                return

            # Prepare notification content
            amount_formatted = f"Rp{self.gross_amount:,.0f}".replace(',', '.')

            if self.transaction_type == 'va_tagihan':
                subject = f"Pembayaran Tagihan Berhasil - {self.siswa_id.name if self.siswa_id else self.partner_id.name}"
                body = f"""
                <p>Assalamualaikum,</p>
                <p>Pembayaran tagihan telah berhasil diterima:</p>
                <ul>
                    <li><strong>Santri:</strong> {self.siswa_id.name if self.siswa_id else self.partner_id.name}</li>
                    <li><strong>Nominal:</strong> {amount_formatted}</li>
                    <li><strong>Invoice:</strong> {self.move_id.name if self.move_id else '-'}</li>
                    <li><strong>VA:</strong> {self.va_number or '-'}</li>
                    <li><strong>Waktu:</strong> {self.settlement_time or fields.Datetime.now()}</li>
                </ul>
                <p>Terima kasih.</p>
                """
            else:
                subject = f"Top-up Saldo Berhasil - {self.siswa_id.name if self.siswa_id else self.partner_id.name}"
                body = f"""
                <p>Assalamualaikum,</p>
                <p>Top-up saldo anak Anda telah berhasil:</p>
                <ul>
                    <li><strong>Santri:</strong> {self.siswa_id.name if self.siswa_id else self.partner_id.name}</li>
                    <li><strong>Nominal Top-up:</strong> {amount_formatted}</li>
                    <li><strong>VA:</strong> {self.va_number or '-'}</li>
                    <li><strong>Waktu:</strong> {self.settlement_time or fields.Datetime.now()}</li>
                </ul>
                <p>Saldo uang saku anak Anda telah bertambah.</p>
                <p>Terima kasih.</p>
                """

            # Send email
            self.message_post(
                body=body,
                subject=subject,
                message_type='email',
                partner_ids=[(4, self.partner_id.id)
                             ] if self.partner_id else [],
            )

            self.notification_sent = True
            _logger.info(f"Payment notification sent for {self.name}")

        except Exception as e:
            _logger.error(f"Error sending notification for {self.name}: {e}")

    def action_cancel(self):
        """Cancel the transaction"""
        self.ensure_one()

        if self.state not in ['pending', 'active']:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Cannot Cancel',
                    'message': 'Only pending or active transactions can be cancelled',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        provider = self._get_provider()
        try:
            result = provider.cancel_transaction(self.name)
            if result.get('success'):
                self.state = 'cancelled'
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Transaction Cancelled',
                        'message': 'Transaction has been cancelled',
                        'type': 'success',
                        'sticky': False,
                    }
                }
        except Exception as e:
            self.state = 'cancelled'  # Still mark as cancelled locally
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Cancelled Locally',
                    'message': f'Marked as cancelled locally. Provider error: {str(e)}',
                    'type': 'warning',
                    'sticky': False,
                }
            }

    def action_simulate_payment(self):
        """
        Simulate a payment for testing purposes (Dummy Provider only).
        This will mark the transaction as settled and trigger all 
        downstream actions like invoice reconciliation.
        """
        self.ensure_one()

        if self.provider != 'dummy':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Hanya untuk Testing',
                    'message': 'Simulasi pembayaran hanya tersedia untuk Dummy Provider',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        if self.state != 'pending':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Transaksi Tidak Pending',
                    'message': f'Transaksi sudah dalam status: {self.state}',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        _logger.info(
            f"[DUMMY] Simulating payment for transaction: {self.name}")

        # Update transaction status
        self.write({
            'state': 'settlement',
            'settlement_time': fields.Datetime.now(),
            'provider_status': 'settlement',
            'provider_response': json.dumps({
                'simulated': True,
                'status': 'settlement',
                'message': 'Payment simulated for testing',
                'settlement_time': str(fields.Datetime.now()),
            }, indent=2),
        })

        # Trigger downstream actions (reconcile invoice or topup saldo)
        self._on_payment_settled()

        # Post message
        amount_formatted = f"Rp{self.gross_amount:,.0f}".replace(',', '.')
        self.message_post(
            body=f"""
            <p><strong>✅ Pembayaran Simulasi Berhasil</strong></p>
            <ul>
                <li><strong>Nominal:</strong> {amount_formatted}</li>
                <li><strong>Waktu:</strong> {fields.Datetime.now()}</li>
            </ul>
            <p><em>Ini adalah simulasi untuk testing. Pada production, pembayaran akan diterima dari BSI via webhook.</em></p>
            """,
            subject="Payment Simulation",
            message_type='notification'
        )

        _logger.info(f"[DUMMY] Payment simulation completed for {self.name}")

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'smart.billing.transaction',
            'res_id': self.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'current',
        }

    @api.model
    def process_bsi_payment_xmlrpc(self, customer_no, amount, payment_request_id=None, trx_datetime=None):
        """
        Process BSI payment via XML-RPC.

        This method is called externally (from FastAPI simulator or BSI via proxy)
        to process a payment notification without needing HTTP webhook routes.

        Args:
            customer_no: The customer number (could be NIS, VA number suffix, or transaction name part)
            amount: Payment amount
            payment_request_id: Optional payment reference ID
            trx_datetime: Optional transaction datetime string

        Returns:
            dict with success status and message
        """
        _logger.info(
            f"[BSI XMLRPC] Processing payment for customer_no: {customer_no}, amount: {amount}")

        try:
            # Try to find transaction by customer_no in various fields
            transaction = self.search([
                '|', '|', '|',
                ('name', 'ilike', customer_no),
                ('va_number', 'ilike', customer_no),
                ('partner_id.nis', '=', customer_no),
                ('partner_id.nis', '=', customer_no.lstrip('0')),
            ], limit=1, order='create_date desc')

            if not transaction:
                # Try finding by siswa NIS
                siswa = self.env['cdn.siswa'].search([
                    '|',
                    ('nis', '=', customer_no),
                    ('nis', '=', customer_no.lstrip('0'))
                ], limit=1)

                if siswa:
                    # Find pending transaction for this siswa
                    transaction = self.search([
                        ('partner_id', '=', siswa.partner_id.id),
                        ('state', '=', 'pending'),
                    ], limit=1, order='create_date desc')

            if not transaction:
                _logger.warning(
                    f"[BSI XMLRPC] No transaction found for customer_no: {customer_no}")
                return {
                    'success': False,
                    'message': f'Transaction not found for customer_no: {customer_no}',
                    'responseCode': '4042412'
                }

            if transaction.state == 'settlement':
                _logger.info(
                    f"[BSI XMLRPC] Transaction {transaction.name} already settled")
                return {
                    'success': True,
                    'message': f'Transaction {transaction.name} already settled',
                    'transaction_name': transaction.name,
                    'responseCode': '2002500'
                }

            if transaction.state != 'pending':
                return {
                    'success': False,
                    'message': f'Transaction {transaction.name} is in {transaction.state} state',
                    'responseCode': '4002500'
                }

            # Update transaction
            from odoo import fields as odoo_fields
            transaction.write({
                'state': 'settlement',
                'settlement_time': odoo_fields.Datetime.now(),
                'gross_amount': float(amount) if amount else transaction.gross_amount,
                'provider_status': 'settlement',
                'provider_transaction_id': payment_request_id or f"XMLRPC-{customer_no}",
                'provider_response': json.dumps({
                    'source': 'xmlrpc',
                    'customer_no': customer_no,
                    'amount': amount,
                    'payment_request_id': payment_request_id,
                    'trx_datetime': trx_datetime,
                    'processed_at': str(odoo_fields.Datetime.now()),
                }, indent=2),
            })

            # Trigger downstream actions
            transaction._on_payment_settled()

            # Post message
            amount_formatted = f"Rp{transaction.gross_amount:,.0f}".replace(
                ',', '.')
            transaction.message_post(
                body=f"""
                <p><strong>✅ Pembayaran BSI Berhasil</strong></p>
                <ul>
                    <li><strong>Customer No:</strong> {customer_no}</li>
                    <li><strong>Nominal:</strong> {amount_formatted}</li>
                    <li><strong>Payment ID:</strong> {payment_request_id or '-'}</li>
                </ul>
                """,
                subject="BSI Payment Received",
                message_type='notification'
            )

            _logger.info(
                f"[BSI XMLRPC] Payment processed for {transaction.name}")

            return {
                'success': True,
                'message': 'Payment processed successfully',
                'transaction_name': transaction.name,
                'customer_name': transaction.partner_id.name if transaction.partner_id else '',
                'amount': transaction.gross_amount,
                'responseCode': '2002500'
            }

        except Exception as e:
            _logger.error(f"[BSI XMLRPC] Error processing payment: {e}")
            import traceback
            _logger.error(traceback.format_exc())
            return {
                'success': False,
                'message': str(e),
                'responseCode': '5002500'
            }
