# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    """
    Extend account.move (Invoice) to add Smart Billing BSI integration.
    """
    _inherit = 'account.move'

    # Smart Billing transactions
    smart_billing_transaction_ids = fields.One2many(
        'smart.billing.transaction',
        'move_id',
        string='Transaksi Smart Billing'
    )

    # BSI Billing status
    bsi_billing_sent = fields.Boolean(
        string='BSI Billing Sent',
        compute='_compute_bsi_billing_status',
        store=False,
        help='True jika sudah ada billing aktif di BSI'
    )
    bsi_billing_order_id = fields.Char(
        string='BSI Order ID',
        compute='_compute_bsi_billing_status',
        store=False
    )

    # Computed VA fields
    smart_billing_va_number = fields.Char(
        string='Virtual Account',
        compute='_compute_smart_billing_va',
        store=False
    )
    smart_billing_va_bank = fields.Char(
        string='VA Bank',
        compute='_compute_smart_billing_va',
        store=False
    )
    smart_billing_payment_url = fields.Char(
        string='Payment Link',
        compute='_compute_smart_billing_payment_url',
        store=False
    )
    has_pending_smart_billing = fields.Boolean(
        string='Has Pending Smart Billing',
        compute='_compute_has_pending_smart_billing'
    )

    @api.depends('smart_billing_transaction_ids', 'smart_billing_transaction_ids.state')
    def _compute_bsi_billing_status(self):
        for move in self:
            pending_va = move.smart_billing_transaction_ids.filtered(
                lambda t: t.transaction_type == 'va_tagihan' and t.state == 'pending'
            ).sorted(key=lambda t: t.create_date, reverse=True)[:1]

            move.bsi_billing_sent = bool(pending_va)
            move.bsi_billing_order_id = pending_va.name if pending_va else False

    @api.depends('smart_billing_transaction_ids', 'smart_billing_transaction_ids.state', 'smart_billing_transaction_ids.va_number')
    def _compute_smart_billing_va(self):
        for move in self:
            va_transaction = move.smart_billing_transaction_ids.filtered(
                lambda t: t.transaction_type == 'va_tagihan' and t.state == 'pending'
            ).sorted(key=lambda t: t.create_date, reverse=True)[:1]

            if va_transaction:
                move.smart_billing_va_number = va_transaction.va_number
                move.smart_billing_va_bank = va_transaction.va_bank
            else:
                move.smart_billing_va_number = False
                move.smart_billing_va_bank = False

    @api.depends('smart_billing_transaction_ids', 'smart_billing_transaction_ids.state', 'smart_billing_transaction_ids.payment_url')
    def _compute_smart_billing_payment_url(self):
        for move in self:
            payment_link = move.smart_billing_transaction_ids.filtered(
                lambda t: t.transaction_type == 'payment_link' and t.state == 'pending' and t.payment_url
            ).sorted(key=lambda t: t.create_date, reverse=True)[:1]

            move.smart_billing_payment_url = payment_link.payment_url if payment_link else False

    @api.depends('smart_billing_transaction_ids', 'smart_billing_transaction_ids.state')
    def _compute_has_pending_smart_billing(self):
        for move in self:
            move.has_pending_smart_billing = bool(
                move.smart_billing_transaction_ids.filtered(
                    lambda t: t.state == 'pending')
            )

    def _prepare_customer_details(self):
        """Prepare customer details for Smart Billing"""
        self.ensure_one()
        partner = self.partner_id
        siswa = self.siswa_id

        email = partner.email or ''
        if siswa and siswa.orangtua_id and siswa.orangtua_id.partner_id.email:
            email = siswa.orangtua_id.partner_id.email

        return {
            "first_name": partner.name or '',
            "email": email or 'no-email@pesantren.id',
            "phone": partner.phone or partner.mobile or '',
        }

    def _prepare_item_details(self):
        """Prepare item details for payment link"""
        self.ensure_one()
        items = []

        for line in self.invoice_line_ids:
            items.append({
                "id": str(line.id),
                "name": line.name[:50] if line.name else "Tagihan",
                "price": int(line.price_unit),
                "quantity": int(line.quantity),
            })

        return items

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

    # =========================================================================
    # BSI BILLING ACTIONS
    # =========================================================================

    def action_send_bsi_billing(self):
        """
        Kirim Billing ke BSI - Create VA for this invoice in BSI Smart Billing.
        Setelah ini, tagihan akan muncul di BSI sandbox/production.
        """
        self.ensure_one()

        if self.state != 'posted':
            raise UserError(
                "Invoice harus dalam status 'Posted' untuk kirim billing.")

        if self.payment_state == 'paid':
            raise UserError("Invoice sudah lunas.")

        if not self.siswa_id:
            raise UserError("Invoice harus memiliki data Santri.")

        # Check for existing pending VA
        existing_va = self.smart_billing_transaction_ids.filtered(
            lambda t: t.transaction_type == 'va_tagihan' and t.state == 'pending'
        )
        if existing_va:
            raise UserError(
                f"Billing sudah ada di BSI.\n\n"
                f"Order ID: {existing_va[0].name}\n"
                f"VA: {existing_va[0].va_number}\n\n"
                "Gunakan 'Update Billing BSI' untuk mengubah atau 'Hapus Billing BSI' untuk menghapus."
            )

        # Get provider
        provider = self._get_billing_provider()

        # Generate unique order ID using invoice name
        invoice_ref = self.name.replace('/', '').replace(' ', '')[-12:]
        order_id = f"TAG-{invoice_ref}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Get customer details
        customer = self._prepare_customer_details()

        try:
            result = provider.create_va_transaction(
                order_id=order_id,
                amount=self.amount_residual,
                customer_details=customer
            )

            if result.get('success'):
                # Create transaction record
                transaction = self.env['smart.billing.transaction'].create({
                    'name': order_id,
                    'provider': provider.get_provider_code(),
                    'transaction_type': 'va_tagihan',
                    'state': 'pending',
                    'move_id': self.id,
                    'partner_id': self.partner_id.id,
                    'va_number': result['va_number'],
                    'va_bank': result['va_bank'],
                    'gross_amount': self.amount_residual,
                    'transaction_time': fields.Datetime.now(),
                    'expiry_time': result.get('expiry_time'),
                    'provider_transaction_id': result.get('transaction_id'),
                    'provider_response': str(result.get('raw_response', {})),
                })

                # Post message to invoice
                amount_formatted = f"Rp{self.amount_residual:,.0f}".replace(
                    ',', '.')
                expiry_str = result.get('expiry_time').strftime(
                    '%d/%m/%Y %H:%M') if result.get('expiry_time') else '-'

                self.message_post(
                    body=f"""
                    <p>🏦 <strong>Billing Berhasil Dikirim ke BSI</strong></p>
                    <ul>
                        <li><strong>Order ID:</strong> {order_id}</li>
                        <li><strong>Bank:</strong> {result['va_bank']}</li>
                        <li><strong>No. VA:</strong> {result['va_number']}</li>
                        <li><strong>Nominal:</strong> {amount_formatted}</li>
                        <li><strong>Berlaku hingga:</strong> {expiry_str}</li>
                    </ul>
                    <p><em>Billing sudah tampil di BSI Smart Billing. Gunakan menu Flagging di sandbox untuk test pembayaran.</em></p>
                    """,
                    subject="BSI Billing Sent",
                    message_type='notification'
                )

                # Reload form to update buttons
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.move',
                    'res_id': self.id,
                    'view_mode': 'form',
                    'view_type': 'form',
                    'target': 'current',
                }
            else:
                raise UserError(
                    f"Gagal kirim billing: {result.get('message', 'Unknown error')}")
        except Exception as e:
            _logger.error(
                f"Error sending BSI billing for invoice {self.name}: {e}")
            raise UserError(f"Gagal kirim Billing ke BSI: {str(e)}")

    def action_send_bsi_billing_bulk(self):
        """
        Kirim Billing ke BSI secara massal untuk multiple invoices.
        Dipanggil dari server action pada list view.
        """
        if not self:
            raise UserError("Tidak ada invoice yang dipilih.")

        success_count = 0
        skip_count = 0
        error_count = 0
        messages = []

        provider = None

        for invoice in self:
            try:
                # Skip invoices that shouldn't be processed
                if invoice.state != 'posted':
                    skip_count += 1
                    messages.append(
                        f"⏭️ {invoice.name}: Dilewati (belum posted)")
                    continue

                if invoice.payment_state == 'paid':
                    skip_count += 1
                    messages.append(
                        f"⏭️ {invoice.name}: Dilewati (sudah lunas)")
                    continue

                if not invoice.siswa_id:
                    skip_count += 1
                    messages.append(
                        f"⏭️ {invoice.name}: Dilewati (tidak ada data santri)")
                    continue

                # Check for existing pending VA
                existing_va = invoice.smart_billing_transaction_ids.filtered(
                    lambda t: t.transaction_type == 'va_tagihan' and t.state == 'pending'
                )
                if existing_va:
                    skip_count += 1
                    messages.append(
                        f"⏭️ {invoice.name}: Dilewati (sudah ada VA: {existing_va[0].va_number})")
                    continue

                # Get provider (lazy init)
                if not provider:
                    provider = invoice._get_billing_provider()

                # Generate unique order ID
                invoice_ref = invoice.name.replace(
                    '/', '').replace(' ', '')[-12:]
                order_id = f"TAG-{invoice_ref}-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:17]}"

                # Get customer details
                customer = invoice._prepare_customer_details()

                # Send to BSI
                result = provider.create_va_transaction(
                    order_id=order_id,
                    amount=invoice.amount_residual,
                    customer_details=customer
                )

                if result.get('success'):
                    # Create transaction record
                    self.env['smart.billing.transaction'].create({
                        'name': order_id,
                        'provider': provider.get_provider_code(),
                        'transaction_type': 'va_tagihan',
                        'state': 'pending',
                        'move_id': invoice.id,
                        'partner_id': invoice.partner_id.id,
                        'va_number': result['va_number'],
                        'va_bank': result['va_bank'],
                        'gross_amount': invoice.amount_residual,
                        'transaction_time': fields.Datetime.now(),
                        'expiry_time': result.get('expiry_time'),
                        'provider_transaction_id': result.get('transaction_id'),
                        'provider_response': str(result.get('raw_response', {})),
                    })

                    # Force invalidation of the One2many field to ensure compute fields see the new record
                    invoice.invalidate_recordset(
                        ['smart_billing_transaction_ids', 'bsi_billing_sent', 'smart_billing_va_number'])

                    success_count += 1
                    amount_formatted = f"Rp{invoice.amount_residual:,.0f}".replace(
                        ',', '.')
                    messages.append(
                        f"✅ {invoice.name}: Berhasil (VA: {result['va_number']}, {amount_formatted})")

                    # Post message to invoice
                    invoice.message_post(
                        body=f"🏦 <b>Billing Dikirim (Bulk)</b><br/>VA: {result['va_number']}<br/>Nominal: {amount_formatted}",
                        message_type='notification'
                    )
                else:
                    error_count += 1
                    messages.append(
                        f"❌ {invoice.name}: Gagal - {result.get('message', 'Unknown error')}")

            except Exception as e:
                error_count += 1
                messages.append(f"❌ {invoice.name}: Error - {str(e)}")
                _logger.error(
                    f"Bulk BSI billing error for {invoice.name}: {e}")

        # Determine notification type
        if error_count > 0:
            notif_type = 'danger'
        elif skip_count > 0:
            notif_type = 'warning'
        else:
            notif_type = 'success'

        # Create summary message
        summary_msg = f"✅ Berhasil: {success_count} | ⏭️ Dilewati: {skip_count} | ❌ Gagal: {error_count}"

        # Log detailed result
        _logger.info(
            f"[BSI BULK] Completed - Success: {success_count}, Skip: {skip_count}, Error: {error_count}")
        for msg in messages:
            _logger.info(f"[BSI BULK] {msg}")

        # Build result summary
        summary = (
            f"📊 Kirim Billing BSI Massal Selesai\n\n"
            f"✅ Berhasil: {success_count}\n"
            f"⏭️ Dilewati: {skip_count}\n"
            f"❌ Gagal: {error_count}"
        )

        if messages:
            summary += "\n\nDetail:\n" + "\n".join(messages[-15:])

        # Explicitly commit to ensure transaction is saved even if UI has issues
        self.env.cr.commit()

        # If there are errors, show them as a warning dialog (so user sees what happened)
        # This is safer than fancy notifications which might fail
        if error_count > 0:
            raise UserError(summary)

        # No return = implicit None
        # In server action XML, we will remove 'action = ' assignment
        # This prevents client-side errors and relies on standard behavior

    def action_update_bsi_billing(self):
        """
        Update Billing di BSI - Update amount atau expiry date.
        """
        self.ensure_one()

        if not self.bsi_billing_sent:
            raise UserError(
                "Belum ada billing di BSI. Silakan kirim billing terlebih dahulu.")

        # Get pending transaction
        pending_va = self.smart_billing_transaction_ids.filtered(
            lambda t: t.transaction_type == 'va_tagihan' and t.state == 'pending'
        ).sorted(key=lambda t: t.create_date, reverse=True)[:1]

        if not pending_va:
            raise UserError("Tidak ada billing pending.")

        # Get provider
        provider = self._get_billing_provider()

        # Get customer details
        customer = self._prepare_customer_details()

        try:
            result = provider.update_billing(
                order_id=pending_va.name,
                amount=self.amount_residual,
                customer_details=customer
            )

            if result.get('success'):
                # Update transaction
                pending_va.write({
                    'gross_amount': self.amount_residual,
                    'provider_response': str(result.get('raw_response', {})),
                })

                amount_formatted = f"Rp{self.amount_residual:,.0f}".replace(
                    ',', '.')

                self.message_post(
                    body=f"""
                    <p>🔄 <strong>Billing BSI Diupdate</strong></p>
                    <ul>
                        <li><strong>Order ID:</strong> {pending_va.name}</li>
                        <li><strong>Nominal Baru:</strong> {amount_formatted}</li>
                    </ul>
                    """,
                    subject="BSI Billing Updated",
                    message_type='notification'
                )

                # Reload form to update view
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.move',
                    'res_id': self.id,
                    'view_mode': 'form',
                    'view_type': 'form',
                    'target': 'current',
                }
            else:
                raise UserError(
                    f"Gagal update billing: {result.get('message', 'Unknown error')}")

        except Exception as e:
            _logger.error(
                f"Error updating BSI billing for invoice {self.name}: {e}")
            raise UserError(f"Gagal update Billing BSI: {str(e)}")

    def action_delete_bsi_billing(self):
        """
        Hapus Billing di BSI - Remove billing from BSI system.
        """
        self.ensure_one()

        if not self.bsi_billing_sent:
            raise UserError("Belum ada billing di BSI.")

        # Get pending transaction
        pending_va = self.smart_billing_transaction_ids.filtered(
            lambda t: t.transaction_type == 'va_tagihan' and t.state == 'pending'
        ).sorted(key=lambda t: t.create_date, reverse=True)[:1]

        if not pending_va:
            raise UserError("Tidak ada billing pending.")

        # Get provider
        provider = self._get_billing_provider()

        try:
            result = provider.cancel_transaction(pending_va.name)

            if result.get('success'):
                # Update transaction status
                pending_va.write({
                    'state': 'cancelled',
                    'provider_response': str(result.get('raw_response', {})),
                })

                self.message_post(
                    body=f"""
                    <p>❌ <strong>Billing BSI Dihapus</strong></p>
                    <ul>
                        <li><strong>Order ID:</strong> {pending_va.name}</li>
                    </ul>
                    <p><em>Billing sudah dihapus dari BSI. Anda bisa kirim billing baru.</em></p>
                    """,
                    subject="BSI Billing Deleted",
                    message_type='notification'
                )

                # Reload form to update buttons
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.move',
                    'res_id': self.id,
                    'view_mode': 'form',
                    'view_type': 'form',
                    'target': 'current',
                }
            else:
                raise UserError(
                    f"Gagal hapus billing: {result.get('message', 'Unknown error')}")

        except Exception as e:
            _logger.error(
                f"Error deleting BSI billing for invoice {self.name}: {e}")
            raise UserError(f"Gagal hapus Billing BSI: {str(e)}")

    def action_send_va_whatsapp(self):
        """Open WhatsApp with VA information"""
        self.ensure_one()

        if not self.smart_billing_va_number:
            raise UserError(
                "Belum ada VA. Silakan kirim billing terlebih dahulu.")

        # Get parent phone
        phone = ''
        if self.siswa_id and self.siswa_id.orangtua_id:
            orangtua = self.siswa_id.orangtua_id
            phone = orangtua.mobile or orangtua.phone or ''

        if not phone:
            phone = self.partner_id.mobile or self.partner_id.phone or ''

        if not phone:
            raise UserError("Nomor telepon orang tua tidak ditemukan.")

        # Clean phone number
        phone = phone.replace(' ', '').replace('-', '').replace('+', '')
        if phone.startswith('0'):
            phone = '62' + phone[1:]
        elif not phone.startswith('62'):
            phone = '62' + phone

        # Prepare message
        amount_formatted = f"Rp{self.amount_residual:,.0f}".replace(',', '.')
        company_name = self.env.company.name or 'Pesantren'

        message = f"""Assalamu'alaikum Wr. Wb.

Bapak/Ibu Orang Tua/Wali dari *{self.siswa_id.name if self.siswa_id else self.partner_id.name}*,

Berikut tagihan yang perlu dibayarkan:

*Invoice:* {self.name}
*Nominal:* {amount_formatted}

*Cara Pembayaran:*
1. Buka aplikasi BSI Mobile / M-Banking
2. Pilih menu Transfer > Virtual Account
3. Masukkan nomor VA: *{self.smart_billing_va_number}*
4. Konfirmasi dan selesaikan pembayaran

*BANK:* {self.smart_billing_va_bank}
*NO. VA:* {self.smart_billing_va_number}

Jazakumullah khairan katsira.
_Tim Keuangan {company_name}_"""

        import urllib.parse
        encoded_message = urllib.parse.quote(message)

        whatsapp_url = f"https://wa.me/{phone}?text={encoded_message}"

        return {
            'type': 'ir.actions.act_url',
            'url': whatsapp_url,
            'target': 'new',
        }

    # =========================================================================
    # LEGACY/GENERIC ACTIONS (keep for compatibility)
    # =========================================================================

    def action_generate_smart_billing_va(self):
        """Alias untuk action_send_bsi_billing"""
        return self.action_send_bsi_billing()

    def action_generate_payment_link(self):
        """Generate Payment Link - BSI doesn't support this, show error"""
        self.ensure_one()

        provider = self._get_billing_provider()
        provider_code = provider.get_provider_code()

        if provider_code == 'bsi':
            raise UserError(
                "BSI Smart Billing tidak mendukung Payment Link.\n\n"
                "Gunakan tombol 'Kirim Billing BSI' untuk membuat Virtual Account."
            )

        # For other providers that support payment link
        if self.state != 'posted':
            raise UserError(
                "Invoice harus dalam status 'Posted' untuk generate Payment Link.")

        if self.payment_state == 'paid':
            raise UserError("Invoice sudah lunas.")

        # Generate unique order ID
        order_id = f"LINK-{self.name}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        order_id = order_id.replace('/', '-')

        # Get customer and item details
        customer = self._prepare_customer_details()
        items = self._prepare_item_details()

        if not items:
            items = [{
                "id": str(self.id),
                "name": f"Tagihan {self.name}",
                "price": int(self.amount_residual),
                "quantity": 1,
            }]

        try:
            result = provider.create_payment_link(
                order_id=order_id,
                amount=self.amount_residual,
                item_details=items,
                customer_details=customer
            )

            if result.get('success'):
                # Create transaction record
                self.env['smart.billing.transaction'].create({
                    'name': order_id,
                    'provider': provider.get_provider_code(),
                    'transaction_type': 'payment_link',
                    'state': 'pending',
                    'move_id': self.id,
                    'partner_id': self.partner_id.id,
                    'payment_url': result['payment_url'],
                    'gross_amount': self.amount_residual,
                    'transaction_time': fields.Datetime.now(),
                    'expiry_time': result.get('expiry_time'),
                    'provider_response': str(result.get('raw_response', {})),
                })

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Payment Link Berhasil Dibuat',
                        'message': result['payment_url'],
                        'type': 'success',
                        'sticky': True,
                    }
                }
            else:
                raise UserError(
                    f"Gagal membuat Payment Link: {result.get('message', 'Unknown error')}")

        except Exception as e:
            _logger.error(
                f"Error creating payment link for invoice {self.name}: {e}")
            raise UserError(f"Gagal membuat Payment Link: {str(e)}")

    def action_check_smart_billing_status(self):
        """Check status of all pending Smart Billing transactions"""
        self.ensure_one()

        pending_transactions = self.smart_billing_transaction_ids.filtered(
            lambda t: t.state == 'pending'
        )

        if not pending_transactions:
            raise UserError("Tidak ada transaksi Smart Billing pending.")

        for transaction in pending_transactions:
            transaction.action_check_status()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Status Dicek',
                'message': f'{len(pending_transactions)} transaksi dicek',
                'type': 'info',
                'sticky': False,
            }
        }
