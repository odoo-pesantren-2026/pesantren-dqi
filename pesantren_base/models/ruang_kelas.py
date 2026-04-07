# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime


class ruang_kelas(models.Model):
    _name = "cdn.ruang_kelas"
    _description = "Tabel Data Ruang Kelas"
    _order = "tingkat_urutan, nama_kelas, id"

    def _get_domain_guru(self):
        admin_user_ids = self.env.ref('base.group_system').users.ids

        return [
            '|',
            ('user_id', '=', admin_user_ids),
            ('jns_pegawai_ids.code', 'in', ['guru', 'superadmin'])
        ]

    name = fields.Many2one(
        comodel_name="cdn.master_kelas",
        string="Rombongan Belajar",
        required=True,
        copy=False,
    )

    siswa_ids = fields.Many2many(
        'cdn.siswa',
        'ruang_kelas_siswa_rel',
        'ruang_kelas_id',
        'siswa_id',
        ondelete='cascade',
        string='Daftar Siswa',
        domain="[('active', '=', True), ('jenjang', '=', jenjang), '|', ('ruang_kelas_id', '=', False), ('ruang_kelas_id', '=', id)]"
    )

    tahunajaran_id = fields.Many2one(
        comodel_name="cdn.ref_tahunajaran",
        string="Tahun Pelajaran",
        required=True,
        default=lambda self: self.env.user.company_id.tahun_ajaran_aktif.id
    )
    walikelas_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Wali Kelas",
        domain=lambda self: self.env['cdn.ruang_kelas']._get_domain_guru()
    )
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
        related='name.jenjang',
        store=True,
        readonly=True
    )
    tingkat = fields.Many2one(
        comodel_name="cdn.tingkat",
        string="Tingkat",
        related='name.tingkat',
        store=True,
        readonly=True
    )

    # Tambahan: field untuk menyimpan urutan tingkat sebagai integer
    tingkat_urutan = fields.Integer(
        string="Urutan Tingkat",
        compute='_compute_tingkat_urutan',
        store=True,
        help="Urutan numerik tingkat untuk sorting (1, 2, 3, dst)"
    )

    jurusan_id = fields.Many2one(
        comodel_name='cdn.master_jurusan',
        string='Jurusan / Peminatan',
        related='name.jurusan_id',
        store=True,
        readonly=True
    )
    nama_kelas = fields.Char(
        string="Nama Kelas", store=True, help="Nama spesifik ruangan kelas.")

    status = fields.Selection(
        string='Status',
        selection=[('draft', 'Draft'), ('konfirm', 'Terkonfirmasi')],
        default="draft"
    )
    jml_siswa = fields.Integer(
        string='Jumlah Siswa',
        compute='_compute_jml_siswa',
        store=True
    )

    aktif_tidak = fields.Selection([
        ('aktif', 'Aktif'),
        ('tidak', 'Tidak Aktif'),
    ], string="Aktif/Tidak", required=True, default='aktif')

    keterangan = fields.Char(
        string="Keterangan", help="Nama spesifik ruangan kelas.")

    angkatan_id = fields.Many2one(
        comodel_name="cdn.ref_tahunajaran",
        string="Angkatan",
        default=lambda self: self._get_default_angkatan(),
    )

    def _get_default_angkatan(self):
        today = date.today()
        tahun = today.year
        bulan = today.month

        # Tahun ajaran mulai dari 1 Juli
        if bulan >= 7:
            start_year = tahun
        else:
            start_year = tahun - 1

        nama_tahun_ajaran = f"{start_year}/{start_year + 1}"

        return self.env['cdn.ref_tahunajaran'].search([
            ('name', '=', nama_tahun_ajaran)
        ], limit=1)

    # Tambahan: compute method untuk menghitung urutan tingkat
    @api.depends('tingkat', 'jenjang')
    def _compute_tingkat_urutan(self):
        """
        Menghitung urutan numerik berdasarkan tingkat dan jenjang
        Mengambil angka dari nama tingkat atau menggunakan mapping default
        """
        for record in self:
            urutan = 999  # default value untuk tingkat yang tidak dikenali

            if record.tingkat:
                # Pastikan tingkat.name adalah string, jika tidak konversi dulu
                try:
                    if hasattr(record.tingkat, 'name') and record.tingkat.name:
                        tingkat_name = str(record.tingkat.name).strip().lower()
                    else:
                        # Jika tidak ada name, coba ambil dari display_name atau id
                        tingkat_name = str(
                            record.tingkat.display_name or record.tingkat.id).strip().lower()
                except (AttributeError, TypeError):
                    # Fallback jika ada masalah dengan akses tingkat
                    tingkat_name = ""

                if tingkat_name:
                    # Import regex di dalam try block untuk keamanan
                    import re

                    # Mapping berdasarkan jenjang
                    if record.jenjang == 'tk':
                        if 'a' in tingkat_name or '1' in tingkat_name:
                            urutan = 1
                        elif 'b' in tingkat_name or '2' in tingkat_name:
                            urutan = 2
                    elif record.jenjang in ['sd', 'smp', 'sma']:
                        # Ekstrak angka dari nama tingkat
                        numbers = re.findall(r'\d+', tingkat_name)
                        if numbers:
                            urutan = int(numbers[0])
                        else:
                            # Mapping manual untuk kelas yang menggunakan huruf romawi
                            tingkat_mapping = {
                                'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5, 'vi': 6,
                                'vii': 7, 'viii': 8, 'ix': 9, 'x': 10, 'xi': 11, 'xii': 12
                            }
                            for key, value in tingkat_mapping.items():
                                if key in tingkat_name:
                                    urutan = value
                                    break
                    elif record.jenjang == 'paud':
                        # Untuk PAUD, bisa disesuaikan dengan kebutuhan
                        if 'play' in tingkat_name or 'bermain' in tingkat_name:
                            urutan = 1
                        elif 'preparation' in tingkat_name or 'persiapan' in tingkat_name:
                            urutan = 2
                        else:
                            # Coba ekstrak angka
                            numbers = re.findall(r'\d+', tingkat_name)
                            if numbers:
                                urutan = int(numbers[0])

            record.tingkat_urutan = urutan

    @api.constrains('name', 'tahunajaran_id', 'status', 'aktif_tidak')
    def _check_duplicate_kelas_konfirm(self):
        """
        Validasi duplikat kelas:
        - Hanya berlaku untuk kelas yang aktif
        - Tidak boleh ada duplikat jika status terkonfirmasi
        - Boleh duplikat jika status draft
        """
        for record in self:
            if record.aktif_tidak == 'aktif' and record.status == 'konfirm':
                # Cek apakah ada kelas lain yang aktif dan terkonfirmasi dengan nama dan tahun ajaran yang sama
                duplicate = self.search([
                    ('id', '!=', record.id),
                    ('name', '=', record.name.id),
                    ('tahunajaran_id', '=', record.tahunajaran_id.id),
                    ('status', '=', 'konfirm'),
                    ('aktif_tidak', '=', 'aktif'),
                ], limit=1)

                if duplicate:
                    raise UserError(
                        _("Tidak boleh ada duplikat kelas yang aktif dan terkonfirmasi! "
                          "Kelas '%s' pada tahun ajaran '%s' sudah ada dengan status terkonfirmasi.") %
                        (record.name.name, record.tahunajaran_id.name)
                    )

    @api.onchange('tingkat', 'jurusan_id', 'nama_kelas')
    def _onchange_tingkat_jurusan_nama(self):
        domain = []

        # Filter berdasarkan tingkat
        if self.tingkat:
            domain.append(('tingkat', '=', self.tingkat.id))

        # Filter jurusan hanya jika jenjang SMA
        if self.jenjang == 'sma' and self.jurusan_id:
            domain.append(('jurusan_id', '=', self.jurusan_id.id))

        # Jika nama_kelas diisi, cari yang sesuai
        if self.nama_kelas:
            domain.append(('nama_kelas', 'ilike', self.nama_kelas.strip()))
        # Hapus kondisi else yang membatasi pencarian ke nama_kelas kosong

        # Jalankan pencarian berdasarkan domain
        if domain:
            kelas = self.env['cdn.master_kelas'].search(domain, limit=1)
            self.name = kelas.id if kelas else False
            return {'domain': {'name': domain}}
        else:
            self.name = False
            return {}

    @api.onchange('name', 'tahunajaran_id', 'aktif_tidak', 'status')
    def _onchange_detect_duplikat_kelas_aktif(self):
        """
        Peringatan duplikat dengan aturan baru:
        - Hanya peringatan untuk kelas aktif
        - Peringatan khusus jika akan membuat duplikat terkonfirmasi
        """
        if self.name and self.tahunajaran_id and self.aktif_tidak == 'aktif':
            # Cek duplikat dengan status terkonfirmasi
            duplikat_konfirm = self.env['cdn.ruang_kelas'].search([
                ('id', '!=', self.id),
                ('name', '=', self.name.id),
                ('tahunajaran_id', '=', self.tahunajaran_id.id),
                ('aktif_tidak', '=', 'aktif'),
                ('status', '=', 'konfirm'),
            ], limit=1)

            # Cek duplikat dengan status draft
            duplikat_draft = self.env['cdn.ruang_kelas'].search([
                ('id', '!=', self.id),
                ('name', '=', self.name.id),
                ('tahunajaran_id', '=', self.tahunajaran_id.id),
                ('aktif_tidak', '=', 'aktif'),
                ('status', '=', 'draft'),
            ], limit=1)

            if duplikat_konfirm and self.status == 'konfirm':
                return {
                    'warning': {
                        'title': "Error: Duplikat Kelas Terkonfirmasi",
                        'message': "Sudah ada kelas aktif yang terkonfirmasi dengan nama dan tahun ajaran yang sama. "
                                 "Tidak diperbolehkan memiliki duplikat kelas terkonfirmasi.",
                    }
                }

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            self.tingkat = self.name.tingkat.id
            self.jurusan_id = self.name.jurusan_id.id
            self.nama_kelas = self.name.nama_kelas
            self.walikelas_id = self.walikelas_id.id

    # Tambahkan method untuk memastikan nama_kelas selalu diisi dari name
    @api.model
    def create(self, vals):
        if vals.get('name'):
            kelas = self.env['cdn.master_kelas'].browse(vals.get('name'))
            if kelas and kelas.nama_kelas:
                vals['nama_kelas'] = kelas.nama_kelas
        return super(ruang_kelas, self).create(vals)

    def write(self, vals):
        if vals.get('name'):
            kelas = self.env['cdn.master_kelas'].browse(vals.get('name'))
            if kelas and kelas.nama_kelas:
                vals['nama_kelas'] = kelas.nama_kelas
        result = super(ruang_kelas, self).write(vals)
        return result

    def konfirmasi(self):
        for rec in self:
            # Pastikan nama_kelas diisi dari name jika kosong
            if rec.name and not rec.nama_kelas:
                rec.nama_kelas = rec.name.nama_kelas

            # Validasi duplikat sebelum konfirmasi (hanya untuk kelas aktif)
            if rec.aktif_tidak == 'aktif':
                duplicate_konfirm = self.env['cdn.ruang_kelas'].search([
                    ('id', '!=', rec.id),
                    ('name', '=', rec.name.id),
                    ('tahunajaran_id', '=', rec.tahunajaran_id.id),
                    ('status', '=', 'konfirm'),
                    ('aktif_tidak', '=', 'aktif'),
                ], limit=1)

                if duplicate_konfirm:
                    raise UserError(
                        _("Tidak dapat mengkonfirmasi kelas ini karena sudah ada kelas aktif yang terkonfirmasi "
                          "dengan nama '%s' pada tahun ajaran '%s'. "
                          "Silakan ubah status kelas lain menjadi draft terlebih dahulu atau nonaktifkan kelas tersebut.") %
                        (rec.name.name, rec.tahunajaran_id.name)
                    )

            rec.status = 'konfirm'

            conflicting_students = [
                (s.name, s.ruang_kelas_id.name.name,
                 s.ruang_kelas_id.tahunajaran_id.name)
                for s in rec.siswa_ids
                if s.ruang_kelas_id and s.ruang_kelas_id.id != rec.id and s.ruang_kelas_id.tahunajaran_id == rec.tahunajaran_id
            ]

            if conflicting_students:
                conflict_message = "\n".join(
                    ["Siswa atas nama %s sudah terdaftar di %s pada Tahun Ajaran %s!" % (name, kelas, tahun)
                     for name, kelas, tahun in conflicting_students]
                )
                raise UserError(
                    "Silakan hapus dulu data siswa yang bersangkutan dari kelas lain:\n\n%s" % conflict_message)

            # Set ruang_kelas_id dan tahunajaran_id pada siswa
            for siswa in rec.siswa_ids:
                siswa.write({
                    'ruang_kelas_id': rec.id,
                    'tahunajaran_id': rec.tahunajaran_id.id,  # Tambahan: set tahun ajaran siswa
                })

            # Reset siswa yang sebelumnya ada tapi sekarang tidak
            siswa_existing = self.env['cdn.siswa'].search(
                [('ruang_kelas_id', '=', rec.id)])
            for siswa in siswa_existing:
                if siswa.id not in rec.siswa_ids.ids:
                    siswa.write({
                        'ruang_kelas_id': False,
                        'tahunajaran_id': False,  # Tambahan: reset tahun ajaran juga
                    })

            message_id = self.env['message.wizard'].create({
                'message': _("Update Ruang Kelas Siswa - SUKSES !!")
            })
            return {
                'name': _('Berhasil'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'message.wizard',
                'res_id': message_id.id,
                'target': 'new'
            }

    def draft(self):
        for rec in self:
            rec.status = 'draft'

    @api.depends('siswa_ids')
    def _compute_jml_siswa(self):
        for record in self:
            record.jml_siswa = len(record.siswa_ids)


class MessageWizard(models.TransientModel):
    _name = 'message.wizard'

    message = fields.Text('Informasi', required=True)

    def action_ok(self):
        """ close wizard"""
        return {'type': 'ir.actions.act_window_close'}
