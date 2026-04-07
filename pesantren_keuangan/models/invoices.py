# # In models/account_move.py
# from odoo import models, fields, api

# class AccountMove(models.Model):
#     _inherit = 'account.move'
    
#     def action_payments_to_reconcile(self):
#         self.ensure_one()
#         return {
#             'name': 'Payments',
#             'type': 'ir.actions.act_window',
#             'view_mode': 'list,form',
#             'res_model': 'account.payment',
#             'domain': [('move_id', 'in', self.payment_move_line_ids.mapped('move_id').ids)],
#             'context': {'create': False}
#         }


# In models/account_move.py
from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    # Define new fields
    payment_move_line_ids = fields.Many2many(
        'account.move.line',
        string='Payment Move Lines',
        compute='_compute_payment_move_lines'
    )
    
    # Method to compute the related payment move lines
    def _compute_payment_move_lines(self):
        for move in self:
            move.payment_move_line_ids = self.env['account.move.line'].search([
                ('move_id.payment_id', '!=', False),
                ('move_id.payment_id.reconciled_bill_ids', 'in', move.id)
            ])
    
    # Also add the first method we needed
    def action_payments_to_reconcile(self):
        self.ensure_one()
        return {
            'name': 'Payments',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'account.payment',
            'domain': [('reconciled_bill_ids', 'in', self.ids)],
            'context': {'create': False}
        }