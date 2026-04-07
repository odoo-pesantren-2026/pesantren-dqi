from odoo import models, fields, api

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    # Field untuk menandai user orang tua
    is_parent_user = fields.Boolean(default=lambda self: self.env.user.has_group('pesantren_kesantrian.group_kesantrian_orang_tua'))

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        # Set default hanya untuk orang tua
        if self.env.user.has_group('pesantren_kesantrian.group_kesantrian_orang_tua'):
            # Set default journal ke Bank Amal Usaha
            bank_amal_usaha = self.env['account.journal'].search([
                ('name', 'ilike', 'Bank Amal Usaha')
            ], limit=1)

            if bank_amal_usaha:
                res['journal_id'] = bank_amal_usaha.id

                # Set default payment method ke Dompet Santri
                dompet_santri_method = self.env['account.payment.method.line'].search([
                    ('journal_id', '=', bank_amal_usaha.id),
                    ('name', 'ilike', 'Dompet Santri')
                ], limit=1)

                if dompet_santri_method:
                    res['payment_method_line_id'] = dompet_santri_method.id

        return res

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_register_payment(self):
        """Override action untuk orang tua"""
        if self.env.user.has_group('pesantren_kesantrian.group_kesantrian_orang_tua'):
            return {
                'name': 'Register Payment',
                'res_model': 'account.payment.register',
                'view_mode': 'form',
                'view_id': self.env.ref('pesantren_orangtua.view_account_payment_register_parent_form').id,
                'context': {
                    'active_model': 'account.move',
                    'active_ids': self.ids,
                    'is_parent_context': True,
                },
                'target': 'new',
                'type': 'ir.actions.act_window',
            }
        else:
            return super().action_register_payment()
