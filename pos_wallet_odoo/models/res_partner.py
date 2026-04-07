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
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """Add field into res partner"""
    _inherit = 'res.partner'

    # active_id = fields.Many2one('cdn.siswa', string='Customer Active')
    wallet_balance = fields.Float(string="Saldo Dompet",
                                  help="Keseimbangan dompet dari setiap karyawan", widget="integer")
    wallet_count = fields.Integer(string="Dompet",
                                  compute='_compute_wallet_count',
                                  help="Hitungan setiap dompet")

    def action_recharge(self):
        """Open wizard for wallet recharge"""

        context = dict(self.env.context)
        active_ids = context.get('active_ids', [])

        return {
            'name': 'Pengisian Saldo Dompet',
            'type': 'ir.actions.act_window',
            'res_model': 'recharge.wallet',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_partner_ids': active_ids}
        }

    def action_recharge_mass(self):
        """Open wizard for wallet recharge"""

        context = dict(self.env.context)
        active_ids = context.get('active_ids', [])

        return {
            'name': 'Wallet Recharge',
            'type': 'ir.actions.act_window',
            'res_model': 'recharge.wallet.mass',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_partner_ids': active_ids}
        }

    

    # def action_recharge_mass(self):
    #     "Membuka Modul Wallet Recharge"
    #     active_ids  = self.ids
    #     return {
    #         'name': 'Isi Ulang Dompet',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'recharge.wallet.mass',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {'default_partner_ids': active_ids}
    #     }

    # def action_recharge_mass(self):
    #     """Opens the Wallet Recharge Wizard"""
    #     # Get the actual IDs of the selected records, not just the selection order
    #     active_ids = self.env.context.get('active_ids', [])
    #     selected_records = self.browse(active_ids)
    #     actual_ids = selected_records.ids
        
    #     return {
    #         'name': 'Isi Ulang Dompet',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'recharge.wallet.mass',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {
    #             'active_ids': actual_ids,
    #             'active_model': self._name,
    #             'default_siswa_ids': [(6, 0, actual_ids)],
    #         }
    # }


    # def action_recharge(self):
    #     """Open wizard for wallet recharge"""
    #     context = dict(self.env.context)
    #     active_ids = context.get('active_ids', [])
    
    #     return {
    #         'name': 'Wallet Recharge',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'recharge.wallet',
    #         'view_mode': 'form',
    #         'view_id': self.env.ref('pos_wallet_odoo.recharge_wallet_view_form').id,
    #         'target': 'new',
    #         'context': {'default_partner_ids': active_ids}
    #     }

    def action_limit_wallet(self):
        """Open wizard for wallet limit"""
        context = dict(self.env.context)
        active_ids = context.get('active_ids', [])
        
        return {
            'name': 'Limit Saldo Dompet',
            'type': 'ir.actions.act_window',
            'res_model': 'recharge.wallet',
            'view_mode': 'form',
            'view_id': self.env.ref('pos_wallet_odoo.limit_wallet_view_form').id,
            'target': 'new',
            'context': {'default_partner_ids': active_ids}
        }

    def action_number_of_wallet(self):
        """Wallet balance tree view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Wallet',
            'view_mode': 'tree',
            'res_model': 'pos.wallet.transaction',
            'domain': [('customer', '=', self.name)],
            'context': "{'create': False}"
        }

    def _compute_wallet_count(self):
        """Count of wallet balance"""
        for record in self:
            record.wallet_count = self.env['pos.wallet.transaction'].search_count(
                [('customer', '=', self.name)])
    
    def write(self, vals):
        """Override write to trigger auto-payment when saldo_uang_saku increases"""
        # Store old balance before update
        old_balances = {rec.id: rec.saldo_uang_saku for rec in self}
        
        res = super(ResPartner, self).write(vals)
        
        # AUTO-PAYMENT: Trigger saat saldo_uang_saku di top-up
        if 'saldo_uang_saku' in vals:
            for record in self:
                old_balance = old_balances.get(record.id, 0)
                new_balance = record.saldo_uang_saku
                
                # Only trigger if balance INCREASED
                if new_balance > old_balance:
                    _logger.info(f"💳 Wallet top-up detected for {record.name}: {old_balance} → {new_balance}")
                    record._try_auto_pay_unpaid_invoices()
        
        return res
    
    def _try_auto_pay_unpaid_invoices(self):
        """Try to auto-pay unpaid invoices from saldo_uang_saku"""
        self.ensure_one()
        
        # Find unpaid invoices for this partner
        unpaid_invoices = self.env['account.move'].search([
            ('partner_id', '=', self.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
            ('amount_residual', '>', 0)
        ], order='invoice_date asc')  # Pay oldest first
        
        if not unpaid_invoices:
            _logger.info(f"No unpaid invoices for {self.name}")
            return
        
        paid_count = 0
        skipped_count = 0
        
        for invoice in unpaid_invoices:
            # Refresh saldo setelah setiap payment
            self.env.cr.commit()  # Commit untuk refresh data
            current_balance = self.saldo_uang_saku
            
            # Check if still have enough balance
            if current_balance >= invoice.amount_residual:
                try:
                    invoice._try_auto_pay_from_wallet()
                    paid_count += 1
                    _logger.info(f"✅ Paid invoice {invoice.name}")
                except Exception as e:
                    _logger.error(f"Error auto-paying invoice {invoice.name}: {e}")
                    skipped_count += 1
            else:
                # Not enough balance for this invoice
                skipped_count += 1
                _logger.info(f"⏸️ Skipped invoice {invoice.name}: need {invoice.amount_residual}, have {current_balance}")
                break  # Stop trying since we sort by date
        
        if paid_count > 0:
            _logger.info(f"✅ Auto-paid {paid_count} invoice(s) for {self.name}, skipped {skipped_count}")



    @api.model
    def write_value(self, balance, order, session, price, currency_id):
        """Write remaining balance into customer wallet balance"""
        self.env['res.partner'].browse(order['id']).write({
            'wallet_balance': balance
        })
        self.env['pos.wallet.transaction'].create({
            'type': "Debit",
            'customer': order['name'],
            'amount': price,
            'pos_order': session,
            'currency': currency_id,
        })
