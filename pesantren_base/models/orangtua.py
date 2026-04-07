# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class OrangTua(models.Model):

    _name = "cdn.orangtua"
    _description = "Tabel Data Akun Orang Tua"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {"res.partner": "partner_id"}

    partner_id = fields.Many2one(
        'res.partner', 'Partner', required=True, ondelete="cascade")
    nik = fields.Char(
        string="NIK",  help="Nomor Induk Kependudukan Orang Tua/Wali")
    hubungan = fields.Selection(selection=[(
        'ayah', 'Ayah'), ('ibu', 'Ibu'), ('wali', 'Wali')],  string="Hubungan",  help="Status hubungan dengan siswa (Ayah/Ibu/Wali)")
    label = fields.Many2many('res.partner.category', 'Tag')
    siswa_ids = fields.One2many(
        comodel_name="cdn.siswa",  inverse_name="orangtua_id",  string="Siswa",  help="", ondelete='cascade')
    isLimit = fields.Boolean(
        string="Akses Limit", help='Saat Diaktifkan sistem akan memberikan orang tua akses untuk mengatur limit penggunaan saldo anaknya')

    user_id = fields.Many2one(
        'res.users',
        string="User Login",
        help="Akun login yang terhubung dengan orang tua",
        ondelete="cascade"
    )

    password = fields.Char(
        string="Password", help="Password login untuk akun orang tua", store=True)

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if record.user_id and record.partner_id:
            record.partner_id.user_id = record.user_id
        return record

    @api.model
    def default_get(self, fields):
        res = super(OrangTua, self).default_get(fields)
        res['jns_partner'] = 'ortu'
        return res

    def _update_user_group_limit(self):
        group_orangtua_limit = self.env.ref(
            'pesantren_kesantrian.group_kesantrian_orang_tua_acces_limit')

        for record in self:
            user = record.partner_id.user_ids[:1]
            if not user:
                continue

            if record.isLimit:
                if group_orangtua_limit not in user.groups_id:
                    user.groups_id = [(4, group_orangtua_limit.id)]
            else:
                if group_orangtua_limit in user.groups_id:
                    user.groups_id = [(3, group_orangtua_limit.id)]
