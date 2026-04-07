from odoo import api, fields, models


class sesi_tahsin(models.Model):
    _name = 'cdn.sesi_tahsin'
    _description = 'Tabel Sesi Tahsin'

    name = fields.Char(string='Sesi Tahsin', required=True)
    keterangan = fields.Char(string='Keterangan')
    
