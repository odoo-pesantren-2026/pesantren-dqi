from odoo import api, fields, models
import logging
from odoo.exceptions import ValidationError, UserError


_logger = logging.getLogger(__name__)


class WizardRegisterKartu(models.TransientModel):
    _name = 'wizard.register.kartu.santri'
    _description = 'Wizard Registrasi Kartu Santri (Angka Acak Unik)'
    
    santri_id        = fields.Many2one('cdn.siswa', string="Santri", required=True)
    musyrif          = fields.Many2one(related='santri_id.musyrif_id', string="Musyrif")
    kelas            = fields.Many2one(related='santri_id.ruang_kelas_id', string="Kelas")
    kamar            = fields.Many2one(related='santri_id.kamar_id')
    halaqoh          = fields.Many2one(related='santri_id.halaqoh_id')
    kartu            = fields.Char(string="Kartu Santri Baru", required=True)
    kartu_lama       = fields.Char(string="Kartu Santri Lama", required=False)
    pin              = fields.Char(string="Masukkan PIN", required=True)
    confirm_pin      = fields.Char(string="Konfirmasi PIN", required=True)


    @api.onchange('kartu_lama')
    def _check_kartu_santri(self):
        if self.kartu_lama:
            siswa = self.env['cdn.siswa'].search([('barcode', '=', self.kartu_lama)], limit=1)
            
            if siswa.barcode:
                self.santri_id = siswa.id
             

    @api.onchange('santri_id')
    def _check_santri(self):
        if self.santri_id:
            if self.santri_id.barcode:
                self.kartu_lama = self.santri_id.barcode



    @api.onchange('kartu')
    def _onchange_kartu_santri(self):
        if self.kartu:
            if not self.kartu.isdigit():
                return  {
                    'warning': {
                        'title' : 'Perhatian !',
                        'message' : 'Kartu Santri harus berupa angka !'
                    }
                }
                
            existing_kartu = self.env['cdn.siswa'].search([('barcode', '=', self.kartu)], limit=1)
            if existing_kartu:
                self.kartu = False
                return {
                    'warning': {
                        'title': 'Registrasi gagal!',
                        'message': 'Kartu yang Anda masukkan sudah terdaftar dalam sistem.'
                    }
                }
            
    @api.constrains('pin')
    def _check_pin_type(self):
        for record in self:
            if not record.pin.isdigit():
                raise UserError("PIN Harus Berupa Angka")

            if len(record.pin) != 6:
                raise UserError("PIN harus terdiri dari 6 digit!")

                
    @api.constrains('pin', 'confirm_pin')
    def _check_confirm_pin(self):
        for record in self:
            if record.pin != record.confirm_pin:
                raise UserError("PIN dan Konfirmasi PIN tidak cocok!")


    def action_save_data(self):
        partner_id = self.santri_id.partner_id.id
        santri_id  = self.santri_id.id

        Partner = self.env['res.partner'].browse(partner_id)
        Partner.write({
            'wallet_pin' : self.pin,
        })

        Santri = self.env['cdn.siswa'].browse(santri_id)
        Santri.write({
            'barcode' : self.kartu,
            'barcode_santri' : self.kartu
        })

        message = f"Kartu santri telah berhasil didaftarkan"
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,  
            'simple_notification',
            {
                'message': message,
                'title': '✅ Registrasi Berhasil!',
                'sticky': False, 
                'type': 'success',
                'timeout': 150000, 
            }
        )
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Registrasi Kartu',
            'res_model': 'wizard.register.kartu.santri',
            'view_mode': 'form',
            'view_id': self.env.ref('pesantren_kesantrian.wizard_kartu_register_form').id,
            'target': 'new',
        }