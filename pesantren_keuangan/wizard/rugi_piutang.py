# from odoo import api, fields, models
# from odoo.exceptions import UserError

# class TagihanKerugianWizard(models.TransientModel):
#     _name = 'tagihan.kerugian.wizard'
#     _description = 'Konfirmasi Kerugian Piutang'
    
#     title = fields.Char(string="Judul", default="Konfirmasi Kerugian Piutang", readonly=True)
#     alasan = fields.Text(
#         string="Alasan Kerugian", 
#         help="Alasan mengapa tagihan ini dijadikan kerugian piutang", 
#         required=True
#     )

#     def action_confirm(self):
#         active_ids = self.env.context.get('active_ids', [])
#         if not active_ids:
#             return {'type': 'ir.actions.act_window_close'}
            
#         if not self.alasan:
#             raise UserError("Silahkan isi alasan mengapa tagihan ini dijadikan kerugian piutang.")

#         tagihans = self.env['account.move'].browse(active_ids)
#         for tagihan in tagihans:
#             tagihan.action_kerugian_piutang(alasan=self.alasan)
            
#         return {'type': 'ir.actions.act_window_close'}