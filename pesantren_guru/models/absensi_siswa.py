# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging
import base64
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AbsensiSiswa(models.Model):
    _name = 'cdn.absensi_siswa'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Data Absensi Siswa'
    _order = 'tanggal desc'

    def _get_domain_guru(self):
        user = self.env.user
        guru_domain = [('jns_pegawai_ids.code', 'in', ['guru'])]
        if user.has_group('pesantren_guru.group_guru_manager'):
            return [('user_id', '=', self.env.user.id)] + guru_domain
        elif user.has_group('pesantren_guru.group_guru_staff'):
            user = self.env['hr.employee'].search([('user_id', '=', user.id)])
            return [('user_id', '=', self.env.user.id)] + guru_domain
        return [('id', '=', False)]

    def _get_default_guru(self):
        user = self.env.user
        if user.has_group('pesantren_guru.group_guru_staff'):
            user = self.env['hr.employee'].search([('user_id', '=', user.id)])
            return user.id
        return False

    name = fields.Char(string='Nama', readonly=True,
                       compute='_compute_name', store=True)
    tanggal = fields.Date(string='Tanggal Absen', required=True,
                          default=fields.Date.today())
    hari = fields.Selection([
        ('1', 'Senin'),
        ('2', 'Selasa'),
        ('3', 'Rabu'),
        ('4', 'Kamis'),
        ('5', 'Jumat'),
        ('6', 'Sabtu'),
        ('7', 'Minggu'),
    ], string='Hari', readonly=True, compute='_compute_hari', store=True)
    jampelajaran_id = fields.Many2many(
        comodel_name='cdn.ref_jam_pelajaran', string='Jam Ke', required=True)
    start_time = fields.Float(
        string='Start Time', related='jampelajaran_id.start_time', readonly=True, store=True)
    end_time = fields.Float(
        string='End Time', related='jampelajaran_id.end_time', readonly=True, store=True)
    kelas_id = fields.Many2one(
        comodel_name='cdn.ruang_kelas', string='Kelas', required=True)
    tingkat_id = fields.Many2one(comodel_name='cdn.tingkat', string='Tingkat',
                                 related='kelas_id.tingkat', readonly=True, store=True)
    walikelas_id = fields.Many2one(comodel_name='hr.employee', string='Wali Kelas',
                                   related='kelas_id.walikelas_id', readonly=True, store=True)
    tahunajaran_id = fields.Many2one(comodel_name='cdn.ref_tahunajaran', string='Tahun Ajaran',
                                     related='kelas_id.tahunajaran_id', readonly=True, store=True)
    semester = fields.Selection(selection=[(
        '1', 'Ganjil'), ('2', 'Genap')], string='Semester', readonly=True, store=True)
    guru_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Guru',
        required=True,
        default=_get_default_guru,
        domain=lambda self: self.env['cdn.absensi_siswa']._domain_guru()
    )
    pertemuan_ke = fields.Integer(
        string='Pertemuan Ke', readonly=True, compute='_compute_pertemuan_ke', store=True)
    mapel_id = fields.Many2one(
        comodel_name='cdn.mata_pelajaran', string='Mata pelajaran', required=True)
    rpp_id = fields.Many2one(comodel_name='cdn.master_rpp', string='RPP')
    dokumen = fields.Binary(
        string='Dokumen', related='rpp_id.dokumen', readonly=True, store=True)
    tema = fields.Char(string='Tema', required=True)
    materi = fields.Text(string='Materi', required=True)
    state = fields.Selection(
        selection=[('draft', 'Draft'), ('done', 'Done')], string='State', default='draft')
    absensi_ids = fields.One2many(
        comodel_name='cdn.absensi_siswa_lines', inverse_name='absensi_id', string='Absensi Siswa')
    row_number = fields.Integer(
        string='No', compute='_compute_row_number', store=False)
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

    def _domain_guru(self):
        admin_user_ids = self.env.ref('base.group_system').users.ids

        return [
            '|',
            ('user_id', 'in', admin_user_ids),
            ('jns_pegawai_ids.code', 'in', ['guru', 'superadmin'])
        ]

    def _compute_row_number(self):
        for index, record in enumerate(self):
            record.row_number = index + 1

    def action_draft(self):
        self.state = 'draft'

    def action_done(self):
        self.state = 'done'

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if record.name:
                if self.search_count([('name', '=', record.name)]) > 1:
                    raise UserError('Absensi Siswa sudah ada')

    @api.depends('tanggal')
    def _compute_hari(self):
        for record in self:
            record.hari = str(record.tanggal.weekday() + 1)

    @api.depends('tanggal', 'jampelajaran_id')
    def _compute_name(self):
        for record in self:
            jam_names = ", ".join(record.jampelajaran_id.mapped(
                'name')) if record.jampelajaran_id else "-"
            record.name = "%s/%s/%s" % (
                record.kelas_id.name.name,
                record.tanggal,
                jam_names
            )

    @api.depends('mapel_id', 'kelas_id')
    def _compute_pertemuan_ke(self):
        for record in self:
            if record.kelas_id and record.mapel_id:
                rid = record.id if type(record.id) == int else False
                record.pertemuan_ke = self.env['cdn.absensi_siswa'].search_count([
                    ('mapel_id', '=', record.mapel_id.id),
                    ('kelas_id', '=', record.kelas_id.id),
                    ('id', '!=', rid),
                ]) + 1

    @api.onchange('guru_id')
    def _onchange_guru_id(self):
        if not self._origin.guru_id and self.guru_id:
            pass

    @api.onchange('kelas_id')
    def _onchange_kelas_id(self):
        """Mengisi absensi_ids berdasarkan kelas, hanya jika absensi_ids kosong atau kelas berubah."""
        if self.kelas_id and (not self.absensi_ids or self._origin.kelas_id != self.kelas_id):
            # Hapus semua baris hanya jika perlu mengisi ulang
            absensi_ids = [(5, 0, 0)]
            siswa_list = self.env['cdn.siswa'].search(
                [('ruang_kelas_id', '=', self.kelas_id.id)])
            if not siswa_list:
                return {
                    'warning': {
                        'title': 'Perhatian',
                        'message': 'Tidak ada siswa yang ditemukan di kelas tersebut.'
                    },
                    'value': {'absensi_ids': [(5, 0, 0)]}
                }
            for siswa in siswa_list:
                permission = self.env['cdn.perijinan'].search([
                    ('siswa_id', '=', siswa.id),
                    ('state', '=', 'Permission')
                ], limit=1)
                if permission:
                    keperluan_name = permission.keperluan.name if permission.keperluan else 'Tidak ada keterangan'
                    waktu_keluar = self.format_datetime_indonesia(
                        permission.waktu_keluar) if permission.waktu_keluar else 'Tidak tercatat'
                    message = f"Santri Keluar pada {waktu_keluar}, karena {keperluan_name}"
                    foto_bukti = False
                    try:
                        if permission.foto_bukti:
                            base64.b64decode(
                                permission.foto_bukti, validate=True)
                            foto_bukti = permission.foto_bukti
                    except Exception as e:
                        _logger.error(
                            f"Invalid foto_bukti for permission {permission.id} (siswa: {siswa.name}): {str(e)}"
                        )
                        foto_bukti = False
                    if permission and permission.foto_bukti_filename:
                        nama_file = permission.foto_bukti_filename
                    elif permission and foto_bukti:
                        nama_file = f"Bukti_Izin_{siswa.nis}_{siswa.name}_{permission.name}.jpg"
                    else:
                        nama_file = False
                    absensi_ids.append((0, 0, {
                        'siswa_id': siswa.id,
                        'kehadiran': 'keluar',
                        'keterangan': message,
                        'keterangan_izin': foto_bukti,
                        'keterangan_izin_filename': nama_file,
                        'company_id': self.company_id.id,
                    }))
                else:
                    absensi_ids.append((0, 0, {
                        'siswa_id': siswa.id,
                        'kehadiran': 'Hadir',
                        'company_id': self.company_id.id,
                    }))
            return {'value': {'absensi_ids': absensi_ids}}
        return {}

    @api.onchange('tanggal', 'kelas_id', 'guru_id', 'jampelajaran_id')
    def _onchange_tanggal(self):
        """Mengatur domain dan mapel_id berdasarkan jadwal, tanpa menimpa absensi_ids yang sudah ada."""
        if self.tanggal and self.guru_id:
            jadwal = self.env['cdn.jadwal_pelajaran_lines'].search([
                ('guru_id', '=', self.guru_id.id),
                ('name', '=', self.hari)
            ])
            if jadwal:
                mapel = False
                if self.hari and self.kelas_id and self.guru_id and self.jampelajaran_id:
                    m = self.env['cdn.jadwal_pelajaran_lines'].search([
                        ('name', '=', self.hari),
                        ('kelas_id', '=', self.kelas_id.id),
                        ('guru_id', '=', self.guru_id.id),
                        ('jampelajaran_id', '=', self.jampelajaran_id.id)
                    ])
                    mapel = m.matapelajaran_id.id if m else False
                return {
                    'domain': {
                        'kelas_id': [('id', 'in', jadwal.mapped('kelas_id').ids)],
                        'jampelajaran_id': [('id', 'in', jadwal.mapped('jampelajaran_id').ids)]
                    },
                    'value': {
                        'mapel_id': mapel,
                    }
                }
        return {}

    @api.onchange('kelas_id', 'tanggal')
    def _onchange_guru_domain(self):
        return {
            'domain': {
                'guru_id': [('jns_pegawai_ids.code', 'in', ['guru'])]
            }
        }

    @staticmethod
    def format_datetime_indonesia(dt):
        bulan_dict = {
            '01': 'Januari', '02': 'Februari', '03': 'Maret', '04': 'April',
            '05': 'Mei', '06': 'Juni', '07': 'Juli', '08': 'Agustus',
            '09': 'September', '10': 'Oktober', '11': 'November', '12': 'Desember'
        }
        if dt:
            hari = dt.strftime('%d')
            bulan_angka = dt.strftime('%m')
            tahun = dt.strftime('%Y')
            jam_menit = dt.strftime('%H:%M')
            nama_bulan = bulan_dict.get(bulan_angka, bulan_angka)
            return f"{hari} {nama_bulan} {tahun} {jam_menit}"
        return 'Tidak tercatat'


class AbsensiSiswaLine(models.Model):
    _name = 'cdn.absensi_siswa_lines'
    _description = 'Data Absensi Siswa Lines'

    absensi_id = fields.Many2one(
        comodel_name='cdn.absensi_siswa', string='Absensi Siswa', ondelete='cascade')
    mapel_id = fields.Many2one(comodel_name='cdn.mata_pelajaran',
                               string='Mata pelajaran', related='absensi_id.mapel_id')
    tanggal = fields.Date(
        string='Tgl Absen', related='absensi_id.tanggal', readonly=True, store=True)
    kelas_id = fields.Many2one(comodel_name='cdn.ruang_kelas', string='Kelas',
                               related='absensi_id.kelas_id', readonly=True, store=True)
    siswa_id = fields.Many2one(
        comodel_name='cdn.siswa',
        string='Siswa',
        required=True,
        domain="[('id', 'in', allowed_siswa_ids)]",
        ondelete='cascade'
    )
    allowed_siswa_ids = fields.Many2many(
        comodel_name='cdn.siswa',
        compute='_compute_allowed_siswa',
        store=False
    )
    name = fields.Char(string='Nama', related='siswa_id.name',
                       readonly=True, store=True)
    nis = fields.Char(string='NIS', related='siswa_id.nis',
                      readonly=True, store=True)
    kehadiran = fields.Selection([
        ('Hadir', 'Hadir'),
        ('Sakit', 'Sakit'),
        ('Izin', 'Izin'),
        ('keluar', 'Izin Keluar'),
        ('Alpa', 'Alpa'),
    ], string='Kehadiran', default='Hadir')

    keterangan_izin = fields.Binary(string='Foto', attachment=True)
    keterangan_izin_filename = fields.Char(string="Nama File Foto")
    keterangan = fields.Char(string='Keterangan')
    panggilan = fields.Char(
        string='Nama Panggilan', related='siswa_id.namapanggilan', readonly=True, store=True)
    guru = fields.Many2one('hr.employee', string="Guru",
                           related='absensi_id.guru_id')
    row_number = fields.Integer(
        string='No', compute='_compute_row_number', store=False)
    company_id = fields.Many2one('res.company', string='Lembaga',
                                 related='absensi_id.company_id', readonly=True, store=True)

    def _compute_row_number(self):
        for index, record in enumerate(self):
            record.row_number = index + 1

    @api.depends('absensi_id.kelas_id')
    def _compute_allowed_siswa(self):
        for record in self:
            if record.absensi_id.kelas_id:
                record.allowed_siswa_ids = self.env['cdn.siswa'].search(
                    [('ruang_kelas_id', '=', record.absensi_id.kelas_id.id)]).ids
            else:
                record.allowed_siswa_ids = []

    @api.onchange('siswa_id')
    def _onchange_siswa_id(self):
        """Check permission when student is selected"""
        if self.siswa_id and self.tanggal:
            permission = self.env['cdn.perijinan'].search([
                ('siswa_id', '=', self.siswa_id.id),
                ('state', '=', 'Permission')
            ], limit=1)
            if permission:
                self.kehadiran = 'keluar'
                keperluan_name = permission.keperluan.name if permission.keperluan else 'Tidak ada keterangan'
                waktu_keluar = self.format_datetime_indonesia(
                    permission.waktu_keluar) if permission.waktu_keluar else 'Tidak tercatat'
                self.keterangan = f"Santri Keluar pada {waktu_keluar}, karena {keperluan_name}"
            else:
                self.kehadiran = 'Hadir'
                self.keterangan = False

    def action_view_permission(self):
        """Open permission form for this student"""
        if not self.siswa_id or not self.tanggal:
            return
        permission = self.env['cdn.perijinan'].search([
            ('siswa_id', '=', self.siswa_id.id),
            ('state', '=', 'Permission')
        ], limit=1)
        if not permission:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '❌ Tidak Dapat Menemukan Data!',
                    'message': 'Data perizinan tidak ditemukan, mungkin santri telah kembali.',
                    'type': 'danger',
                    'sticky': False,
                }
            }
        return {
            'type': 'ir.actions.act_window',
            'name': 'Detail Perijinan',
            'res_model': 'cdn.perijinan',
            'res_id': permission.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @staticmethod
    def format_datetime_indonesia(dt):
        bulan_dict = {
            '01': 'Januari', '02': 'Februari', '03': 'Maret', '04': 'April',
            '05': 'Mei', '06': 'Juni', '07': 'Juli', '08': 'Agustus',
            '09': 'September', '10': 'Oktober', '11': 'November', '12': 'Desember'
        }
        if dt:
            hari = dt.strftime('%d')
            bulan_angka = dt.strftime('%m')
            tahun = dt.strftime('%Y')
            jam_menit = dt.strftime('%H:%M')
            nama_bulan = bulan_dict.get(bulan_angka, bulan_angka)
            return f"{hari} {nama_bulan} {tahun} {jam_menit}"
        return 'Tidak tercatat'


class Kbm_Siswa(models.Model):
    _inherit = 'cdn.siswa'
    _description = 'Kbm_Siswa'
    kbm_id = fields.One2many(
        string='Kegiatan Belajar Mengajar',
        comodel_name='cdn.absensi_siswa_lines',
        inverse_name='siswa_id',
    )
