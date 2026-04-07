# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class KenaikanKelasLine(models.Model):
    _name = 'cdn.kenaikan_kelas.line'
    _description = 'Detail santri dalam proses kenaikan kelas'

    kenaikan_id = fields.Many2one('cdn.kenaikan_kelas', string='Header')
    siswa_id = fields.Many2one('cdn.siswa', string='Santri')
    nis = fields.Char(related='siswa_id.nis', string='NIS', store=False)
    kelas_sekarang_id = fields.Many2one(
        related='siswa_id.ruang_kelas_id', string='Kelas Sekarang', store=False)
    next_class_id = fields.Many2one(
        'cdn.master_kelas', string='Kelas Selanjutnya')


class KenaikanKelas(models.Model):
    _name = 'cdn.kenaikan_kelas'
    _description = 'Menu POP UP untuk mengatur kenaikan kelas dan kelas yang lulus'
    _rec_name = 'tahunajaran_id'

    jenjang = fields.Selection(
        selection=[('paud', 'PAUD'), ('tk', 'TK/RA'), ('sd', 'SD/MI'),
                   ('smp', 'SMP/MTS'), ('sma', 'SMA/MA/SMK'), ('nonformal', 'Nonformal')],
        string="Jenjang",
        store=True,
        related='kelas_id.jenjang',
    )

    tahunajaran_id = fields.Many2one(
        comodel_name="cdn.ref_tahunajaran", string="Tahun Ajaran", readonly=False, store=True)
    kelas_id = fields.Many2one('cdn.ruang_kelas', string='Kelas',
                               domain="[('tahunajaran_id','=',tahunajaran_id), ('aktif_tidak','=','aktif'), ('status','=','konfirm')]")
    partner_ids = fields.Many2many(
        'cdn.siswa', 'kenaikan_santri_rel', 'kenaikan_id', 'santri_id', 'Santri')

    tingkat_id = fields.Many2one(
        'cdn.tingkat', string="Tingkat", store=True, readonly=False)

    walikelas_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Wali Kelas",
        domain="[('jns_pegawai_ids.code', 'in', ['guru'])]"
    )

    status = fields.Selection(
        selection=[('naik', 'Naik Kelas'), ('tidak_naik', 'Tidak Naik'),
                   ('lulus', 'Lulus'), ('tidak_lulus', 'Tidak Lulus'), ],
        string="Status",
    )

    # Field baru untuk menampilkan kelas selanjutnya
    next_class = fields.Many2one(
        comodel_name='cdn.master_kelas',
        string='Kelas Selanjutnya',
        compute='_compute_next_class',
        store=True,
        help="Kelas selanjutnya berdasarkan tingkat, nama kelas, dan jurusan"
    )

    # Field untuk menampilkan hasil proses
    message_result = fields.Text(string="Hasil Proses", readonly=True)

    angkatan_id = fields.Many2one(
        related="kelas_id.angkatan_id", string="Angkatan", readoly=True)

    partner_lines = fields.One2many(
        'cdn.kenaikan_kelas.line', 'kenaikan_id', string='Santri')

    filtered_santri_ids = fields.Many2many(
        'cdn.siswa',
        'kenaikan_filtered_santri_rel',
        'kenaikan_id',
        'santri_id',
        string='Santri',
        domain="[('ruang_kelas_id', '=', kelas_id)]",
        help="Hanya menampilkan santri yang berada di kelas yang dipilih"
    )

    # Tambahkan field ini setelah field tahunajaran_id
    next_tahunajaran_id = fields.Many2one(
        comodel_name="cdn.ref_tahunajaran",
        string="Tahun Ajaran Berikutnya",
        compute='_compute_next_tahunajaran',
        store=True,
        readonly=True,
        help="Tahun ajaran berikutnya yang akan digunakan untuk kenaikan kelas"
    )

    # Tambahkan field untuk menampilkan nama tahun ajaran berikutnya dalam format text
    next_tahunajaran_name = fields.Char(
        string="Tahun Ajaran Berikutnya",
        compute='_compute_next_tahunajaran',
        store=True,
        readonly=True,
        help="Nama tahun ajaran berikutnya"
    )

    @api.onchange('kelas_id')
    def _onchange_kelas_id(self):
        """Auto-fill tingkat_id, walikelas_id, status, partner_ids, dan partner_lines berdasarkan kelas"""
        # RESET SEMUA FIELD TERLEBIH DAHULU
        self._reset_kelas_related_fields()

        if self.kelas_id:
            # Ambil data kelas
            kelas = self.kelas_id

            # Set tingkat_id - coba beberapa kemungkinan nama field
            if hasattr(kelas, 'tingkat_id') and kelas.tingkat_id:
                self.tingkat_id = kelas.tingkat_id.id
            elif hasattr(kelas, 'tingkat') and kelas.tingkat:
                self.tingkat_id = kelas.tingkat.id

            # Set walikelas_id
            if hasattr(kelas, 'walikelas_id') and kelas.walikelas_id:
                self.walikelas_id = kelas.walikelas_id.id

            # Set status otomatis berdasarkan tingkat (pastikan method ini ada)
            if hasattr(self, '_set_status_by_tingkat'):
                self._set_status_by_tingkat(kelas)

            # Cari siswa yang berada di kelas yang dipilih
            santri = self.env['cdn.siswa'].search(
                [('ruang_kelas_id', '=', self.kelas_id.id)])

            # Set semua field santri jika ada data
            if santri:
                santri.write({'centang': True})
                self.partner_ids = [(6, 0, santri.ids)]
                # self.filtered_santri_ids = [(6, 0, santri.ids)]

                # Buat partner_lines baru
                lines = []
                for s in santri:
                    lines.append((0, 0, {
                        'siswa_id': s.id,
                        'next_class_id': self.next_class.id if self.next_class else False,
                    }))
                self.partner_lines = lines

            # Trigger compute untuk next_class jika perlu
            self._compute_next_class()

    # Tambahkan method compute untuk menghitung tahun ajaran berikutnya

    @api.depends('tahunajaran_id')
    def _compute_next_tahunajaran(self):
        """
        Compute tahun ajaran berikutnya berdasarkan tahun ajaran saat ini
        Jika tidak ada di database, akan membuat preview berdasarkan logic pembuatan tahun ajaran baru
        """
        for record in self:
            if not record.tahunajaran_id:
                record.next_tahunajaran_id = False
                record.next_tahunajaran_name = ""
                continue

            try:
                # Ekstrak tahun dari nama tahun ajaran saat ini
                current_year = int(record.tahunajaran_id.name.split('/')[0])
                next_year = current_year + 1
                next_ta_name = f"{next_year}/{next_year+1}"

                # Cari tahun ajaran berikutnya yang sudah ada
                existing_next_ta = self.env['cdn.ref_tahunajaran'].search([
                    ('name', '=', next_ta_name)
                ], limit=1)

                if existing_next_ta:
                    # Jika sudah ada, gunakan yang sudah ada
                    record.next_tahunajaran_id = existing_next_ta.id
                    record.next_tahunajaran_name = existing_next_ta.name
                else:
                    # Jika belum ada, tampilkan preview nama tahun ajaran yang akan dibuat
                    record.next_tahunajaran_id = False
                    record.next_tahunajaran_name = next_ta_name

            except (ValueError, IndexError) as e:
                # Jika format tahun ajaran tidak sesuai
                _logger.warning(
                    f"Format tahun ajaran tidak valid untuk record {record.id}: {e}")
                record.next_tahunajaran_id = False
                record.next_tahunajaran_name = "Format tahun ajaran tidak valid"
            except Exception as e:
                _logger.error(
                    f"Error computing next tahun ajaran for record {record.id}: {e}")
                record.next_tahunajaran_id = False
                record.next_tahunajaran_name = "Error menghitung tahun ajaran berikutnya"

    # Method untuk mendapatkan atau membuat tahun ajaran berikutnya
    def get_or_create_next_tahunajaran(self):
        """
        Method untuk mendapatkan tahun ajaran berikutnya
        Jika belum ada, akan membuatnya menggunakan fungsi _create_next_tahun_ajaran

        Returns:
            cdn.ref_tahunajaran: Record tahun ajaran berikutnya
        """
        self.ensure_one()

        if not self.tahunajaran_id:
            raise UserError("Tahun ajaran saat ini belum dipilih")

        # Cek apakah sudah ada tahun ajaran berikutnya
        if self.next_tahunajaran_id:
            return self.next_tahunajaran_id

        # Jika belum ada, buat tahun ajaran baru
        try:
            next_ta = self._create_next_tahun_ajaran(self.tahunajaran_id)

            # Update field computed untuk refresh tampilan
            self._compute_next_tahunajaran()

            return next_ta

        except Exception as e:
            _logger.error(f"Gagal membuat tahun ajaran berikutnya: {str(e)}")
            raise UserError(f"Gagal membuat tahun ajaran berikutnya: {str(e)}")

    # Method untuk refresh data tahun ajaran berikutnya (opsional, untuk button)
    def action_refresh_next_tahunajaran(self):
        """
        Action untuk merefresh data tahun ajaran berikutnya
        Berguna jika ada perubahan data tahun ajaran
        """
        self._compute_next_tahunajaran()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def _create_next_tahun_ajaran(self, current_ta):
        """
        Fungsi untuk membuat tahun ajaran berikutnya jika belum ada
        Disesuaikan dengan sistem pendidikan di Indonesia (Juli-Juni)

        Args:
            current_ta: Tahun ajaran saat ini

        Returns:
            cdn.ref_tahunajaran: Tahun ajaran baru yang dibuat
        """
        try:
            _logger.info(
                f"Mencoba membuat tahun ajaran baru setelah {current_ta.name}")

            # Ekstrak tahun dari nama tahun ajaran saat ini
            current_year = int(current_ta.name.split('/')[0])
            next_year = current_year + 1
            next_ta_name = f"{next_year}/{next_year+1}"

            _logger.info(
                f"Tahun yang diekstrak: {current_year}, Tahun berikutnya: {next_year}")
            _logger.info(f"Nama tahun ajaran baru: {next_ta_name}")

            # Tentukan tanggal mulai dan akhir sesuai sistem pendidikan Indonesia
            start_date = datetime(next_year, 7, 1).date()
            end_date = datetime(next_year + 1, 6, 30).date()

            _logger.info(
                f"Tanggal mulai: {start_date}, Tanggal akhir: {end_date}")

            # Cek apakah sudah ada tahun ajaran dengan nama tersebut
            existing_ta_by_name = self.env['cdn.ref_tahunajaran'].search([
                ('name', '=', next_ta_name)
            ], limit=1)

            if existing_ta_by_name:
                _logger.info(
                    f"Tahun ajaran dengan nama {next_ta_name} sudah ada")
                return existing_ta_by_name

            # Cek apakah sudah ada tahun ajaran dengan rentang waktu tersebut
            existing_ta = self.env['cdn.ref_tahunajaran'].search([
                ('start_date', '=', start_date),
                ('end_date', '=', end_date)
            ], limit=1)

            if existing_ta:
                _logger.info(
                    f"Tahun ajaran dengan rentang {start_date} - {end_date} sudah ada")
                return existing_ta

            _logger.info(f"Membuat tahun ajaran baru: {next_ta_name}")

            # Ambil data tambahan dari tahun ajaran saat ini
            create_vals = {
                'name': next_ta_name,
                'start_date': start_date,
                'end_date': end_date,
                'keterangan': f"Dibuat otomatis dari proses kenaikan kelas pada {fields.Date.today()}"
            }

            # Copy field yang ada dari tahun ajaran saat ini
            if hasattr(current_ta, 'term_structure') and current_ta.term_structure:
                create_vals['term_structure'] = current_ta.term_structure

            if hasattr(current_ta, 'company_id') and current_ta.company_id:
                create_vals['company_id'] = current_ta.company_id.id

            # Buat tahun ajaran baru dengan sudo untuk memastikan hak akses
            new_ta = self.env['cdn.ref_tahunajaran'].sudo().create(create_vals)

            # Verifikasi record telah dibuat
            if not new_ta:
                raise UserError(
                    f"Gagal membuat tahun ajaran baru {next_ta_name}")

            # Commit transaksi untuk memastikan data tersimpan
            self.env.cr.commit()

            # Buat termin akademik dan periode tagihan jika method tersedia
            if hasattr(new_ta, 'term_create'):
                try:
                    new_ta.term_create()
                except Exception as e:
                    _logger.warning(
                        f"Gagal membuat termin untuk tahun ajaran {next_ta_name}: {str(e)}")

            _logger.info(
                f"Tahun ajaran baru berhasil dibuat: {new_ta.name} ({new_ta.start_date} - {new_ta.end_date})")

            return new_ta
        except Exception as e:
            _logger.error(f"Gagal membuat tahun ajaran baru: {str(e)}")
            raise UserError(f"Gagal membuat tahun ajaran baru: {str(e)}")

    @api.depends('kelas_id', 'kelas_id.nama_kelas', 'kelas_id.jurusan_id', 'kelas_id.tingkat', 'status')
    def _compute_next_class(self):
        """Compute kelas selanjutnya berdasarkan kelas yang dipilih dan status"""
        for record in self:
            if not record.kelas_id:
                record.next_class = False
                continue

            # Jika status adalah tidak_naik atau tidak_lulus,
            # maka next_class tetap menampilkan kelas yang sama
            if record.status in ['tidak_naik', 'tidak_lulus']:
                # Cari master kelas yang sesuai dengan kelas_id saat ini
                current_class = record.kelas_id
                current_tingkat = current_class.tingkat
                current_nama_kelas = current_class.nama_kelas
                current_jurusan = current_class.jurusan_id

                if not current_tingkat:
                    record.next_class = False
                    continue

                # Cari master kelas yang cocok dengan kelas saat ini
                domain = [('tingkat', '=', current_tingkat.id)]

                # Filter berdasarkan nama kelas jika ada
                if current_nama_kelas:
                    domain.append(('nama_kelas', '=', current_nama_kelas))

                # Filter berdasarkan jurusan jika ada
                if current_jurusan:
                    domain.append(('jurusan_id', '=', current_jurusan.id))

                # Cari master kelas yang cocok dengan kelas saat ini
                current_master_class = self.env['cdn.master_kelas'].search(
                    domain, limit=1)

                # Jika tidak ditemukan dengan nama_kelas, coba tanpa nama_kelas (hanya tingkat dan jurusan)
                if not current_master_class and current_jurusan:
                    domain_alternative = [
                        ('tingkat', '=', current_tingkat.id),
                        ('jurusan_id', '=', current_jurusan.id)
                    ]
                    current_master_class = self.env['cdn.master_kelas'].search(
                        domain_alternative, limit=1)

                # Jika masih tidak ditemukan, coba hanya berdasarkan tingkat
                if not current_master_class:
                    domain_simple = [('tingkat', '=', current_tingkat.id)]
                    current_master_class = self.env['cdn.master_kelas'].search(
                        domain_simple, limit=1)

                record.next_class = current_master_class.id if current_master_class else False
                continue

                # Untuk status naik, cari kelas selanjutnya
            # Ambil data kelas saat ini
            current_class = record.kelas_id
            current_tingkat = current_class.tingkat
            current_nama_kelas = current_class.nama_kelas
            current_jurusan = current_class.jurusan_id

            if not current_tingkat:
                record.next_class = False
                continue

            # Cari tingkat selanjutnya
            next_tingkat = record._get_next_tingkat(current_tingkat)
            if not next_tingkat:
                record.next_class = False
                continue

            # Cari master kelas yang cocok dengan kriteria:
            # 1. Tingkat = tingkat selanjutnya
            # 2. nama_kelas = sama dengan kelas saat ini (jika ada)
            # 3. jurusan_id = sama dengan kelas saat ini (jika ada)
            domain = [('tingkat', '=', next_tingkat.id)]

            # Filter berdasarkan nama kelas jika ada
            if current_nama_kelas:
                domain.append(('nama_kelas', '=', current_nama_kelas))

            # Filter berdasarkan jurusan jika ada
            if current_jurusan:
                domain.append(('jurusan_id', '=', current_jurusan.id))

            # Cari master kelas yang cocok
            next_master_class = self.env['cdn.master_kelas'].search(
                domain, limit=1)

            # Jika tidak ditemukan dengan nama_kelas, coba tanpa nama_kelas (hanya tingkat dan jurusan)
            if not next_master_class and current_jurusan:
                domain_alternative = [
                    ('tingkat', '=', next_tingkat.id),
                    ('jurusan_id', '=', current_jurusan.id)
                ]
                next_master_class = self.env['cdn.master_kelas'].search(
                    domain_alternative, limit=1)

            # Jika masih tidak ditemukan, coba hanya berdasarkan tingkat
            if not next_master_class:
                domain_simple = [('tingkat', '=', next_tingkat.id)]
                next_master_class = self.env['cdn.master_kelas'].search(
                    domain_simple, limit=1)

            record.next_class = next_master_class.id if next_master_class else False

    def _get_next_tingkat(self, current_tingkat):
        """Mendapatkan tingkat selanjutnya berdasarkan tingkat saat ini"""
        if not current_tingkat:
            return False

        # Coba ambil urutan tingkat
        current_order = None

        # Cara 1: Berdasarkan field urutan
        if hasattr(current_tingkat, 'urutan') and current_tingkat.urutan:
            current_order = current_tingkat.urutan

        # Cara 2: Berdasarkan field level
        elif hasattr(current_tingkat, 'level') and current_tingkat.level:
            current_order = current_tingkat.level

        # Cara 3: Extract dari nama tingkat
        elif hasattr(current_tingkat, 'name') and current_tingkat.name:
            current_order = self._extract_tingkat_number(current_tingkat.name)

        if not current_order:
            return False

        next_order = current_order + 1

        # Cari tingkat dengan urutan selanjutnya
        # Prioritas pencarian: urutan -> level -> nama
        next_tingkat = None

        # Cari berdasarkan urutan
        if hasattr(current_tingkat, 'urutan'):
            next_tingkat = self.env['cdn.tingkat'].search(
                [('urutan', '=', next_order)], limit=1)

        # Jika tidak ditemukan, cari berdasarkan level
        if not next_tingkat and hasattr(current_tingkat, 'level'):
            next_tingkat = self.env['cdn.tingkat'].search(
                [('level', '=', next_order)], limit=1)

        # Jika tidak ditemukan, cari berdasarkan nama
        if not next_tingkat:
            # Cari berdasarkan angka
            next_tingkat = self.env['cdn.tingkat'].search([
                '|', '|',
                ('name', 'ilike', str(next_order)),
                ('name', 'ilike', self._number_to_roman(next_order)),
                ('name', 'ilike', self._number_to_word(next_order))
            ], limit=1)

        return next_tingkat

    def _extract_tingkat_number(self, tingkat_name):
        """Extract nomor tingkat dari nama tingkat"""
        if not tingkat_name:
            return None

        tingkat_name = str(tingkat_name).upper()

        # Dictionary untuk konversi angka romawi ke angka
        roman_to_num = {
            'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6,
            'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12,
            'XIII': 13, 'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17, 'XVIII': 18
        }

        # Dictionary untuk konversi kata ke angka
        word_to_num = {
            'SATU': 1, 'DUA': 2, 'TIGA': 3, 'EMPAT': 4, 'LIMA': 5, 'ENAM': 6,
            'TUJUH': 7, 'DELAPAN': 8, 'SEMBILAN': 9, 'SEPULUH': 10,
            'SEBELAS': 11, 'DUABELAS': 12, 'TIGABELAS': 13, 'EMPATBELAS': 14
        }

        # Cari angka langsung
        import re
        numbers = re.findall(r'\d+', tingkat_name)
        if numbers:
            return int(numbers[0])

        # Cari angka romawi
        for roman, num in roman_to_num.items():
            if roman in tingkat_name:
                return num

        # Cari kata
        for word, num in word_to_num.items():
            if word in tingkat_name:
                return num

        return None

    def _number_to_roman(self, num):
        """Convert number to roman numeral"""
        roman_numerals = {
            1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI',
            7: 'VII', 8: 'VIII', 9: 'IX', 10: 'X', 11: 'XI', 12: 'XII',
            13: 'XIII', 14: 'XIV', 15: 'XV', 16: 'XVI', 17: 'XVII', 18: 'XVIII'
        }
        return roman_numerals.get(num, str(num))

    def _number_to_word(self, num):
        """Convert number to Indonesian word"""
        word_numerals = {
            1: 'SATU', 2: 'DUA', 3: 'TIGA', 4: 'EMPAT', 5: 'LIMA', 6: 'ENAM',
            7: 'TUJUH', 8: 'DELAPAN', 9: 'SEMBILAN', 10: 'SEPULUH',
            11: 'SEBELAS', 12: 'DUABELAS', 13: 'TIGABELAS', 14: 'EMPATBELAS'
        }
        return word_numerals.get(num, str(num))

    def _reset_kelas_related_fields(self):
        """Helper method untuk reset semua field yang terkait dengan kelas"""
        self.tingkat_id = False
        self.walikelas_id = False
        self.status = False
        self.partner_ids = [(5, 0, 0)]  # kosongkan M2M
        self.partner_lines = [(5, 0, 0)]  # kosongkan One2many
        self.filtered_santri_ids = [(5, 0, 0)]  # kosongkan filtered santri
        self.next_class = False
        self.message_result = False

    def _set_status_by_tingkat(self, kelas):
        """Set status berdasarkan tingkat kelas"""
        if not kelas.tingkat:
            self.status = 'naik'  # Default jika tidak ada tingkat
            return

        # Ambil data tingkat
        tingkat = kelas.tingkat

        # Cek apakah tingkat 12 (kelas SMA/MA/SMK)
        is_tingkat_12 = self._is_tingkat_12(tingkat)
        if is_tingkat_12:
            # Untuk tingkat 12, cek apakah ada kelas selanjutnya
            has_next_class = self._check_next_class_exists(kelas)
            if has_next_class:
                self.status = 'naik'
            else:
                self.status = 'lulus'
            return

        # Cara 1: Cek berdasarkan nama tingkat (jika ada field nama/name)
        if hasattr(tingkat, 'name'):
            tingkat_name = str(tingkat.name).lower()
            # Cek apakah tingkat 6 atau 9
            if '6' in tingkat_name or 'vi' in tingkat_name or 'enam' in tingkat_name:
                self.status = 'lulus'
            elif '9' in tingkat_name or 'ix' in tingkat_name or 'sembilan' in tingkat_name:
                self.status = 'lulus'
            else:
                self.status = 'naik'

        # Cara 2: Cek berdasarkan field urutan (jika ada)
        elif hasattr(tingkat, 'urutan'):
            if tingkat.urutan in [6, 9]:
                self.status = 'lulus'
            else:
                self.status = 'naik'

        # Cara 3: Cek berdasarkan field level (jika ada)
        elif hasattr(tingkat, 'level'):
            if tingkat.level in [6, 9]:
                self.status = 'lulus'
            else:
                self.status = 'naik'

        # Cara 4: Cek berdasarkan jenjang dan tingkat
        elif hasattr(kelas, 'jenjang'):
            # Untuk SD/MI: tingkat 6 = lulus
            if kelas.jenjang in ['sd'] and hasattr(tingkat, 'name'):
                if '6' in str(tingkat.name) or 'vi' in str(tingkat.name).lower():
                    self.status = 'lulus'
                else:
                    self.status = 'naik'
            # Untuk SMP/MTS: tingkat 9 = lulus
            elif kelas.jenjang in ['smp'] and hasattr(tingkat, 'name'):
                if '9' in str(tingkat.name) or 'ix' in str(tingkat.name).lower():
                    self.status = 'lulus'
                else:
                    self.status = 'naik'
            else:
                self.status = 'naik'

        else:
            # Default jika tidak bisa menentukan
            self.status = 'naik'

    @api.onchange('tingkat_id')
    def _onchange_tingkat_id(self):
        """Update status ketika tingkat_id diubah manual"""
        if self.tingkat_id and self.kelas_id:
            # Buat object kelas sementara untuk menggunakan method yang sama
            class MockKelas:
                def __init__(self, tingkat, jenjang):
                    self.tingkat = tingkat
                    self.jenjang = jenjang

            mock_kelas = MockKelas(self.tingkat_id, self.jenjang)
            self._set_status_by_tingkat(mock_kelas)

    def _is_tingkat_12(self, tingkat):
        """Cek apakah tingkat adalah kelas 12"""
        if hasattr(tingkat, 'name'):
            tingkat_name = str(tingkat.name).lower()
            if '12' in tingkat_name or 'xii' in tingkat_name or 'duabelas' in tingkat_name:
                return True

        if hasattr(tingkat, 'urutan'):
            if tingkat.urutan == 12:
                return True

        if hasattr(tingkat, 'level'):
            if tingkat.level == 12:
                return True

        return False

    def _check_next_class_exists(self, kelas):
        """Cek apakah ada kelas selanjutnya setelah tingkat 12 di cdn.master_kelas"""
        try:
            # Ambil tingkat saat ini
            current_tingkat = kelas.tingkat
            if not current_tingkat:
                return False

            # Ambil jenjang dan jurusan dari kelas saat ini
            current_jenjang = kelas.jenjang if hasattr(
                kelas, 'jenjang') else None
            current_jurusan = None

            # Coba ambil jurusan dari kelas saat ini
            if hasattr(kelas, 'jurusan_id'):
                current_jurusan = kelas.jurusan_id
            elif hasattr(kelas, 'name') and hasattr(kelas.name, 'jurusan_id'):
                current_jurusan = kelas.name.jurusan_id

            # Tentukan tingkat selanjutnya yang mungkin (13, 14, dst)
            next_tingkat_numbers = [13, 14, 15, 16]  # Bisa disesuaikan

            # Cari tingkat selanjutnya di cdn.tingkat
            next_tingkat_ids = []
            for num in next_tingkat_numbers:
                tingkat_domain = []

                # Cari berdasarkan nama
                tingkat_records = self.env['cdn.tingkat'].search([
                    '|', '|', '|',
                    ('name', 'ilike', str(num)),
                    ('name', 'ilike', self._number_to_roman(num)),
                    ('urutan', '=', num),
                    ('level', '=', num)
                ])

                if tingkat_records:
                    next_tingkat_ids.extend(tingkat_records.ids)

            if not next_tingkat_ids:
                return False

            # Cari di cdn.master_kelas apakah ada kelas dengan tingkat selanjutnya
            master_kelas_domain = [('tingkat', 'in', next_tingkat_ids)]

            # Filter berdasarkan jenjang jika ada
            if current_jenjang:
                master_kelas_domain.append(('jenjang', '=', current_jenjang))

            # Filter berdasarkan jurusan jika ada
            if current_jurusan:
                master_kelas_domain.append(
                    ('jurusan_id', '=', current_jurusan.id))

            next_classes = self.env['cdn.master_kelas'].search(
                master_kelas_domain, limit=1)

            return bool(next_classes)

        except Exception as e:
            # Jika terjadi error, default ke False (lulus)
            _logger.warning(f"Error checking next class: {str(e)}")
            return False

    def action_proses_kenaikan_kelas(self):
        """
        Aksi untuk memproses kenaikan kelas dengan memperbarui data siswa
        berdasarkan status centang masing-masing siswa
        """
        _logger.info(
            f"Memulai proses kenaikan kelas untuk tahun ajaran: {self.tahunajaran_id.name}")

        if not self.partner_ids:
            raise UserError("Belum ada santri yang dipilih!")

        if not self.kelas_id:
            raise UserError("Belum ada kelas yang dipilih!")

        self.ensure_one()
        message = ""
        count_siswa_naik = 0
        count_siswa_tidak_naik = 0
        count_siswa_lulus = 0
        count_siswa_tidak_lulus = 0

        # Mendapatkan tahun ajaran berikutnya
        try:
            current_year = int(self.tahunajaran_id.name.split('/')[0])
            next_year = current_year + 1
            next_ta_name = f"{next_year}/{next_year+1}"

            _logger.info(
                f"Current year: {current_year}, Next year: {next_year}")
            _logger.info(f"Mencari tahun ajaran dengan nama: {next_ta_name}")

            # Cari tahun ajaran berikutnya
            tahun_ajaran_berikutnya = self.env['cdn.ref_tahunajaran'].search([
                ('name', '=', next_ta_name)
            ], limit=1)

            _logger.info(
                f"Hasil pencarian tahun ajaran berikutnya: {tahun_ajaran_berikutnya.name if tahun_ajaran_berikutnya else 'Tidak ditemukan'}")

        except (ValueError, IndexError) as e:
            _logger.error(f"Format tahun ajaran tidak valid: {str(e)}")
            raise UserError(
                f"Format tahun ajaran tidak valid: {self.tahunajaran_id.name}. Format yang diharapkan: YYYY/YYYY")

        # Jika tahun ajaran berikutnya tidak ditemukan, buat yang baru
        if not tahun_ajaran_berikutnya:
            message += f"Tahun ajaran {next_ta_name} tidak ditemukan. Mencoba membuat tahun ajaran baru...\n"
            try:
                tahun_ajaran_berikutnya = self._create_next_tahun_ajaran(
                    self.tahunajaran_id)
                message += f"Berhasil membuat tahun ajaran baru: {tahun_ajaran_berikutnya.name}\n\n"
            except Exception as e:
                message += f"Gagal membuat tahun ajaran baru: {str(e)}\n\n"
                raise UserError(f"Gagal membuat tahun ajaran baru: {str(e)}")

        # Pisahkan santri berdasarkan status centang
        santri_naik = self.partner_ids.filtered(lambda s: s.centang == True)
        santri_tidak_naik = self.partner_ids.filtered(
            lambda s: s.centang == False)

        _logger.info(f"Santri naik kelas: {len(santri_naik)}")
        _logger.info(f"Santri tidak naik kelas: {len(santri_tidak_naik)}")

        try:
            # ===== PROSES BERDASARKAN STATUS (NAIK ATAU LULUS) =====
            if self.status == 'naik':
                message += f"\n=== PROSES KENAIKAN KELAS ===\n"

                if not self.next_class:
                    raise UserError(
                        "Kelas selanjutnya tidak ditentukan untuk proses kenaikan kelas!")

                # Proses santri yang naik kelas (dicentang)
                if santri_naik:
                    for siswa in santri_naik:
                        siswa.write({
                            'tahunajaran_id': tahun_ajaran_berikutnya.id,
                        })
                        count_siswa_naik += 1

                    message += f"✓ {len(santri_naik)} siswa naik kelas ke {self.next_class.name}\n"

                # Proses santri yang tidak naik kelas (tidak dicentang)
                if santri_tidak_naik:
                    # PENTING: Hapus siswa yang tidak naik dari kelas saat ini DULU
                    self.kelas_id.write({
                        'siswa_ids': [(3, siswa.id) for siswa in santri_tidak_naik]
                    })
                    message += f"✓ Menghapus {len(santri_tidak_naik)} siswa dari kelas {self.kelas_id.nama_kelas}\n"

                    # Cari atau buat kelas untuk siswa yang tinggal kelas
                    kelas_tinggal_kelas = self._find_or_create_tinggal_kelas(
                        tahun_ajaran_berikutnya)

                    if kelas_tinggal_kelas:
                        # Masukkan siswa ke kelas tinggal kelas
                        kelas_tinggal_kelas.write({
                            'siswa_ids': [(4, siswa.id) for siswa in santri_tidak_naik]
                        })

                        # Update data siswa yang tidak naik
                        for siswa in santri_tidak_naik:
                            siswa.write({
                                'ruang_kelas_id': kelas_tinggal_kelas.id,
                                'tahunajaran_id': tahun_ajaran_berikutnya.id,
                            })
                            count_siswa_tidak_naik += 1

                        message += f"✓ {len(santri_tidak_naik)} siswa dipindahkan ke kelas tinggal kelas: {kelas_tinggal_kelas.nama_kelas}\n"
                    else:
                        # Jika gagal membuat kelas tinggal kelas, siswa tetap dihapus dari kelas
                        for siswa in santri_tidak_naik:
                            siswa.write({
                                'ruang_kelas_id': False,  # Hapus dari kelas
                                'tahunajaran_id': tahun_ajaran_berikutnya.id,
                            })
                            count_siswa_tidak_naik += 1

                        message += f"⚠ {len(santri_tidak_naik)} siswa dihapus dari kelas (tidak dapat membuat kelas tinggal kelas)\n"

                # Update kelas utama ke tingkat selanjutnya (hanya untuk siswa yang naik)
                if santri_naik:
                    self.kelas_id.write({
                        'name': self.next_class.id,
                        'tahunajaran_id': tahun_ajaran_berikutnya.id,
                        # 'walikelas_id': self.wali_kelas_selanjutnya.id,
                    })
                    message += f"✓ Kelas {self.kelas_id.nama_kelas} diupdate ke {self.next_class.name}\n"

            elif self.status == 'lulus':
                message += f"\n=== PROSES KELULUSAN ===\n"

                # Proses santri yang lulus (dicentang)
                if santri_naik:

                    self.kelas_id.write({
                        'aktif_tidak': 'tidak',
                        # 'tahunajaran_id': tahun_ajaran_berikutnya.id,
                    })

                    for siswa in santri_naik:
                        siswa.write({
                            # 'tahun_lulus': tahun_ajaran_berikutnya.name,
                        })
                        count_siswa_lulus += 1

                    message += f"✓ {len(santri_naik)} siswa lulus\n"

                # Proses santri yang tidak lulus (tidak dicentang)
                if santri_tidak_naik:
                    # Hapus siswa yang tidak lulus dari kelas
                    self.kelas_id.write({
                        'siswa_ids': [(3, siswa.id) for siswa in santri_tidak_naik]
                    })

                    kelas_tinggal_kelas = self._find_or_create_tinggal_kelas(
                        tahun_ajaran_berikutnya)

                    if kelas_tinggal_kelas:
                        # Masukkan siswa ke kelas tinggal kelas
                        kelas_tinggal_kelas.write({
                            'siswa_ids': [(4, siswa.id) for siswa in santri_tidak_naik]
                        })

                        # Update data siswa yang tidak naik
                        for siswa in santri_tidak_naik:
                            siswa.write({
                                'ruang_kelas_id': kelas_tinggal_kelas.id,
                                'tahunajaran_id': tahun_ajaran_berikutnya.id,
                            })
                            count_siswa_tidak_naik += 1

                        message += f"✓ {len(santri_tidak_naik)} siswa dipindahkan ke kelas tinggal kelas: {kelas_tinggal_kelas.nama_kelas}\n"
                    else:
                        # Jika gagal membuat kelas tinggal kelas, siswa tetap dihapus dari kelas
                        for siswa in santri_tidak_naik:
                            siswa.write({
                                'ruang_kelas_id': False,  # Hapus dari kelas
                                'tahunajaran_id': tahun_ajaran_berikutnya.id,
                            })
                            count_siswa_tidak_naik += 1

                        message += f"⚠ {len(santri_tidak_naik)} siswa dihapus dari kelas (tidak dapat membuat kelas tinggal kelas)\n"

                # Jika semua siswa lulus, nonaktifkan kelas
                if len(santri_naik) == len(self.partner_ids):
                    self.kelas_id.write({
                        'aktif_tidak': 'tidak',
                    })
                    message += f"✓ Kelas {self.kelas_id.nama_kelas} dinonaktifkan (semua siswal lulus)\n"

        except Exception as e:
            error_msg = f"ERROR memproses kenaikan kelas: {str(e)}"
            message += f"❌ {error_msg}\n"
            _logger.error(error_msg)
            raise UserError(error_msg)

        # Commit perubahan
        try:
            self.env.cr.commit()
            _logger.info("Perubahan berhasil di-commit ke database")
        except Exception as e:
            _logger.error(f"Gagal melakukan commit perubahan: {str(e)}")
            raise UserError(f"Gagal menyimpan perubahan: {str(e)}")

        # Buat summary hasil proses
        result_message = f"✅ Proses Kenaikan Kelas berhasil dilakukan!\n\n"
        result_message += f"📊 Ringkasan Hasil:\n"
        result_message += f"- Siswa naik kelas: {count_siswa_naik}\n"
        result_message += f"- Siswa tidak naik: {count_siswa_tidak_naik}\n"
        result_message += f"- Siswa lulus: {count_siswa_lulus}\n"
        result_message += f"- Siswa tidak lulus: {count_siswa_tidak_lulus}\n"
        result_message += f"Total siswa diproses: {len(self.partner_ids)}\n\n"
        result_message += f"📝 Detail Proses:\n{message}"

        _logger.info(
            f"Proses kenaikan kelas selesai dengan hasil: {result_message}")

        # Update field message_result
        self.message_result = result_message

        # Reset field centang semua siswa
        self.partner_ids.write({'centang': False})

        # Kirim notification via bus
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {
                'title': 'Sukses!',
                # 'message': f'Proses kenaikan kelas berhasil! Total {len(self.partner_ids)} siswa diproses.',
                'message': 'Proses kenaikan kelas berhasil!',
                'type': 'success',
                'sticky': False,
                'timeout': 150000,
            }
        )

        # Buat wizard baru dan return
        new_wizard = self.create({})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Kenaikan Kelas',
            'res_model': 'cdn.kenaikan_kelas',
            'view_mode': 'form',
            'res_id': new_wizard.id,
            'target': 'new',
        }

    def _find_or_create_tinggal_kelas(self, tahun_ajaran_berikutnya):
        """
        Helper method untuk mencari atau membuat kelas tinggal kelas
        """
        try:
            # Cari kelas dengan tingkat, nama kelas, dan jurusan yang sama untuk tahun ajaran berikutnya
            domain = [
                ('name.tingkat', '=', self.kelas_id.name.tingkat.id),
                ('name.nama_kelas', '=', self.kelas_id.name.nama_kelas),
                ('tahunajaran_id', '=', tahun_ajaran_berikutnya.id),
                ('aktif_tidak', '=', 'aktif'),
            ]

            # Tambahkan filter jurusan jika ada
            if self.kelas_id.name.jurusan_id:
                domain.append(
                    ('name.jurusan_id', '=', self.kelas_id.name.jurusan_id.id))

            kelas_tinggal_kelas = self.env['cdn.ruang_kelas'].search(
                domain, limit=1)

            if not kelas_tinggal_kelas:
                # Buat kelas baru untuk tinggal kelas
                kelas_tinggal_kelas = self.env['cdn.ruang_kelas'].create({
                    'name': self.kelas_id.name.id,  # Nama kelas sama dengan kelas asal
                    'tahunajaran_id': tahun_ajaran_berikutnya.id,
                    'walikelas_id': self.walikelas_id.id,
                    'status': 'konfirm',
                    'aktif_tidak': 'aktif',
                    'keterangan': 'Kelas baru untuk santri yang tiddak naik/lulus.',
                })
                _logger.info(
                    f"Berhasil membuat kelas tinggal kelas baru: {kelas_tinggal_kelas.nama_kelas}")

            return kelas_tinggal_kelas

        except Exception as e:
            _logger.error(
                f"Gagal mencari/membuat kelas tinggal kelas: {str(e)}")
            return False
