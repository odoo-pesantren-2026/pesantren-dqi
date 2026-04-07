from email import message
from email.policy import default
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import UserError


class Penilaian(models.Model):
    _name = 'cdn.penilaian_santri'
    _description = 'Tabel Data Penilaian Santri'

    # get domain
    def _domain_halaqoh_id(self):
        tahun_ajaran = self.env.user.company_id.tahun_ajaran_aktif.id

        # Jika user adalah Manager Kesantrian -> lihat semua halaqoh di tahun ajaran aktif
        if self.env.user.has_group('pesantren_kesantrian.group_kesantrian_manager'):
            return [
                ('fiscalyear_id', '=', tahun_ajaran)
            ]

        # Jika bukan manager -> halaqoh di tahun ajaran aktif yang user ini sebagai pengganti
        return [
            '|',
            '&',
            ('penanggung_jawab_id.user_id', '=', self.env.user.id),
            ('fiscalyear_id', '=', tahun_ajaran),
            '&',
            ('pengganti_ids.user_id', '=', self.env.user.id),
            ('fiscalyear_id', '=', tahun_ajaran)
        ]

    name = fields.Char(string='Nama', compute='_compute_name', default=False)
    halaqoh_id = fields.Many2one('cdn.halaqoh', string='Halaqoh', required=True,
                                 domain=_domain_halaqoh_id, states={'Done': [('readonly', True)]})
    kategori_penilaian = fields.Selection(string='Kategori Penilaian', selection=[
        ('tahfidz', 'Tahfidz'),
        ('tahsin', 'Tahsin'),
    ], required=True, help="Pilih kategori penilaian: Tahfidz (hafalan Al-Qur'an) atau Tahsin (perbaikan bacaan)")
    guru_id = fields.Many2one(
        'hr.employee',
        string='Guru',
        required=True,
        # domain=_domain_guru,
        default=lambda self: self.env['hr.employee'].search([
            ('user_id', '=', self.env.uid),
            ('jns_pegawai_ids.code', 'in', ['guruquran'])
        ],
            limit=1),
        domain=lambda self: self.env['cdn.penilaian_santri']._domain_guruquran(
        )
    )
    tipe = fields.Selection(string='Tipe', selection=[
        ('Ujian Juz', 'Ujian Juz'),
        ('Ujian Tahfidz', 'Ujian Tahfidz'),
        ('Ujian Tasmi', 'Ujian Tasmi'),
        ('Ujian Tahsin', 'Ujian Tahsin'),
        ('Ujian Harian', 'Ujian Harian'),
        ('Ujian Bulanan', 'Ujian Bulanan'),
    ], required=True, help="Pilih jenis ujian yang ingin dilaksanakan")
    state = fields.Selection(string='Status', selection=[(
        'draft', 'Draft'), ('done', 'Done')], default='draft', help="Status penilaian: Draft (belum final) atau Done (sudah selesai)")
    penilaian_santri_ids = fields.One2many(
        comodel_name='cdn.penilaian_santri_lines', inverse_name='penilaian_santri_id', string='Penilaian Santri')
    company_id = fields.Many2one(
        'res.company', string='Lembaga', default=lambda self: self.env.company)

    def _domain_guruquran(self):
        admin_user_ids = self.env.ref('base.group_system').users.ids

        return [
            '|',
            ('user_id', '=', admin_user_ids),
            ('jns_pegawai', 'in', [
                'guruquran',
                'guru,guruquran',
                'musyrif,guruquran',
                'musyrif,guru,guruquran',
                'superadmin'
            ])
        ]

    @api.depends('tipe')
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.tipe}" if rec.tipe else "Penilaian Santri"

    @api.onchange('halaqoh_id')
    def _onchange_halaqoh_id(self):
        """Jika halaqoh dipilih, filter guru_id sesuai guru login"""
        if not self.env.user.has_group('pesantren_guruquran.group_guru_quran_manager'):
            guru_login = self.env['hr.employee'].search(
                [('user_id', '=', self.env.user.id)], limit=1)
            if guru_login:
                self.guru_id = guru_login

    @api.onchange('halaqoh_id', 'tipe')
    def _onchange_halaqoh_id(self):
        lines = [(5, 0, 0)]
        for santri in self.halaqoh_id.siswa_ids:
            lines.append((0, 0, {
                'santri_id': santri.id,
                'nilai': 0,
                'company_id': self.company_id.id,
            }))
        return {
            'value': {'penilaian_santri_ids': lines},
            'domain': {
                'penilaian_santri_ids.santri_id': [('id', 'in', self.halaqoh_id.siswa_ids.ids)]
            }
        }

    def _check_halaqoh_guru_quran(self):
        """Validasi backend supaya tetap aman walaupun user modifikasi via devtools"""
        for rec in self:
            if rec.guru_id not in rec.halaqoh_id.penanggung_jawab_id:
                raise UserError(
                    _("Guru ini tidak mengajar di halaqoh tersebut."))

    @api.model
    def create(self, vals):
        if not vals.get('guru_id'):
            guru = self.env['hr.employee'].search([
                ('user_id', '=', self.env.uid),
                ('jns_pegawai', 'in', [
                 'guruquran', 'guru,guruquran', 'musyrif,guruquran', 'musyrif,guru,guruquran'])
            ], limit=1)
            if guru:
                vals['guru_id'] = guru.id
        rec = super().create(vals)
        rec._check_halaqoh_guru_quran()
        return rec

    def write(self, vals):
        res = super().write(vals)
        self._check_halaqoh_guru_quran()
        return res

    # action buttons
    def action_draft(self):
        self.state = 'draft'

    def action_done(self):
        self.state = 'done'


class PenilaianSantriLines(models.Model):
    _name = 'cdn.penilaian_santri_lines'
    _description = 'Tabel Data Penilaian Santri Lines'
    _rec_name = 'name'

    penilaian_santri_id = fields.Many2one(
        comodel_name='cdn.penilaian_santri', string='Penilaian Santri', required=True, ondelete='cascade')
    name = fields.Char(string='Nama', readonly=False,
                       store=True, compute='_compute_name')
    santri_id = fields.Many2one(
        comodel_name='cdn.siswa', string='Santri', required=True, ondelete='cascade')
    tipe = fields.Selection(string='Tipe', selection=[
                            ('Ujian Juz', 'Ujian Juz'),
                            ('Ujian Tahfidz', 'Ujian Tahfidz'),
                            ('Ujian Tasmi', 'Ujian Tasmi')], related="penilaian_santri_id.tipe", readonly=True, store=True)
    state = fields.Selection(string='Status', selection=[('draft', 'Draft'), (
        'done', 'Done')], related='penilaian_santri_id.state', readonly=True, store=True)
    kategori_penilaian = fields.Selection(string='Kategori Penilaian', selection=[
        ('tahfidz', 'Tahfidz'),
        ('tahsin', 'Tahsin'),
    ], related='penilaian_santri_id.kategori_penilaian', readonly=True, store=True)
    nilai = fields.Float(string='Nilai', help="Nilai hasil ujian santri, antara 0 hingga 100")
    predikat = fields.Char(string='Predikat', help="Predikat otomatis berdasarkan nilai (terisi otomatis)")
    juz = fields.Char(string='Juz', store=True, help="Nomor juz Al-Qur'an yang diujikan")
    panggilan = fields.Char(
        string='Nama Panggilan', related='santri_id.namapanggilan', readonly=True, store=True)
    id_halaqoh = fields.Integer(
        string='Halaqoh ID', compute='_compute_id_halaqoh')
    id_penilaian_santri = fields.Integer(
        string='Penilaian Santri ID', compute='_compute_id_penilaian_santri')
    company_id = fields.Many2one('res.company', string='Lembaga',
                                 related='penilaian_santri_id.company_id', readonly=True, store=True)

    # compute
    @api.depends('penilaian_santri_id')
    def _compute_name(self):
        for record in self:
            record.name = record.penilaian_santri_id.name

    def _compute_id_halaqoh(self):
        for record in self:
            record.id_halaqoh = record.penilaian_santri_id.halaqoh_id.id

    def _compute_id_penilaian_santri(self):
        for record in self:
            record.id_penilaian_santri = record.penilaian_santri_id.id

    @api.onchange('nilai')
    def _onchange_nilai(self):
        message = {
            'title': "Harap diperhatikan!",
            'message': "Nilai tidak boleh kurang dari 0 atau melebihi 100"
        }
        if not self._validate_nilai(self.nilai):
            return {'warning': message, 'value': {'nilai': self._origin.nilai}}

        predikat = self.env['cdn.predikat'].search(
            [('tipe', '=', 'kepesantrenan')])
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
