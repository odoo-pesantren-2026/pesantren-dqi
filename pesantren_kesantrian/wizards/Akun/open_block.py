from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta

class OpenBlock(models.TransientModel):
    _name = "wizard.open.block"

    def _get_block_santri(self):
        return [('status_akun', '=', 'blokir')]

    santri_id    = fields.Many2one('cdn.siswa', string="Santri",domain=_get_block_santri ,required=True)
    kelas_id     = fields.Many2one('cdn.ruang_kelas', string='Kelas', related='santri_id.ruang_kelas_id', readonly=True)
    kamar_id     = fields.Many2one('cdn.kamar_santri', string='Kamar', related='santri_id.kamar_id', readonly=True)
    halaqoh_id   = fields.Many2one('cdn.halaqoh', string='Halaqoh', related='santri_id.halaqoh_id', readonly=True)
    musyrif_id   = fields.Many2one('hr.employee', string='Musyrif', related='santri_id.musyrif_id', readonly=True)
    kartu_santri = fields.Char(string="Kartu", required=True)
    status       = fields.Selection(string="Status" , related='santri_id.status_akun',readonly=True)        
    alasan       = fields.Char(string="Alasan" , related='santri_id.alasan_akun',readonly=True)
    catatan      = fields.Text(string="Catatan" , related='santri_id.catatan_akun',readonly=True)


    @api.onchange('santri_id')
    def _onchange_santri_id(self):
        for record in self:
            santri = record.santri_id

            if santri:
                record.kartu_santri = santri.barcode_santri

    @api.onchange('kartu_santri')
    def _onchange_kartu_santri(self):
        if self.kartu_santri:
            domain = [
                ('barcode_santri', '=', self.kartu_santri),
                ('status_akun', '=', 'blokir')
            ]
            santri = self.env['cdn.siswa'].search(domain, limit=1)

            if not santri:
                santri_aktif = self.env['cdn.siswa'].search([
                    ('barcode_santri', '=', self.kartu_santri)
                ], limit=1)

                if santri_aktif:
                    self.kartu_santri = False
                    return {
                        'warning': {
                            'title': 'Informasi',
                            'message': f"Kartu ditemukan, tetapi akun atas nama '{santri_aktif.name}' saat ini sudah aktif. Silakan pilih santri lain yang status akunnya nonaktif."
                        }
                    }

                else:
                    self.kartu_santri = False
                    return {
                        'warning': {
                            'title': 'Data Tidak Ditemukan',
                            'message': f"Tidak ditemukan data santri dengan kode kartu '{self.kartu_santri}'. Pastikan kode kartu sudah benar atau hubungi pengurus untuk verifikasi lebih lanjut."
                        }
                    }
            else:
                self.santri_id = santri.id

    def action_submit(self):
        self.santri_id.sudo().write({
            'status_akun' : 'aktif'
        })

        message = f"Akun santri {self.santri_id.name} telah berhasil di aktifkan kembali"
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {
                'message': message,
                'title': '✅ Akun Berhasil DiAktifkan',
                'sticky': False,
                'type': 'success',
                'timeout': 8000 
            }
        )

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.open.block',  
            'view_mode': 'form',
            'target': 'new',
            'name': 'Buka Blokir',
            'context': {
                'default_santri_id': False,
            }
        }