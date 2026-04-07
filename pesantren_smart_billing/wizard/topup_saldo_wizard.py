# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class TopupSaldoWizard(models.TransientModel):
    """
    Wizard untuk menampilkan informasi VA dan top-up saldo santri.
    """
    _name = 'smart.billing.topup.wizard'
    _description = 'Top-up Saldo via Smart Billing'

    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True
    )
    siswa_id = fields.Many2one(
        'cdn.siswa',
        string='Santri',
        compute='_compute_siswa_id'
    )

    # VA Information (readonly)
    va_number = fields.Char(
        string='Nomor Virtual Account',
        related='partner_id.va_saku',
        readonly=True
    )
    va_bank = fields.Char(
        string='Bank',
        related='partner_id.va_saku_bank',
        readonly=True
    )
    va_expiry = fields.Date(
        string='Berlaku Hingga',
        related='partner_id.va_saku_expiry',
        readonly=True
    )

    # Current balance
    saldo_saat_ini = fields.Float(
        string='Saldo Saat Ini',
        compute='_compute_saldo',
        digits=(16, 2)
    )
    saldo_display = fields.Char(
        string='Saldo (Formatted)',
        compute='_compute_saldo'
    )

    # Instructions
    instruksi = fields.Text(
        string='Cara Top-up',
        compute='_compute_instruksi'
    )

    @api.depends('partner_id')
    def _compute_siswa_id(self):
        for record in self:
            siswa = self.env['cdn.siswa'].search([
                ('partner_id', '=', record.partner_id.id)
            ], limit=1)
            record.siswa_id = siswa.id if siswa else False

    @api.depends('siswa_id')
    def _compute_saldo(self):
        for record in self:
            if record.siswa_id:
                record.saldo_saat_ini = record.siswa_id.saldo_uang_saku or 0
                record.saldo_display = f"Rp{record.saldo_saat_ini:,.0f}".replace(
                    ',', '.')
            else:
                record.saldo_saat_ini = 0
                record.saldo_display = "Rp0"

    @api.depends('va_number', 'va_bank')
    def _compute_instruksi(self):
        for record in self:
            if record.va_number and record.va_bank:
                record.instruksi = f"""
CARA TOP-UP SALDO:

1. Buka aplikasi Mobile Banking atau ATM bank Anda
2. Pilih menu Transfer / Virtual Account
3. Masukkan nomor VA: {record.va_number}
4. Masukkan nominal top-up sesuai keinginan Anda
5. Konfirmasi dan selesaikan pembayaran

Bank Tujuan: {record.va_bank}
Nomor VA: {record.va_number}

Catatan:
- Anda bisa transfer dengan nominal berapa saja
- Saldo akan otomatis bertambah setelah transfer berhasil
- Transfer bisa dari bank manapun (akan dikenakan biaya transfer antar bank)
                """.strip()
            else:
                record.instruksi = "Virtual Account belum tersedia."

    def action_copy_va(self):
        """Copy VA number to clipboard (opens notification with VA)"""
        self.ensure_one()

        if not self.va_number:
            raise UserError("Virtual Account belum tersedia.")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Nomor Virtual Account',
                'message': f"Bank: {self.va_bank}\nNo. VA: {self.va_number}\n\nSalin nomor ini untuk transfer.",
                'type': 'info',
                'sticky': True,
            }
        }

    def action_view_history(self):
        """View top-up history for this santri"""
        self.ensure_one()

        return {
            'name': f'Riwayat Top-up - {self.siswa_id.name if self.siswa_id else ""}',
            'type': 'ir.actions.act_window',
            'res_model': 'smart.billing.transaction',
            'view_mode': 'list,form',
            'domain': [
                ('partner_id', '=', self.partner_id.id),
                ('transaction_type', '=', 'va_topup'),
            ],
            'context': {'create': False},
            'target': 'current',
        }
