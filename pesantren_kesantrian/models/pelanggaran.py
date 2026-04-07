from odoo import api, fields, models
from lxml import etree
from datetime import datetime, timedelta
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class Pelanggaran(models.Model):
    _name = 'cdn.pelanggaran'
    _description = 'Model untuk Mencatat Aktivitas Pelanggaran'
    _order = 'create_date desc'

    name = fields.Char(string='No. Referensi', readonly=True)
    state = fields.Selection(string='Status', selection=[
        ('draft', 'Draft'),
        ('confirmed', 'Konfirmasi'),
        ('approved', 'Disetujui'),
    ], default='draft')
    #data santri
    tgl_pelanggaran = fields.Date(string='Tgl Pelanggaran',
        states={
            'draft': [('readonly', False)],
            'confirmed': [('readonly', True)],
            'approved': [('readonly', True)],
        }, default=fields.Date.context_today, required=True)
    siswa_id = fields.Many2one(comodel_name='cdn.siswa', string='Santri',
        states={
            'draft': [('readonly', False)],
            'confirmed': [('readonly', True)],
            'approved': [('readonly', True)],
        } ,
        required=True, ondelete='cascade' ,readonly=True)
    barcode = fields.Char(string='Kartu Santri', states= {
        'draft': [('readonly', False)],
        'confirmed': [('readonly', True)],
        'approved': [('readonly', True)],
    })

    kelas_id = fields.Many2one(comodel_name='cdn.ruang_kelas', string='Kelas', 
        related='siswa_id.ruang_kelas_id', readonly=True, store=True)

    #data pelanggaran

    pelanggaran_id = fields.Many2one(comodel_name='cdn.data_pelanggaran', string='Kategori Pelanggaran', 
        states={
            'draft': [('readonly', False)],
            'confirmed': [('readonly', True)],
            'approved': [('readonly', True)],
        },
        required=False, readonly=True)

    kategori = fields.Selection(string='Kategori', selection=[
        ('ringan', 'Ringan'), ('sedang', 'Sedang'), ('berat', 'Berat'), ('sangat_berat', 'Sangat Berat')
    ], related='pelanggaran_id.kategori', store=True)

    poin = fields.Integer(string='Poin', store=True, states={
        'draft': [('readonly', False)],
        'confirmed': [('readonly', True)],
        'approved': [('readonly', True)],
    })

    deskripsi = fields.Text(string='Deskripsi Pelanggaran', 
        states={
            'draft': [('readonly', False)],
            'confirmed': [('readonly', True)],
            'approved': [('readonly', True)],
        })
    
    company_id      = fields.Many2one('res.company', string='Lembaga', default=lambda self: self.env.company)

    #data tindakan
    tindakan_id = fields.Many2one(comodel_name='cdn.tindakan_hukuman', string='Tindakan',
        states={
            'draft': [('readonly', False)],
            'confirmed': [('readonly', True)],
            'approved': [('readonly', True)],
        },
        required=True, readonly=True)

    deskripsi_tindakan = fields.Text(string='Deskripsi Tindakan', 
        states={
            'draft': [('readonly', False)],
            'confirmed': [('readonly', True)],
            'approved': [('readonly', True)],
        })

    diperiksa_oleh = fields.Many2one(comodel_name='hr.employee', string='Diperiksa Oleh',
        states={
            'draft': [('readonly', False)],
            'confirmed': [('readonly', True)],
            'approved': [('readonly', True)],
        },
        default=lambda self: self.env['res.users'].browse(self.env.uid).employee_id.id if self.env.uid else False,
        required=True, readonly=True)

    catatan_ka_asrama = fields.Text(string='Catatan Ustadz / Kepala Asrama',
        states={
            'draft': [('readonly', True)],
            'confirmed': [('readonly', False)],
            'approved': [('readonly', False)],
        }
    )
    tgl_disetujui = fields.Date(string='Tgl Disetujui',
        states={
            'draft': [('readonly', True)],
            'confirmed': [('readonly', False)],
            'approved': [('readonly', False)],
        },readonly=True)
    user_disetujui = fields.Many2one(comodel_name='res.users', string='Disetujui oleh', 
        states={
            'draft': [('readonly', True)],
            'confirmed': [('readonly', False)],
            'approved': [('readonly', False)],
        }, readonly=True)

    musyrif_id = fields.Many2one(
        comodel_name='hr.employee', 
        string='Musyrif', 
        related='siswa_id.musyrif_id', 
        readonly=True, 
        store=True
    )

    barcode = fields.Char(string="Kartu Santri", states={
            'draft': [('readonly', False)],
            'confirmed': [('readonly', True)],
            'approved': [('readonly', True)],
        } ,
        readonly=True)
    kamar_id    = fields.Many2one('cdn.kamar_santri', string='Kamar', related='siswa_id.kamar_id', readonly=True)
    halaqoh_id  = fields.Many2one('cdn.halaqoh', string='Halaqoh', related='siswa_id.halaqoh_id', readonly=True)
    musyrif_id  = fields.Many2one('hr.employee', string='Musyrif', related='siswa_id.musyrif_id', readonly=True)

    @api.onchange('pelanggaran_id')
    def _onchange_pelanggaran_id(self):
        if self.pelanggaran_id:
            self.poin = self.pelanggaran_id.poin

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
            _logger.info(f"Data Santri: {siswa}")
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


    # ir_squence for no. referensi
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('cdn.pelanggaran')
        return super(Pelanggaran, self).create(vals)

    def action_confirmed(self):
        self.state = 'confirmed'
    def action_approved(self):
        if not self.tgl_disetujui:
            self.tgl_disetujui = fields.Date.context_today(self)
        if not self.user_disetujui:
            self.user_disetujui = self.env.user.id
        self.state = 'approved'
    def action_set_to_draft(self):
        self.state = 'draft'

    @api.onchange('kategori')
    def _onchange_kategori(self):
        mapping = {
            'ringan': 'Ringan',
            'sedang': 'Sedang',
            'berat': 'Berat',
            'sangat_berat': 'Dikeluarkan'
        }
        if self.kategori:
            return {
                'domain': {
                    'tindakan_id': [('level_pelanggaran', '=', mapping.get(self.kategori))]
                }
            }
        else:
            # Kalau kategori belum dipilih, tampilkan semua
            return {
                'domain': {
                    'tindakan_id': []
                }
            }

    # @api.model
    # def _search(self, domain, offset=0, limit=None, order=None, count=False):
    #     # Handle empty domain
    #     if not domain:
    #         return super(Pelanggaran, self)._search(domain, offset=offset, limit=limit, order=order, )
        
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
    #                     elif 'konfirmasi' in value.lower() or 'dikonfirmasi' in value.lower():
    #                         new_domain.append(('state', '=', 'confirmed'))
    #                     elif 'disetujui' in value.lower() or 'setuju' in value.lower():
    #                         new_domain.append(('state', '=', 'approved'))
    #                     else: 
    #                         new_domain.append(item)
                            
    #                 # Handle tanggal
    #                 elif field in ['tgl_pelanggaran'] and operator == 'ilike' and value:
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
    #             return super(Pelanggaran, self)._search([('name', 'ilike', '')], offset=offset, limit=limit, order=order, )
            
    #         domain = valid_domain if valid_domain else domain
        
    #     return super(Pelanggaran, self)._search(domain, offset=offset, limit=limit, order=order, )
    

