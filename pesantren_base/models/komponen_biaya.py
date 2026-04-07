# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class komponen_biaya(models.Model):

    _name = "cdn.komponen_biaya"
    _description = "Tabel Komponen Biaya"

    name = fields.Char(required=True, string="Nama",
                       help="Isikan nama komponen biaya, misal: Uang Pangkal, SPP Bulanan")
    tipe_bayar = fields.Selection(selection=[('cicil', 'Cicilan'), (
        'tunai', 'Tunai')],  string="Tipe bayar", required=True, default='tunai', help="")
    product_id = fields.Many2one(
        comodel_name="product.product", string='Produk', required=True)
    biaya_tahunan = fields.One2many(
        comodel_name='cdn.biaya_tahunajaran', inverse_name='name', string='Biaya Per Tahun Ajaran')
    active = fields.Boolean(string='Aktif', default=True)
    kredit = fields.Boolean(string="Kredit", default=False,
                            help='Tagihan bisa dibayar dengan cicilan')
    autodebet = fields.Boolean(
        string="Autodebet", default=False, help='Tagihan otomatis terpotong saat topup')
