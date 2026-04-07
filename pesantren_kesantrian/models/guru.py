from odoo import api, fields, models
import re
from odoo.exceptions import UserError


class Guru(models.Model):
    _inherit = 'hr.employee'

    @api.constrains('work_email')
    def _check_unique_email(self):
        for guru in self:
            if guru.work_email:
                existing = self.search(
                    [('work_email', '=', guru.work_email), ('id', '!=', guru.id)], limit=1)
                if existing:
                    raise UserError('Email sudah ada!')

    work_email = fields.Char(string='Email', required=True)

    @api.model
    def create(self, vals):
        res = super(Guru, self).create(vals)
        # create partner
        partner = self.env['res.partner'].create({
            'name': res.name,
            'email': res.work_email,
        })
        # create user
        users = self.env['res.users'].create({
            'login': res.work_email,
            'partner_id': partner.id,
            'password': 'employee',
        })
        res.user_id = users.id

        return res

    def unlink(self):
        for guru in self:
            users = self.env['res.users'].browse(guru.user_id.id)
            if users:
                partner = users.partner_id
                users.unlink()
                partner.unlink()
        return super(Guru, self).unlink()

    @api.constrains('work_email')
    def _check_email(self):
        for guru in self:
            if guru.work_email:
                # regex
                if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', guru.work_email):
                    raise UserError('Email tidak valid!')
