from odoo import api, fields, models
from odoo.exceptions import UserError
import logging
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

class WizardTransferSaldo(models.TransientModel):
    _name = 'wizard.transfer.saldo'

    def _default_validation(self):
        return self.env.user.id
    
    santri_id        = fields.Many2one('cdn.siswa', string="Santri", required=True)
    kartu            = fields.Char(string="Kartu Santri", required=True)
    wallet_santri    = fields.Float(related='santri_id.saldo_uang_saku', required=True, digits=(16, 0))
    
    santri_penerima  = fields.Many2one('cdn.siswa', string="Santri", required=True)
    kartu_penerima   = fields.Char(string="Kartu Santri", required=True)
    wallet_penerima  = fields.Float(related='santri_penerima.saldo_uang_saku', required=True, digits=(16, 0))
    jumlah_transfer = fields.Float(string="Nominal Transfer", required=True, digits=(16,0))
    validasi_id     = fields.Many2one(comodel_name='res.users', string='Validasi', readonly=True, default=_default_validation)
    santri_pin      = fields.Char(string="Masukkan PIN", required=True)


    @api.onchange('santri_id')
    def _onchange_santri_id(self):
        if self.santri_id:

            if self.santri_id.status_akun in ['nonaktif', 'blokir']:
                nama_santri     = self.santri_id.name
                status_akun     = self.santri_id.status_akun

                self.santri_id  = False
                self.kartu      = False
                return {    
                    'warning': {
                        'title' :  'Akses Ditolak !',
                        'message': f"Transaksi tidak dapat diproses karena akun santri bernama {nama_santri} saat ini berada dalam status {status_akun}. Mohon hubungi pengurus pesantren untuk informasi lebih lanjut."
                    }
                }

            elif self.santri_id.saldo_uang_saku == 0:
                nama_santri     = self.santri_id.name
                self.santri_id  = False
                self.kartu      = False
                return {
                    'warning': {
                        'title': 'Perhatian !',
                        'message': f"Santri bernama {nama_santri} tidak memiliki saldo"
                    }
                }
                
            self.kartu = self.santri_id.barcode_santri

        else:
            self.kartu = False

    @api.onchange('santri_penerima')
    def _onchange_santri_penerima(self):
        if self.santri_penerima:

            if self.santri_penerima.status_akun in ['nonaktif', 'blokir']:
                nama_santri          = self.santri_penerima.name
                status_akun          = self.santri_penerima.status_akun
                self.santri_penerima = False
                self.kartu_penerima  = False
                return {
                    'warning': {
                        'title' :  'Akses Ditolak !',
                        'message': f"Transaksi tidak dapat diproses karena akun santri bernama {nama_santri} saat ini berada dalam status {status_akun}. Mohon hubungi pengurus pesantren untuk informasi lebih lanjut."
                    }
                }

            self.kartu_penerima = self.santri_penerima.barcode_santri
        else:
            self.kartu_penerima = False

    @api.onchange('kartu')
    def _onchange_kartu(self):
        """Mengisi siswa_id berdasarkan barcode yang diinput"""
        if self.kartu:
            siswa = self.env['cdn.siswa'].search([('barcode_santri', '=', self.kartu)], limit=1)
            
            if siswa:
                self.santri_id = siswa.id
                if siswa.saldo_uang_saku == 0:
                    return {
                        'warning': {
                            'title': 'Perhatian !',
                            'message': f"Santri bernama {siswa.name} tidak memiliki saldo"
                        }
                    }
            else:
                self.santri_id = False
                barcode_sementara = self.kartu
                self.kartu = False
                return {
                    'warning': {
                        'title': "Perhatian !",
                        'message': f"Data Santri dengan Kartu Santri {barcode_sementara} tidak ditemukan."
                    }
                }

    @api.onchange('kartu_penerima')
    def _onchange_kartu_penerima(self):
        if self.kartu_penerima:
            siswa = self.env['cdn.siswa'].search([('barcode_santri', '=', self.kartu_penerima)], limit=1)
            
            if siswa:
                self.santri_penerima = siswa.id
            else:
                self.santri_penerima = False
                barcode_sementara = self.kartu_penerima  
                self.kartu_penerima = False
                return {
                    'warning' : {
                        'title' : "Perhatian !",
                        'message': f"Data Santri dengan Kartu Santri {barcode_sementara} tidak ditemukan."
                    }
                }

    @api.constrains('pin')
    def _check_pin_type(self):
        for record in self:
            if not record.pin.isdigit():
                raise UserError("PIN Harus Berupa Angka")

            if len(record.pin) != 6:
                raise UserError("PIN harus terdiri dari 6 digit!")

            if record.pin != record.confirm_pin:
                raise UserError("PIN dan Konfirmasi PIN tidak cocok!")


    def action_transfer(self):
        timestamp = fields.Datetime.now()

        santri_wallet_pin = self.santri_id.partner_id.wallet_pin

        if self.santri_pin != santri_wallet_pin:
            raise UserError("PIN salah coba lagi")
        
        if self.santri_id == self.santri_penerima:
            raise UserError("Santri pengirim dan penerima tidak boleh sama")
                
        if self.jumlah_transfer <= 0:
            raise UserError("Nominal transfer harus lebih dari 0")

        if self.santri_id.saldo_uang_saku < self.jumlah_transfer:
            raise UserError(f"Saldo {self.santri_id.name} tidak cukup untuk melakukan transaksi. Saldo tersedia: {self.santri_id.saldo_uang_saku:,.0f}")
        
        # Transaksi Pengirim (Keluar)
        self.env['cdn.uang_saku'].sudo().create({
            'tgl_transaksi': timestamp,
            'siswa_id': self.santri_id.partner_id.id,  
            'jns_transaksi': 'keluar',
            'amount_out': self.jumlah_transfer, 
            'validasi_id': self.env.user.id,
            'validasi_time': timestamp,
            'keterangan': f'Transfer saldo ke {self.santri_penerima.name}',
            'state': 'confirm',
        })

        partner_pengirim = self.santri_id.partner_id
        partner_pengirim.saldo_uang_saku = partner_pengirim.calculate_saku()

        # Transaksi Penerima (Masuk)
        self.env['cdn.uang_saku'].sudo().create({
            'tgl_transaksi': timestamp,
            'siswa_id': self.santri_penerima.partner_id.id,  
            'jns_transaksi': 'masuk',  
            'amount_in': self.jumlah_transfer,  
            'validasi_id': self.env.user.id,
            'validasi_time': timestamp,
            'keterangan': f'Diterima transfer dari {self.santri_id.name}',
            'state': 'confirm',
        })
        
        partner_penerima = self.santri_penerima.partner_id
        partner_penerima.saldo_uang_saku = partner_penerima.calculate_saku()


        message = f"Transfer sebesar {self.jumlah_transfer:,.0f} berhasil dikirim dari {self.santri_id.name} ke {self.santri_penerima.name}."
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {
                'message': message,
                'title': 'Transfer Berhasil',
                'sticky': False,
                'type': 'success',
                'timeout': 8000 
            }
        )

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.transfer.saldo',  
            'view_mode': 'form',
            'target': 'new',
            'name' : 'Transfer Antar Santri',
            'context': {
                'default_name': 'Transfer Antar Santri',
                'default_santri_id': False,  
                'default_santri_penerima': False,
                'default_kartu': False,
                'default_kartu_penerima': False,
                'default_jumlah_transfer': 0.0,
            }
        }
