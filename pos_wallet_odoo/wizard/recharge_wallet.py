# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class RechargeWallet(models.TransientModel):
    """Wallet recharge fields"""
    _name = "recharge.wallet"
    _description = "Create Wallet Recharge Of Each Customer"
    # _inherits = {'res.partner': 'active_id'}

    # active_id = fields.Many2one('res.partner', required=True, ondelete='cascade')
    

    journal_id = fields.Many2one("account.journal", string="Jurnal Pembayaran",
                                 help="Pilih jenis jurnal")
    recharge_amount = fields.Float(string="Jumlah isi ulang",
                                   help="Jumlah pengisian ulang di dompet")


# class RechargeWallet(models.TransientModel):
#     """Wallet recharge fields"""
#     _name = "recharge.wallet"
#     _description = "Create Wallet Recharge Of Each Customer"
    
#     partner_ids = fields.Many2many('res.partner', string="Santri", ondelete='cascade')
#     journal_id = fields.Many2one("account.journal", string="Jurnal Pembayaran",
#                                help="Pilih jenis jurnal")
#     recharge_amount = fields.Float(string="Jumlah isi ulang",
#                                  help="Jumlah pengisian ulang di dompet")
    
#     # Fungsi untuk konfirmasi isi saldo
#     def action_confirm(self):
#         # Cek santri yang saldo tidak cukup
#         insufficient_partners = []
        
#         for partner in self.partner_ids:
#             # Asumsi ada field wallet_balance di res.partner
#             if partner.wallet_balance < self.recharge_amount:
#                 insufficient_partners.append(partner.name)
        
#         # Tampilkan error dengan nama santri yang saldo tidak cukup
#         if insufficient_partners:
#             raise ValidationError(
#                 f"Saldo tidak mencukupi untuk santri berikut: {', '.join(insufficient_partners)}"
#             )
            
#         # Proses isi saldo untuk santri yang lolos validasi
#         for partner in self.partner_ids:
#             partner.wallet_balance += self.recharge_amount
            
#         return {'type': 'ir.actions.act_window_close'}
    
#     # Fungsi untuk konfirmasi limit saldo (tanpa validasi saldo)
#     def action_limit_confirm(self):
#         for partner in self.partner_ids:
#             # Asumsi ada field wallet_limit di res.partner
#             partner.wallet_limit = self.recharge_amount
            
#         return {'type': 'ir.actions.act_window_close'}





