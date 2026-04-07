import logging
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class DeleteVAWizard(models.TransientModel):
    _name = "wizard.delete.va"
    _description = "Wizard Hapus Virtual Account Santri"

    santri_id = fields.Many2one('cdn.siswa', string="Santri", required=True)
    kelas_id = fields.Many2one(
        'cdn.ruang_kelas', string='Kelas', related='santri_id.ruang_kelas_id', readonly=True)
    kamar_id = fields.Many2one(
        'cdn.kamar_santri', string='Kamar', related='santri_id.kamar_id', readonly=True)

    kartu_santri = fields.Char(string="Kartu", required=False)

    va_utama = fields.Char(
        string="VA Utama", compute='_compute_va_info', readonly=True)
    va_saku = fields.Char(string="VA Uang Saku",
                          compute='_compute_va_info', readonly=True)

    catatan = fields.Text(string="Alasan Penghapusan", required=True)

    @api.depends('santri_id')
    def _compute_va_info(self):
        for record in self:
            if record.santri_id and record.santri_id.partner_id:
                partner = record.santri_id.partner_id
                # Menggunakan getattr untuk akses aman jika field belum terdefinisi di registry
                record.va_utama = getattr(partner, 'virtual_account', False)
                record.va_saku = getattr(partner, 'va_saku', False)
            else:
                record.va_utama = False
                record.va_saku = False

    @api.onchange('santri_id')
    def _onchange_santri_id(self):
        if self.santri_id:
            self.kartu_santri = self.santri_id.barcode_santri

    @api.onchange('kartu_santri')
    def _onchange_kartu_santri(self):
        if self.kartu_santri:
            santri = self.env['cdn.siswa'].search(
                [('barcode_santri', '=', self.kartu_santri)], limit=1)
            if not santri:
                santri = self.env['cdn.siswa'].search(
                    [('barcode', '=', self.kartu_santri)], limit=1)

            if santri:
                self.santri_id = santri.id
            else:
                return {
                    'warning': {
                        'title': 'Kartu Tidak Ditemukan',
                        'message': f"Tidak dapat menemukan data santri dengan kode kartu '{self.kartu_santri}'."
                    }
                }

    def action_submit(self):
        self.ensure_one()

        partner = self.santri_id.partner_id
        if not partner:
            raise UserError("Data partner santri tidak ditemukan.")

        _logger.info(
            f"[VA DELETION] Starting VA deletion for {self.santri_id.name} (Partner ID: {partner.id})")

        # 1. Cari dan Batalkan Transaksi VA di Smart Billing (BSI)
        # Mencari semua transaksi VA permanen (top-up) yang aktif/pending
        active_va_txs = self.env['smart.billing.transaction'].sudo().search([
            ('partner_id', '=', partner.id),
            ('transaction_type', '=', 'va_topup'),
            ('state', 'in', ['active', 'pending'])
        ])

        for tx in active_va_txs:
            try:
                tx.action_cancel()
                _logger.info(
                    f"[VA DELETION] Cancelled transaction {tx.name} for VA {tx.va_number}")
            except Exception as e:
                _logger.error(
                    f"[VA DELETION] Error cancelling transaction {tx.name}: {e}")

        # 2. Hapus nomor VA dari record partner (Odoo side)
        # Menghapus both VA Utama dan VA Saku sesuai request user
        partner.sudo().write({
            'virtual_account': False,
            'va_saku': False
        })

        # 3. Beri catatan di chatter santri
        self.santri_id.message_post(
            body=f"<b>Virtual Account Dihapus</b><br/>"
            f"Alasan: {self.catatan}<br/>"
            f"User: {self.env.user.name}",
            message_type='notification'
        )

        message = f"Virtual Account untuk {self.santri_id.name} telah berhasil dihapus dari sistem dan bank."
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {
                'message': message,
                'title': 'Hapus VA Berhasil',
                'sticky': False,
                'type': 'success',
                'timeout': 8000
            }
        )

        return {'type': 'ir.actions.act_window_close'}
