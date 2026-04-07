from odoo import api, fields, models


class sesi_halaqoh(models.Model):
    _name = 'cdn.sesi_halaqoh'
    _description = 'Tabel Sesi Halaqoh'

    name = fields.Char(string='Sesi Halaqoh', required=True)
    keterangan = fields.Char(string='Keterangan')
    
