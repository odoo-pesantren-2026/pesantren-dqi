# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class WizardKelolaPIN(models.TransientModel):
    _name = "wizard.kelola.pin"
    _description = "Wizard Kelola PIN Dompet Santri"

    def _get_active_account(self):
        """Domain untuk santri yang akunnya aktif"""
        return [('status_akun', '=', 'aktif')]

    kartu_santri = fields.Char(string="No. Kartu Santri")
    santri_id = fields.Many2one(
        'cdn.siswa', 
        string="Santri", 
        domain=_get_active_account,
        required=True
    )
    
    # Related fields untuk info santri
    nis = fields.Char(string="NIS", related='santri_id.nis', readonly=True)
    kelas_id = fields.Many2one('cdn.ruang_kelas', string='Kelas', related='santri_id.ruang_kelas_id', readonly=True)
    kamar_id = fields.Many2one('cdn.kamar_santri', string='Kamar', related='santri_id.kamar_id', readonly=True)
    
    # PIN fields
    current_pin = fields.Char(
        string="PIN Saat Ini", 
        compute='_compute_current_pin',
        readonly=True
    )
    new_pin = fields.Char(string="PIN Baru", size=6)
    confirm_pin = fields.Char(string="Konfirmasi PIN Baru", size=6)
    
    # Untuk toggle visibility PIN
    show_pin = fields.Boolean(string="Tampilkan PIN", default=False)

    @api.depends('santri_id', 'show_pin')
    def _compute_current_pin(self):
        for record in self:
            if record.santri_id and record.santri_id.partner_id:
                pin = record.santri_id.partner_id.wallet_pin
                if pin:
                    if record.show_pin:
                        record.current_pin = pin
                    else:
                        record.current_pin = '••••'
                else:
                    record.current_pin = '(Belum ada PIN)'
            else:
                record.current_pin = False

    @api.onchange('santri_id')
    def _onchange_santri_id(self):
        """Saat santri dipilih, isi no kartu otomatis"""
        for record in self:
            if record.santri_id:
                record.kartu_santri = record.santri_id.barcode_santri
            else:
                record.kartu_santri = False

    @api.onchange('kartu_santri')
    def _onchange_kartu_santri(self):
        """Saat no kartu diisi, cari santri yang sesuai"""
        if self.kartu_santri:
            domain = [
                ('barcode_santri', '=', self.kartu_santri),
                ('status_akun', '=', 'aktif')
            ]
            santri = self.env['cdn.siswa'].search(domain, limit=1)

            if not santri:
                # Cek apakah kartu ada tapi akun tidak aktif
                santri_nonaktif = self.env['cdn.siswa'].search([
                    ('barcode_santri', '=', self.kartu_santri)
                ], limit=1)

                if santri_nonaktif:
                    self.kartu_santri = False
                    return {
                        'warning': {
                            'title': 'Akun Tidak Aktif',
                            'message': f"Kartu ditemukan untuk '{santri_nonaktif.name}', tetapi akun santri tidak aktif. Aktifkan akun terlebih dahulu."
                        }
                    }
                else:
                    self.kartu_santri = False
                    return {
                        'warning': {
                            'title': 'Data Tidak Ditemukan',
                            'message': f"Tidak ditemukan santri dengan nomor kartu tersebut."
                        }
                    }
            else:
                self.santri_id = santri.id

    def action_toggle_pin(self):
        """Toggle visibility PIN"""
        self.ensure_one()
        self.show_pin = not self.show_pin
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.kelola.pin',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'name': 'Kelola PIN Dompet Santri',
        }

    def action_submit(self):
        """Simpan perubahan PIN"""
        self.ensure_one()
        
        if not self.santri_id:
            raise UserError("Silakan pilih santri terlebih dahulu.")
        
        if not self.santri_id.partner_id:
            raise UserError("Santri tidak memiliki partner yang terkait.")
        
        # Validasi PIN baru
        if not self.new_pin:
            raise UserError("PIN baru harus diisi.")
        
        if len(self.new_pin) < 4:
            raise UserError("PIN minimal 4 digit.")
        
        if not self.new_pin.isdigit():
            raise UserError("PIN harus berupa angka.")
        
        if self.new_pin != self.confirm_pin:
            raise UserError("PIN baru dan konfirmasi PIN tidak sama.")
        
        # Update PIN
        old_pin = self.santri_id.partner_id.wallet_pin or '(kosong)'
        self.santri_id.partner_id.wallet_pin = self.new_pin
        
        # Log perubahan di chatter santri
        self.santri_id.message_post(
            body=f"""
            <p><strong>PIN Dompet Diubah</strong></p>
            <p>PIN dompet santri telah diubah oleh <b>{self.env.user.name}</b>.</p>
            """,
            message_type='notification'
        )
        
        # Notifikasi sukses
        message = f"PIN untuk {self.santri_id.name} berhasil diubah."
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {
                'message': message,
                'title': '✅ PIN Berhasil Diubah',
                'sticky': False,
                'type': 'success',
                'timeout': 5000 
            }
        )

        # Buka wizard lagi untuk kelola santri lain
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.kelola.pin',
            'view_mode': 'form',
            'target': 'new',
            'name': 'Kelola PIN Dompet Santri',
            'context': {
                'default_santri_id': False,
                'default_kartu_santri': False,
            }
        }
