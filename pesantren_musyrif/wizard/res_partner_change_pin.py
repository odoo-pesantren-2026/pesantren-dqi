from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ResPartnerChangePin(models.TransientModel):
    _name = 'res.partner.change.pin'

    wallet_pin = fields.Char(string='PIN Dompet')

    # def action_open_custom_wizard(self):
    #      return {
    #         # 'type': 'ir.actions.client',
    #         # 'tag': 'open_custom_pin_wizard',
    #         'type': 'ir.actions.client',
    #         'tag': 'open_custom_pin_wizard',
    #         'target': 'new',
    #         'context': {'default_id': self.id}
    #     }



    @api.constrains('wallet_pin')
    def _check_pin_type(self):
        for record in self:
            if not record.wallet_pin.isdigit():
                raise UserError("PIN harus berupa angka!")
            
            if len(record.wallet_pin) != 6:
                raise UserError("PIN harus terdiri dari 6 digit!")


    def _get_partner_id(self):
        context = self._context
        active_id = context.get('active_id')
        model = context.get('active_model')

        partner_id = active_id
        if model == 'cdn.siswa':
            Siswa = self.env['cdn.siswa'].browse(active_id)
            partner_id = Siswa.partner_id.id
        return partner_id
    def change_pin(self):
        Partner = self.env['res.partner'].browse(self._get_partner_id())
        Partner.write({
            'wallet_pin':self.wallet_pin
        })



