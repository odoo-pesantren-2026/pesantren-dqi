from odoo import api, fields, models
from odoo.exceptions import UserError


class BiayaPendidikan(models.Model):
    _name           = 'ubig.pendidikan'
    _description    = 'Tabel Data Biaya Pendidikan'

    name            = fields.Char(string='Jenjang Pendidikan', required=True)
    jenjang         = fields.Selection(selection=[('paud','PAUD'),('tk','TK'),('sdmi','SD / MI'),('smpmts','SMP / MTS'),('smama','SMA / MA'),('smk','SMK'), ('nonformal', 'Nonformal')], string='Jenjang', required=True)

    # name            = fields.Many2one("cdn.pengaturan_jejang",)
    
    # jenjang         = fields.Many2one(related="name.name", string="Jenjang Pendidikan")
    # jenjang_id      = fields.Selection(related='name.jenjang', string='Jenjang')

    biaya           = fields.Integer(string='Biaya Pendidikan')
    keterangan      = fields.Char(string='Keterangan', help='')
    status          = fields.Selection(string='Status', selection=[('draft', 'Draft'), ('konfirm', 'Terkonfirmasi')], default="draft")
    biaya_ids       = fields.One2many('ubig.biaya_daftarulang',inverse_name="biaya_id", string='Rincian Biaya')
    rincian_ids     = fields.One2many('ubig.rincian_biaya',inverse_name="biaya_id", string='Rincian Biaya')
    
    @api.model
    def create(self, vals):
        if self.search([('name', '=', vals.get('name')), ('jenjang', '=', vals.get('jenjang'))]):
            raise UserError('Nama jenjang dengan kombinasi yang sama sudah ada!')
        return super(BiayaPendidikan, self).create(vals)

    def write(self, vals):
        name = vals.get('name', self.name)
        jenjang = vals.get('jenjang', self.jenjang)
        domain = [('name', '=', name), ('jenjang', '=', jenjang), ('id', '!=', self.id)]
        if self.search(domain):
            raise UserError('Nama jenjang dengan kombinasi yang sama sudah ada!')
        return super(BiayaPendidikan, self).write(vals)

    # Action untuk mengubah status ke 'konfirm'
    def konfirmasi(self):
        for record in self:
            record.status = 'konfirm'

    # Action untuk mengubah status ke 'draft'
    def draft(self):
        for record in self:
            record.status = 'draft'



# from odoo import api, fields, models


# class BiayaPendidikan(models.Model):
#     _name           = 'ubig.pendidikan'
#     _description    = 'Tabel Data Biaya Pendidikan'

#     # name            = fields.Char(string='Jenjang Pendidikan', required=True)
#     # jenjang         = fields.Selection(selection=[('paud','PAUD'),('tk','TK'),('sdmi','SD / MI'),('smpmts','SMP / MTS'),('smama','SMA / MA'),('smk','SMK')], string='Jenjang', required=True)

#     # Perbaikan typo pada nama model: cdn.pengaturan_jejang -> cdn.pengaturan_jenjang
#     jenjang            = fields.Many2one("cdn.pengaturan_jenjang", string="Jenjang Pendidikan", required=True)
    
#     # fields.Many2one tidak bisa related ke fields.Char, maka dihapus
#     # jenjang         = fields.Many2one(related="name.name", string="Jenjang Pendidikan")
    
#     # Mengambil nilai jenjang dari model cdn.pengaturan_jenjang
#     jenjang_id      = fields.Selection(related='name.jenjang', string='Jenjang', store=True)

#     biaya           = fields.Integer(string='Biaya Pendidikan')
#     keterangan      = fields.Char(string='Keterangan', help='')
#     status          = fields.Selection(string='Status', selection=[('draft', 'Draft'), ('konfirm', 'Terkonfirmasi')], default="draft")
#     biaya_ids       = fields.One2many('ubig.biaya_daftarulang',inverse_name="biaya_id", string='Rincian Biaya')
#     rincian_ids     = fields.One2many('ubig.rincian_biaya',inverse_name="biaya_id", string='Rincian Biaya')
 
#     # Fungsi ini diperlukan agar name menampilkan nilai yang benar saat ditampilkan di form/list view
#     @api.depends('name')
#     def name_get(self):
#         result = []
#         for record in self:
#             if record.name:
#                 display_name = record.name.name
#                 result.append((record.id, display_name))
#             else:
#                 result.append((record.id, ""))
#         return result

#     # Action untuk mengubah status ke 'konfirm'
#     def konfirmasi(self):
#         for record in self:
#             record.status = 'konfirm'

#     # Action untuk mengubah status ke 'draft'
#     def draft(self):
#         for record in self:
#             record.status = 'draft'