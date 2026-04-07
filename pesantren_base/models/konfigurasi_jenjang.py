from odoo import fields, models, api


class Konfigurasi(models.Model):
    _name = 'cdn.pengaturan_jenjang'
    _description = 'ya hoooo'
    _order = 'create_date desc'

    name = fields.Char(string='Jenjang Pendidikan', required=True)
    keterangan = fields.Text(string='Keterangan', help='')
    status = fields.Selection(string='Status', selection=[(
        'draft', 'Draft'), ('konfirm', 'Terkonfirmasi')], default="draft")
    jenjang = fields.Selection(selection=[('paud', 'PAUD'), ('tk', 'TK/RA'), ('sd', 'SD/MI'), ('smp', 'SMP/MTS'), ('sma',
                               'SMA/MA/SMK'), ('nonformal', 'Non Formal'), ('rtq', 'Rumah Tahfidz Quran')], required=True,  string="Jenjang", help="")

    # Action untuk mengubah status ke 'konfirm'
    def konfirmasi(self):
        for record in self:
            record.status = 'konfirm'

    # Action untuk mengubah status ke 'draft'
    def draft(self):
        for record in self:
            record.status = 'draft'
