from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta

class PencairanSaldo(models.TransientModel):
    _name = "wizard.pencairan.saldo"
    _description = "Wizard Untuk Melakukan Pencairan Saldo Santri"

    santri_id = fields.Many2one('cdn.siswa', string="Santri", required=True)
    saldo_santri = fields.Float(string="Saldo Santri", readonly=True, digits=(16, 0))
    nominal_pencairan = fields.Float(string="Nominal", required=True, digits=(16, 0))
    kelas_id    = fields.Many2one('cdn.ruang_kelas', string='Kelas', related='santri_id.ruang_kelas_id', readonly=True)
    kamar_id    = fields.Many2one('cdn.kamar_santri', string='Kamar', related='santri_id.kamar_id', readonly=True)
    halaqoh_id  = fields.Many2one('cdn.halaqoh', string='Halaqoh', related='santri_id.halaqoh_id', readonly=True)
    musyrif_id  = fields.Many2one('hr.employee', string='Musyrif', related='santri_id.musyrif_id', readonly=True)
    kartu_santri = fields.Char(string="Kartu", required=True)
    catatan = fields.Text(string="Catatan")

    @api.onchange('santri_id')
    def _onchange_santri_id(self):
        for record in self:
            if record.santri_id and record.santri_id.partner_id:
                record.saldo_santri = record.santri_id.partner_id.saldo_uang_saku
                record.kartu_santri = record.santri_id.barcode_santri

                # 🔒 Kalau saldo 0 beri warning
                if record.saldo_santri <= 0:
                    return {
                        'warning': {
                            'title': 'Perhatian!',
                            'message': f"Saldo santri {record.santri_id.name} adalah Rp.0, tidak bisa dilakukan pencairan."
                        }
                    }
            else:
                record.saldo_santri = 0.0
    
    @api.onchange('kartu_santri')
    def _onchange_kartu_santri(self):
        if self.kartu_santri:
            santri = self.env['cdn.siswa'].search([('barcode_santri', '=', self.kartu_santri)], limit=1)
            if not santri:
                santri = self.env['cdn.siswa'].search([('barcode', '=', self.kartu_santri)]),
            
            if santri:
                self.santri_id = santri.id
            
            else:
                kartu_sementara = self.kartu_santri
                self.barcode = False
                return {
                    'warning': {
                        'title': 'Perhatian !',
                        'message': f"Tidak dapat menemukan kartu santri dengan kode {kartu_sementara}"
                    }
                }
    @api.onchange('nominal_pencairan')
    def _onchange_nominal_pencairan(self):
        if self.nominal_pencairan and self.saldo_santri:
            if self.nominal_pencairan > self.saldo_santri:
                self.nominal_pencairan = 0
                return {
                    'warning': {
                        'title': "Saldo Tidak Mencukupi",
                        'message': f"Nominal pencairan melebihi saldo santri (Rp.{self.saldo_santri:,.0f})."
                    }
                }

    def action_submit(self):
        timestamp = fields.Datetime.now()

        partner = self.santri_id.partner_id

        self.env['cdn.uang_saku'].sudo().create({
            'tgl_transaksi': timestamp,
            'siswa_id': self.santri_id.partner_id.id,  
            'jns_transaksi': 'keluar',
            'amount_out': self.nominal_pencairan, 
            'validasi_id': self.env.user.id,
            'validasi_time': timestamp,
            'keterangan': f'Pencairan Saldo Sebesar Rp.{self.nominal_pencairan}',
            'state': 'confirm',
        })
        
        partner.saldo_uang_saku = partner.calculate_saku()

        message = f"Pencairan Saldo sebesar Rp.{self.nominal_pencairan} telah berhasil"
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {
                'message': message,
                'title': '✅ Pecairan Saldo Berhasil',
                'sticky': False,
                'type': 'success',
                'timeout': 8000 
            }
        )



        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.pencairan.saldo',  
            'view_mode': 'form',
            'target': 'new',
            'name' : 'Pencairan Saldo',
            'context': {
                'default_santri_id' : False,
                'default_nominal_pencairan' : False,
                'default_catatan' : False,
            }
        }