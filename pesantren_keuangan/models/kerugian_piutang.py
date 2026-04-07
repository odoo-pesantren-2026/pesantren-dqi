# from odoo import api, fields, models
# from odoo.exceptions import UserError
# from datetime import timedelta, datetime
# import logging

# _logger = logging.getLogger(__name__)

# class TagihanKerugian(models.Model):
#     _inherit = "account.move"
    
#     # Menambahkan state 'kerugian' ke dalam selection field state bawaan Odoo
#     state = fields.Selection(selection_add=[('kerugian', 'Kerugian Piutang')], ondelete={'kerugian': 'cascade'})
    
#     # Field untuk mencatat alasan kerugian piutang
#     kerugian_piutang_alasan = fields.Text(string="Alasan Kerugian", help="Alasan mengapa tagihan ini dijadikan kerugian piutang")
    
#     # Field untuk mencatat tanggal ketika tagihan dijadikan kerugian piutang
#     kerugian_piutang_date = fields.Date(string="Tanggal Kerugian Piutang", readonly=True)
    
#     # Menampilkan di laporan kerugian piutang (untuk filter)
#     is_kerugian_piutang = fields.Boolean(string="Kerugian Piutang", default=False, 
#                                         help="Menandakan bahwa tagihan ini masuk kategori kerugian piutang",
#                                         compute="_compute_is_kerugian_piutang", store=True)
        
#     @api.depends('state')
#     def _compute_is_kerugian_piutang(self):
#         for record in self:
#             record.is_kerugian_piutang = record.state == 'kerugian'

#     def open_wizard_kerugian_piutang(self):
#         if any(move.state != 'posted' or move.payment_state == 'paid' or move.state == 'kerugian' for move in self):
#             raise UserError("Tagihan harus berstatus 'Posted', belum lunas, dan belum menjadi kerugian piutang.")
#         return {
#             'type': 'ir.actions.act_window',
#             'name': 'Konfirmasi Kerugian Piutang',
#             'res_model': 'tagihan.kerugian.wizard',
#             'view_mode': 'form',
#             'target': 'new',
#             'context': {'active_ids': self.ids}
#         }

#     def action_kerugian_piutang(self, alasan=None):
#         for move in self:
#             if move.state == 'posted' and move.payment_state != 'paid':
#                 move.write({
#                     'state': 'kerugian',
#                     'kerugian_piutang_date': fields.Date.today(),
#                     'kerugian_piutang_alasan': alasan or move.kerugian_piutang_alasan,
#                 })
#                 move.message_post(body=f"Tagihan diubah statusnya menjadi Kerugian Piutang. Alasan: {alasan or '-'}")
#             else:
#                 raise UserError("Hanya tagihan yang telah diposting dan belum lunas yang dapat dijadikan Kerugian Piutang.")

#     def action_recover_kerugian_piutang(self):
#         for move in self:
#             if move.state == 'kerugian':
#                 move.write({
#                     'state': 'posted',
#                     'kerugian_piutang_date': False,
#                     'kerugian_piutang_alasan': False,
#                 })
#                 move.message_post(body="Tagihan dipulihkan dari status Kerugian Piutang.")
#             else:
#                 raise UserError("Hanya tagihan dengan status Kerugian Piutang yang dapat dipulihkan.")

#     def action_open_kerugian_wizard(self):
#         return {
#             'type': 'ir.actions.act_window',
#             'name': 'Konfirmasi Kerugian Piutang',
#             'res_model': 'tagihan.kerugian.wizard',
#             'view_mode': 'form',
#             'target': 'new',
#             'context': {
#                 'active_ids': self.ids,
#                 'default_title': 'Konfirmasi Kerugian Piutang',
#             },
#         }