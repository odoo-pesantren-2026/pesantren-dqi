# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Penugasan(models.Model):
    _name = 'cdn.penugasan'
    _description = 'Data Penugasan'
    _rec_name = 'tugas_ujian'

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

    kelas_id = fields.Many2one(
        'cdn.ruang_kelas', string='Ruang Kelas', required=True)
    tugas_ujian = fields.Text(string='Deskripsi Tugas / Ujian', required=True,
                              help="Jelaskan secara detail mengenai tugas atau ujian yang diberikan kepada siswa")
    tanggal = fields.Date(string='Tgl Penugasan', default=fields.Date.today())
    deadline = fields.Date(
        string='Deadline', help="Batas akhir waktu pengumpulan tugas/pelaksanaan ujian")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('proses', 'Ditugaskan'),
        ('done', 'Selesai'),
    ], default='draft', string='Status', help="Status penugasan saat ini")
    tugas_line_ids = fields.One2many(
        comodel_name='cdn.tugas_line', inverse_name='penugasan_id', string='Tugas Line')
    tingkat_id = fields.Many2one(
        'cdn.tingkat', string='Kelas', related='kelas_id.tingkat', store=True)
    matpel_id = fields.Many2one(
        comodel_name='cdn.mata_pelajaran', string='Mata Pelajaran', required=True)
    guru_id = fields.Many2one(
        'hr.employee',
        string='Guru',
        required=True,
        domain=lambda self: self.env['cdn.penugasan']._domain_guru(),
        default=lambda self: self.env['hr.employee'].search([
            ('user_id', '=', self.env.uid),
            ('jns_pegawai_ids.code', 'in', ['guru'])
        ], limit=1)
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

    def action_proses(self):
        self.state = 'proses'

    def action_done(self):
        self.state = 'done'

    @api.onchange('kelas_id')
    def _onchange_kelas_id(self):
        if self.kelas_id:
            kelas = self.env['cdn.ruang_kelas'].search(
                [('id', '=', self.kelas_id.id)])
            if kelas:
                tugas_line_ids = [(5, 0, 0)]
                if self.kelas_id.siswa_ids:
                    for siswa in self.kelas_id.siswa_ids:
                        tugas_line_ids.append((0, 0, {
                            'siswa_id': siswa.id,
                            'nilai': 0,
                            'company_id': self.company_id.id,
                        }))
                return {'domain': {
                    'kelas_id': [('id', '=', self.kelas_id.id)],
                    'tugas_line_ids': [('siswa_id', 'in', self.kelas_id.siswa_ids.ids)]
                }, 'value': {
                    'tugas_line_ids': tugas_line_ids
                }
                }
            else:
                return {
                }

    @api.onchange('matpel_id')
    def _onchange_matpel_id(self):
        if self.matpel_id:
            # Ambil domain guru dari hak akses
            base_domain = self._domain_guru()

            # Ambil guru dari mata pelajaran
            guru_ids = self.matpel_id.guru_ids.ids
            domain_mapel = [('id', 'in', guru_ids)]

            # Gabungkan kedua domain
            final_domain = base_domain + domain_mapel

            # Isi otomatis guru_id
            if guru_ids:
                # Kalau hanya 1 guru → langsung isi
                if len(guru_ids) == 1:
                    self.guru_id = guru_ids[0]
                # Kalau mau isi otomatis guru pertama walau > 1
                elif not self.guru_id:
                    self.guru_id = guru_ids[0]
            else:
                self.guru_id = False

            return {'domain': {'guru_id': final_domain}}
        else:
            self.guru_id = False
            return {'domain': {'guru_id': self._domain_guru()}}

    class TugasLine(models.Model):
        _name = 'cdn.tugas_line'
        _description = 'Tugas Line'

        name = fields.Char(
            string='Nama', related='siswa_id.name', readonly=True, store=True)
        siswa_id = fields.Many2one(
            'cdn.siswa', string='Nama', required=True, ondelete='cascade')
        kelas_id = fields.Many2one('cdn.ruang_kelas', string='Kelas',
                                   related='penugasan_id.kelas_id', readonly=True, store=True)
        nilai = fields.Float(string='Nilai')
        keterangan = fields.Char(string='Keterangan')
        penugasan_id = fields.Many2one(
            'cdn.penugasan', string='Penugasan', ondelete='cascade')
        state = fields.Selection([
            ('draft', 'Draft'),
            ('proses', 'Ditugaskan'),
            ('done', 'Selesai'),
        ], default='draft', string='Status', related='penugasan_id.state', readonly=True, store=True)

        panggilan = fields.Char(
            string='Nama Panggilan', related='siswa_id.namapanggilan', readonly=True, store=True)
        company_id = fields.Many2one('res.company', string='Lembaga',
                                     related='penugasan_id.company_id', readonly=True, store=True)
