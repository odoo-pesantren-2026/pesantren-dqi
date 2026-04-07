from odoo import api, fields, models
from datetime import datetime
from odoo.exceptions import UserError # type: ignore

class TahsinQuran(models.Model):
    _name           = 'cdn.tahsin_quran'
    _description    = 'Tabel Tahsin Quran'

    name            = fields.Char(string='No Referensi', readonly=True)
    tanggal         = fields.Date(string='Tgl Tahsin', required=True, states={'done': [('readonly', True)]})

    siswa_id        = fields.Many2one('cdn.siswa', string='Santri', required=True , ondelete='cascade')
    kelas_id        = fields.Many2one('cdn.ruang_kelas', string='Kelas', related='siswa_id.ruang_kelas_id', readonly=True, store=True)

    halaqoh_id      = fields.Many2one('cdn.halaqoh', string='Halaqoh', required=True, states={'done': [('readonly', True)]})
    ustadz_id       = fields.Many2one('hr.employee', string='Ustadz Pembimbing', required=True, states={'done': [('readonly', True)]})

    level_tahsin_id = fields.Many2one('cdn.level_tahsin', string='Level Tahsin', states={'done': [('readonly', True)]})
    nilai_tajwid    = fields.Integer(string='Nilai Tajwid', states={'done': [('readonly', True)]})
    nilai_makhroj   = fields.Integer(string='Nilai Makhroj', states={'done': [('readonly', True)]})
    nilai_mad       = fields.Integer(string='Mad', states={'done': [('readonly', True)]})
    nilai_id        = fields.Many2one('cdn.nilai_tahsin', string='Nilai', states={'done': [('readonly', True)]})
    # Revisi : Tambahkan field Buku Tahsin
    buku_tahsin_id  = fields.Many2one('cdn.buku_tahsin', string='Buku Tahsin', states={'done': [('readonly', True)]})
    jilid_tahsin_id = fields.Many2one('cdn.jilid_tahsin', string='Jilid Tahsin', states={'done': [('readonly', True)]})
    halaman_tahsin  = fields.Char(string='Halaman', states={'done': [('readonly', True)]})
    

    catatan_musyrif = fields.Char(string='catatan_musyrif', states={'done': [('readonly', True)]})
    keterangan      = fields.Char(string='Keterangan', states={'done': [('readonly', True)]})

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Selesai')
    ], default='draft', string='Status')
    penanggung_jawab_id = fields.Many2one('hr.employee', string='Penanggung Jawab', related='halaqoh_id.penanggung_jawab_id', readonly=True, store=True)


    barcode             = fields.Char(string="Kartu Santri", related="siswa_id.barcode_santri", readonly=True)
    sesi_tahsin_id      = fields.Many2one('cdn.sesi_tahsin', string='Sesi')
    kamar_id    = fields.Many2one('cdn.kamar_santri', string='Kamar', related='siswa_id.kamar_id', readonly=True)
    # halaqoh_id  = fields.Many2one('cdn.halaqoh', string='Halaqoh', related='siswa_id.halaqoh_id', readonly=True)
    musyrif_id  = fields.Many2one('hr.employee', string='Musyrif', related='siswa_id.musyrif_id', readonly=True)

    @api.onchange('siswa_id')
    def _onchange_siswa_id(self):
        if self.siswa_id:
            self.barcode = self.siswa_id.barcode_santri
        else:
            self.barcode = False


    # Jika buku tahsin diubah, maka jilid dan halaman direset
    @api.onchange('buku_tahsin_id')
    def _onchange_buku_tahsin_id(self):
        self.jilid_tahsin_id = False
        self.halaman_tahsin = False

    def action_confirm(self):
        # if not self.level_tahsin_id or not self.nilai_tajwid or not self.nilai_makhroj or not self.nilai_mad:
        #     raise models.ValidationError('Proses KONFIRMASI harus menyertakan Keterangan Jilid Tahsin dan Nilai-nilainya !')
        # Cek buku tahsin, jilid dan halaman
        if not self.buku_tahsin_id or not self.jilid_tahsin_id or not self.halaman_tahsin:
            raise models.UserError('Proses KONFIRMASI harus menyertakan Buku Tahsin, Jilid dan Halaman !')
        self.state = 'done'
    def action_draft(self):
        self.state = 'draft'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('cdn.tahsin_quran')
        return super(TahsinQuran, self).create(vals)
    # def write(self, vals):
    #     if not vals.get('level_tahsin_id',self.level_tahsin_id.id) or not vals.get('nilai_tajwid',self.nilai_tajwid) or not vals.get('nilai_makhroj',self.nilai_makhroj) or not vals.get('nilai_mad',self.nilai_mad):
    #         raise models.ValidationError('ERROR ! Periksa kembali pengisian KATEGORI Tahsin dan Nilai-nilainya !')
    #     return super(TahsinQuran, self).write(vals)


    # @api.model
    # def _search(self, domain, offset=0, limit=None, order=None, count=False):
    #     # Handle empty domain
    #     if not domain:
    #         return super(TahsinQuran, self)._search(domain, offset=offset, limit=limit, order=order, )
        
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
    #                     return super(TahsinQuran, self)._search([('id', 'in', absen_line_ids)], offset=offset, limit=limit, order=order)
            
    #         domain = valid_domain if valid_domain else domain
            
    #     return super(TahsinQuran, self)._search(domain, offset=offset, limit=limit, order=order, )
    


class BukuTahsin(models.Model):
    _name           = 'cdn.buku_tahsin'
    _description    = 'Tabel Buku Tahsin'

    name            = fields.Char(string='Nama Buku', required=True)
    jilid_ids       = fields.One2many('cdn.jilid_tahsin', 'buku_tahsin_id', string='Jilid Tahsin')
    keterangan      = fields.Char(string='Keterangan')

class JilidTahsin(models.Model):
    _name           = 'cdn.jilid_tahsin'
    _description    = 'Tabel Jilid Tahsin'

    name            = fields.Char(string='Jilid', required=True)
    buku_tahsin_id  = fields.Many2one('cdn.buku_tahsin', string='Buku Tahsin', required=True)
    keterangan      = fields.Char(string='Keterangan')