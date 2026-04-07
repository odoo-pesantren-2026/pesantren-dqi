# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date
from odoo.exceptions import UserError


class PenilaianAkhir(models.Model):
    _name = 'cdn.penilaian_akhir'
    _description = 'Data Penilain Akhir Evaluasi Untuk Rapor'

    @api.constrains('siswa_id', 'tahunajaran_id', 'semester')
    def _check_unique_penilaian_akhir(self):
        for rec in self:
            domain = [
                ('siswa_id', '=', rec.siswa_id.id),
                ('tahunajaran_id', '=', rec.tahunajaran_id.id),
                ('semester', '=', rec.semester),
                ('id', '!=', rec.id)
            ]
            if self.search_count(domain):
                raise UserError('Data Penilaian Akhir sudah ada !')

    def _get_default_semester(self):
        tahun_ajaran = self.env.user.company_id.tahun_ajaran_aktif
        if not tahun_ajaran.term_akademik_ids:
            return False
        for term in tahun_ajaran.term_akademik_ids:
            today = fields.Date.today()
            if term.term_start_date <= today and term.term_end_date >= today:
                return term.name.split(' ')[1]

    def _get_domain_siswa(self):
        if self.env.user.has_group('pesantren_guru.group_guru_manager'):
            return [('id', '!=', False)]
        elif self.env.user.has_group('pesantren_guru.group_guru_staff'):
            guru = self.env['hr.employee'].search(
                [('user_id', '=', self.env.uid)]).id
            ruang_kelas = self.env['cdn.ruang_kelas'].search(
                [('walikelas_id', '=', guru)])
            return [('id', 'in', ruang_kelas.siswa_ids.ids)]
        return [('id', '=', False)]

    def _get_domain_walikelas(self):
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

    def _get_default_walikelas(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    name = fields.Char(string='Nama', readonly=True, compute='_compute_name')
    siswa_id = fields.Many2one('cdn.siswa', string='Siswa',
                               required=True, domain=_get_domain_siswa, ondelete='cascade')
    nis = fields.Char(string='NIS', related='siswa_id.nis',
                      readonly=True, store=True)
    kelas_id = fields.Many2one('cdn.ruang_kelas', string='Kelas',
                               related='siswa_id.ruang_kelas_id', readonly=True, store=True)
    tahunajaran_id = fields.Many2one('cdn.ref_tahunajaran', string='Tahun Ajaran',
                                     required=True, default=lambda self: self.env.user.company_id.tahun_ajaran_aktif.id)
    semester = fields.Selection(string='Semester', selection=[
        ('1', 'Semester 1'),
        ('2', 'Semester 2'),], required=True, default=_get_default_semester)
    state = fields.Selection(string='Status', selection=[
                            ('draft', 'Draft'),
                            ('confirm', 'Confirm'),
                            ('approved', 'Di Setujui')], default='draft')
    tgl_disetujui = fields.Date(string='Tgl di Setujui', readonly=True)
    walikelas_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Wali Kelas',
        required=True,
        domain=lambda self: self.env['cdn.penilaian_akhir']._get_domain_walikelas(
        ),
        default=_get_default_walikelas,
        readonly=True  # Opsional: agar tidak bisa diganti
    )

    penilaianakhir_ids = fields.One2many('cdn.penilaian_akhir_lines', 'penilaianakhir_id', string='Nilai Raport', domain=[
                                         ('penilaianguru_id.state', '=', 'confirm')])
    ekstrakulikuler_ids = fields.One2many(
        'cdn.penilaian_ekstrakulikuler', 'penilaianakhir_id', string='Nilai Ekstrakulikuler')
    organisasi_ids = fields.One2many(
        'cdn.organisasi_penilaian_akhir', 'penilaianakhir_id', string='Organisasi')
    company_id = fields.Many2one(
        'res.company', string='Lembaga', default=lambda self: self.env.company)

    def act_confirm(self):
        self.state = 'confirm'

    def act_approved(self):
        self.state = 'approved'
        self.tgl_disetujui = date.today()

    # compute
    @api.depends('siswa_id', 'semester')
    def _compute_name(self):
        for rec in self:
            # rec.name = '%s/%s' % (rec.siswa_id.name, rec.semester)
            rec.name = rec.siswa_id.name if rec.siswa_id else ''

    # onchange
    @api.onchange('siswa_id', 'semester', 'tahunajaran_id')
    def _onchange_siswa(self):
        if not self.siswa_id or not self.semester or not self.tahunajaran_id:
            return
        nilai_akhir = self.env['cdn.penilaian_akhir_lines'].search([('siswa_id', '=', self.siswa_id.id), (
            'semester', '=', self.semester), ('tahunajaran_id', '=', self.tahunajaran_id.id)])
        data = [(5, 0, 0)]
        ekstrakulikuler = [(5, 0, 0)]
        organisasi = [(5, 0, 0)]
        for ekstra in self.siswa_id.ekstrakulikuler_ids:
            ekstrakulikuler.append((0, 0, {
                'name': ekstra.name,
                'is_wajib': ekstra.is_wajib,
            }))
        for o in self.siswa_id.partner_id.organisasi_ids:
            organisasi.append(
                (0, 0, {'name': o.organisasi_id.name, 'position': o.position}))
        if nilai_akhir:
            for rec in nilai_akhir:
                if rec.penilaianguru_id.state == 'confirm':
                    data.append((4, rec.id, {
                        'mapel_id': rec.mapel_id.id,
                        'nilai1': rec.nilai1,
                        'predikat1': rec.predikat1,
                        'nilai2': rec.nilai2,
                        'predikat2': rec.predikat2,
                        'aspek1': rec.aspek1,
                        'aspek2': rec.aspek2,
                        'aspek3': rec.aspek3,
                        'aspek4': rec.aspek4,
                        'aspek5': rec.aspek5,
                        'aspek6': rec.aspek6,
                    }))
        return {'value': {
            'penilaianakhir_ids': data,
            'ekstrakulikuler_ids': ekstrakulikuler,
            'organisasi_ids': organisasi
        }}
    # check others requirements

    @api.model
    def default_get(self, fields_tree):
        if not self.env.user.company_id.tahun_ajaran_aktif.id:
            raise UserError('Tahun ajaran belum di set')
        return super().default_get(fields_tree)


class PenilaianAkhirLines(models.Model):
    _name = 'cdn.penilaian_akhir_lines'
    _description = 'Data Nilai Rapor Siswa'
    _rec_name = 'mapel_id'

    penilaianakhir_id = fields.Many2one(
        'cdn.penilaian_akhir', string='penilaian_akhir')
    penilaianguru_id = fields.Many2one(
        'cdn.penilaian_akhir_guru', string='penilaian_akhir_guru', ondelete='cascade')
    tahunajaran_id = fields.Many2one(
        'cdn.ref_tahunajaran', related="penilaianguru_id.tahunajaran_id", string='Tahun Ajaran', store=True)
    semester = fields.Selection(string='Semester', related="penilaianguru_id.semester", selection=[
        ('1', 'Semester 1'),
        ('2', 'Semester 2'),], store=True)
    siswa_id = fields.Many2one('cdn.siswa', string='Siswa')
    mapel_id = fields.Many2one(
        'cdn.mata_pelajaran', related="penilaianguru_id.mapel_id", string='Mata Pelajaran', store=True)
    nilai1 = fields.Float(string='Nilai')
    predikat1 = fields.Char(string='Predikat')
    nilai2 = fields.Float(string='Nilai')
    predikat2 = fields.Char(string='Predikat')
    aspek1 = fields.Char(string='Aspek 1')
    aspek2 = fields.Char(string='Aspek 2')
    aspek3 = fields.Char(string='Aspek 3')
    aspek4 = fields.Char(string='Aspek 4')
    aspek5 = fields.Char(string='Aspek 5')
    aspek6 = fields.Char(string='Aspek 6')

    @api.onchange('nilai1', 'nilai2')
    def _onchange_nilai1(self):
        message = {
            'title': "Harap diperhatikan!",
            'message': "Nilai tidak boleh kurang dari 0 atau melebihi 100"
        }
        if not self._validate_nilai(self.nilai1):
            return {'warning': message, 'value': {'nilai1': self._origin.nilai1}}
        if not self._validate_nilai(self.nilai2):
            return {'warning': message, 'value': {'nilai2': self._origin.nilai2}}
        # nilai predikat
        predikat = self.env['cdn.predikat'].search([('tipe', '=', 'akademik')])
        val = {'value': {'predikat1': '', 'predikat2': ''}}
        if predikat and self.nilai1:
            for pred in predikat.predikat_ids:
                if pred.min_nilai <= self.nilai1 <= pred.max_nilai:
                    val['value']['predikat1'] = pred.name
        if predikat and self.nilai2:
            for pred in predikat.predikat_ids:
                if pred.min_nilai <= self.nilai2 <= pred.max_nilai:
                    val['value']['predikat2'] = pred.name
        return val

    def _validate_nilai(self, nilai):
        if nilai < 0 or nilai > 100:
            return False
        return True
