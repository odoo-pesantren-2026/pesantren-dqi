import logging
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class BlokirSaldo(models.TransientModel):
    _name = "wizard.blokir.saldo"
    _description = "Wizard Blokir Akun Santri"

    santri_id = fields.Many2one('cdn.siswa', string="Santri", required=True)
    kelas_id = fields.Many2one(
        'cdn.ruang_kelas', string='Kelas', related='santri_id.ruang_kelas_id', readonly=True)
    kamar_id = fields.Many2one(
        'cdn.kamar_santri', string='Kamar', related='santri_id.kamar_id', readonly=True)
    halaqoh_id = fields.Many2one(
        'cdn.halaqoh', string='Halaqoh', related='santri_id.halaqoh_id', readonly=True)
    musyrif_id = fields.Many2one(
        'hr.employee', string='Musyrif', related='santri_id.musyrif_id', readonly=True)
    kartu_santri = fields.Char(string="Kartu", required=False)
    status = fields.Selection(
        string="Status", related='santri_id.status_akun', readonly=True)
    alasan_block = fields.Selection([
        ('Penyalahgunaan Saldo', 'Penyalahgunaan Saldo'),
        ('Pemalsuan Data', 'Pemalsuan Data'),
        ('Akses Tidak Sah ke Sistem', 'Akses Tidak Sah ke Sistem'),
        ('Menggunakan Kartu Santri Lain', 'Menggunakan Kartu Santri Lain'),
        ('Pelanggaran Berulang', 'Pelanggaran Berulang'),
        ('Transaksi Mencurigakan', 'Transaksi Mencurigakan'),
        ('Kartu Rusak karena Kelalaian', 'Kartu Rusak karena Kelalaian'),
        ('Menghambat Operasional Pesantren', 'Menghambat Operasional Pesantren'),
        ('Membahayakan Santri/Petugas', 'Membahayakan Santri/Petugas'),
        ('Lainnya', 'Lainnya'),
    ], string="Alasan Blokir", required=True)
    catatan = fields.Text(string="Catatan")

    @api.onchange('santri_id')
    def _onchange_santri_id(self):
        if self.santri_id:
            santri = self.santri_id
            # Jangan timpa kalau sudah ada input manual di kartu_santri
            if not self.kartu_santri:
                self.kartu_santri = santri.barcode_santri or santri.barcode

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
                # Jika tidak ditemukan, jangan hapus input user, beri warning saja
                return {
                    'warning': {
                        'title': 'Kartu Tidak Ditemukan',
                        'message': f"Tidak dapat menemukan data santri dengan kode kartu '{self.kartu_santri}'."
                    }
                }

    def _cancel_active_va(self, siswa_id):
        """Cancel any active/pending permanent VA top-up transactions for the santri"""
        try:
            # Mencari transaksi VA top-up yang aktif atau pending untuk santri ini
            active_topup_va = self.env['smart.billing.transaction'].sudo().search([
                ('siswa_id', '=', siswa_id),
                ('transaction_type', '=', 'va_topup'),
                ('state', 'in', ['active', 'pending'])
            ])
            
            for va in active_topup_va:
                va.action_cancel()
                _logger.info(f"[VA DISABLING] Berhasil membatalkan VA {va.va_number} untuk santri ID {siswa_id}")
        except Exception as e:
            _logger.error(f"[VA DISABLING] Gagal membatalkan VA untuk santri ID {siswa_id}: {e}")

    def action_submit(self):
        self.ensure_one()
        
        # 1. Update status akun santri
        self.santri_id.sudo().write({
            'status_akun': "blokir",
            "alasan_akun": self.alasan_block,
            "catatan_akun": self.catatan
        })

        # Clear VA fields on partner
        if self.santri_id.partner_id:
            self.santri_id.partner_id.sudo().write({
                'virtual_account': False,
                'va_saku': False
            })
            
        # Log to chatter
        self.santri_id.message_post(
            body=f"<b>Virtual Account Dinonaktifkan (Blokir)</b><br/>"
                 f"Alasan: {self.alasan_block}<br/>"
                 f"Catatan: {self.catatan or '-'}",
            message_type='notification'
        )

        # 2. Batalkan VA Top-up jika ada (Bekerja Optimal)
        self._cancel_active_va(self.santri_id.id)

        message = f"Akun santri {self.santri_id.name} dan VA Top-up terkait telah berhasil dinonaktifkan (Blokir)."
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {
                'message': message,
                'title': 'Blokir Akun Berhasil',
                'sticky': False,
                'type': 'danger',
                'timeout': 8000
            }
        )

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.blokir.saldo',
            'view_mode': 'form',
            'target': 'new',
            'name': 'Blokir Saldo',
            'context': {
                'default_santri_id': False,
                'default_alasan_block': False,
                'default_catatan': False,
                'default_kartu_santri': False,
            }
        }
