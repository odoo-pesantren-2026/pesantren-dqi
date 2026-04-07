from odoo import api, fields, models, exceptions

class WalletRechargeMass(models.TransientModel):
    _name = 'recharge.wallet.mass'
    _description = 'Mass Wallet Recharge Wizard'

    siswa_ids = fields.Many2many('res.partner', string="Santri", required=True)
    recharge_amount = fields.Float(string="Jumlah Isi Ulang", required=True, default=0)
    journal_id = fields.Many2one("account.journal", string="Jurnal Pembayaran", required=True)

    def action_confirm_mass_recharge(self):
        """Proses isi ulang saldo untuk banyak siswa"""
        if self.recharge_amount <= 1000:
            raise exceptions.UserError('Nilai isi ulang harus lebih dari 1000 Rupiah.')

        for siswa in self.siswa_ids:
            siswa.write({'wallet_balance': siswa.wallet_balance + self.recharge_amount})

        return {'type': 'ir.actions.act_window_close'}
