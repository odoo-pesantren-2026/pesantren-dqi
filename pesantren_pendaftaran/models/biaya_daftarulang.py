#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import os 

class biaya_daftarulang(models.Model):

    _name               = "ubig.biaya_daftarulang"
    _description        = "Tabel Biaya Tahun Ajaran"

    name                = fields.Many2one(comodel_name="ubig.komponen_biaya", string="Komponen Biaya", required=True, ondelete="cascade")
    nominal             = fields.Integer( string="Nominal",  help="")
    daftarulang_id      = fields.Many2one(comodel_name="ubig.pendidikan",  string="Jenjang Pendidikan",  help="")
# class biaya_daftarulang(models.Model):

#     _name               = "ubig.biaya_daftarulang"
#     _description        = "Tabel Biaya Tahun Ajaran"
#     # Versi Old
#     # name                = fields.Many2one(comodel_name="ubig.komponen_biaya", string="Komponen Biaya", required=True, ondelete="cascade")
#     #Versi Baru
#     name                = fields.Char(string="Nama Biaya")
    gambar              = fields.Binary( string="Gambar Biaya",  help="", filename="Rincian Biaya")
    jenjang             = fields.Selection(selection=[('paud','PAUD'),('tk','TK'),('sdmi','SD / MI'),('smpmts','SMP / MTS'),('smama','SMA / MA'),('smk','SMK'), ('nonformal', 'Nonformal')], string='Jenjang', required=True)
    is_alumni           = fields.Boolean(string="Alumni DQI",  help="", default=False)
    is_pindahan_sd      = fields.Boolean(string="Pindahan SD",  help="", default=False)
    biaya_id            = fields.Many2one('ubig.pendidikan', string="Jenjang Pendidikan",  help="")

class RincianBiaya(models.Model):

    _name               = "ubig.rincian_biaya"
    _description        = "Tabel Rincian Biaya Tahun Ajaran"

    name                = fields.Char(string="Nama Biaya", required=True)
    gambar              = fields.Binary( string="Gambar Biaya",  help="", filename="Rincian Biaya")
    jenjang             = fields.Selection(related='biaya_id.jenjang', string='Jenjang')
    is_alumni           = fields.Boolean(string="Alumni DQI",  help="", default=False)
    is_pindahan_sd      = fields.Boolean(string="Pindahan SD",  help="", default=False)
    biaya_id            = fields.Many2one('ubig.pendidikan', string="Jenjang Pendidikan",  help="")