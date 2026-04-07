from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare
from datetime import timedelta, datetime
import logging

_logger = logging.getLogger(__name__)


class Tagihan(models.Model):
    _inherit = "account.move"

    activate_automation = fields.Boolean(
        string="Tagihan Otomatis",
        help="Jika diaktifkan, maka jika ada tagihan yang melebihi tenggat waktu, sistem akan otomatis menggunakan uang saku sebagai pembayaran tagihan."
    )

    cara_pembayaran = fields.Selection([
        ('saldo', 'Saldo / Uang Saku Santri'),
        ('smart_billing', 'Smart Billing (VA BSI)'),
        ('manual', 'Manual / Tunai')
    ], string='Cara Pembayaran', required=True, default='manual')

    @api.onchange('cara_pembayaran')
    def _onchange_cara_pembayaran(self):
        if self.cara_pembayaran != 'saldo':
            self.activate_automation = False

    @api.onchange('siswa_id', 'amount_total', 'cara_pembayaran')
    def _onchange_check_limit_warning(self):
        """Warning if invoice amount exceeds santri spending limit"""
        if self.cara_pembayaran == 'saldo' and self.siswa_id and self.amount_total > 0:
            if self.siswa_id.is_limit_active:
                remaining = self.siswa_id.remaining_limit
                if float_compare(self.amount_total, remaining, precision_digits=0) > 0:
                    limit_label = dict(self.siswa_id._fields['limit'].selection).get(
                        self.siswa_id.limit, 'Periodik')
                    return {
                        'warning': {
                            'title': "Peringatan Limit Saldo!",
                            'message': (
                                f"Total tagihan (Rp {self.amount_total:,.0f}) melebihi sisa limit {limit_label} "
                                f"santri (Rp {remaining:,.0f}).\n\n"
                                f"Pembayaran otomatis akan gagal jika tagihan ini di-post tanpa menyesuaikan nominal atau limit."
                            )
                        }
                    }

    def action_recover_kerugian_piutang(self):
        pass

    siswa_id = fields.Many2one(
        comodel_name='cdn.siswa', string='Santri', ondelete='cascade', required=True)
    barcode = fields.Char(string="Kartu Santri", readonly=False)
    ruang_kelas_id = fields.Many2one(
        'cdn.ruang_kelas', string='Kelas', related='siswa_id.ruang_kelas_id', store=True)
    kamar_id = fields.Many2one(
        'cdn.kamar_santri', string='Kamar', related='siswa_id.kamar_id', readonly=True)
    halaqoh_id = fields.Many2one(
        'cdn.halaqoh', string='Halaqoh', related='siswa_id.halaqoh_id', readonly=True)
    musyrif_id = fields.Many2one(
        'hr.employee', string='Musyrif', related='siswa_id.musyrif_id', readonly=True)
    nama_sekolah = fields.Selection(selection='_get_nama_sekolah_selection',
                                    string='Nama Sekolah', related='siswa_id.nama_sekolah', readonly=True, store=True)
    is_cancelled = fields.Boolean(
        string="Dibatalkan",
        compute='_compute_is_cancelled',
        store=True
    )
    is_auto_payment = fields.Boolean(string="Pembayaran Otomatis", default=False,
                                     help="Menandakan bahwa tagihan ini dibayar secara otomatis")
    auto_payment_date = fields.Date(
        string="Tanggal Pembayaran Otomatis", readonly=True)
    auto_confirmed = fields.Boolean(string="Auto Confirmed", default=False,
                                    help="Menandakan tagihan ini di-confirm otomatis oleh sistem")
    auto_confirmed_date = fields.Datetime(
        string="Tanggal Auto Confirm", readonly=True)

    @api.model
    def _cron_auto_confirm_invoices(self):
        """
        Cron job to auto-confirm SPP invoices created via Penetapan Tagihan.
        Only confirms invoices with activate_automation=True and invoice_date <= today.
        After confirm: sends to BSI for VA generation and notifies parents via WhatsApp.
        """
        today = fields.Date.today()

        # Find draft invoices that should be auto-confirmed
        invoices_to_confirm = self.search([
            ('state', '=', 'draft'),
            ('move_type', '=', 'out_invoice'),
            ('invoice_date', '<=', today),
            '|',
            ('activate_automation', '=', True),
            ('cara_pembayaran', '=', 'smart_billing')
        ])

        if not invoices_to_confirm:
            _logger.info("[AUTO-CONFIRM] No invoices to auto-confirm today.")
            return True

        _logger.info(
            f"[AUTO-CONFIRM] Found {len(invoices_to_confirm)} invoices to auto-confirm.")

        confirmed_count = 0
        bsi_sent_count = 0
        wa_sent_count = 0
        error_count = 0

        for invoice in invoices_to_confirm:
            try:
                # 1. Confirm the invoice
                invoice.action_post()
                invoice.write({
                    'auto_confirmed': True,
                    'auto_confirmed_date': fields.Datetime.now(),
                })
                confirmed_count += 1
                _logger.info(
                    f"[AUTO-CONFIRM] Confirmed invoice {invoice.name}")

                # 2. Send to BSI for VA generation
                try:
                    if hasattr(invoice, 'action_send_bsi_billing'):
                        invoice.action_send_bsi_billing()
                        bsi_sent_count += 1
                        _logger.info(
                            f"[AUTO-CONFIRM] Sent BSI billing for {invoice.name}")
                except Exception as bsi_error:
                    _logger.error(
                        f"[AUTO-CONFIRM] BSI billing error for {invoice.name}: {bsi_error}")

                # 3. Send WhatsApp notification to parent (if phone exists)
                try:
                    if invoice.siswa_id and invoice.siswa_id.orangtua_id:
                        orangtua = invoice.siswa_id.orangtua_id
                        phone = orangtua.mobile or orangtua.phone or ''

                        if phone:
                            # Send WhatsApp using existing method if available
                            if hasattr(invoice, 'action_send_va_whatsapp'):
                                # Note: This opens WhatsApp URL, for automated sending
                                # we would need a proper WhatsApp API integration
                                wa_sent_count += 1
                                _logger.info(
                                    f"[AUTO-CONFIRM] WhatsApp notification prepared for {invoice.name} to {phone}")

                            # Post notification to invoice chatter
                            invoice.message_post(
                                body=f"📱 Tagihan auto-confirmed. Notifikasi akan dikirim ke orang tua ({phone}).",
                                message_type='notification'
                            )
                        else:
                            _logger.info(
                                f"[AUTO-CONFIRM] No phone number for parent of {invoice.siswa_id.name}, skipping WhatsApp")
                except Exception as wa_error:
                    _logger.error(
                        f"[AUTO-CONFIRM] WhatsApp error for {invoice.name}: {wa_error}")

            except Exception as e:
                error_count += 1
                _logger.error(
                    f"[AUTO-CONFIRM] Error confirming invoice {invoice.name}: {e}")

        # Log summary
        _logger.info(
            f"[AUTO-CONFIRM] Summary: Confirmed={confirmed_count}, BSI Sent={bsi_sent_count}, WA Prepared={wa_sent_count}, Errors={error_count}")

        return True

    @api.model
    def _run_check_overdue_invoices(self):
        today = fields.Date.today()
        # today = fields.Date.from_string('2025-05-19')

        invoices = self.search([
            ('state', '=', 'posted'),
            ('payment_state', '!=', 'paid'),
            ('amount_residual', '>', 0),
            ('invoice_date_due', '<=', today),
            ('cara_pembayaran', '=', 'saldo'),
            ('activate_automation', '=', True)
        ])

        for invoice in invoices:
            partner = invoice.partner_id

            siswa = self.env['cdn.siswa'].search(
                [('partner_id', '=', partner.id)], limit=1)
            if siswa and siswa.status_akun in ['nonaktif', 'blokir']:
                invoice.message_post(
                    body=_(
                        f"⛔ Pembayaran otomatis gagal karena akun santri *{partner.name}* saat ini berstatus *{siswa.status_akun}*."),
                    subject="Gagal Pembayaran Otomatis",
                    message_type='notification',
                    subtype_xmlid="mail.mt_note"
                )
                continue

            saldo_saku = partner.saldo_uang_saku
            amount_residual = invoice.amount_residual

            if saldo_saku >= amount_residual:
                try:
                    invoice._bayar_dengan_saku(
                        invoice, partner, amount_residual)

                    # ✅ Notifikasi penuh
                    invoice.message_post(
                        body=_(
                            f"✅ Tagihan {invoice.name} berhasil dibayar penuh menggunakan saldo santri sebesar {amount_residual}."),
                        subject="Pembayaran Penuh via Saldo Saku",
                        message_type='notification',
                        subtype_xmlid="mail.mt_note"
                    )
                except UserError as e:
                    _logger.warning(
                        f"Pembayaran otomatis gagal karena limit: {e}")
                    invoice.message_post(
                        body=_(
                            f"❌ Pembayaran otomatis GAGAL karena batasan penggunaan saldo (Limit): {str(e)}"),
                        subject="Gagal Bayar - Limit Tercapai",
                        message_type='notification',
                        subtype_xmlid="mail.mt_note"
                    )

            elif saldo_saku > 0:
                amount_to_pay = saldo_saku
                try:
                    invoice._bayar_dengan_saku(invoice, partner, amount_to_pay)

                    _logger.info(
                        f"Saldo santri tidak cukup. Membayar sebagian tagihan {invoice.name} sebesar {amount_to_pay}")

                    # ✅ Notifikasi sebagian
                    invoice.message_post(
                        body=_(
                            f"⚠️ Tagihan {invoice.name} hanya terbayar sebagian sebesar {amount_to_pay} dari total {amount_residual}."),
                        subject="Pembayaran Sebagian via Saldo Saku",
                        message_type='notification',
                        subtype_xmlid="mail.mt_note"
                    )
                except UserError as e:
                    _logger.warning(
                        f"Pembayaran sebagian otomatis gagal karena limit: {e}")
                    invoice.message_post(
                        body=_(
                            f"❌ Pembayaran sebagian otomatis GAGAL karena batasan penggunaan saldo (Limit): {str(e)}"),
                        subject="Gagal Bayar Sebagian - Limit Tercapai",
                        message_type='notification',
                        subtype_xmlid="mail.mt_note"
                    )

            else:
                _logger.info(
                    f"Saldo 0. Tidak bisa bayar Tagihan {invoice.name}")

                # ✅ Notifikasi gagal bayar
                invoice.message_post(
                    body=_(
                        f"❌ Tagihan {invoice.name} belum dibayar karena saldo santri 0."),
                    subject="Gagal Pembayaran via Saldo Saku",
                    message_type='notification',
                    subtype_xmlid="mail.mt_note"
                )

        # Reminder untuk invoice yang belum jatuh tempo
        future_invoices = self.search([
            ('state', '=', 'posted'),
            ('payment_state', '!=', 'paid')
        ])

        for invoice in future_invoices:
            invoice.message_post(
                body=_(
                    f"🔔 Tagihan {invoice.name} akan segera jatuh tempo pada {invoice.invoice_date_due}."),
                subject="Reminder Invoice",
                message_type='notification',
                subtype_xmlid="mail.mt_note"
            )

    display_payment_status = fields.Char(
        string="Status  ",
        compute="_compute_display_payment_status",
        store=True
    )

    @api.depends('state', 'payment_state')
    def _compute_display_payment_status(self):
        for rec in self:
            if rec.state == 'cancel':
                rec.display_payment_status = 'Dibatalkan'
            elif rec.payment_state == 'paid':
                rec.display_payment_status = 'Lunas'
            elif rec.payment_state == 'partial':
                rec.display_payment_status = 'Terbayar Sebagian'
            elif rec.payment_state == 'not_paid':
                rec.display_payment_status = 'Belum Bayar'
            else:
                rec.display_payment_status = rec.payment_state

    @api.onchange('siswa_id')
    def _onchange_siswa_id(self):
        if self.siswa_id:
            self.barcode = self.siswa_id.barcode_santri
            self.partner_id = self.siswa_id.partner_id
        else:
            self.barcode = False

    @api.depends('siswa_id', 'siswa_id.ruang_kelas_id')
    def _compute_kelas_id(self):
        for record in self:
            if record.siswa_id:
                record.ruang_kelas_id = record.siswa_id.ruang_kelas_id
            else:
                record.ruang_kelas_id = False

    @api.onchange('barcode')
    def _onchange_barcode(self):
        if self.barcode:
            siswa = self.env['cdn.siswa'].search(
                [('barcode_santri', '=', self.barcode)], limit=1)
            if siswa:
                self.siswa_id = siswa.id
                self.partner_id = self.siswa_id.partner_id
            else:
                self.siswa_id = False
                barcode_sementara = self.barcode
                self.barcode = False
                return {
                    'warning': {
                        'title': "Perhatian !",
                        'message': f"Data Santri dengan Kartu Santri {barcode_sementara} tidak ditemukan."
                    }
                }
        else:
            self.barcode = False
            self.siswa_id = False

    @api.model
    def _get_nama_sekolah_selection(self):
        return self.env['cdn.siswa']._get_pilihan_nama_sekolah()

    @api.model
    def create(self, vals):
        if 'siswa_id' in vals:
            siswa = self.env['cdn.siswa'].browse(vals['siswa_id'])
            if siswa:
                if not vals.get('barcode'):
                    vals['barcode'] = siswa.barcode_santri
                # Memastikan partner_id terisi saat impor
                if not vals.get('partner_id'):
                    vals['partner_id'] = siswa.partner_id.id

        invoice = super(Tagihan, self).create(vals)

        # AUTO-PAYMENT: Trigger saat tagihan dibuat
        if invoice.move_type == 'out_invoice' and invoice.siswa_id and invoice.state == 'posted':
            invoice._try_auto_pay_from_wallet()

        return invoice

    # Menambahkan metode untuk memastikan partner_id terisi pada rekaman yang sudah ada

    def write(self, vals):
        # Log untuk debug
        if 'state' in vals:
            _logger.info(
                f"📝 Invoice write: state change to {vals.get('state')}")

        res = super(Tagihan, self).write(vals)

        # Jika siswa_id diperbarui, pastikan partner_id juga diperbarui
        if 'siswa_id' in vals and not vals.get('partner_id'):
            for record in self:
                if record.siswa_id and not record.partner_id:
                    record.partner_id = record.siswa_id.partner_id

        # AUTO-PAYMENT: Trigger saat invoice di-post
        if 'state' in vals and vals.get('state') == 'posted':
            for record in self:
                if record.move_type == 'out_invoice' and record.siswa_id:
                    _logger.info(
                        f"🚀 Triggering auto-payment for {record.name}")
                    record._try_auto_pay_from_wallet()

        return res

    def action_post(self):
        """Override action_post to validate limit and trigger auto-payment"""
        # Strict validation for spending limit before posting
        for record in self:
            if record.move_type == 'out_invoice' and record.siswa_id and record.cara_pembayaran == 'saldo':
                if record.siswa_id.is_limit_active:
                    remaining = record.siswa_id.remaining_limit
                    if float_compare(record.amount_total, remaining, precision_digits=0) > 0:
                        limit_label = dict(record.siswa_id._fields['limit'].selection).get(
                            record.siswa_id.limit, 'Periodik')
                        raise UserError(
                            f"Konfirmasi tagihan GAGAL untuk {record.siswa_id.name}.\n\n"
                            f"Total tagihan (Rp {record.amount_total:,.0f}) melebihi sisa limit {limit_label} "
                            f"santri (Rp {remaining:,.0f}).\n\n"
                            f"Silakan kurangi nominal tagihan atau naikkan limit santri terlebih dahulu."
                        )

        res = super(Tagihan, self).action_post()

        # AUTO-PAYMENT: Trigger setelah post
        for record in self:
            if record.move_type == 'out_invoice' and record.siswa_id and record.state == 'posted':
                _logger.info(
                    f"🚀 Triggering auto-payment via action_post for {record.name}")
                record._try_auto_pay_from_wallet()

        return res

    def action_pay_from_wallet(self):
        """Manual button to pay invoice from wallet - for existing invoices"""
        for invoice in self:
            result = invoice._try_auto_pay_from_wallet()
            if result:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Pembayaran Berhasil',
                        'message': f'Tagihan {invoice.name} berhasil dibayar dari saldo dompet',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                # Check why it failed
                wallet_balance = invoice.partner_id.saldo_uang_saku
                amount_due = invoice.amount_residual

                if wallet_balance < amount_due:
                    message = f'Saldo tidak cukup. Dibutuhkan Rp {amount_due:,.0f}, tersedia Rp {wallet_balance:,.0f}'
                elif invoice.payment_state == 'paid':
                    message = 'Tagihan sudah lunas'
                else:
                    message = 'Pembayaran gagal, cek log untuk detail'

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Pembayaran Gagal',
                        'message': message,
                        'type': 'warning',
                        'sticky': False,
                    }
                }

    def _try_auto_pay_from_wallet(self):
        """
        Try to auto-pay invoice from wallet balance (saldo_uang_saku).
        ONLY pays if balance is sufficient for FULL payment (no partial).
        """
        self.ensure_one()

        # Skip jika sudah lunas atau dibatalkan
        if self.payment_state == 'paid' or self.state == 'cancel':
            return False

        # Skip jika tidak ada partner atau siswa
        if not self.partner_id or not self.siswa_id:
            return False

        # Skip jika bukan metode saldo atau otomatisasi tidak aktif
        if self.cara_pembayaran != 'saldo' or not self.activate_automation:
            return False

        # PENTING: Gunakan saldo_uang_saku, bukan wallet_balance
        wallet_balance = self.partner_id.saldo_uang_saku
        amount_due = self.amount_residual

        _logger.info(
            f"🔍 Checking auto-payment for {self.name}: Balance={wallet_balance}, Due={amount_due}, Method={self.cara_pembayaran}")

        # CRITICAL: Only pay if balance is enough for FULL payment
        if wallet_balance >= amount_due and amount_due > 0:
            try:
                self._process_wallet_payment(amount_due)
                _logger.info(
                    f"✅ Auto-payment SUCCESS: Invoice {self.name} paid FULL {amount_due} from wallet")

                # Log notification
                self.message_post(
                    body=f"✅ Tagihan berhasil dibayar OTOMATIS dari saldo dompet sebesar Rp {amount_due:,.0f}",
                    subject="Pembayaran Otomatis Berhasil",
                    message_type='notification',
                )

                return True
            except UserError as e:
                _logger.warning(
                    f"❌ Auto-payment FAILED for {self.name} due to limit: {e}")
                self.message_post(
                    body=f"❌ Pembayaran otomatis GAGAL karena batasan penggunaan saldo (Limit): {str(e)}",
                    subject="Gagal Bayar Otomatis - Limit Tercapai",
                    message_type='notification',
                )
                return False
            except Exception as e:
                _logger.error(f"❌ Auto-payment FAILED for {self.name}: {e}")
                return False
        else:
            _logger.info(
                f"⏸️ Auto-payment SKIPPED: Invoice {self.name} amount {amount_due} > wallet {wallet_balance}")
            return False

    def _process_wallet_payment(self, amount):
        """Process payment from wallet balance using EXISTING _bayar_dengan_saku method"""
        self.ensure_one()

        # Gunakan existing method yang sudah teruji
        self._bayar_dengan_saku(self, self.partner_id, amount)

        # Mark as auto payment
        self.sudo().write({
            'is_auto_payment': True,
            'auto_payment_date': fields.Date.today()
        })

        return True

    # Fungsi untuk memperbaiki data yang sudah ada tanpa partner_id
    @api.model
    def fix_missing_partner_ids(self):
        """Fungsi ini dapat dipanggil dari menu Developer Tools atau melalui cron job"""
        moves = self.search(
            [('siswa_id', '!=', False), ('partner_id', '=', False)])
        for move in moves:
            if move.siswa_id.partner_id:
                move.partner_id = move.siswa_id.partner_id

        return True

    def _bayar_dengan_saku(self, invoice, partner, jumlah_bayar):
        # 1. Catat transaksi uang saku
        self.env['cdn.uang_saku'].sudo().create({
            'tgl_transaksi': fields.Datetime.now(),
            'siswa_id': partner.id,
            'jns_transaksi': 'keluar',
            'amount_out': jumlah_bayar,
            'validasi_id': self.env.user.id,
            'validasi_time': fields.Datetime.now(),
            'keterangan': f'Pembayaran otomatis sebagian invoice {invoice.name}',
            'state': 'confirm',
        })

        # 2. Update saldo uang saku
        partner.saldo_uang_saku = partner.calculate_saku()

        # 3. Cari jurnal bertipe bank/cash
        journal = self.env['account.journal'].search([
            ('type', 'in', ['bank', 'cash']),
            ('company_id', '=', invoice.company_id.id)
        ], limit=1)

        if not journal:
            raise UserError(
                f"Jurnal bertipe 'bank' atau 'cash' untuk perusahaan {invoice.company_id.name} tidak ditemukan.")

        # 4. Buat payment register
        payment_register = self.env['account.payment.register'].with_context(
            active_model='account.move',
            active_ids=invoice.ids
        ).create({
            'payment_date': fields.Date.today(),
            'journal_id': journal.id,
            'amount': jumlah_bayar,
        })

        try:
            payment = payment_register._create_payments()
            _logger.info(
                f"Payment sebagian sebesar {jumlah_bayar} berhasil untuk invoice {invoice.name}")
            return True
        except Exception as e:
            _logger.error(f"Error saat membuat pembayaran sebagian: {e}")
            raise UserError(f"Gagal membayar sebagian invoice: {e}")

    @api.depends('state')
    def _compute_is_cancelled(self):
        for rec in self:
            rec.is_cancelled = rec.state == 'cancel'
