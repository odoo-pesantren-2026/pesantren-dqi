from odoo import models, fields, api
from datetime import date, datetime


class PembagianEkstra(models.Model):
    _name = "cdn.pembagian_ekstra"
    _description = "Tabel untuk Pembagian Ekstrakulikuler untuk Santri"

    def _get_domain_guru(self):
        admin_user_ids = self.env.ref('base.group_system').users.ids

        return [
            '|',
            ('user_id', '=', admin_user_ids),
            ('jns_pegawai_ids.code', 'in', ['guru', 'superadmin'])
        ]

    name = fields.Many2one("cdn.ekstrakulikuler", string="Ekstrakulikuler")
    siswa_ids = fields.Many2many(
        'cdn.siswa', string='Daftar Siswa', ondelete='cascade')
    penanggung_id = fields.Many2one(
        "hr.employee",
        string="Penanggung Jawab",
        help="Guru yang bertanggung jawab membina atau mengelola kegiatan ekstrakurikuler ini",
        domain=lambda self: self.env['cdn.pembagian_ekstra']._get_domain_guru()
    )

    @api.model
    def write(self, vals):
        record = super().write(vals)
        for rec in self:
            if rec.siswa_ids and rec.name:
                rec.siswa_ids.write({
                    'ekstrakulikuler_ids': [(4, rec.name.id)]
                })
        return record
