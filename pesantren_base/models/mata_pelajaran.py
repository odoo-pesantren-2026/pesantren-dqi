# -*- coding: utf-8 -*-

from odoo import api, fields, models


class MataPelajaran(models.Model):
    _name = 'cdn.mata_pelajaran'
    _description = 'Daftar Mata Pelajaran'

    name = fields.Char(string='Nama Matpel', required=True,
                       help="Nama lengkap mata pelajaran")
    urut = fields.Integer(string='No. Urut', default=0,
                          readonly=True, help="Urutan tampil mata pelajaran")
    kode = fields.Char(string='Kode Matpel', required=True,
                       help="Kode singkatan atau identifier mata pelajaran (harus unik)")
    kategori = fields.Selection([
        ('akademik', 'Akademik'),
        ('diniyyah', 'Diniyyah'),
        ('tahfidz', 'Tahfidz'),
        ('ekstrakurikuler', 'Ekstrakurikuler'),
        ('lainnya', 'Lainnya')
    ], string='Kategori Matpel')
    jenjang = fields.Selection([
        ('paud', 'PAUD'),
        ('tk', 'TK'),
        ('rtq', 'Rumah Tahfidz Quran'),
        ('sd', 'SD'),
        ('smp', 'SMP'),
        ('sma', 'SMA'),
        ('nonformal', 'Nonformal'),
    ], string='Jenjang Pendidikan', required=True)
    tingkat_id = fields.Many2one('cdn.tingkat', string='Kelas')
    jurusan_id = fields.Many2one(
        comodel_name='cdn.master_jurusan', string='Jurusan / Peminatan')
    guru_ids = fields.Many2many(
        comodel_name='hr.employee',
        string='Guru',
        domain=lambda self: self.env['cdn.mata_pelajaran']._get_domain_guru()
    )

    def _get_domain_guru(self):
        admin_user_ids = self.env.ref('base.group_system').users.ids

        return [
            '|',
            ('user_id', '=', admin_user_ids),
            ('jns_pegawai_ids.code', 'in', ['guru', 'guruquran', 'superadmin'])
        ]

    @api.model
    def create(self, vals):
        if vals.get('urut', False):
            return super(MataPelajaran, self).create(vals)
        else:
            vals['urut'] = self.env['cdn.mata_pelajaran'].search(
                [], order='urut desc', limit=1).urut + 1
            return super(MataPelajaran, self).create(vals)
