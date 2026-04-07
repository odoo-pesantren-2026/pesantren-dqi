from odoo import models, fields

class LihatPasswordWizard(models.TransientModel):
    _name = 'lihat.password.wizard'
    _description = 'Lihat Kata Sandi'

    password = fields.Char(string="Kata Sandi", readonly=True)
