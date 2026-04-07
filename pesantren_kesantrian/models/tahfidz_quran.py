# from odoo import api, fields, models
# from datetime import date, datetime

# class TahfidzQuran(models.Model):
#     _name = 'cdn.tahfidz_quran'

#     name            = fields.Char(string='No Referensi', readonly=True)
#     tanggal         = fields.Date(string='Tgl Tahfidz', required=True)
#     siswa_id        = fields.Many2one('cdn.siswa', string='Santri', required=True)
#     last_tahfidz    = fields.Many2one('cdn.tahfidz_quran', string='Tahfidz Terakhir', related='siswa_id.last_tahfidz', readonly=True, store=True)
#     halaqoh_id      = fields.Many2one('cdn.halaqoh', string='Halaqoh', readonly=True)
#     ustadz_id       = fields.Many2one('hr.employee', string='Ustadz')
#     sesi_tahfidz_id = fields.Many2one('cdn.sesi_tahfidz', string='Sesi', required=True)
#     surah_id        = fields.Many2one('cdn.surah', string='Surah', states={'done': [('readonly', True)]})
#     number          = fields.Integer(string='Surah Ke', related='surah_id.number', readonly=True)
#     jml_ayat        = fields.Integer(string='Jumlah Ayat', related='surah_id.jml_ayat', readonly=True, store=True)
 
#     ayat_awal       = fields.Many2one('cdn.ayat', string='Ayat Awal', states={'done': [('readonly', True)]})
#     ayat_awal_name  = fields.Integer(string='Ayat Awal', related='ayat_awal.name', readonly=True)
#     ayat_akhir      = fields.Many2one('cdn.ayat', string='Ayat Akhir', states={'done': [('readonly', True)]})
#     jml_baris       = fields.Integer(string='Jumlah Baris', states={'done': [('readonly', True)]})
#     nilai_id        = fields.Many2one('cdn.nilai_tahfidz', string='Nilai', states={'done': [('readonly', True)]})
#     keterangan      = fields.Char(string='Keterangan', states={'done': [('readonly', True)]})
#     state           = fields.Selection([('draft', 'Draft'),('done', 'Done')], default='draft', string='Status')
#     penanggung_jawab_id = fields.Many2one('hr.employee', string='Penanggung Jawab', related='halaqoh_id.penanggung_jawab_id', readonly=True, store=True)
    
#     nilai = fields.Integer(string='Nilai', default=75, states={'done': [('readonly', True)]})

#     predikat = fields.Selection(
#         string='Predikat',
#         selection=[('a+', 'A+'), ('a', 'A'), ('b+', 'B+'), ('b', 'B'), ('c+', 'C+'), ('c', 'C')],
#         compute='_compute_predikat',
#         store=True,
#         states={'done': [('readonly', True)]}
#     )

#     @api.depends('nilai')
#     def _compute_predikat(self):
#         for record in self:
#             if record.nilai >= 90:
#                 record.predikat = 'a+'
#             elif 80 <= record.nilai < 90:
#                 record.predikat = 'a'
#             elif 70 <= record.nilai < 80:
#                 record.predikat = 'b+'
#             elif 60 <= record.nilai < 70:
#                 record.predikat = 'b'
#             elif record.nilai < 60:
#                 record.predikat = 'c+'
#             else:
#                 record.predikat = 'c'

#     def get_last_tahfidz(self):
#         last_tahfidz = self.env['cdn.tahfidz_quran'].search([
#             ('siswa_id', '=', self.siswa_id.id),
#             ('state', '=', 'done'),
#         ], order='id desc', limit=1)
#         return last_tahfidz

#     def action_confirm(self):
#         self.state = 'done'
#         self.siswa_id.last_tahfidz = self.get_last_tahfidz()
#     def action_draft(self):
#         self.state = 'draft'
#         self.siswa_id.last_tahfidz = self.get_last_tahfidz()

#     @api.onchange('ayat_awal')
#     def _onchange_ayat_awal(self):
#         return {
#             'value': {'ayat_akhir': False}
#         }


#     @api.model
#     def create(self, vals):
#         vals['name'] = self.env['ir.sequence'].next_by_code('cdn.tahfidz_quran')
#         return super(TahfidzQuran, self).create(vals)
        
#     def name_get(self):
#         result = []
#         for record in self:
#             if record.state == 'draft':
#                 result.append((record.id, record.name))
#             else:
#                 result.append((
#                     record.id, 
#                     '{} # {} - {} # {} baris # {}'.format(
#                         record.surah_id.display_name, 
#                         record.ayat_awal.name, 
#                         record.ayat_akhir.name, 
#                         record.jml_baris, 
#                         record.nilai_id.name
#                     )
#                 ))
#         return result


    # @api.model
    # def _search(self, domain, offset=0, limit=None, order=None, count=False):
    #     # Handle empty domain
    #     if not domain:
    #         return super(TahfidzQuran, self)._search(domain, offset=offset, limit=limit, order=order, )
        
    #     # Periksa domain untuk mencegah error
    #     if isinstance(domain, list):
            
    #         new_domain = []
    #         for item in domain:
    #             if isinstance(item, (list, tuple)) and len(item) == 3:
    #                 field, operator, value = item
                    
    #                 if field == 'state' and operator == 'ilike' and value:
    #                     if 'draft' in value.lower() or 'Draft' in value.lower() or 'draf' in value.lower():
    #                         new_domain.append(('state', '=', 'draft'))
    #                     elif 'Done' in value.lower() or 'selesai' in value.lower() or 'done' in value.lower():
    #                         new_domain.append(('state', '=', 'done'))
    #                     else: 
    #                         new_domain.append(item)
                    
    #                 # Handle selection fields untuk pencarian label dan bukan hanya value
    #                 elif field == 'predikat' and operator == 'ilike' and value:
    #                     if 'a+' in value.lower() :
    #                         new_domain.append(('predikat', '=', 'a+'))
    #                     elif 'a' in value.lower() :
    #                         new_domain.append(('predikat', '=', 'a'))
    #                     elif 'b+' in value.lower() :
    #                         new_domain.append(('predikat', '=', 'b+'))
    #                     elif 'b' in value.lower() :
    #                         new_domain.append(('predikat', '=', 'b'))
    #                     elif 'c+' in value.lower() :
    #                         new_domain.append(('predikat', '=', 'c+'))
    #                     elif 'c' in value.lower() :
    #                         new_domain.append(('predikat', '=', 'c'))
    #                     else: 
    #                         new_domain.append(item)
                            
    #                 # Handle tanggal
    #                 elif field in ['tanggal'] and operator == 'ilike' and value:
    #                     try:
    #                         # Coba parsing format tanggal yang umum
    #                         date_formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d.%m.%Y']
    #                         parsed_date = None
                            
    #                         for fmt in date_formats:
    #                             try:
    #                                 parsed_date = datetime.strptime(value, fmt)
    #                                 break
    #                             except ValueError:
    #                                 continue
                            
    #                         if parsed_date:
    #                             start_date = datetime.combine(parsed_date.date(), datetime.min.time())
    #                             end_date = datetime.combine(parsed_date.date(), datetime.max.time())
    #                             new_domain.append('&')
    #                             new_domain.append((field, '>=', start_date))
    #                             new_domain.append((field, '<=', end_date))
    #                         else:
    #                             # Jika tidak bisa diparsing sebagai tanggal, gunakan pencarian biasa
    #                             new_domain.append(item)
    #                     except Exception:
    #                         # Fallback ke pencarian biasa jika ada error
    #                         new_domain.append(item)
                    
    #                 else:
    #                     new_domain.append(item)
    #             else:
    #                 new_domain.append(item)
            
    #         domain = new_domain
            
    #         # Filter hanya domain valid (list/tuple dengan panjang 3)
    #         valid_domain = []
    #         has_barcode_search = False
    #         barcode_value = None
            
    #         for item in domain:
    #             if isinstance(item, (list, tuple)) and len(item) == 3:
    #                 field, operator, value = item
    #                 if field == 'absen_ids' and operator == 'ilike' and value:
    #                     # Cek jika memenuhi format barcode
    #                     if value.isdigit() and len(value) >= 8:  # Asumsi panjang barcode
    #                         has_barcode_search = True
    #                         barcode_value = value
    #                         # Tetap tambahkan domain asli untuk jaga-jaga
    #                         valid_domain.append(item)
    #                     else:
    #                         valid_domain.append(item)
    #                 else:
    #                     valid_domain.append(item)
    #             elif isinstance(item, str) and item in ['&', '|', '!']:
    #                 valid_domain.append(item)
            
    #         # Jika ditemukan format barcode, tambahkan domain untuk pencarian barcode
    #         if has_barcode_search:
    #             # Cari ID siswa berdasarkan barcode
    #             siswa_ids = self.env['cdn.siswa'].search([('barcode_santri', '=', barcode_value)]).ids
    #             if siswa_ids:
    #                 # Cari absen line yang memiliki siswa tersebut
    #                 absen_line_ids = self.env['cdn.absen_tahfidz_quran_line'].search([('siswa_id', 'in', siswa_ids)]).mapped('absen_id').ids
    #                 if absen_line_ids:
    #                     # Tambahkan domain untuk filter berdasarkan ID absen
    #                     return super(TahfidzQuran, self)._search([('id', 'in', absen_line_ids)], offset=offset, limit=limit, order=order)
            
    #         domain = valid_domain if valid_domain else domain
            
    #     return super(TahfidzQuran, self)._search(domain, offset=offset, limit=limit, order=order, )
    
from odoo import api, fields, models
from datetime import date, datetime

class TahfidzQuran(models.Model):
    _name = 'cdn.tahfidz_quran'
 
    name            = fields.Char(string='No Referensi', readonly=True)
    tanggal         = fields.Date(string='Tgl Tahfidz', required=True)
    siswa_id        = fields.Many2one('cdn.siswa', string='Santri', required=True , ondelete='cascade')
    last_tahfidz    = fields.Many2one('cdn.tahfidz_quran', string='Tahfidz Terakhir', related='siswa_id.last_tahfidz', readonly=True, store=True)
    # last_tahfidz    = fields.Related('siswa_id.tahfidz_terakhir_id', string='Tahfidz Terakhir', readonly=True, store=True)
    halaqoh_id      = fields.Many2one('cdn.halaqoh', string='Halaqoh', readonly=True)
    ustadz_id       = fields.Many2one('hr.employee', string='Ustadz')
    sesi_tahfidz_id = fields.Many2one('cdn.sesi_tahfidz', string='Sesi', required=True)
    surah_id        = fields.Many2one('cdn.surah', string='Surah', states={'done': [('readonly', True)]}, ondelete='cascade')
    number          = fields.Integer(string='Surah Ke', related='surah_id.number', readonly=True)
    jml_ayat        = fields.Integer(string='Jumlah Ayat', related='surah_id.jml_ayat', readonly=True, store=True)
 
    ayat_awal       = fields.Many2one('cdn.ayat', string='Ayat Awal', states={'done': [('readonly', True)]}, ondelete='cascade')
    ayat_awal_name  = fields.Integer(string='Ayat Awal', related='ayat_awal.name', readonly=True)
    ayat_akhir      = fields.Many2one('cdn.ayat', string='Ayat Akhir', states={'done': [('readonly', True)]}, ondelete='cascade')
    jml_baris       = fields.Integer(string='Jumlah Maqrok', states={'done': [('readonly', True)]})
    nilai_id        = fields.Many2one('cdn.nilai_tahfidz', string='Nilai', states={'done': [('readonly', True)]})
    keterangan      = fields.Char(string='Keterangan', states={'done': [('readonly', True)]})
    state           = fields.Selection([('draft', 'Draft'),('done', 'Done')], default='draft', string='Status')
    penanggung_jawab_id = fields.Many2one('hr.employee', string='Penanggung Jawab', related='halaqoh_id.penanggung_jawab_id', readonly=True, store=True)
    
    nilai = fields.Integer(string='Nilai', default=75, states={'done': [('readonly', True)]})

    predikat = fields.Selection(
        string='Predikat',
        selection=[('a+', 'MUMTAZ'), ('a', 'JAYYID JIDDAN'), ('b+', 'JAYYID'), ('b', 'MAQBUL'), ('c+', 'DHAIF'), ('c', 'DHAIF JIDDAN')],
        compute='_compute_predikat',
        store=True,
        states={'done': [('readonly', True)]}
    )
    
    barcode          = fields.Char(string="Kartu Santri", related="siswa_id.barcode_santri", readonly=True)

    kelas_id    = fields.Many2one('cdn.ruang_kelas', string='Kelas', related='siswa_id.ruang_kelas_id', readonly=True, store=True)
    kamar_id    = fields.Many2one('cdn.kamar_santri', string='Kamar', related='siswa_id.kamar_id', readonly=True)
    halaqoh_id  = fields.Many2one('cdn.halaqoh', string='Halaqoh', related='siswa_id.halaqoh_id', readonly=True)
    musyrif_id  = fields.Many2one('hr.employee', string='Musyrif', related='siswa_id.musyrif_id', readonly=True)

    @api.onchange('siswa_id')
    def _onchange_siswa_id(self):
        if self.siswa_id:
            self.barcode = self.siswa_id.barcode_santri
        else:
            self.barcode = False

    # @api.onchange('barcode')
    # def _onchange_barcode(self):
    #     if self.barcode:
    #         siswa = self.env['cdn.siswa'].search([('barcode_santri', '=', self.barcode)], limit=1)
    #         if siswa:
    #             self.siswa_id = siswa.id
    #         else:
    #             self.siswa_id = False
    #             barcode_sementara = self.barcode
    #             self.barcode = False
    #             return {
    #                 'warning': {
    #                     'title': "Perhatian !",
    #                     'message': f"Data Santri dengan Kartu Santri {barcode_sementara} tidak ditemukan."
    #                 }
    #             }
    #     else:
    #         self.barcode = False
    #         self.siswa_id = False



    @api.depends('nilai')
    def _compute_predikat(self):
        for record in self:
            if record.nilai >= 90:
                record.predikat = 'a+'
            elif 80 <= record.nilai < 90:
                record.predikat = 'a'
            elif 70 <= record.nilai < 80:
                record.predikat = 'b+'
            elif 60 <= record.nilai < 70:
                record.predikat = 'b'
            elif record.nilai < 60:
                record.predikat = 'c+'
            else:
                record.predikat = 'c'

    def get_last_tahfidz(self):
        last_tahfidz = self.env['cdn.tahfidz_quran'].search([
            ('siswa_id', '=', self.siswa_id.id),
            ('state', '=', 'done'),
        ], order='id desc', limit=1)
        return last_tahfidz

    def action_confirm(self):
        self.state = 'done'
        self.siswa_id.last_tahfidz = self.get_last_tahfidz()
    def action_draft(self):
        self.state = 'draft'
        self.siswa_id.last_tahfidz = self.get_last_tahfidz()

    @api.onchange('ayat_awal')
    def _onchange_ayat_awal(self):
        return {
            'value': {'ayat_akhir': False}
        }




    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('cdn.tahfidz_quran')
        
        # return super(TahfidzQuran, self).create(vals)

        # If siswa_id is provided but barcode is not, get the barcode from the siswa record
        if vals.get('siswa_id') and not vals.get('barcode'):
            siswa = self.env['cdn.siswa'].browse(vals.get('siswa_id'))
            if siswa and siswa.barcode_santri:
                vals['barcode'] = siswa.barcode_santri
                
        return super(TahfidzQuran, self).create(vals)
        
    def write(self, vals):
        # If siswa_id is changed, update barcode accordingly
        if vals.get('siswa_id') and 'barcode' not in vals:
            siswa = self.env['cdn.siswa'].browse(vals.get('siswa_id'))
            if siswa and siswa.barcode_santri:
                vals['barcode'] = siswa.barcode_santri
                
        return super(TahfidzQuran, self).write(vals)


    def name_get(self):
        result = []
        for record in self:
            if record.state == 'draft':
                result.append((record.id, record.name))
            else:
                result.append((
                    record.id, 
                    '{} # {} - {} # {} baris # {}'.format(
                        record.surah_id.display_name, 
                        record.ayat_awal.name, 
                        record.ayat_akhir.name, 
                        record.jml_baris, 
                        record.nilai_id.name
                    )
                ))
        return result


    # @api.model
    # def _search(self, domain, offset=0, limit=None, order=None, count=False):
    #     # Handle empty domain
    #     if not domain:
    #         return super(TahfidzQuran, self)._search(domain, offset=offset, limit=limit, order=order, )
        
    #     # Periksa domain untuk mencegah error
    #     if isinstance(domain, list):
            
    #         new_domain = []
    #         for item in domain:
    #             if isinstance(item, (list, tuple)) and len(item) == 3:
    #                 field, operator, value = item
                    
    #                 if field == 'state' and operator == 'ilike' and value:
    #                     if 'draft' in value.lower() or 'Draft' in value.lower() or 'draf' in value.lower():
    #                         new_domain.append(('state', '=', 'draft'))
    #                     elif 'Done' in value.lower() or 'selesai' in value.lower() or 'done' in value.lower():
    #                         new_domain.append(('state', '=', 'done'))
    #                     else: 
    #                         new_domain.append(item)
                    
    #                 # Handle selection fields untuk pencarian label dan bukan hanya value
    #                 elif field == 'predikat' and operator == 'ilike' and value:
    #                     if 'a+' in value.lower() :
    #                         new_domain.append(('predikat', '=', 'a+'))
    #                     elif 'a' in value.lower() :
    #                         new_domain.append(('predikat', '=', 'a'))
    #                     elif 'b+' in value.lower() :
    #                         new_domain.append(('predikat', '=', 'b+'))
    #                     elif 'b' in value.lower() :
    #                         new_domain.append(('predikat', '=', 'b'))
    #                     elif 'c+' in value.lower() :
    #                         new_domain.append(('predikat', '=', 'c+'))
    #                     elif 'c' in value.lower() :
    #                         new_domain.append(('predikat', '=', 'c'))
    #                     else: 
    #                         new_domain.append(item)
                            
    #                 # Handle tanggal
    #                 elif field in ['tanggal'] and operator == 'ilike' and value:
    #                     try:
    #                         # Coba parsing format tanggal yang umum
    #                         date_formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d.%m.%Y']
    #                         parsed_date = None
                            
    #                         for fmt in date_formats:
    #                             try:
    #                                 parsed_date = datetime.strptime(value, fmt)
    #                                 break
    #                             except ValueError:
    #                                 continue
                            
    #                         if parsed_date:
    #                             start_date = datetime.combine(parsed_date.date(), datetime.min.time())
    #                             end_date = datetime.combine(parsed_date.date(), datetime.max.time())
    #                             new_domain.append('&')
    #                             new_domain.append((field, '>=', start_date))
    #                             new_domain.append((field, '<=', end_date))
    #                         else:
    #                             # Jika tidak bisa diparsing sebagai tanggal, gunakan pencarian biasa
    #                             new_domain.append(item)
    #                     except Exception:
    #                         # Fallback ke pencarian biasa jika ada error
    #                         new_domain.append(item)
                    
    #                 else:
    #                     new_domain.append(item)
    #             else:
    #                 new_domain.append(item)
            
    #         domain = new_domain
            
    #         # Filter hanya domain valid (list/tuple dengan panjang 3)
    #         valid_domain = []
    #         has_barcode_search = False
    #         barcode_value = None
            
    #         for item in domain:
    #             if isinstance(item, (list, tuple)) and len(item) == 3:
    #                 field, operator, value = item
    #                 if field == 'absen_ids' and operator == 'ilike' and value:
    #                     # Cek jika memenuhi format barcode
    #                     if value.isdigit() and len(value) >= 8:  # Asumsi panjang barcode
    #                         has_barcode_search = True
    #                         barcode_value = value
    #                         # Tetap tambahkan domain asli untuk jaga-jaga
    #                         valid_domain.append(item)
    #                     else:
    #                         valid_domain.append(item)
    #                 else:
    #                     valid_domain.append(item)
    #             elif isinstance(item, str) and item in ['&', '|', '!']:
    #                 valid_domain.append(item)
            
    #         # Jika ditemukan format barcode, tambahkan domain untuk pencarian barcode
    #         if has_barcode_search:
    #             # Cari ID siswa berdasarkan barcode
    #             siswa_ids = self.env['cdn.siswa'].search([('barcode_santri', '=', barcode_value)]).ids
    #             if siswa_ids:
    #                 # Cari absen line yang memiliki siswa tersebut
    #                 absen_line_ids = self.env['cdn.absen_tahfidz_quran_line'].search([('siswa_id', 'in', siswa_ids)]).mapped('absen_id').ids
    #                 if absen_line_ids:
    #                     # Tambahkan domain untuk filter berdasarkan ID absen
    #                     return super(TahfidzQuran, self)._search([('id', 'in', absen_line_ids)], offset=offset, limit=limit, order=order)
            
    #         domain = valid_domain if valid_domain else domain
            
    #     return super(TahfidzQuran, self)._search(domain, offset=offset, limit=limit, order=order, )