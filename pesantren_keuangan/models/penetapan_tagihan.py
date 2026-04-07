from odoo import api, fields, models


class PenetapanTagihan(models.TransientModel):
    _inherit = 'generate.invoice'

    cara_pembayaran = fields.Selection([
        ('saldo', 'Saldo / Uang Saku Santri'),
        ('smart_billing', 'Smart Billing (VA BSI)'),
        ('manual', 'Manual / Tunai')
    ], string='Cara Pembayaran', required=True, default='saldo')

    activate_automation = fields.Boolean(string='Tagihan Otomatis', default=True,
                                         help="Jika diaktifkan, maka sistem akan otomatis menggunakan uang saku sebagai pembayaran tagihan.")

    @api.onchange('cara_pembayaran')
    def _onchange_cara_pembayaran(self):
        if self.cara_pembayaran != 'saldo':
            self.activate_automation = False
