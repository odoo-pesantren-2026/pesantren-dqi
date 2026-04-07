# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Ekstrakulikuler(models.Model):
    _name = 'cdn.ekstrakulikuler'
    _description = 'Data Ekstrakulikuler'

    name = fields.Char(string='Nama', required=True,
                       help="Nama kegiatan ekstrakurikuler")
    is_wajib = fields.Boolean(string='Ekstra Wajib', required=True,
                              help="Centang jika ekstrakurikuler ini wajib diikuti oleh setiap siswa")
    tingkat_ids = fields.Many2many(
        comodel_name="cdn.tingkat",  string="Tingkat", required=True)
