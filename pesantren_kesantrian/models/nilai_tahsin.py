from odoo import api, fields, models


class NilaiTahsin(models.Model):
    _name = 'cdn.nilai_tahsin'
    _description = 'Tabel Nilai Tahsin'

    name = fields.Char(string='Nilai Tahsin', required=True)
    lulus = fields.Boolean(string='Lulus')
