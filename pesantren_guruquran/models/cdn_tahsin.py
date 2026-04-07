from odoo import models, fields


class CdnSiswa(models.Model):
    _inherit = 'cdn.tahsin_quran'

    fashohah = fields.Integer(string='Nilai Fashohah', help="Nilai aspek fashohah (kejelasan dan ketepatan makhraj huruf)")
    tajwid = fields.Integer(string='Nilai Tajwid', help="Nilai aspek tajwid (aturan dan cara membaca Al-Qur'an)")
    ghorib_musykilat = fields.Integer(string='Nilai Ghorib/Musykilat', help="Nilai aspek ghorib dan musykilat (bacaan-bacaan khusus yang berbeda)")
    suara_lagu = fields.Integer(string='Nilai Suara Lagu', help="Nilai aspek suara dan irama/lagu tilawah")
