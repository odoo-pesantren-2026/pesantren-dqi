# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class JadwalPelajaran(models.Model):
    _name = 'cdn.jadwal_pelajaran'
    _description = 'Data Jadwal Pelajaran'

    name = fields.Char(string='Nama', readonly=True,
                       compute='_compute_name', store=True)
    tahunajaran_id = fields.Many2one('cdn.ref_tahunajaran', string='Tahun Ajaran', required=True,
                                     default=lambda self: self.env.user.company_id.tahun_ajaran_aktif.id)
    kelas_id = fields.Many2one(
        'cdn.ruang_kelas', string='Kelas', required=True)
    jenjang = fields.Selection(
        selection=[('paud', 'PAUD'), ('tk', 'TK/RA'), ('sd', 'SD/MI'),
                   ('smp', 'SMP/MTS'), ('sma', 'SMA/MA'), ('nonformal', 'Nonformal')],
        store=True, string='Jenjang', related='kelas_id.jenjang', readonly=True)
    walikelas_id = fields.Many2one(
        'hr.employee', string='Wali Kelas', readonly=True, related='kelas_id.walikelas_id')
    semester = fields.Selection(selection=[(
        '1', 'Semester 1'), ('2', 'Semester 2')], string='Semester', required=True, help="Pilih jadwal ini berlaku untuk semester berapa")
    jadwal_ids = fields.One2many('cdn.jadwal_pelajaran_lines',
                                 inverse_name='jadwalpelajaran_id', string='Jadwal Pelajaran')

    @api.depends('kelas_id', 'semester', 'tahunajaran_id')
    def _compute_name(self):
        for rec in self:
            if rec.kelas_id and rec.semester and rec.tahunajaran_id:
                rec.name = '%s/Semester %s.%s' % (
                    rec.kelas_id.name.name, rec.semester, rec.tahunajaran_id.name)
            else:
                rec.name = ''

    @api.model
    def default_get(self, fields_tree):
        if not self.env.user.company_id.tahun_ajaran_aktif.id:
            raise UserError('Tahun ajaran belum di set')
        return super().default_get(fields_tree)

    @api.onchange('kelas_id')
    def _onchange_kelas_id(self):
        if self.kelas_id:
            for line in self.jadwal_ids:
                line.matapelajaran_id = False
            return {
                'domain': {
                    'jadwal_ids.matapelajaran_id': [('jenjang', '=', self.kelas_id.jenjang)]
                }
            }
        return {}

    @api.constrains('name')
    def _check_name_unique(self):
        for rec in self:
            if rec.name and self.search_count([('name', '=', rec.name), ('id', '!=', rec.id)]) > 0:
                raise UserError('Jadwal kelas sudah ada!')

    @api.constrains('kelas_id')
    def _check_mata_pelajaran_exist(self):
        for rec in self:
            if rec.kelas_id:
                mapel = self.env['cdn.mata_pelajaran'].search([
                    ('jenjang', '=', rec.kelas_id.jenjang)
                ], limit=1)
                if not mapel:
                    raise UserError(
                        f"Tidak ada Mata Pelajaran untuk jenjang {rec.kelas_id.jenjang}. "
                        "Silakan tambahkan Mata Pelajaran di master terlebih dahulu."
                    )


class JadwalPelajaranLine(models.Model):
    _name = 'cdn.jadwal_pelajaran_lines'
    _description = 'Data Jadwal Pelajaran Line'

    name = fields.Selection(selection=[
        ('1', 'Senin'),
        ('2', 'Selasa'),
        ('3', 'Rabu'),
        ('4', 'Kamis'),
        ('5', 'Jumat'),
        ('6', 'Sabtu'),
        ('7', 'Minggu')], string='Hari', required=True)
    jadwalpelajaran_id = fields.Many2one(
        'cdn.jadwal_pelajaran', string='Jadwal Pelajaran', ondelete='cascade')
    kelas_id = fields.Many2one(
        'cdn.ruang_kelas',
        string='Kelas',
        related='jadwalpelajaran_id.kelas_id',
        store=True,
        readonly=True
    )
    jenjang = fields.Selection(
        related='jadwalpelajaran_id.jenjang',
        store=True,
        string='Jenjang'
    )
    jampelajaran_id = fields.Many2one(
        'cdn.ref_jam_pelajaran', string='Jam Pelajaran', required=True)
    start_time = fields.Float(
        string='Jam Mulai', related='jampelajaran_id.start_time', readonly=True, widget="float_time")
    end_time = fields.Float(
        string='Jam Selesai', related='jampelajaran_id.end_time', readonly=True, widget="float_time")
    matapelajaran_id = fields.Many2one(
        'cdn.mata_pelajaran', string='Mata Pelajaran', domain="[('jenjang', '=', jenjang)]")
    guru_id = fields.Many2many(
        'hr.employee',
        string='Guru',
        domain=lambda self: self.env['cdn.jadwal_pelajaran_lines']._get_domain_guru())

    def _get_domain_guru(self):
        admin_user_ids = self.env.ref('base.group_system').users.ids

        return [
            '|',
            ('user_id', '=', admin_user_ids),
            ('jns_pegawai_ids.code', 'in', ['guru', 'superadmin'])
        ]

    def _onchange_matapelajaran_id(self):
        if self.matapelajaran_id and self.jadwalpelajaran_id:
            # validasi jenjang tetap
            if self.matapelajaran_id.jenjang != self.jadwalpelajaran_id.jenjang:
                warning = {
                    'title': 'Peringatan',
                    'message': f'Mata pelajaran {self.matapelajaran_id.name} tidak sesuai jenjang {self.jadwalpelajaran_id.jenjang}'
                }
                self.matapelajaran_id = False
                self.guru_id = [(5, 0, 0)]  # kosongkan
                return {'warning': warning}

            # isi otomatis guru_id dari master matapelajaran
            self.guru_id = [(6, 0, self.matapelajaran_id.guru_ids.ids)]
        else:
            self.guru_id = [(5, 0, 0)]  # kosongkan jika tidak ada matpel

    @api.onchange('start_time', 'end_time')
    def _onchange_jam(self):
        if self.start_time is not None and self.end_time is not None:
            start_time = max(0, min(int(self.start_time), 23))
            menit_mulai = max(
                0, min(int((self.start_time - start_time) * 60), 59))
            end_time = max(0, min(int(self.end_time), 23))
            menit_selesai = max(
                0, min(int((self.end_time - end_time) * 60), 59))

            mulai_total = start_time * 60 + menit_mulai
            selesai_total = end_time * 60 + menit_selesai
            if selesai_total < mulai_total:
                return {
                    'warning': {
                        'title': 'Perhatian',
                        'message': 'Jam Selesai tidak boleh lebih awal dari Jam Mulai.'
                    }
                }

            self.start_time = round(start_time + menit_mulai / 60, 2)
            self.end_time = round(end_time + menit_selesai / 60, 2)

    @api.constrains('matapelajaran_id')
    def _check_matapelajaran_required(self):
        for rec in self:
            if not rec.matapelajaran_id:
                raise UserError(
                    "Mata Pelajaran wajib diisi pada Jadwal Pelajaran Line.")
