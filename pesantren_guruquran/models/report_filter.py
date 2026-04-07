from odoo import models, fields, api


class ReportFilterWizard(models.TransientModel):
    _name = 'report.filter.wizard'
    _description = 'Wizard untuk memfilter data berdasarkan bulan'

    start_month = fields.Integer(
        string='Bulan Mulai', required=True, default=5, help="Masukkan angka bulan awal (1=Januari, 12=Desember)")
    end_month = fields.Integer(string='Bulan Akhir', required=True, default=10, help="Masukkan angka bulan akhir (1=Januari, 12=Desember)")

    @api.constrains('start_month', 'end_month')
    def _check_month_range(self):
        for record in self:
            if not (1 <= record.start_month <= 12) or not (1 <= record.end_month <= 12):
                raise ValueError("Bulan harus di antara 1 hingga 12.")
            if record.start_month > record.end_month:
                raise ValueError(
                    "Bulan mulai tidak boleh lebih besar dari bulan akhir.")

    def action_print_report(self):
        """
        Fungsi ini memanggil action dari class inherit lain.
        """
        # Cari data dari model `cdn.siswa` berdasarkan filter bulan
        siswa_records = self.env['cdn.siswa'].search([
            ('bulan', '>=', self.start_month),
            ('bulan', '<=', self.end_month),
        ])

        # Panggil method `action_print_sertifikat` untuk setiap siswa yang ditemukan
        actions = []
        for siswa in siswa_records:
            action = siswa.action_print_sertifikat()
            if action:
                actions.append(action)

        # Pilihan: Return salah satu action atau logika pengolahan lainnya
        if actions:
            return actions[0]  # Contoh: Mengembalikan action pertama
        else:
            raise ValueError(
                "Tidak ada data siswa yang sesuai dengan filter bulan.")
