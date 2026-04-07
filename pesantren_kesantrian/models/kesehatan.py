from email.policy import default
from odoo import api, fields, models
from datetime import date, datetime, timedelta

class Kesehatan(models.Model):
    _name = 'cdn.kesehatan'
    _description = 'Model untuk Aktivitas Kesehatan'
    _order = 'name desc'
     
    # draft
    name = fields.Char(string='No Referensi', readonly=True)
    tgl_diperiksa = fields.Date(string='Tgl Diperiksa', default=date.today(), required=True)
    siswa_id = fields.Many2one(comodel_name='cdn.siswa', string='Santri',  ondelete='cascade' ,required=True)
    kelas_id = fields.Many2one(comodel_name='cdn.ruang_kelas', string='Kelas', readonly=True, related='siswa_id.ruang_kelas_id')
    keluhan = fields.Text(string='Keluhan', required=True)
    
    # periksa
    diperiksa_oleh = fields.Char(string='Diperiksa Oleh', readonly=False, states={'draft': [('readonly', True)]})
    diagnosa = fields.Text(string='Diagnosa', readonly=False, states={'draft': [('readonly', True)]})
    
    # pengobatan
    obat = fields.Text(string='Obat', readonly=False, states={'draft': [('readonly', True)]})
    catatan = fields.Text(string='Catatan', readonly=False, states={'draft': [('readonly', True)]})
    
    # rawat
    lokasi_rawat = fields.Selection(string='Lokasi Rawat', selection=[
        ('uks', 'UKS'),
        ('rumah', 'Pulang ke Rumah'),
        ('rumah_sakit', 'Rumah Sakit/Klinik')
    ], readonly=False, states={'draft': [('readonly', True)]})
    keterangan_rawat = fields.Char(string='Keterangan Rawat', readonly=False, states={'draft': [('readonly', True)]})
    
    # sembuh
    tgl_selesai = fields.Date(string='Tgl Selesai', readonly=False, states={'draft': [('readonly', True)]})
    
    state = fields.Selection(string='Kondisi', selection=[
        # ('draft', 'Draft'),
        ('periksa', 'Pemeriksaan'),
        ('pengobatan', 'Perawatan'),
        # ('rawat', 'Rawat'),
        ('sembuh', 'Sembuh'),
        # ('batal', 'Dibatalkan')
    ], default='periksa')
    
    kamar_id    = fields.Many2one('cdn.kamar_santri', string='Kamar', related='siswa_id.kamar_id', readonly=True)
    halaqoh_id  = fields.Many2one('cdn.halaqoh', string='Halaqoh', related='siswa_id.halaqoh_id', readonly=True)
    musyrif_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Musyrif',
        related='siswa_id.musyrif_id',
        readonly=True,
        store=True
    )

    barcode = fields.Char(string="Kartu Santri",readonly=True)
    
    company_id      = fields.Many2one('res.company', string='Lembaga', default=lambda self: self.env.company)

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
    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('cdn.kesehatan')
        return super(Kesehatan, self).create(vals)
    
    # def action_periksa(self):
    #     self.state = 'periksa'
    
    def action_pengobatan(self):
        self.state = 'pengobatan'
        
    # def action_batal(self):
    #     self.state = 'batal'
    
    # def action_rawat(self):
    #     self.state = 'rawat'
    
    def action_sembuh(self):
        self.tgl_selesai = date.today()
        self.state = 'sembuh'

    # @api.model
    # def _search(self, domain, offset=0, limit=None, order=None, count=False):
    #     # Handle empty domain
    #     if not domain:
    #         return super(Kesehatan, self)._search(domain, offset=offset, limit=limit, order=order, )
        
    #     # Periksa domain untuk mencegah error
    #     if isinstance(domain, list):

    #         new_domain = []
    #         for item in domain:
    #             if isinstance(item, (list, tuple)) and len(item) == 3:
    #                 field, operator, value = item
                    
    #                 # Handle selection fields untuk pencarian label dan bukan hanya value
    #                 if field == 'state' and operator == 'ilike' and value:
    #                     if 'draft' in value.lower():
    #                         new_domain.append(('state', '=', 'draft'))
    #                     elif 'periksa' in value.lower() or 'diperiksa' in value.lower():
    #                         new_domain.append(('state', '=', 'periksa'))
    #                     elif 'pengobatan' in value.lower() or 'obat' in value.lower():
    #                         new_domain.append(('state', '=', 'pengobatan'))
    #                     elif 'rawat' in value.lower() or 'dirawat' in value.lower():
    #                         new_domain.append(('state', '=', 'rawat'))
    #                     elif 'sembuh' in value.lower():
    #                         new_domain.append(('state', '=', 'sembuh'))
    #                     else: 
    #                         new_domain.append(item)
                            
    #                 # Handle tanggal
    #                 elif field in ['tgl_diperiksa'] and operator == 'ilike' and value:
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
    #             return super(Kesehatan, self)._search([('name', 'ilike', '')], offset=offset, limit=limit, order=order, )
            
    #         domain = valid_domain if valid_domain else domain
        
    #     return super(Kesehatan, self)._search(domain, offset=offset, limit=limit, order=order, )