from odoo import fields, models, _, api
from odoo.exceptions import UserError


class DompetSantriPinWizard(models.TransientModel):
    _name = 'dompet.santri.pin.wizard'
    _description = 'Konfirmasi PIN Dompet Santri'

    santri_id = fields.Many2one('cdn.siswa', string="Santri", required=True)
    nomor_tagihan = fields.Char(string="Nomor Tagihan")
    wallet_santri = fields.Float(related='santri_id.saldo_uang_saku', required=True, digits=(16, 0))
    santri_pin = fields.Char(string="Masukkan PIN", required=True)
    amount = fields.Float(string="Jumlah Pembayaran", required=True, digits=(16, 0))
    payment_id = fields.Many2one('account.payment.register', string="Pembayaran", required=True)
    invoice_id = fields.Many2one('account.move', string="Faktur", required=True)

    def action_confirm_payment(self):
        """Konfirmasi pembayaran setelah PIN divalidasi"""
        # Cek PIN
        santri_wallet_pin = self.santri_id.partner_id.wallet_pin

        if not self.santri_pin:
            raise UserError("PIN harus diisi")
        
        if self.santri_pin != santri_wallet_pin:
            raise UserError("PIN salah, coba lagi")
        
        # Cek saldo
        if self.santri_id.saldo_uang_saku < self.amount:
            raise UserError(f"Saldo {self.santri_id.name} tidak cukup untuk melakukan transaksi. Saldo tersedia: {self.santri_id.saldo_uang_saku:,.0f}")
        
        timestamp = fields.Datetime.now()
        
        # Membuat transaksi Uang Saku (keluar)
        self.env['cdn.uang_saku'].sudo().create({
            'tgl_transaksi': timestamp,
            'siswa_id': self.santri_id.partner_id.id,  
            'jns_transaksi': 'keluar',
            'amount_out': self.amount, 
            'validasi_id': self.env.user.id,
            'validasi_time': timestamp,
            'keterangan': f'Pembayaran tagihan {self.invoice_id.name or self.invoice_id.ref or ""}',
            'state': 'confirm',
        })

        # Update saldo santri
        partner_pengirim = self.santri_id.partner_id
        partner_pengirim.saldo_uang_saku = partner_pengirim.calculate_saku()
        
        # Buat pembayaran pada invoice
        self.payment_id.action_create_payments()
        
        # Tampilkan notifikasi
        message = f"Pembayaran sebesar {self.amount:,.0f} berhasil dilakukan menggunakan Dompet Santri {self.santri_id.name}."
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {
                'message': message,
                'title': 'Pembayaran Berhasil',
                'sticky': False,
                'type': 'success',
                'timeout': 8000 
            }
        )
        
        # Opsi untuk menampilkan wizard unduh transaksi
        return {
            'type': 'ir.actions.act_window',
            'name': 'Unduh Transaksi',
            'res_model': 'invoice.download.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_invoice_id': self.invoice_id.id,
                'default_invoice_name': self.invoice_id.name or self.invoice_id.ref or '',
            },
            'views': [(False, 'form')],
        }