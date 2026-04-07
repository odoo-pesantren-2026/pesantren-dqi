from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id', readonly=True)
    product_names = fields.Char(string="Produk", compute="_compute_product_names")
    telah_dibayar = fields.Monetary(string='Telah Dibayar', compute='_compute_telah_dibayar', currency_field='currency_id', store=True)
    total_tagihan = fields.Monetary(string='Total Tagihan', related='amount_total_signed',currency_field='currency_id',store=True)
    sisa_tagihan = fields.Monetary(string='Sisa Tagihan', related='amount_residual_signed',currency_field='currency_id',store=True)
    
    # Field untuk menampilkan total dengan store=True
    total_amount = fields.Monetary(string='Total Semua Tagihan', compute='_compute_total_amount', currency_field='currency_id', store=True)
    total_paid = fields.Monetary(string='Total Dibayar', compute='_compute_total_paid', currency_field='currency_id', store=True)
    total_residual = fields.Monetary(string='Total Sisa', compute='_compute_total_residual', currency_field='currency_id', store=True)

    @api.depends('invoice_line_ids.product_id')
    def _compute_product_names(self):
        for move in self:
            product_names = move.invoice_line_ids.mapped('product_id.name')
            move.product_names = ', '.join(product_names)

    @api.depends('amount_total_signed', 'amount_residual_signed')
    def _compute_telah_dibayar(self):
        for rec in self:
            rec.telah_dibayar = rec.amount_total_signed - rec.amount_residual_signed
            
    @api.depends() 
    def _compute_total_amount(self):
        domain = [('move_type', '=', 'out_invoice')]
        total = sum(self.env['account.move'].search(domain).mapped('amount_total_signed'))
        for record in self:
            record.total_amount = total
            
    @api.depends()  
    def _compute_total_paid(self):
        domain = [('move_type', '=', 'out_invoice')]
        total = sum(self.env['account.move'].search(domain).mapped('telah_dibayar'))
        for record in self:
            record.total_paid = total
            
    @api.depends() 
    def _compute_total_residual(self):
        domain = [('move_type', '=', 'out_invoice')]
        total = sum(self.env['account.move'].search(domain).mapped('amount_residual_signed'))
        for record in self:
            record.total_residual = total