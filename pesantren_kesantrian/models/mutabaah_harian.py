from itertools import count
from odoo import api, fields, models
from datetime import date, datetime

class Mutabaah_harian(models.Model):
    _name = 'cdn.mutabaah_harian'
    _description = 'Mutabaah Harian'
    _order = 'tgl Desc'

    #get domain
   
    name        = fields.Char(string='No. Referensi', readonly=True)
    tgl         = fields.Date('Tgl Mutabaah', required=True, default=lambda self: date.today())
    sesi_id     = fields.Many2one(comodel_name='cdn.mutabaah.sesi', string='Sesi')
    siswa_id    = fields.Many2one('cdn.siswa', string='Santri',  ondelete='cascade', required=True)
    halaqoh_id  = fields.Many2one('cdn.halaqoh', string='Halaqoh', readonly=True, related='siswa_id.halaqoh_id')
    
    barcode         = fields.Char(string="Kartu Santri", readonly=False)

    kamar_id        = fields.Many2one('cdn.kamar_santri', string='Kamar', related='siswa_id.kamar_id', readonly=True)
    musyrif_id      = fields.Many2one('hr.employee', string='Musyrif', related='siswa_id.musyrif_id', readonly=True)
    kelas_id        = fields.Many2one('cdn.ruang_kelas', string='Kelas', related='siswa_id.ruang_kelas_id', readonly=True, store=True)
    halaqoh_id      = fields.Many2one('cdn.halaqoh', string='Halaqoh', related='siswa_id.halaqoh_id', readonly=True)
    company_id      = fields.Many2one('res.company', string='Lembaga', default=lambda self: self.env.company)
    
    mutabaah_lines  = fields.One2many('cdn.mutabaah_line', 'mutabaah_harian_id', string='Check Aktivitas')

    total_skor          = fields.Integer(string='Total Skor', compute='_compute_total_skor', store=True)
    total_skor_display  = fields.Char(string='Skor Mutabaah', compute='_compute_total_skor_display')
    state               = fields.Selection([
        ('Draft', 'Draft'),
        ('Done','Selesai'),
    ], default='Draft', string='Status')

    # total_skor_adab = fields.Integer(string='Aktivitas Adab', related='mutabaah_lines.total_skor_adab', store=True)
    # total_skor_kedisiplinan = fields.Integer(string='Aktivitas Kedisiplinan', related='mutabaah_lines.total_skor_kedisiplinan', store=True)
    # total_skor_ibadah = fields.Integer(string='Aktivitas ibadah', related='mutabaah_lines.total_skor_ibadah', store=True)
    # total_skor_kebersihan = fields.Integer(string='Aktivitas Kebersihan', related='mutabaah_lines.total_skor_kebersihan', store=True)
    
    @api.model
    def default_get(self, fields_list):
        res = super(Mutabaah_harian, self).default_get(fields_list)
        sesi = self.env['cdn.mutabaah.sesi'].search([], limit=1, order="id asc")
        if sesi:
            res['sesi_id'] = sesi.id
        return res
    
    # @api.onchange('siswa_id')
    # def _onchange_siswa_id(self):
    #     if self.siswa_id:
    #         self.barcode = self.siswa_id.barcode_santri
    #     else:
    #         self.barcode = False

    @api.onchange('siswa_id')
    def _onchange_siswa_id(self):
        if self.siswa_id:
            self.barcode = self.siswa_id.barcode_santri
            self.halaqoh_id = self.siswa_id.halaqoh_id.id
        else:
            self.barcode = False
            self.halaqoh_id = False


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
        vals["name"] = self.env["ir.sequence"].next_by_code("cdn.mutabaah_harian")
        return super(Mutabaah_harian, self).create(vals)
    
    #insert one2many
    # @api.onchange('siswa_id')
    # def onchange_siswa_id(self):
        
    
            
    @api.onchange('siswa_id','tgl','sesi_id')
    def onchange_siswa_id(self):
        self.ensure_one()
        if self.siswa_id:
            mutabaah_harian = self.env['cdn.mutabaah_harian'].search([
                ('siswa_id','=', self.siswa_id.id),
                ('tgl','=', self.tgl),
                ('sesi_id','=', self.sesi_id.id),
                ])
            
            # Jika sudah pernah diinput data mutabaah
            if mutabaah_harian:
                return {
                    'warning' : {
                        'title' : "Harap diperhatikan!",
                        'message' : "Santri yang sudah di catat tidak boleh di catat lagi dalam sehari"
                    },
                    'value' : {
                        'mutabaah_lines' : False,
                        'siswa_id' : False
                    }

                }
            # Jika Belum pernah diinput data mutabaah
            else:
                # Cek apakah data diinput jam sekarang melebih batas waktu sesi 
                jam_sekarang = fields.Datetime.now().hour in range(0,24)
                print(jam_sekarang)
                if int(jam_sekarang) > int(self.sesi_id.jam_selesai):
                    return {
                        'warning' : {
                            'title' : "Harap diperhatikan!",
                            'message' : "Waktu sesi mutabaah sudah berakhir"
                        },
                        'value' : {
                            'mutabaah_lines' : False,
                            'siswa_id' : False
                        }
                    }


                nilai = [(5,0,0)] 

                objek_mutabaah = self.env['cdn.mutabaah'].search([('sesi_id','=',self.sesi_id.id)], order = 'id asc')
                
                for ye in objek_mutabaah:
                    nilai.append(
                        (0, 0,{'name': ye.id, 'is_sudah':True, 'keterangan':'-'})
                    )
                return {'value' : {'mutabaah_lines' : nilai}}
            
    @api.depends('mutabaah_lines.is_sudah')
    def _compute_total_skor(self):
        for rec in self:
            rec.total_skor = sum(rec.mutabaah_lines.filtered('is_sudah').mapped('name.skor'))
            
    @api.depends('mutabaah_lines.is_sudah')
    def _compute_total_skor_display(self):
        for rec in self:
            total_records = len(rec.mutabaah_lines)
            completed_records = sum(1 for line in rec.mutabaah_lines if line.is_sudah)
            rec.total_skor_display = f"{completed_records} dari {total_records}"

    def btn_uncheckall(self):
        self.mutabaah_lines.is_sudah = False

    def btn_checkall(self):
        self.mutabaah_lines.is_sudah = True
    
    def action_confirm(self):
        self.state = 'Done'
        
    def action_draft(self):
        self.state = 'Draft'


    # @api.model
    # def _search(self, domain, offset=0, limit=None, order=None, count=False):
    #     # Handle empty domain
    #     if not domain:
    #         return super(Mutabaah_harian, self)._search(domain, offset=offset, limit=limit, order=order, )
        
    #     # Periksa domain untuk mencegah error
    #     if isinstance(domain, list):
            
    #         new_domain = []
    #         for item in domain:
    #             if isinstance(item, (list, tuple)) and len(item) == 3:
    #                 field, operator, value = item
                    
    #                 if field == 'state' and operator == 'ilike' and value:
    #                     if 'draft' in value.lower() or 'Draft' in value.lower() or 'draf' in value.lower():
    #                         new_domain.append(('state', '=', 'Draft'))
    #                     elif 'Done' in value.lower() or 'selesai' in value.lower() or 'done' in value.lower():
    #                         new_domain.append(('state', '=', 'Done'))
    #                     else: 
    #                         new_domain.append(item)
                            
    #                 # Handle tanggal
    #                 elif field in ['tgl'] and operator == 'ilike' and value:
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
    #                 absen_line_ids = self.env['cdn.mutabaah_line'].search([('siswa_id', 'in', siswa_ids)]).mapped('absen_id').ids
    #                 if absen_line_ids:
    #                     # Tambahkan domain untuk filter berdasarkan ID absen
    #                     return super(Mutabaah_harian, self)._search([('id', 'in', absen_line_ids)], offset=offset, limit=limit, order=order)
            
    #         domain = valid_domain if valid_domain else domain
            
    #     return super(Mutabaah_harian, self)._search(domain, offset=offset, limit=limit, order=order, )



class Mutabaah_line(models.Model):
    _name = 'cdn.mutabaah_line'
    _description = 'Mutabaah line'

    mutabaah_harian_id = fields.Many2one('cdn.mutabaah_harian', string='mutabaah_harian')
    skor = fields.Integer(string='Skor', related='name.skor')
    siswa_id = fields.Many2one('cdn.siswa', string='Siswa', related='mutabaah_harian_id.siswa_id', ondelete='cascade' , readonly=True, store=True)
    tgl = fields.Date('Tgl Mutabaah', related='mutabaah_harian_id.tgl', readonly=True, store=True)
    name = fields.Many2one('cdn.mutabaah', string='Aktivitas / Perbuatan')
    kategori_id = fields.Many2one(comodel_name='cdn.mutabaah.kategori', string='Kategori', related='name.kategori_id')
    
    is_sudah = fields.Boolean(string='Dilakukan', )
    keterangan = fields.Char(string='Keterangan')

    # total_skor_adab = fields.Integer(string='Aktivitas Adab', compute='_compute_total_skor', store=True)
    # total_skor_kedisiplinan = fields.Integer(string='Aktivitas Kedisiplinan', compute='_compute_total_skor', store=True)
    # total_skor_ibadah = fields.Integer(string='Aktivitas Ibadah', compute='_compute_total_skor', store=True)
    # total_skor_kebersihan = fields.Integer(string='Aktivitas Kebersihan', compute='_compute_total_skor', store=True)
    
    # @api.depends('siswa_id','is_sudah')
    # def _compute_total_skor(self):

        # for rec in self:

        #     adab = self.env['cdn.mutabaah'].search([
        #         ('kategori','=', 'adab'),
        #         ('is_tampil','=',True)]).mapped('skor')

        #     if rec.siswa_id:    
        #         rec.total_skor_adab = sum(adab)
        #     # elif rec.is_sudah == False:
        #     #     rec.total_skor_adab = sum(adab) - adab  

        #     disiplin = self.env['cdn.mutabaah'].search([
        #         ('kategori','=', 'disiplin'),
        #         ('is_tampil','=',True)]).mapped('skor')
            
        #     if rec.siswa_id:    
        #         rec.total_skor_kedisiplinan = sum(disiplin)

        #     ibadah = self.env['cdn.mutabaah'].search([
        #         ('kategori','=', 'ibadah'),
        #         ('is_tampil','=',True)]).mapped('skor')

        #     if rec.siswa_id:    
        #         rec.total_skor_ibadah = sum(ibadah)

        #     kebersihan = self.env['cdn.mutabaah'].search([
        #         ('kategori','=', 'kebersihan'),
        #         ('is_tampil','=',True)]).mapped('skor')

        #     if rec.siswa_id:    
        #         rec.total_skor_kebersihan = sum(kebersihan)