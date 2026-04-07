# -*- coding: utf-8 -*-

from email import message
from email.policy import default
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import UserError


class Penilaian(models.Model):
    _name = 'cdn.penilaian'
    _description = 'Tabel Data Penilaian Siswa'

    @api.model
    def _get_action_domain(self):
        if not self.env.user.has_group('base.group_system'):
            return [('guru_id.user_id', '=', self.env.uid)]
        return []

    def _domain_guru(self):
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

    name = fields.Char(string='Nama', compute='_compute_name', default=False)
    tingkat_id = fields.Many2one(
        'cdn.tingkat', string='Tingkat', store=True, compute='_compute_tingkat_id')
    kelas_id = fields.Many2one(
        'cdn.ruang_kelas',
        string='Kelas',
        required=True,
    )
    mapel_id = fields.Many2one(
        comodel_name='cdn.mata_pelajaran', string='Mapel', required=True)
    guru_id = fields.Many2one(
        'hr.employee',
        string='Guru',
        required=True,
        domain=lambda self: self.env['cdn.penilaian']._domain_guru(),
        default=lambda self: self.env['hr.employee'].search([
            ('user_id', '=', self.env.uid),
            ('jns_pegawai_ids.code', 'in', ['guru'])
        ], limit=1)
    )
    semester = fields.Selection(
        selection=[('1', 'Ganjil'), ('2', 'Genap')], string='Semester', required=True)
    tipe = fields.Selection(string='Tipe', selection=[
                            ('Ulangan', 'Ulangan'),
                            ('UTS', 'UTS'),
                            ('UAS', 'UAS'),
                            ('Ujian Sekolah', 'Ujian Sekolah'),
                            ('Ujian Nasional', 'Ujian Nasional')], required=True)
    state = fields.Selection(string='Status', selection=[(
        'draft', 'Draft'), ('done', 'Done')], default='draft')
    penilaian_ids = fields.One2many(
        comodel_name='cdn.penilaian_lines', inverse_name='penilaian_id', string='Penilaian')
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

    @api.depends('kelas_id')
    def _compute_tingkat_id(self):
        for rec in self:
            rec.tingkat_id = rec.kelas_id.tingkat if rec.kelas_id else False
    # onchange

    @api.onchange('kelas_id')
    def _onchange_kelas_id(self):
        """Jika kelas dipilih, filter guru_id sesuai guru login"""
        if not self.env.user.has_group('pesantren_guru.group_guru_manager'):
            guru_login = self.env['hr.employee'].search(
                [('user_id', '=', self.env.user.id)], limit=1)
            if guru_login:
                self.guru_id = guru_login

    @api.onchange('kelas_id', 'guru_id')
    def _onchange_kelas_guru(self):
        """Filter mapel hanya sesuai tingkat kelas dan guru"""
        domain_mapel = []
        if self.tingkat_id and self.guru_id:
            domain_mapel = [
                ('tingkat_id', '=', self.tingkat_id.id),
                # hanya mapel yang diajar guru
                ('guru_ids', 'in', [self.guru_id.id])
            ]
        return {'domain': {'mapel_id': domain_mapel}}

    @api.onchange('kelas_id', 'tipe')
    def _onchange_kelas_id(self):
        lines = [(5, 0, 0)]
        for siswa in self.kelas_id.siswa_ids:
            lines.append((0, 0, {
                'siswa_id': siswa.id,
                'nilai': 0,
                'company_id': self.company_id.id,
            }))
        return {
            'value': {'penilaian_ids': lines},
            'domain': {
                'penilaian_ids.siswa_id': [('id', 'in', self.kelas_id.siswa_ids.ids)]
            }
        }

    # compute

    def _compute_penialainid_id(self):
        for record in self:
            record.penialainid_id = record.id

    @api.depends('tipe')
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.tipe}" if rec.tipe else "Penilaian"

    def _check_mapel_guru_kelas(self):
        """Validasi backend supaya tetap aman walaupun user modifikasi via devtools"""
        for rec in self:
            if not rec.kelas_id.tingkat:
                raise UserError(_("Kelas belum memiliki tingkat."))
            if rec.mapel_id.tingkat_id != rec.kelas_id.tingkat:
                raise UserError(
                    _("Mata pelajaran tidak sesuai dengan tingkat kelas."))
            if rec.guru_id not in rec.mapel_id.guru_ids:
                raise UserError(
                    _("Guru ini tidak mengajar mata pelajaran tersebut."))

    @api.model
    def create(self, vals):
        if not vals.get('guru_id'):
            guru = self.env['hr.employee'].search([
                ('user_id', '=', self.env.uid),
                ('jns_pegawai_ids.code', 'in', ['guru'])
            ], limit=1)
            if guru:
                vals['guru_id'] = guru.id
        rec = super().create(vals)
        rec._check_mapel_guru_kelas()
        return rec

    def write(self, vals):
        res = super().write(vals)
        self._check_mapel_guru_kelas()
        return res

    # action buttons
    def action_draft(self):
        self.state = 'draft'

    def action_done(self):
        self.state = 'done'


class PenilaianLines(models.Model):
    _name = 'cdn.penilaian_lines'
    _description = 'Tabel Data Penilaian Siswa'
    _rec_name = 'name'

    penilaian_id = fields.Many2one(
        comodel_name='cdn.penilaian', string='Penilaian', required=True)
    name = fields.Char(string='Nama', readonly=False,
                       store=True, compute='_compute_name')
    mapel_id = fields.Many2one(comodel_name='cdn.mata_pelajaran', string='Mapel',
                               related='penilaian_id.mapel_id', readonly=True, store=True)
    tipe = fields.Selection(string='Tipe', selection=[
                            ('ulangan', 'Ulangan'),
                            ('uts', 'UTS'),
                            ('uas', 'UAS'),
                            ('ujian_sekolah', 'Ujian Sekolah'),
                            ('ujian_nasional', 'Ujian Nasional')], related='penilaian_id.tipe', readonly=True, store=True)
    semester = fields.Selection(selection=[('1', 'Ganjil'), ('2', 'Genap')],
                                string='Semester', related='penilaian_id.semester', readonly=True, store=True)
    state = fields.Selection(string='Status', selection=[(
        'draft', 'Draft'), ('done', 'Done')], related='penilaian_id.state', readonly=True, store=True)
    siswa_id = fields.Many2one(
        comodel_name='cdn.siswa', string='Siswa', required=True, ondelete='cascade')
    nilai = fields.Float(string='Nilai')
    predikat = fields.Char(string='Predikat')
    # Field untuk domain di view penilaian
    id_kelas = fields.Integer(string='Kelas ID', compute='_compute_id_kelas')
    id_penilaian = fields.Integer(
        string='Penilaian ID', compute='_compute_id_penilaian')

    panggilan = fields.Char(
        string='Nama Panggilan', related='siswa_id.namapanggilan', readonly=True, store=True)
    company_id = fields.Many2one('res.company', string='Lembaga',
                                 related='penilaian_id.company_id', readonly=True, store=True)

    # compute

    @api.depends('penilaian_id')
    def _compute_name(self):
        for record in self:
            record.name = record.penilaian_id.name

    def _compute_id_kelas(self):
        for record in self:
            record.id_kelas = record.penilaian_id.kelas_id.id

    def _compute_id_penilaian(self):
        for record in self:
            record.id_penilaian = record.penilaian_id.id

    @api.onchange('nilai')
    def _onchange_nilai(self):
        message = {
            'title': "Harap diperhatikan!",
            'message': "Nilai tidak boleh kurang dari 0 atau melebihi 100"
        }
        if not self._validate_nilai(self.nilai):
            return {'warning': message, 'value': {'nilai': self._origin.nilai}}

        predikat = self.env['cdn.predikat'].search([('tipe', '=', 'akademik')])
        val = {'value': {'predikat': ''}}
        if predikat and self.nilai:
            for pred in predikat.predikat_ids:
                if pred.min_nilai <= self.nilai <= pred.max_nilai:
                    val['value']['predikat'] = pred.name
        return val

    def _validate_nilai(self, nilai):
        if nilai < 0 or nilai > 100:
            return False
        return True
