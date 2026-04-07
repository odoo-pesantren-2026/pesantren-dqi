from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class PencairanSaldo(models.TransientModel):
    _name = "wizard.pencairan.saldo"
    _description = "Wizard Untuk Melakukan Pencairan Saldo Santri"

    santri_id = fields.Many2one('cdn.siswa', string="Santri", required=True)
    saldo_santri = fields.Float(string="Saldo Santri", readonly=True, digits=(16, 0))
    nominal_pencairan = fields.Float(string="Nominal", required=True, digits=(16, 0))
    kelas_id = fields.Many2one('cdn.ruang_kelas', string='Kelas', related='santri_id.ruang_kelas_id', readonly=True)
    kamar_id = fields.Many2one('cdn.kamar_santri', string='Kamar', related='santri_id.kamar_id', readonly=True)
    halaqoh_id = fields.Many2one('cdn.halaqoh', string='Halaqoh', related='santri_id.halaqoh_id', readonly=True)
    musyrif_id = fields.Many2one('hr.employee', string='Musyrif', related='santri_id.musyrif_id', readonly=True)
    kartu_santri = fields.Char(string="Kartu", required=False)
    catatan = fields.Text(string="Catatan")

    @api.onchange('santri_id')
    def _onchange_santri_id(self):
        for record in self:
            if record.santri_id and record.santri_id.partner_id:
                record.saldo_santri = record.santri_id.partner_id.saldo_uang_saku
                if not record.kartu_santri:
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
                santri = self.env['cdn.siswa'].search([('barcode', '=', self.kartu_santri)], limit=1)
            
            if santri:
                self.santri_id = santri.id
            else:
                return {
                    'warning': {
                        'title': 'Kartu Tidak Ditemukan',
                        'message': f"Tidak dapat menemukan kartu santri dengan kode '{self.kartu_santri}'"
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
        self.ensure_one()
        timestamp = fields.Datetime.now()
        partner = self.santri_id.partner_id

        if self.nominal_pencairan <= 0:
            raise UserError("Nominal pencairan harus lebih dari 0.")
        
        if self.nominal_pencairan > partner.saldo_uang_saku:
            raise UserError(f"Saldo tidak mencukupi. Saldo saat ini: Rp.{partner.saldo_uang_saku:,.0f}")

        # Create uang saku transaction
        self.env['cdn.uang_saku'].sudo().create({
            'tgl_transaksi': timestamp,
            'siswa_id': partner.id,  
            'jns_transaksi': 'keluar',
            'amount_out': self.nominal_pencairan, 
            'validasi_id': self.env.user.id,
            'validasi_time': timestamp,
            'keterangan': f'Pencairan Saldo Sebesar Rp.{self.nominal_pencairan:,.0f} - {self.catatan or ""}',
            'state': 'confirm',
        })
        
        # Trigger recompute
        partner.saldo_uang_saku = partner.calculate_saku()

        message = f"Pencairan Saldo sebesar Rp.{self.nominal_pencairan:,.0f} untuk {self.santri_id.name} telah berhasil."
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {
                'message': message,
                'title': '✅ Pencairan Saldo Berhasil',
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
                'default_kartu_santri': False,
            }
        }