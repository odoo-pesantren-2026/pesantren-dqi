from odoo import api, fields, models, _
from datetime import date, datetime
import logging

_logger = logging.getLogger(__name__)


class TahfidzTahsin(models.Model):
    _name = 'cdn.penilaian_quran'
    _description = 'Rekam absensi per Santri'

    def _get_default_ustadz(self):
        user = self.env.user
        employee = self.env['hr.employee'].search(
            [('user_id', '=', user.id)], limit=1)
        return employee.id if employee else False

    ustadz_id = fields.Many2one(
        'hr.employee',
        string='Ustadz',
        required=True,
        default=_get_default_ustadz,
        store=True
    )
    name = fields.Char(string='No Referensi', readonly=True,
                       copy=False, default='/')
    tanggal = fields.Date(string='Tanggal', required=True,
                          default=fields.Date.context_today)
    siswa_id = fields.Many2one(
        'cdn.siswa', string='Santri', required=True, ondelete='cascade')
    # Data Santri (related)
    barcode = fields.Char(related='siswa_id.barcode_santri',
                          string="Kartu Santri", readonly=True)
    kelas_id = fields.Many2one(
        related='siswa_id.ruang_kelas_id', string='Kelas', readonly=True, store=True)
    kamar_id = fields.Many2one(
        related='siswa_id.kamar_id', string='Kamar', readonly=True)
    halaqoh_id = fields.Many2one(
        'cdn.halaqoh', string='Halaqoh', readonly=True, store=True, ondelete='cascade')
    musyrif_id = fields.Many2one(
        related='siswa_id.musyrif_id', string='Musyrif', readonly=True)
    penanggung_jawab_id = fields.Many2one(
        'hr.employee', string="Penanggung Jawab")
    pengganti_ids = fields.Many2many('hr.employee', string="Pengganti")
    # Umum
    # ustadz_id = fields.Many2one('hr.employee', string='Ustadz', required=True)
    jenjang_display = fields.Selection(
        related='siswa_id.jenjang', string='Jenjang', store=True)
    is_jenjang_paud_tk = fields.Boolean(
        string='Is PAUD/TK',
        compute='_compute_is_jenjang_paud_tk',
        store=True,
        help='True jika jenjang adalah PAUD, TK, atau TK/RA'
    )
    company_id = fields.Many2one(
        'res.company', string='Lembaga', default=lambda self: self.env.company)

    sesi_id = fields.Many2one('cdn.sesi_halaqoh', string='Sesi')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Selesai')
    ], default='draft', string='Status')

    # === TAB TAHFIDZ ===
    surah_id = fields.Many2one('cdn.surah', compute='_compute_main_fields',
                               string='Surah', ondelete='cascade', store="True")
    ayat_awal = fields.Many2one('cdn.ayat', string='Ayat Awal', compute='_compute_main_fields',
                                domain="[('surah_id','=',surah_id)]", ondelete='cascade', store="True")
    ayat_akhir = fields.Many2one('cdn.ayat', string='Ayat Akhir', compute='_compute_main_fields',
                                 domain="[('surah_id','=',surah_id)]", ondelete='cascade', store="True")
    jml_baris = fields.Integer(string="Jumlah Maqra'", store=True)
    # === TAHFIDZ ===
    nilai_hafalan = fields.Integer(string='Nilai Hafalan')
    nilai_tahfidz = fields.Many2one(
        'cdn.nilai_tahfidz', string='Nilai Tahfidz')
    last_jml_baris = fields.Integer(
        string="Jumlah Maqra'",
        compute='_compute_last_nilai_predikat',
        store=True
    )
    last_nilai_hafalan = fields.Integer(
        string='Nilai Hafalan',
        compute='_compute_last_nilai_predikat',
        store=True
    )
    last_predikat = fields.Char(
        string='Predikat',
        compute='_compute_last_nilai_predikat',
        store=True
    )

    # PREDIKAT (otomatis tergantung jenjang)
    predikat = fields.Char(
        string='Predikat', compute='_compute_predikat', store=True)
    keterangan_predikat = fields.Char(
        string='Keterangan', compute='_compute_predikat', store=True)
    keterangan_tahfidz = fields.Text(string='Keterangan Tahfidz')
    tahfidz_line_ids = fields.One2many(
        'cdn.penilaian_quran_line',
        'penilaian_id',
        string='Setoran Tahfidz'
    )

    # === TAB Tahfidz Ujian ===
    buku_tahfidz_ujian_id = fields.Many2one(
        'cdn.buku_tahsin',
        string='Buku',
        default=lambda self: self.env['cdn.buku_tahsin'].search(
            [('name', '=', "Al-Qur'an")], limit=1),
        readonly=True
    )

    # Ambil daftar Juz unik dari cdn.ayat
    juz_tahfidz_ujian = fields.Selection(
        selection=lambda self: self._get_juz_selection(),
        string='Juz'
    )

    halaman_tahfidz_ujian = fields.Char(string='Halaman')
    catatan_tahfidz = fields.Text(string='Catatan Tahfidz (Ujian)')

    surah_id_ujian_tahfidz = fields.Many2one(
        'cdn.surah', string='Surah', domain="[('id', 'in', available_surah_ids_tahfidz_ujian)]", ondelete='cascade')
    ayat_awal_ujian_tahfidz = fields.Many2one(
        'cdn.ayat', string='Ayat Awal', domain="[('surah_id','=',surah_id_ujian_tahfidz)]", ondelete='cascade')
    ayat_akhir_ujian_tahfidz = fields.Many2one(
        'cdn.ayat', string='Ayat Akhir', domain="[('surah_id','=',surah_id_ujian_tahfidz)]", ondelete='cascade')
    nilai_ujian_tahfidz = fields.Integer(string="Nilai")
    predikat_ujian_tahfidz = fields.Char(
        string='Predikat', compute='_compute_predikat_ujian_tahfidz', store=True)

    # Field bantu (computed, tidak disimpan)
    available_surah_ids_tahfidz_ujian = fields.Many2many(
        'cdn.surah',
        compute='_compute_available_surah_ids_tahfidz_ujian',
        string='Available Surahs',
        ondelete='cascade'
    )

    # === TAB Riwayat Hafalan ===
    riwayat_hafalan_ids = fields.One2many(
        'cdn.penilaian_quran_line',
        compute='_compute_riwayat_hafalan',
        string='Riwayat Hafalan',
        readonly=True
    )

    # === TAB Riwayat Tahfizh Ujian ===
    riwayat_tahfidz_ujian_ids = fields.Many2many(
        'cdn.penilaian_quran',
        compute='_compute_riwayat_tahfidz_ujian',
        string='Riwayat Tahfizh Ujian',
        readonly=True
    )

    # === TAB Riwayat Tahsin Harian ===
    riwayat_tahsin_harian_ids = fields.Many2many(
        'cdn.penilaian_quran',
        compute='_compute_riwayat_tahsin_harian',
        string='Riwayat Tahsin Harian',
        readonly=True
    )

    # === TAB Riwayat Tahsin Ujian ===
    riwayat_tahsin_ujian_ids = fields.Many2many(
        'cdn.penilaian_quran',
        compute='_compute_riwayat_tahsin_ujian',
        string='Riwayat Tahsin Ujian',
        readonly=True
    )

    # === TAB Murajaah Harian ===
    buku_murajaah_id = fields.Many2one(
        'cdn.buku_tahsin',
        string='Buku',
        default=lambda self: self.env['cdn.buku_tahsin'].search(
            [('name', '=', "Al-Qur'an")], limit=1),
        readonly=True
    )

    # Ambil daftar Juz unik dari cdn.ayat
    juz_murajaah = fields.Selection(
        selection=lambda self: self._get_juz_selection(),
        string='Juz'
    )

    # Surah (akan difilter berdasar juz)
    surah_murajaah_id = fields.Many2one(
        'cdn.surah',
        string='Surah',
        domain="[('id', 'in', available_surah_ids)]",
        ondelete='cascade'
    )

    halaman_murajaah = fields.Char(string='Halaman')
    catatan_murajaah_harian = fields.Text(string='Catatan Murajaah (Harian)')

    # Field bantu (computed, tidak disimpan)
    available_surah_ids = fields.Many2many(
        'cdn.surah',
        compute='_compute_available_surah_ids',
        string='Available Surahs',
        ondelete='cascade'
    )

    # === Helper Functions ===
    def _get_juz_selection(self):
        try:
            ayat_records = self.env['cdn.ayat'].search(
                [('juz', '!=', False), ('juz', '!=', 0)])
            juz_values = sorted(set(ayat_records.mapped('juz')))
            return [(str(j), f"{j}") for j in juz_values]
        except Exception:
            return []

    @api.depends('juz_tahfidz_ujian')
    def _compute_available_surah_ids_tahfidz_ujian(self):
        for rec in self:
            if rec.juz_tahfidz_ujian:
                ayat_ids = self.env['cdn.ayat'].search(
                    [('juz', '=', rec.juz_tahfidz_ujian)])
                rec.available_surah_ids_tahfidz_ujian = ayat_ids.mapped(
                    'surah_id')
            else:
                rec.available_surah_ids_tahfidz_ujian = False

    @api.depends('juz_murajaah')
    def _compute_available_surah_ids(self):
        for rec in self:
            if rec.juz_murajaah:
                ayat_ids = self.env['cdn.ayat'].search(
                    [('juz', '=', rec.juz_murajaah)])
                rec.available_surah_ids = ayat_ids.mapped('surah_id')
            else:
                rec.available_surah_ids = False

    # === TAB TAHsin HARIAN ===
    buku_harian_id = fields.Many2one('cdn.buku_tahsin', string='Buku (Harian)')
    jilid_harian_id = fields.Many2one('cdn.jilid_tahsin', string='Jilid (Harian)',
                                      domain="[('buku_tahsin_id', '=', buku_harian_id)]")
    halaman_harian = fields.Char(string='Halaman (Harian)')
    nilai_harian = fields.Selection(selection=[
        ('bb', '(BB) Belum Berkembang'),
        ('mb', '(MB) Mulai Berkembang'),
        ('bsa', '(BSA) Berkembang Sesuai Harapan'),
        ('bsb', '(BSB) Berkembang Sangat Bagus')
    ], string='Nilai (Harian)', default='bb')
    nilai_tahsin_harian = fields.Integer(string="Nilai")
    predikat_tahsin_harian = fields.Char(
        string='Predikat', compute='_compute_predikat_tahsin_harian', store=True)
    catatan_harian = fields.Text(string='Catatan (Harian)')
    surah_id_harian = fields.Many2one(
        'cdn.surah', string='Surah', ondelete='cascade')
    ayat_awal_harian = fields.Many2one(
        'cdn.ayat', string='Ayat Awal', domain="[('surah_id','=',surah_id_harian)]", ondelete='cascade')
    ayat_akhir_harian = fields.Many2one(
        'cdn.ayat', string='Ayat Akhir', domain="[('surah_id','=',surah_id_harian)]", ondelete='cascade')

    # === TAB TAHsin UJIAN ===
    buku_ujian_id = fields.Many2one('cdn.buku_tahsin', string='Buku (Ujian)')
    jilid_ujian_id = fields.Many2one('cdn.jilid_tahsin', string='Jilid (Ujian)',
                                     domain="[('buku_tahsin_id', '=', buku_ujian_id)]")
    halaman_ujian = fields.Char(string='Halaman (Ujian)')
    nilai_tajwid_ujian = fields.Integer(string='Nilai Tajwid')
    nilai_makhroj_ujian = fields.Integer(string='Nilai Makhroj')
    nilai_mad_ujian = fields.Integer(string='Nilai Mad')
    catatan_ujian = fields.Text(string='Catatan (Ujian)')
    surah_id_ujian = fields.Many2one(
        'cdn.surah', string='Surah', ondelete='cascade')
    ayat_awal_ujian = fields.Many2one(
        'cdn.ayat', string='Ayat Awal', domain="[('surah_id','=',surah_id_ujian)]", ondelete='cascade')
    ayat_akhir_ujian = fields.Many2one(
        'cdn.ayat', string='Ayat Akhir', domain="[('surah_id','=',surah_id_ujian)]", ondelete='cascade')
    # === INFORMASI TAHFIDZ TERAKHIR ===
    last_surah_id = fields.Many2one(
        'cdn.surah', string='Surah Terakhir',
        compute='_compute_last_tahfidz', store=True, readonly=True,
        ondelete='cascade'
    )
    last_ayat_akhir = fields.Many2one(
        'cdn.ayat', string='Ayat Terakhir',
        compute='_compute_last_tahfidz', store=True, readonly=True,
        ondelete='cascade'
    )

    @api.depends('siswa_id')
    def _compute_riwayat_hafalan(self):
        for rec in self:
            if not rec.siswa_id:
                rec.riwayat_hafalan_ids = False
                continue
            # Ambil semua penilaian_quran_line dari penilaian yang sudah done untuk santri ini
            penilaian_ids = self.env['cdn.penilaian_quran'].search([
                ('siswa_id', '=', rec.siswa_id.id),
                ('state', '=', 'done')
            ]).ids
            riwayat_lines = self.env['cdn.penilaian_quran_line'].search([
                ('penilaian_id', 'in', penilaian_ids)
            ])
            rec.riwayat_hafalan_ids = riwayat_lines

    @api.depends('siswa_id')
    def _compute_riwayat_tahfidz_ujian(self):
        """Compute riwayat tahfidz ujian dari penilaian yang sudah done dan memiliki data nilai_ujian_tahfidz"""
        for rec in self:
            if not rec.siswa_id:
                rec.riwayat_tahfidz_ujian_ids = False
                continue
            # Ambil semua penilaian_quran yang done dan ada tahfidz ujian untuk santri ini
            riwayat = self.env['cdn.penilaian_quran'].search([
                ('siswa_id', '=', rec.siswa_id.id),
                ('state', '=', 'done'),
                ('surah_id_ujian_tahfidz', '!=', False)
            ])
            rec.riwayat_tahfidz_ujian_ids = riwayat

    @api.depends('siswa_id')
    def _compute_riwayat_tahsin_harian(self):
        """Compute riwayat tahsin harian dari penilaian yang sudah done dan memiliki data buku_harian_id"""
        for rec in self:
            if not rec.siswa_id:
                rec.riwayat_tahsin_harian_ids = False
                continue
            # Ambil semua penilaian_quran yang done dan ada tahsin harian untuk santri ini
            riwayat = self.env['cdn.penilaian_quran'].search([
                ('siswa_id', '=', rec.siswa_id.id),
                ('state', '=', 'done'),
                ('buku_harian_id', '!=', False)
            ])
            rec.riwayat_tahsin_harian_ids = riwayat

    @api.depends('siswa_id')
    def _compute_riwayat_tahsin_ujian(self):
        """Compute riwayat tahsin ujian dari penilaian yang sudah done dan memiliki data buku_ujian_id"""
        for rec in self:
            if not rec.siswa_id:
                rec.riwayat_tahsin_ujian_ids = False
                continue
            # Ambil semua penilaian_quran yang done dan ada tahsin ujian untuk santri ini
            riwayat = self.env['cdn.penilaian_quran'].search([
                ('siswa_id', '=', rec.siswa_id.id),
                ('state', '=', 'done'),
                ('buku_ujian_id', '!=', False)
            ])
            rec.riwayat_tahsin_ujian_ids = riwayat

    @api.depends('jenjang_display')
    def _compute_is_jenjang_paud_tk(self):
        """Compute boolean untuk mengecek apakah jenjang PAUD/TK"""
        for rec in self:
            jenjang = (rec.jenjang_display or '').lower()
            rec.is_jenjang_paud_tk = jenjang in ['paud', 'tk', 'tk/ra']

    @api.depends('tahfidz_line_ids', 'tahfidz_line_ids.nilai_hafalan', 'tahfidz_line_ids.penilaian_id.jenjang_display')
    def _compute_last_nilai_predikat(self):
        for rec in self:
            if rec.tahfidz_line_ids:
                # Ambil line terakhir berdasarkan sequence
                last_line = rec.tahfidz_line_ids.sorted(
                    key=lambda r: r.sequence or 0)[-1]
                rec.last_jml_baris = last_line.jml_baris
                rec.last_nilai_hafalan = last_line.nilai_hafalan
                rec.last_predikat = last_line.predikat
            else:
                rec.last_nilai_hafalan = 0
                rec.last_predikat = ''

    # === HELPER METHOD UNTUK PREDIKAT ===
    def _get_predikat(self, nilai, jenjang):
        """
        Method helper untuk menghitung predikat berdasarkan nilai dan jenjang.
        Returns: tuple (predikat, keterangan) atau (False, False)
        """
        n = nilai or 0
        jenjang_lower = (jenjang or '').lower()

        # === PAUD/TK ===
        if jenjang_lower in ['paud', 'tk', 'tk/ra']:
            if n >= 90:
                return 'BSB', 'Berkembang Sangat Bagus'
            elif n >= 75:
                return 'BSA', 'Berkembang Sesuai Harapan'
            elif n >= 60:
                return 'MB', 'Mulai Berkembang'
            else:
                return 'BB', 'Belum Berkembang'

        # === SD ===
        elif jenjang_lower in ['sd', 'sd/mi', 'sdmi']:
            if n >= 95:
                return 'A+', 'Mumtaz'
            elif n >= 91:
                return 'A', 'Jayyid Jiddan'
            elif n >= 80:
                return 'B+', 'Jayyid'
            elif n >= 70:
                return 'B', 'Maqbul'
            elif n >= 60:
                return 'C', 'Dhaif'
            else:
                return 'D', 'Dhaif Jiddan'

        # === SMP ===
        elif jenjang_lower in ['smp', 'smp/mts', 'smpmts']:
            if n >= 90:
                return 'A', 'Mumtaz'
            elif n >= 80:
                return 'B', 'Jayyid Jiddan'
            elif n >= 70:
                return 'C', 'Jayyid'
            else:
                return 'D', 'Mardud'

        # === SMA ===
        elif jenjang_lower in ['sma', 'ma', 'smama']:
            if n >= 96:
                return 'A+', 'Mumtaz'
            elif n >= 90:
                return 'A', 'Mumtaz'
            elif n >= 80:
                return 'B+', 'Jayyid Jiddan'
            elif n >= 75:
                return 'B', 'Jayyid'
            elif n >= 70:
                return 'C', 'Maqbul'
            elif n >= 60:
                return 'D', 'Dhaif'
            else:
                return 'E', 'Dhaif Jiddan'

        # === Default ===
        return False, False

    # === COMPUTE ===
    @api.depends('nilai_tahfidz.name', 'jenjang_display')
    def _compute_predikat(self):
        """Compute predikat untuk Tahfidz"""
        for rec in self:
            n = rec.nilai_tahfidz.name if rec.nilai_tahfidz else 0
            predikat, keterangan = rec._get_predikat(n, rec.jenjang_display)
            rec.predikat = predikat
            rec.keterangan_predikat = keterangan

    @api.depends('nilai_tahsin_harian', 'jenjang_display')
    def _compute_predikat_tahsin_harian(self):
        """Compute predikat untuk Tahsin Harian"""
        for rec in self:
            predikat, keterangan = rec._get_predikat(
                rec.nilai_tahsin_harian, rec.jenjang_display)
            if predikat:
                rec.predikat_tahsin_harian = f"{predikat} ({keterangan})"
            else:
                rec.predikat_tahsin_harian = False

    @api.depends('nilai_ujian_tahfidz', 'jenjang_display')
    def _compute_predikat_ujian_tahfidz(self):
        """Compute predikat untuk Ujian Tahfidz"""
        for rec in self:
            predikat, keterangan = rec._get_predikat(
                rec.nilai_ujian_tahfidz, rec.jenjang_display)
            if predikat:
                rec.predikat_ujian_tahfidz = f"{predikat} ({keterangan})"
            else:
                rec.predikat_ujian_tahfidz = False

    @api.depends('tahfidz_line_ids', 'tahfidz_line_ids.sequence')
    def _compute_main_fields(self):
        for rec in self:
            lines = rec.tahfidz_line_ids
            if lines:
                # urutkan manual berdasarkan sequence saja (aman tanpa id)
                sorted_lines = lines.sorted(key=lambda r: (r.sequence or 0))
                first_line = sorted_lines[0]
                last_line = sorted_lines[-1]

                rec.surah_id = last_line.surah_id.id
                rec.ayat_awal = first_line.ayat_awal.id
                rec.ayat_akhir = last_line.ayat_akhir.id
            else:
                rec.surah_id = False
                rec.ayat_awal = False
                rec.ayat_akhir = False

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'cdn.penilaian_quran') or '/'
        record = super().create(vals)
        record._compute_main_fields()  # isi surah_id, ayat_awal, ayat_akhir
        return record

    @api.depends('siswa_id', 'tahfidz_line_ids.surah_id', 'tahfidz_line_ids.ayat_akhir', 'state', 'halaqoh_id')
    def _compute_last_tahfidz(self):
        for rec in self:
            if not rec.siswa_id:
                rec.last_surah_id = False
                rec.last_ayat_akhir = False
                continue

            # Jika record ini sudah done dan ada tahfidz_line_ids, gunakan data dari line
            if rec.state == 'done' and rec.tahfidz_line_ids:
                last_line = rec.tahfidz_line_ids.sorted(
                    key=lambda r: (r.sequence or 0, r.id))[-1]
                rec.last_surah_id = last_line.surah_id.id
                rec.last_ayat_akhir = last_line.ayat_akhir.id
                continue

            # Cari penilaian terakhir yang sudah done (kecuali record ini)
            domain = [
                ('siswa_id', '=', rec.siswa_id.id),
                ('state', '=', 'done')
            ]
            if rec.id:
                domain.append(('id', '!=', rec.id))

            last = self.search(domain, order='tanggal desc, id desc', limit=1)

            if last and last.tahfidz_line_ids:
                # Ambil dari tahfidz_line_ids terakhir
                last_line = last.tahfidz_line_ids.sorted(
                    key=lambda r: (r.sequence or 0, r.id))[-1]
                rec.last_surah_id = last_line.surah_id.id
                rec.last_ayat_akhir = last_line.ayat_akhir.id
            elif last and last.last_surah_id and last.last_ayat_akhir:
                # Ambil dari last_surah_id dan last_ayat_akhir
                rec.last_surah_id = last.last_surah_id.id
                rec.last_ayat_akhir = last.last_ayat_akhir.id
            else:
                # Jika tidak ada data sebelumnya, gunakan Al-Fatihah ayat 1
                surah_fatihah = self.env['cdn.surah'].search(
                    [('number', '=', 1)], limit=1)
                if surah_fatihah:
                    rec.last_surah_id = surah_fatihah.id
                    ayat_1 = self.env['cdn.ayat'].search([
                        ('surah_id', '=', surah_fatihah.id),
                        ('name', '=', 1)
                    ], limit=1)
                    rec.last_ayat_akhir = ayat_1.id
                else:
                    rec.last_surah_id = False
                    rec.last_ayat_akhir = False

    # === ONCHANGE ===
    @api.onchange('buku_harian_id')
    def _onchange_buku_harian(self):
        self.jilid_harian_id = False
        self.halaman_harian = False

    @api.onchange('buku_ujian_id')
    def _onchange_buku_ujian(self):
        self.jilid_ujian_id = False
        self.halaman_ujian = False

    @api.onchange('siswa_id')
    def _onchange_siswa_id(self):
        _logger.warning("ONCHANGE: siswa_id = %s", self.siswa_id)
        if not self.siswa_id:
            return

        # Ambil penilaian terakhir DONE (pakai logika sama seperti compute)
        last_penilaian = self.env['cdn.penilaian_quran'].search([
            ('siswa_id', '=', self.siswa_id.id),
            ('state', '=', 'done')
        ], order='tanggal desc, id desc', limit=1)

        if last_penilaian:
            if last_penilaian.tahfidz_line_ids:
                last_line = last_penilaian.tahfidz_line_ids.sorted(
                    key=lambda r: (r.sequence or 0, r.id))[-1]
                self.last_surah_id = last_line.surah_id.id
                self.last_ayat_akhir = last_line.ayat_akhir.id

                # Tentukan ayat awal berikutnya
                surah = last_line.surah_id
                ayat_akhir = last_line.ayat_akhir.name if last_line.ayat_akhir else 0
                total_ayat = surah.jml_ayat if surah else 0

                if ayat_akhir and ayat_akhir < total_ayat:
                    # Lanjut surah sama
                    self.surah_id = surah.id
                    next_ayat_num = ayat_akhir + 1
                    next_ayat = self.env['cdn.ayat'].search([
                        ('surah_id', '=', surah.id),
                        ('name', '=', next_ayat_num)
                    ], limit=1)
                    self.ayat_awal = next_ayat.id
                else:
                    # Pindah surah berikutnya
                    next_surah = self.env['cdn.surah'].search([
                        ('number', '>', surah.number)
                    ], order='number', limit=1)
                    if next_surah:
                        self.surah_id = next_surah.id
                        ayat_1 = self.env['cdn.ayat'].search([
                            ('surah_id', '=', next_surah.id),
                            ('name', '=', 1)
                        ], limit=1)
                        self.ayat_awal = ayat_1.id
            else:
                # fallback kalau tidak ada line
                self.last_surah_id = last_penilaian.surah_id.id
                self.last_ayat_akhir = last_penilaian.ayat_akhir.id
        else:
            # Belum ada data → mulai dari Al-Fatihah
            surah_fatihah = self.env['cdn.surah'].search(
                [('number', '=', 1)], limit=1)
            if surah_fatihah:
                self.surah_id = surah_fatihah.id
                ayat_1 = self.env['cdn.ayat'].search([
                    ('surah_id', '=', surah_fatihah.id),
                    ('name', '=', 1)
                ], limit=1)
                self.ayat_awal = ayat_1.id

    # === WORKFLOW ===
    def action_confirm(self):
        for rec in self:
            rec.state = 'done'
            rec._compute_last_tahfidz()  # Perbarui last_surah_id dan last_ayat_akhir
            rec._compute_main_fields()   # Perbarui surah_id, ayat_awal, ayat_akhir

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    # === OTHER ===
    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'cdn.penilaian_quran') or '/'
        return super().create(vals)

    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.siswa_id.name} - {rec.tanggal}"
            result.append((rec.id, name))
        return result


class PenilaianQuranLine(models.Model):
    _name = 'cdn.penilaian_quran_line'
    _description = 'Detail Setoran Tahfidz'
    _order = 'sequence, id'

    penilaian_id = fields.Many2one(
        'cdn.penilaian_quran', string='Penilaian', ondelete='cascade')
    sequence = fields.Integer(string='No', default=1)
    surah_id = fields.Many2one(
        'cdn.surah', string='Surah', required=True, ondelete='cascade')
    ayat_awal = fields.Many2one('cdn.ayat', string='Ayat Awal',
                                domain="[('surah_id','=',surah_id)]", ondelete='cascade')
    ayat_akhir = fields.Many2one('cdn.ayat', string='Ayat Akhir',
                                 domain="[('surah_id','=',surah_id)]", ondelete='cascade')
    jml_baris = fields.Integer(string="Jumlah Maqra")
    nilai_hafalan = fields.Integer(string='Nilai Hafalan', default=75)
    tanggal_penilaian = fields.Date(
        string='Tanggal Penilaian',
        related='penilaian_id.tanggal',
        store=True
    )
    halaqoh_id = fields.Many2one(
        'cdn.halaqoh',
        string='Halaqoh',
        related='penilaian_id.halaqoh_id',
        store=True,
        readonly=True
    )
    sesi_id = fields.Many2one(
        'cdn.sesi_halaqoh',
        string='Sesi',
        related='penilaian_id.sesi_id',
        store=True,
        readonly=True
    )
    ustadz_id = fields.Many2one(
        'hr.employee',
        string='Ustadz',
        related='penilaian_id.ustadz_id',
        store=True,
        readonly=True
    )

    predikat = fields.Char(
        string='Predikat', compute='_compute_predikat', store=True)
    keterangan = fields.Char(string='Keterangan')

    @api.depends('nilai_hafalan', 'penilaian_id.jenjang_display')
    def _compute_predikat(self):
        for rec in self:
            n = rec.nilai_hafalan or 0
            jenjang = (rec.penilaian_id.jenjang_display or '').lower()

            # === PAUD/TK ===
            if jenjang in ['paud', 'tk', 'tk/ra']:
                if n >= 90:
                    rec.predikat = 'BSB - Berkembang Sangat Bagus'
                elif n >= 75:
                    rec.predikat = 'BSA - Berkembang Sesuai Harapan'
                elif n >= 60:
                    rec.predikat = 'MB - Mulai Berkembang'
                else:
                    rec.predikat = 'BB - Belum Berkembang'

            # === SD ===
            elif jenjang in ['sd', 'sd/mi', 'sdmi']:
                if n >= 95:
                    rec.predikat = 'A+ (Mumtaz)'
                elif n >= 91:
                    rec.predikat = 'A (Jayyid Jiddan)'
                elif n >= 80:
                    rec.predikat = 'B+ (Jayyid)'
                elif n >= 70:
                    rec.predikat = 'B (Maqbul)'
                elif n >= 60:
                    rec.predikat = 'C (Dhaif)'
                else:
                    rec.predikat = 'D (Dhaif Jiddan)'

            # === SMP ===
            elif jenjang in ['smp', 'smp/mts', 'smpmts']:
                if n >= 90:
                    rec.predikat = 'A (Mumtaz)'
                elif n >= 80:
                    rec.predikat = 'B (Jayyid Jiddan)'
                elif n >= 70:
                    rec.predikat = 'C (Jayyid)'
                else:
                    rec.predikat = 'D (Mardud)'

            # === SMA ===
            elif jenjang in ['sma', 'ma', 'smama']:
                if n >= 96:
                    rec.predikat = 'A+ (Mumtaz)'
                elif n >= 90:
                    rec.predikat = 'A (Mumtaz)'
                elif n >= 80:
                    rec.predikat = 'B+ (Jayyid Jiddan)'
                elif n >= 75:
                    rec.predikat = 'B (Jayyid)'
                elif n >= 70:
                    rec.predikat = 'C (Maqbul)'
                elif n >= 60:
                    rec.predikat = 'D (Dhaif)'
                else:
                    rec.predikat = 'E (Dhaif Jiddan)'
