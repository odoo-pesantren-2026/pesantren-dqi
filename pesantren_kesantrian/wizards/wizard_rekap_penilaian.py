from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
import csv
import io

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class WizardRekapPenilaian(models.TransientModel):
    _name = 'cdn.wizard_rekap_penilaian'
    _description = 'Wizard Rekap Penilaian Santri'

    siswa_id = fields.Many2one('cdn.siswa', string='Nama Siswa', required=True)
    barcode = fields.Char(string='Kartu Santri')
    tgl_awal = fields.Date(string='Tanggal Awal',
                           required=True, default=fields.Date.context_today)
    tgl_akhir = fields.Date(string='Tanggal Akhir',
                            required=True, default=fields.Date.context_today)

    # Inline results
    rekap_line_ids = fields.One2many(
        'cdn.wizard_rekap_penilaian_line', 'wizard_id', string='Detail Penilaian', readonly=True)

    # Export fields
    data_file = fields.Binary(string='File')
    file_name = fields.Char(string='Nama File')

    @api.onchange('barcode')
    def _onchange_barcode(self):
        if self.barcode:
            siswa = self.env['cdn.siswa'].search(
                [('barcode_santri', '=', self.barcode)], limit=1)
            if siswa:
                self.siswa_id = siswa.id
            else:
                self.siswa_id = False
                barcode_sementara = self.barcode
                self.barcode = False
                return {
                    'warning': {
                        'title': "Perhatian !",
                        'message': f"Data Santri dengan Kartu Santri {barcode_sementara} tidak ditemukan."
                    }
                }
        else:
            self.siswa_id = False

    @api.onchange('siswa_id', 'tgl_awal', 'tgl_akhir')
    def _onchange_rekap_params(self):
        if self.siswa_id:
            self.barcode = self.siswa_id.barcode_santri
        else:
            self.barcode = False

        if not (self.siswa_id and self.tgl_awal and self.tgl_akhir):
            self.rekap_line_ids = [(5, 0, 0)]
            return

        if self.tgl_awal > self.tgl_akhir:
            return

        lines = []

        # Penilaian Quran records
        penilaian_records = self.env['cdn.penilaian_quran'].search([
            ('siswa_id', '=', self.siswa_id.id),
            ('tanggal', '>=', self.tgl_awal),
            ('tanggal', '<=', self.tgl_akhir),
            ('state', '=', 'done')
        ], order='tanggal asc')

        for rec in penilaian_records:
            # 1. Tahfidz (Lines)
            for line in rec.tahfidz_line_ids:
                materi = f"{line.surah_id.name} {line.ayat_awal.name}-{line.ayat_akhir.name}"
                lines.append((0, 0, {
                    'tanggal': rec.tanggal,
                    'kegiatan': 'Tahfidz',
                    'materi': materi,
                    'nilai': str(line.nilai_hafalan),
                    'predikat': line.predikat or '-',
                    'keterangan': line.keterangan or '-'
                }))

            # 2. Tahsin
            if rec.buku_harian_id:
                materi_tahsin = f"{rec.buku_harian_id.name} - {rec.jilid_harian_id.name} Hal {rec.halaman_harian}"
                lines.append((0, 0, {
                    'tanggal': rec.tanggal,
                    'kegiatan': 'Tahsin',
                    'materi': materi_tahsin,
                    'nilai': str(rec.nilai_tahsin_harian),
                    'predikat': rec.predikat_tahsin_harian or '-',
                    'keterangan': rec.catatan_harian or '-'
                }))

            # 3. Murajaah
            if rec.juz_murajaah:
                materi_murajaah = f"Juz {rec.juz_murajaah} {rec.surah_murajaah_id.name} Hal {rec.halaman_murajaah}"
                lines.append((0, 0, {
                    'tanggal': rec.tanggal,
                    'kegiatan': 'Murajaah',
                    'materi': materi_murajaah,
                    'nilai': '-',
                    'predikat': '-',
                    'keterangan': rec.catatan_murajaah_harian or '-'
                }))

        self.rekap_line_ids = [(5, 0, 0)] + lines

    def action_export_csv(self):
        self._onchange_rekap_params()
        if not self.rekap_line_ids:
            raise UserError(_("Tidak ada data untuk diekspor."))

        output = io.StringIO()
        writer = csv.writer(output, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)

        # Header
        writer.writerow(['No', 'Tanggal', 'Kegiatan', 'Materi',
                        'Nilai', 'Predikat', 'Keterangan'])

        # Data
        for i, line in enumerate(self.rekap_line_ids, 1):
            writer.writerow([
                i,
                line.tanggal,
                line.kegiatan,
                line.materi,
                line.nilai,
                line.predikat,
                line.keterangan
            ])

        csv_data = output.getvalue().encode('utf-8')
        file_name = f"Rekap_Penilaian_{self.siswa_id.name}_{self.tgl_awal}_sd_{self.tgl_akhir}.csv"

        self.write({
            'data_file': base64.b64encode(csv_data),
            'file_name': file_name
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model={self._name}&id={self.id}&field=data_file&download=true&filename={self.file_name}',
            'target': 'self',
        }

    def action_export_xlsx(self):
        if not xlsxwriter:
            raise UserError(
                _("Modul 'xlsxwriter' tidak ditemukan. Silakan hubungi administrator."))

        self._onchange_rekap_params()
        if not self.rekap_line_ids:
            raise UserError(_("Tidak ada data untuk diekspor."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Rekap Penilaian')

        # Formats
        header_format = workbook.add_format(
            {'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
        title_format = workbook.add_format({'bold': True, 'font_size': 14})
        date_format = workbook.add_format(
            {'num_format': 'dd/mm/yyyy', 'border': 1})
        border_format = workbook.add_format({'border': 1})

        # Title
        sheet.write(0, 0, 'Rekap Penilaian Santri (Halaqoh)', title_format)
        sheet.write(1, 0, f'Nama Siswa: {self.siswa_id.name}')
        sheet.write(2, 0, f'NIS: {self.siswa_id.nis}')
        sheet.write(3, 0, f'Periode: {self.tgl_awal} s/d {self.tgl_akhir}')

        # Table Header
        headers = ['No', 'Tanggal', 'Kegiatan',
                   'Materi', 'Nilai', 'Predikat', 'Keterangan']
        for col, header in enumerate(headers):
            sheet.write(5, col, header, header_format)

        # Table Data
        row = 6
        for i, line in enumerate(self.rekap_line_ids, 1):
            sheet.write(row, 0, i, border_format)
            sheet.write(row, 1, line.tanggal, date_format)
            sheet.write(row, 2, line.kegiatan, border_format)
            sheet.write(row, 3, line.materi, border_format)
            sheet.write(row, 4, line.nilai, border_format)
            sheet.write(row, 5, line.predikat, border_format)
            sheet.write(row, 6, line.keterangan, border_format)
            row += 1

        workbook.close()
        output.seek(0)
        xlsx_data = output.read()

        file_name = f"Rekap_Penilaian_{self.siswa_id.name}_{self.tgl_awal}_sd_{self.tgl_akhir}.xlsx"

        self.write({
            'data_file': base64.b64encode(xlsx_data),
            'file_name': file_name
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model={self._name}&id={self.id}&field=data_file&download=true&filename={self.file_name}',
            'target': 'self',
        }


class WizardRekapPenilaianLine(models.TransientModel):
    _name = 'cdn.wizard_rekap_penilaian_line'
    _description = 'Line Rekap Penilaian Santri'

    wizard_id = fields.Many2one(
        'cdn.wizard_rekap_penilaian', string='Wizard', ondelete='cascade')
    tanggal = fields.Date(string='Tanggal')
    kegiatan = fields.Char(string='Kegiatan')
    materi = fields.Char(string='Materi')
    nilai = fields.Char(string='Nilai')
    predikat = fields.Char(string='Predikat')
    keterangan = fields.Char(string='Keterangan')
