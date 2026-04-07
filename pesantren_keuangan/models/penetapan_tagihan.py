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

    def create_invoice(self):
        # Let the base method create the invoices first
        res = super(PenetapanTagihan, self).create_invoice()
        
        # Capture the generation sequence ID from the returned action domain
        domain = res.get('domain', [])
        gen_invoice = False
        for leaf in domain:
            if isinstance(leaf, (list, tuple)) and leaf[0] == 'generate_invoice':
                gen_invoice = leaf[2]
        
        # Update all newly created invoices with the wizard's settings
        if gen_invoice:
            new_invoices = self.env['account.move'].search([('generate_invoice', '=', gen_invoice)])
            if new_invoices:
                new_invoices.write({
                    'cara_pembayaran': self.cara_pembayaran,
                    'activate_automation': self.activate_automation,
                })
        
        return res
