from odoo import api, fields, models, _
from datetime import date, datetime
from odoo.exceptions import UserError
class AbsenTahfidzQuran(models.Model):
    _name           = 'cdn.absen_tahfidz_quran'
    _description    = 'Model Absen Tahfidz Quran'

    #get domain 
    def _domain_halaqoh_id(self):
        tahun_ajaran = self.env.user.company_id.tahun_ajaran_aktif.id
        user = self.env.user

        # Jika user adalah Manager Kesantrian -> lihat semua halaqoh di tahun ajaran aktif
        if self.env.user.has_group('pesantren_kesantrian.group_kesantrian_manager'):
            return [
                ('fiscalyear_id', '=', tahun_ajaran)
            ]
    # Cari employee dari user
        employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)

        if employee:
            # Guru Qur’an: hanya halaqoh yang dia pegang atau dia jadi pengganti
            return [
                ('fiscalyear_id', '=', tahun_ajaran),
                '|',
                ('penanggung_jawab_id', '=', employee.id),
                ('pengganti_ids', 'in', [employee.id])
            ]

        # Jika user bukan guru dan tidak punya employee
        return [('id', '=', 0)]


    # def _get_domain_guru(self):
    #     tahun_ajaran = self.env.user.company_id.tahun_ajaran_aktif.id
    #     user = self.env.user
    #     if self.env.user.has_group('pesantren_kesantrian.group_kesantrian_manager'):
    #         return [
    #             ('fiscalyear_id', '=', tahun_ajaran)
    #         ]


    #     employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)



    #     return [
    #         ('jns_pegawai', 'in', ['guruquran','guru,guruquran']),
    #     ]

    def _get_domain_guru(self):
        return [
            ('jns_pegawai_ids.code', 'in', ['guruquran'])
        ]

    def _get_default_guru(self):
        user = self.env.user
        employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        return employee.id if employee else False

    name            = fields.Date(string='Tgl Absen', required=True, default=fields.Date.context_today, states={'Done': [('readonly', True)]})
    halaqoh_id      = fields.Many2one('cdn.halaqoh', string='Halaqoh', required=True, domain=_domain_halaqoh_id, states={'Done': [('readonly', True)]})
    ustadz_id       = fields.Many2one('hr.employee', string='Ustadz', required=True, domain=_get_domain_guru, states={'Done': [('readonly', True)]}, default=_get_default_guru)
    fiscalyear_id   = fields.Many2one('cdn.ref_tahunajaran', string='Tahun Ajaran', readonly=True, default=lambda self:self.env.user.company_id.tahun_ajaran_aktif.id, states={'Done': [('readonly', True)]})
    sesi_id         = fields.Many2one('cdn.sesi_tahfidz', string='Sesi', states={'Done': [('readonly', True)]})
    keterangan      = fields.Text(string='Keterangan', states={'Done': [('readonly', True)]})
    absen_ids       = fields.One2many('cdn.absen_tahfidz_quran_line', 'absen_id', string='Absen', states={'Done': [('readonly', True)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('proses', 'Proses'),
        ('done','Selesai'),
    ], default='draft', string='Status')
    penanggung_jawab_id = fields.Many2one('hr.employee', string='Penanggung Jawab', related='halaqoh_id.penanggung_jawab_id', readonly=True, store=True)

    def action_proses(self):
        self.state = 'proses'
        for absen in self.absen_ids:
            if absen.kehadiran == 'Hadir':
                surah, ayat_awal = None, None
                last_tahfidz = self.env['cdn.tahfidz_quran'].search([
                    ('siswa_id', '=', absen.siswa_id.id),
                    ('state', '=', 'done'),
                ], order='id desc', limit=1)
                if last_tahfidz:
                    if not last_tahfidz.surah_id.number == 114 and last_tahfidz.ayat_akhir.name == last_tahfidz.surah_id.jml_ayat:
                        surah = self.env['cdn.surah'].search([('number', '>', last_tahfidz.surah_id.number)], limit=1).id
                        ayat_awal = self.env['cdn.ayat'].search([('surah_id', '=', last_tahfidz.surah_id.id)], limit=1).id
                    else:
                        ayat_awal = last_tahfidz.ayat_akhir.id + 1
                        surah = last_tahfidz.surah_id.id       
                tahfidz_quran_vals = {
                    'tanggal': self.name,
                    'siswa_id': absen.siswa_id.id,
                    'halaqoh_id': self.halaqoh_id.id,
                    'ustadz_id': self.ustadz_id.id,
                    'sesi_tahfidz_id': self.sesi_id.id,
                    'state': 'draft',
                    'surah_id': surah,
                    'ayat_awal': ayat_awal,
                }
                self.env['cdn.tahfidz_quran'].create(tahfidz_quran_vals)


    def action_confirm(self):
        self.state = 'done'

    @staticmethod
    def format_datetime_indonesia(dt):
        bulan_dict = {
            '01': 'Januari', '02': 'Februari', '03': 'Maret', '04': 'April',
            '05': 'Mei', '06': 'Juni', '07': 'Juli', '08': 'Agustus',
            '09': 'September', '10': 'Oktober', '11': 'November', '12': 'Desember'
        }
        if dt:
            hari = dt.strftime('%d')
            bulan_angka = dt.strftime('%m')
            tahun = dt.strftime('%Y')
            jam_menit = dt.strftime('%H:%M')
            nama_bulan = bulan_dict.get(bulan_angka, bulan_angka)
            return f"{hari} {nama_bulan} {tahun} {jam_menit}"
        return 'Tidak tercatat'


    @api.onchange('halaqoh_id')
    def _onchange_halaqoh_id(self):
        halaqoh = self.halaqoh_id
        if halaqoh:
            absen_ids = [(5, 0, 0)]
            for siswa in halaqoh.siswa_ids:
                permission = self.env['cdn.perijinan'].search([
                    ('siswa_id', '=', siswa.id),
                    ('state', '=', 'Permission')
                ], limit=1)

                if permission:
                    keperluan_name = permission.keperluan.name if permission.keperluan else 'Tidak ada keterangan'
                    waktu_keluar = self.format_datetime_indonesia(permission.waktu_keluar) if permission.waktu_keluar else 'Tidak tercatat'

                    message = f"Santri Keluar pada {waktu_keluar}, karena {keperluan_name}".encode()
                    absen_ids.append((0,0, {
                        'siswa_id' : siswa.id,
                        'kehadiran' : 'keluar',
                        'keterangan' : message,
                    }))

                else:
                    absen_ids.append((0, 0, {
                        'siswa_id': siswa.id,
                        'kehadiran':'Hadir'
                    }))

            ustadz = halaqoh.penanggung_jawab_id + halaqoh.pengganti_ids
            if not self.env.user.has_group('pesantren_kesantrian.group_kesantrian_manager'):
                ustadz = [x for x in ustadz if x.user_id.id == self.env.user.id]
            return {
                'domain':{
                    'ustadz_id': [
                        ('id','in',[x.id for x in ustadz])
                    ]
                },
                'value': {
                    'absen_ids': absen_ids,
                    'ustadz_id': ustadz[0].id if ustadz else False
                },
            }
    #check others requirements
    @api.model
    def default_get(self, fields_tree):
        tahun_ajaran = self.env['res.company'].search([('id', '=', self.env.ref('base.main_company').id)]).tahun_ajaran_aktif.id
        if not tahun_ajaran:
            raise UserError(_('Tahun ajaran belum di set'))
        return super().default_get(fields_tree)
        
    
    # @api.model
    # def _search(self, domain, offset=0, limit=None, order=None, count=False):
    #     # Handle empty  domain
    #     if not domain:
    #         return super(AbsenTahfidzQuran, self)._search(domain, offset=offset, limit=limit, order=order, )
        
    #     # Periksa domain untuk mencegah error
    #     if isinstance(domain, list):
            
    #         new_domain = []
    #         for item in domain:
    #             if isinstance(item, (list, tuple)) and len(item) == 3:
    #                 field, operator, value = item
                    
    #                 # Handle selection fields untuk pencarian label dan bukan hanya value
    #                 if field == 'state' and operator == 'ilike' and value:
    #                     if 'draft' in value.lower() or 'Draft' in value.lower() or 'draf' in value.lower():
    #                         new_domain.append(('state', '=', 'Draft'))
    #                     elif 'proses' in value.lower() or 'Proses' in value.lower():
    #                         new_domain.append(('state', '=', 'Proses'))
    #                     elif 'Done' in value.lower() or 'selesai' in value.lower():
    #                         new_domain.append(('state', '=', 'Done'))
    #                     else: 
    #                         new_domain.append(item)
                            
    #                 # Handle tanggal
    #                 elif field in ['name'] and operator == 'ilike' and value:
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
    #         # valid_domain = []
    #         # or_count = 0
            
    #         # for item in domain:
    #         #     if isinstance(item, (list, tuple)) and len(item) == 3:
    #         #         valid_domain.append(item)
    #         #     elif isinstance(item, str) and item in ['&', '|', '!']:
    #         #         if item == '|':
    #         #             or_count += 1
    #         #         valid_domain.append(item)
            
    #         # # Ensure proper balancing for OR operators
    #         # if or_count > 0 and len(valid_domain) < (or_count * 2 + 1):
    #         #     # Domain is invalid, fall back to simple name search
    #         #     return super(AbsenTahfidzQuran, self)._search([('name', 'ilike', '')], offset=offset, limit=limit, order=order, )
            
    #         # domain = valid_domain if valid_domain else domain
            
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
    #                     return super(AbsenTahfidzQuran, self)._search([('id', 'in', absen_line_ids)], offset=offset, limit=limit, order=order)
            
    #         domain = valid_domain if valid_domain else domain
            
    #     return super(AbsenTahfidzQuran, self)._search(domain, offset=offset, limit=limit, order=order, )
    

 
class AbsenTahfidzQuranLine(models.Model):
    _name           = 'cdn.absen_tahfidz_quran_line'
    _description    = 'Model Absen Tahfidz Quran Line'

    name            = fields.Char(string='Nama', related='siswa_id.name', readonly=True, store=True)
    absen_id        = fields.Many2one('cdn.absen_tahfidz_quran', string='Absen', ondelete='cascade')
    tanggal         = fields.Date(string='Tgl Absen', related='absen_id.name', readonly=True, store=True)
    halaqoh_id      = fields.Many2one('cdn.halaqoh', string='Halaqoh', related='absen_id.halaqoh_id', readonly=True, store=True)
    siswa_id        = fields.Many2one('cdn.siswa', string='Siswa', required=True , ondelete='cascade')
    nis             = fields.Char(string='NIS', related='siswa_id.nis', readonly=True, store=True)
    panggilan       = fields.Char(string='Nama Panggilan', related='siswa_id.namapanggilan', readonly=True, store=True)
    keterangan      = fields.Char(string="Keterangan")
    keterangan_izin = fields.Char(string='Foto', store=True)
    kehadiran       = fields.Selection([
        ('Hadir', 'Hadir'),
        ('Izin', 'Izin'),
        ('keluar', 'Izin Keluar'),
        ('Sakit', 'Sakit'),
        ('Alpa', 'Alpa'),
    ], string='Kehadiran', required=True)
    penanggung_jawab_id = fields.Many2one('hr.employee', string='Penanggung Jawab', related='halaqoh_id.penanggung_jawab_id', readonly=True, store=True)

    def action_view_permission(self):
        """Open permission form for this student"""
        if not self.siswa_id or not self.tanggal:
            return
            
        permission = self.env['cdn.perijinan'].search([
            ('siswa_id', '=', self.siswa_id.id),
            ('state', '=', 'Permission')
        ], limit=1)
        
        if not permission:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title' : '❌ Tidak Dapat Menemukan Data !',
                    'message': 'Data perizinan tidak ditemukan, mungkin santri telah kembali.',
                    'type': 'danger',
                    'sticky': False,
                }
            }
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Detail Perijinan',
            'res_model': 'cdn.perijinan',
            'res_id': permission.id,
            'view_mode': 'form',
            'target': 'current',
        }
