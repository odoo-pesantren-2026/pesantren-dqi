# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class PenilaianAkhirGuru(models.Model):
    _name = 'cdn.penilaian_akhir_guru'
    _description = 'Penilaian Akhir Guru'
    _rec_name = 'guru_id'

    def _get_default_guru(self):
        emp = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
        if not emp:
            emp = self.env['hr.employee'].search(
                [('jns_pegawai_ids.code', 'in', ['guru'])], limit=1)
        return emp.id if emp else False

    def _get_default_semester(self):
        tahun_ajaran = self.env.user.company_id.tahun_ajaran_aktif
        if not tahun_ajaran or not tahun_ajaran.term_akademik_ids:
            return False
        today = fields.Date.today()
        for term in tahun_ajaran.term_akademik_ids:
            if term.term_start_date <= today <= term.term_end_date:
                return term.name.split(' ')[1]
        return '1'  # fallback ke semester 1

    def _get_domain_guru(self):
        # dapatkan semua user yang merupakan administrator
        admin_user_ids = self.env.ref('base.group_system').users.ids

        # domain guru normal
        guru_domain = [('jns_pegawai_ids.code', 'in', ['guru', 'superadmin'])]

        # domain employee milik admin
        admin_domain = [('user_id', 'in', admin_user_ids)]

        # --- bangun domain OR: admin OR guru ---
        base_domain = ['|'] + admin_domain + guru_domain

        # tambahan domain berdasarkan role user sekarang
        if self.env.user.has_group('pesantren_guru.group_guru_manager'):
            # manager boleh lihat semua guru + admin
            return base_domain

        elif self.env.user.has_group('pesantren_guru.group_guru_staff'):
            # staff hanya melihat diri sendiri + admin
            return [('user_id', '=', self.env.uid)]

        else:
            # user lain tidak boleh lihat apapun
            return [('id', '=', False)]

    # Fields
    guru_id = fields.Many2one(
        'hr.employee',
        string='Guru',
        required=True,
        domain=lambda self: self.env['cdn.penilaian_akhir_guru']._get_domain_guru(
        ),
        default=_get_default_guru
    )
    kelas_id = fields.Many2one(
        'cdn.ruang_kelas',
        string='Kelas',
        required=True,
    )
    tingkat_id = fields.Many2one(
        'cdn.tingkat', string='Tingkat', store=True, compute='_compute_tingkat_id')

    tahunajaran_id = fields.Many2one(
        'cdn.ref_tahunajaran',
        string='Tahun Ajaran',
        required=True,
        default=lambda self: self.env.user.company_id.tahun_ajaran_aktif.id
    )
    semester = fields.Selection(
        string='Semester',
        selection=[
            ('1', 'Semester 1'),
            ('2', 'Semester 2'),
        ],
        required=True,
        default=_get_default_semester
    )
    mapel_id = fields.Many2one(
        'cdn.mata_pelajaran',
        string='Mata Pelajaran',
        required=True,
    )
    state = fields.Selection(
        string='Status',
        selection=[
            ('draft', 'Draft'),
            ('confirm', 'Confirm'),
        ],
        default='draft'
    )
    penilaian_ids = fields.One2many(
        'cdn.penilaian_akhir_lines',
        inverse_name='penilaianguru_id',
        string='Penilaian Siswa'
    )
    company_id = fields.Many2one(
        'res.company', string='Lembaga', default=lambda self: self.env.company)
    jenjang = fields.Selection(
        selection=[
            ('paud', 'PAUD'),
            ('tk', 'TK/RA'),
            ('sd', 'SD/MI'),
            ('smp', 'SMP/MTS'),
            ('sma', 'SMA/MA/SMK'),
            ('nonformal', 'Non formal'),
            ('rtq', 'Rumah Tahfidz Quran')
        ],
        string="Jenjang",
        related='kelas_id.jenjang',
        store=True,
        readonly=True
    )

    # Actions
    def act_confirm(self):
        self.state = 'confirm'
        for nilai in self.penilaian_ids:
            penilaianakhir_id = self.env['cdn.penilaian_akhir'].search([
                ('siswa_id', '=', nilai.siswa_id.id),
                ('tahunajaran_id', '=', self.tahunajaran_id.id),
                ('semester', '=', self.semester)
            ])
            if penilaianakhir_id:
                nilai.penilaianakhir_id = penilaianakhir_id.id

    def act_draft(self):
        self.state = 'draft'

    @api.onchange('guru_id')
    def _onchange_guru_id(self):
        if self.guru_id:
            kelas_ids = self.env['cdn.jadwal_pelajaran_lines'].search([
                ('guru_id', '=', self.guru_id.id)
            ]).mapped('kelas_id').ids
            return {
                'domain': {'kelas_id': [('id', 'in', kelas_ids)]},
                # Reset kelas & mapel
                'value': {'kelas_id': False, 'mapel_id': False}
            }
        return {
            'domain': {'kelas_id': [], 'mapel_id': []},
            'value': {'kelas_id': False, 'mapel_id': False}
        }

    @api.onchange('kelas_id', 'guru_id')
    def _onchange_kelas_guru(self):
        domain_mapel = []
        if self.kelas_id and self.guru_id:
            # ambil mapel dari jadwal pelajaran
            jadwal_lines = self.env['cdn.jadwal_pelajaran_lines'].search([
                ('guru_id', '=', self.guru_id.id),
                ('kelas_id', '=', self.kelas_id.id)
            ])
            mapel_ids = jadwal_lines.mapped('matapelajaran_id').ids

            domain_mapel = [('id', 'in', mapel_ids)]
        return {
            'domain': {'mapel_id': domain_mapel},
            'value': {'mapel_id': False}
        }

    @api.depends('kelas_id')
    def _compute_tingkat_id(self):
        for rec in self:
            rec.tingkat_id = rec.kelas_id.tingkat if rec.kelas_id else False

    @api.onchange('kelas_id')
    def _onchange_kelas_id(self):
        if self.kelas_id:
            lines = [(5, 0, 0)]  # hapus dulu semua line lama
            for siswa in self.kelas_id.siswa_ids:
                lines.append((0, 0, {
                    'siswa_id': siswa.id,
                }))
            self.penilaian_ids = lines
        else:
            self.penilaian_ids = [(5, 0, 0)]  # reset

    # Default Get
    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if not self.env.user.company_id.tahun_ajaran_aktif:
            raise UserError(
                "Tahun ajaran aktif belum diatur di pengaturan perusahaan.")
        return defaults

    @api.constrains('tahunajaran_id', 'semester', 'kelas_id', 'mapel_id')
    def _check_unique_penilaian_akhir_guru(self):
        for rec in self:
            domain = [
                ('tahunajaran_id', '=', rec.tahunajaran_id.id),
                ('semester', '=', rec.semester),
                ('kelas_id', '=', rec.kelas_id.id),
                ('mapel_id', '=', rec.mapel_id.id),
                ('id', '!=', rec.id)
            ]
            if self.search(domain, limit=1):
                raise UserError('Penilaian Akhir Guru sudah ada!')
