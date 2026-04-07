# from addons.pesantren_kesantrian.models.mutabaah_harian import Mutabaah_harian
from odoo import api, fields, models
from datetime import date, datetime, timedelta

class Prestasi_siswa(models.Model):
    _name = 'cdn.prestasi_siswa'
    _description = 'prestasi Siswa'
    _order = 'tgl_prestasi desc'

    #get domain
    
    name             = fields.Char(string='No. Referensi', readonly=True)
    tgl_prestasi     = fields.Date(string='Tgl Prestasi', default=lambda self: date.today(), required=True)
    siswa_id         = fields.Many2one(comodel_name='cdn.siswa', string='Santri', ondelete='cascade' ,required=True)
    tingkat_prestasi = fields.Selection(string='Tingkat Prestasi', selection=[('Internal', 'Internal'), ('Lokal', 'Lokal'), ('Kecamatan', 'Kecamatan'),('Kota', 'Kota'), ('Provinsi', 'Provinsi'), ('Nasional', 'Nasional'), ('Internasional', 'Internasional')], required=True)
    jns_prestasi_id  = fields.Many2one(comodel_name='cdn.jns_prestasi', string='Jenis Prestasi', required=True)
    #juara = fields.Selection(string='Juara', selection=[('1', 'Ke-1'), ('2', 'Ke-2'), ('3', 'Ke-3'), ('harapan 1','Harapan 1'), ('harapan 2', 'Harapan 2'), ('harapan 3', 'Harapan 3')], required=True)
    joara            = fields.Char(string='Juara', required=True)
    keterangan       = fields.Text(string='Keterangan')
    foto             = fields.Binary(string='Foto')
    
    MutabaahHarian   = fields.Many2one(comodel_name='cdn.mutabaah_harian')

    barcode          = fields.Char(string="Kartu Santri",readonly=False)

    kelas_id    = fields.Many2one('cdn.ruang_kelas', string='Kelas', related='siswa_id.ruang_kelas_id', readonly=True, store=True)
    kamar_id    = fields.Many2one('cdn.kamar_santri', string='Kamar', related='siswa_id.kamar_id', readonly=True)
    halaqoh_id  = fields.Many2one('cdn.halaqoh', string='Halaqoh', related='siswa_id.halaqoh_id', readonly=True)
    musyrif_id  = fields.Many2one('hr.employee', string='Musyrif', related='siswa_id.musyrif_id', readonly=True)
    company_id  = fields.Many2one('res.company', string='Lembaga', default=lambda self: self.env.company)
    
    @api.model
    def create(self, vals):
        vals["name"] = self.env["ir.sequence"].next_by_code("cdn.prestasi_siswa")
        return super(Prestasi_siswa, self).create(vals)

    @api.onchange('siswa_id')
    def _onchange_siswa_id(self):
        if self.siswa_id:
            self.barcode = self.siswa_id.barcode_santri
        else:
            self.barcode = False

    @api.onchange('barcode')
    def _onchange_barcode(self):
        if self.barcode:
            siswa = self.env['cdn.siswa'].search([('barcode_santri', '=', self.barcode)], limit=1)
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
            self.barcode = False
            self.siswa_id = False

    # @api.onchange('juara')
    # def _onchange_juara(self):
    #     MutabaahHarian = 

    # @api.model
    # def _search(self, domain, offset=0, limit=None, order=None, count=False):
    #     # Handle empty domain
    #     if not domain:
    #         return super(Prestasi_siswa, self)._search(domain, offset=offset, limit=limit, order=order, )
        
    #     # Periksa domain untuk mencegah error
    #     if isinstance(domain, list):

    #         new_domain = []
    #         for item in domain:
    #             if isinstance(item, (list, tuple)) and len(item) == 3:
    #                 field, operator, value = item
                    
    #                 # Handle selection fields untuk pencarian label dan bukan hanya value
    #                 if field == 'tingkat_prestasi' and operator == 'ilike' and value:
    #                     if 'internal' in value.lower():
    #                         new_domain.append(('tingkat_prestasi', '=', 'Internal'))
    #                     elif 'lokal' in value.lower():
    #                         new_domain.append(('tingkat_prestasi', '=', 'Lokal'))
    #                     elif 'kecamatan' in value.lower():
    #                         new_domain.append(('tingkat_prestasi', '=', 'Kecamatan'))
    #                     elif 'kota' in value.lower():
    #                         new_domain.append(('tingkat_prestasi', '=', 'Kota'))
    #                     elif 'provinsi' in value.lower():
    #                         new_domain.append(('tingkat_prestasi', '=', 'Provinsi'))
    #                     elif 'nasional' in value.lower():
    #                         new_domain.append(('tingkat_prestasi', '=', 'Nasional'))
    #                     elif 'internasional' in value.lower():
    #                         new_domain.append(('tingkat_prestasi', '=', 'Internasional'))
    #                     else: 
    #                         new_domain.append(item)
                            
    #                 # Handle tanggal
    #                 elif field in ['tgl_prestasi'] and operator == 'ilike' and value:
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
    #         or_count = 0
            
    #         for item in domain:
    #             if isinstance(item, (list, tuple)) and len(item) == 3:
    #                 valid_domain.append(item)
    #             elif isinstance(item, str) and item in ['&', '|', '!']:
    #                 if item == '|':
    #                     or_count += 1
    #                 valid_domain.append(item)
            
    #         # Ensure proper balancing for OR operators
    #         if or_count > 0 and len(valid_domain) < (or_count * 2 + 1):
    #             # Domain is invalid, fall back to simple name search
    #             return super(Prestasi_siswa, self)._search([('name', 'ilike', '')], offset=offset, limit=limit, order=order, )
            
    #         domain = valid_domain if valid_domain else domain
        
    #     return super(Prestasi_siswa, self)._search(domain, offset=offset, limit=limit, order=order, )
    
    

    
    
    
