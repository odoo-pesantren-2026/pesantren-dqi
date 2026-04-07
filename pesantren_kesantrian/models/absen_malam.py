# from odoo import api, fields, models
# from datetime import date

# class AbsensiMalam(models.Model):
#     _name = 'cdn.absensi_malam'
#     _description = 'Absensi Malam Santri'
#     _order = 'tgl desc'

#     name        = fields.Char(string='No. Referensi', readonly=True)
#     tgl         = fields.Date(string='Tanggal', required=True, default=lambda self: date.today())
#     siswa_id    = fields.Many2one('cdn.siswa', string='Santri',  ondelete='cascade', required=True)
#     halaqoh_id  = fields.Many2one('cdn.halaqoh', string='Halaqoh', readonly=True, related='siswa_id.halaqoh_id')
    
#     barcode          = fields.Char(string="Kartu Santri", readonly=False)

#     kamar_id    = fields.Many2one('cdn.kamar_santri', string='Kamar', related='siswa_id.kamar_id', readonly=True)
#     musyrif_id  = fields.Many2one('hr.employee', string='Musyrif', related='siswa_id.musyrif_id', readonly=True)
#     kelas_id        = fields.Many2one('cdn.ruang_kelas', string='Kelas', related='siswa_id.ruang_kelas_id', readonly=True, store=True)
#     halaqoh_id  = fields.Many2one('cdn.halaqoh', string='Halaqoh', related='siswa_id.halaqoh_id', readonly=True)


#     kehadiran = fields.Selection([
#         ('hadir', 'Hadir'),
#         ('masybul', 'Masybul'),
#         ('izin', 'Izin'),
#         ('sakit', 'Sakit'),
#     ], string='Kehadiran', default='hadir')

#     keterangan = fields.Char(string='Keterangan')

#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('done', 'Selesai'),
#     ], default='draft', string='Status')
#     row_number      = fields.Integer(string='No', compute='_compute_row_number', store=False)

#     def _compute_row_number(self):
#         for index, record in enumerate(self):
#             record.row_number = index + 1    # --- onchange barcode & siswa ---
#     @api.onchange('siswa_id')
#     def _onchange_siswa_id(self):
#         if self.siswa_id:
#             self.barcode = self.siswa_id.barcode_santri
#         else:
#             self.barcode = False

#     @api.onchange('barcode')
#     def _onchange_barcode(self):
#         if self.barcode:
#             siswa = self.env['cdn.siswa'].search([('barcode_santri', '=', self.barcode)], limit=1)
#             if siswa:
#                 self.siswa_id = siswa.id
#             else:
#                 barcode_sementara = self.barcode
#                 self.barcode = False
#                 self.siswa_id = False
#                 return {
#                     'warning': {
#                         'title': "Perhatian!",
#                         'message': f"Santri dengan kartu {barcode_sementara} tidak ditemukan."
#                     }
#                 }

#     # --- Cegah duplikasi absen per santri per hari per sesi ---
#     @api.onchange('siswa_id', 'tgl')
#     def _onchange_check_duplikat(self):
#         if self.siswa_id and self.tgl:
#             existing = self.env['cdn.absensi_malam'].search([
#                 ('siswa_id', '=', self.siswa_id.id),
#                 ('tgl', '=', self.tgl),
#                 ('id', '!=', self._origin.id if self._origin else False)
#             ])
#             if existing:
#                 return {
#                     'warning': {
#                         'title': "Duplikasi!",
#                         'message': "Santri ini sudah diabsen pada sesi dan tanggal ini."
#                     },
#                     'value': {
#                         'siswa_id': False,
#                         'barcode': False,
#                         'kehadiran': 'hadir',
#                         'keterangan': False
#                     }
#                 }

#     # --- Sequence number ---
#     @api.model
#     def create(self, vals):
#         if not vals.get('name'):
#             vals['name'] = self.env['ir.sequence'].next_by_code('cdn.absensi_malam') or '/'
#         return super(AbsensiMalam, self).create(vals)

#     # --- Tombol action ---
#     def action_confirm(self):
#         self.write({'state': 'done'})

#     def action_draft(self):
#         self.write({'state': 'draft'})

from odoo import api, fields, models
from datetime import date
from odoo.exceptions import UserError

class AbsensiMalam(models.Model):
    _name = 'cdn.absensi_malam'
    _description = 'Absensi Malam Santri'
    _order = 'tgl desc'

    name            = fields.Char(string='No. Referensi', readonly=True)
    tgl             = fields.Date(string='Tanggal', required=True, default=lambda self: date.today())
    
    # Filter untuk kamar atau halaqoh
    kamar_id        = fields.Many2one('cdn.kamar_santri', string='Kamar', domain=lambda self: self._domain_kamar_id())
    fiscalyear_id   = fields.Many2one('cdn.ref_tahunajaran', string='Tahun Ajaran', readonly=True, default=lambda self:self.env.user.company_id.tahun_ajaran_aktif.id, states={'Done': [('readonly', True)]})
    
    musyrif_id      = fields.Many2one(
        'hr.employee', 
        string='Musyrif', 
        domain=lambda self: self.env['cdn.absensi_malam']._domain_musyrif(), 
        default=lambda self: self.env['cdn.absensi_malam']._default_musyrif_id())
    
    absen_ids       = fields.One2many('cdn.absensi_malam_line', 'absen_id', string='Daftar Kehadiran')
    
    keterangan      = fields.Char(string='Keterangan')
    
    state           = fields.Selection([
        ('draft', 'Draft'),
        ('proses', 'Proses'),
        ('done', 'Selesai'),
    ], default='draft', string='Status')
    
    row_number      = fields.Integer(string='No', compute='_compute_row_number', store=False)
    company_id      = fields.Many2one('res.company', string='Lembaga', default=lambda self: self.env.company)

    def _compute_row_number(self):
        for index, record in enumerate(self):
            record.row_number = index + 1

    # ---------- DEFAULT & DOMAIN FUNCTION ----------
    def _domain_musyrif(self):
        admin_user_ids = self.env.ref('base.group_system').users.ids

        return [
            '|',
            ('user_id', 'in', admin_user_ids),
            ('jns_pegawai_ids.code', 'in', ['musyrif', 'superadmin'])
        ]
    @api.model
    def _default_musyrif_id(self):
        """Set default musyrif sesuai user login."""
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        if employee and (employee.has_role('musyrif') or employee.has_role('superadmin')):
            return employee.id
        return False

    @api.model
    def _domain_kamar_id(self):
        """Filter kamar sesuai musyrif yang login dan tahun ajaran aktif."""
        user = self.env.user
        employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        
        # Ambil tahun ajaran aktif
        tahun_ajaran = self.env.user.company_id.tahun_ajaran_aktif.id
        
        # Base domain: filter berdasarkan tahun ajaran
        base_domain = [('fiscalyear_id', '=', tahun_ajaran)]
        
        # Jika admin, tampilkan semua kamar (hanya filter tahun ajaran)
        if user.has_group('base.group_system'):
            return base_domain
        
        # Jika musyrif, hanya tampilkan kamar di bawahnya (filter tahun ajaran + musyrif)
        if employee and (employee.has_role('musyrif') or employee.has_role('superadmin')):
            kamar_ids = self.env['cdn.kamar_santri'].search([
                ('musyrif_id', '=', employee.id),
                ('fiscalyear_id', '=', tahun_ajaran)
            ]).ids
            return [('id', 'in', kamar_ids)]
        
        # Default: hanya filter tahun ajaran (untuk user lain)
        return base_domain

    # @api.onchange('kamar_id')
    # def _onchange_filter_santri(self):
    #     """Mengisi absen_ids berdasarkan kamar dan mengatur ustadz_id ke pengguna login untuk staff."""
    #     kamar = self.kamar_id
    #     if kamar:
    #         absen_ids = [(5, 0, 0)]

    #         # Ambil semua santri di kamar yang dipilih
    #         siswa_list = self.env['cdn.siswa'].search([('kamar_id', '=', kamar.id)])

    #         # Jika tidak ada santri, beri peringatan
    #         if not siswa_list:
    #             return {
    #                 'warning': {
    #                     'title': 'Perhatian',
    #                     'message': 'Tidak ada santri yang ditemukan dengan kamar tersebut.'
    #                 },
    #                 'value': {'absen_ids': [(5, 0, 0)]}
    #             }

    #         # Isi absen berdasarkan izin atau kehadiran
    #         for siswa in siswa_list:
    #             permission = self.env['cdn.perijinan'].search([
    #                 ('siswa_id', '=', siswa.id),
    #                 ('state', '=', 'Permission')
    #             ], limit=1)
    #             if permission:
    #                 keperluan_name = permission.keperluan.name if permission.keperluan else 'Tidak ada keterangan'
    #                 waktu_keluar = self.format_datetime_indonesia(permission.waktu_keluar) if permission.waktu_keluar else 'Tidak tercatat'
    #                 message = f"Santri Keluar pada {waktu_keluar}, karena {keperluan_name}"
    #                 absen_ids.append((0, 0, {
    #                     'siswa_id': siswa.id,
    #                     'kehadiran_absen': 'keluar',
    #                     'keterangan': message,
    #                 }))
    #             else:
    #                 absen_ids.append((0, 0, {
    #                     'siswa_id': siswa.id,
    #                     'kehadiran_absen': 'Hadir'
    #                 }))

    #         # Tentukan ustadz_id sesuai user login
    #         user = self.env.user
    #         employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
    #         ustadz_id = employee.id if employee else False

    #         # Jika user adalah manager kesantrian, boleh pilih musyrif dari kamar
    #         if self.env.user.has_group('pesantren_kesantrian.group_kesantrian_manager'):
    #             musyrif = kamar.musyrif_id | kamar.pengganti_ids
    #             return {
    #                 'domain': {
    #                     'musyrif_id': [('id', 'in', musyrif.ids)]
    #                 },
    #                 'value': {
    #                     'absen_ids': absen_ids,
    #                     'musyrif_id': musyrif[0].id if musyrif else False
    #                 }
    #             }

    #         # Jika bukan manager, musyrif otomatis dari user login
    #         return {
    #             'domain': {
    #                 'musyrif_id': [('id', '=', self.musyrif_id)] if self.musyrif_id else [('id', '=', False)]
    #             },
    #             'value': {
    #                 'absen_ids': absen_ids,
    #                 'musyrif_id': self.musyrif_id
    #             }
    #         }

    #     # Jika kamar tidak dipilih, kosongkan daftar absen
    #     return {'value': {'absen_ids': [(5, 0, 0)]}}
    
    @api.onchange('kamar_id')
    def _onchange_filter_santri(self):
        """Mengisi absen_ids berdasarkan kamar dan mengatur ustadz_id ke pengguna login untuk staff."""
        kamar = self.kamar_id
        if kamar:
            absen_ids = [(5, 0, 0)]

            # Ambil semua santri di kamar yang dipilih
            siswa_list = self.env['cdn.siswa'].search([('kamar_id', '=', kamar.id)])

            # Jika tidak ada santri, beri peringatan
            if not siswa_list:
                return {
                    'warning': {
                        'title': 'Perhatian',
                        'message': 'Tidak ada santri yang ditemukan dengan kamar tersebut.'
                    },
                    'value': {'absen_ids': [(5, 0, 0)]}
                }

            # Isi absen berdasarkan izin atau kehadiran
            for siswa in siswa_list:
                permission = self.env['cdn.perijinan'].search([
                    ('siswa_id', '=', siswa.id),
                    ('state', '=', 'Permission')
                ], limit=1)
                
                if permission:
                    keperluan_name = permission.keperluan.name if permission.keperluan else 'Tidak ada keterangan'
                    waktu_keluar = self.format_datetime_indonesia(permission.waktu_keluar) if permission.waktu_keluar else 'Tidak tercatat'
                    message = f"Santri Keluar pada {waktu_keluar}, karena {keperluan_name}"
                    
                    # PERBAIKAN: Ambil foto bukti dari perijinan
                    foto_bukti = permission.foto_bukti if permission.foto_bukti else False
                    
                    # Ambil nama file asli dari perijinan, atau generate jika kosong
                    if permission.foto_bukti_filename:
                        nama_file = permission.foto_bukti_filename
                    elif foto_bukti:
                        # Generate nama file jika tidak ada
                        nama_file = f"Bukti_Izin_{siswa.nis}_{siswa.name}_{permission.name}.jpg"
                    else:
                        nama_file = False
                    
                    absen_ids.append((0, 0, {
                        'siswa_id': siswa.id,
                        'kehadiran_absen': 'keluar',
                        'keterangan': message,
                        'keterangan_izin': foto_bukti,  # Auto-fill foto bukti
                        'keterangan_izin_filename': nama_file,  # Auto-fill nama file
                        'company_id': self.company_id.id,
                    }))
                else:
                    absen_ids.append((0, 0, {
                        'siswa_id': siswa.id,
                        'kehadiran_absen': 'Hadir',
                        'company_id': self.company_id.id,
                    }))

            # Tentukan ustadz_id sesuai user login
            user = self.env.user
            employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
            ustadz_id = employee.id if employee else False

            # Jika user adalah manager kesantrian, boleh pilih musyrif dari kamar
            if self.env.user.has_group('pesantren_kesantrian.group_kesantrian_manager'):
                musyrif = kamar.musyrif_id | kamar.pengganti_ids
                return {
                    'domain': {
                        'musyrif_id': [('id', 'in', musyrif.ids)]
                    },
                    'value': {
                        'absen_ids': absen_ids,
                        'musyrif_id': musyrif[0].id if musyrif else False
                    }
                }

            # Jika bukan manager, musyrif otomatis dari user login
            return {
                'domain': {
                    'musyrif_id': [('id', '=', self.musyrif_id)] if self.musyrif_id else [('id', '=', False)]
                },
                'value': {
                    'absen_ids': absen_ids,
                    'musyrif_id': self.musyrif_id
                }
            }

        # Jika kamar tidak dipilih, kosongkan daftar absen
        return {'value': {'absen_ids': [(5, 0, 0)]}}
    
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

    @api.model
    def default_get(self, fields_list):
        """Memastikan tahun ajaran aktif diset."""
        res = super().default_get(fields_list)
        tahun_ajaran = self.env['res.company'].search([('id', '=', self.env.ref('base.main_company').id)]).tahun_ajaran_aktif.id
        if not tahun_ajaran:
            raise UserError('Tahun ajaran belum di set')
        return res

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('cdn.absensi_malam') or '/'
        return super(AbsensiMalam, self).create(vals)

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_proses(self):
        self.write({'state': 'proses'})
        
    def action_done(self):
        self.write({'state': 'done'})


class AbsensiMalamLine(models.Model):
    _name           = 'cdn.absensi_malam_line'
    _description    = 'Detail Absensi Malam Santri'

    absen_id    = fields.Many2one('cdn.absensi_malam', string='Absen', ondelete='cascade', required=True)
    tanggal     = fields.Date(string='Tgl Absen', related='absen_id.tgl', readonly=True, store=True)
    
    siswa_id    = fields.Many2one('cdn.siswa', string='Santri', ondelete='cascade')
    name        = fields.Char(string='Nama', related='siswa_id.name', readonly=True, store=True)
    nis         = fields.Char(string='NIS', related='siswa_id.nis', readonly=True, store=True)
    panggilan   = fields.Char(string='Nama Panggilan', related='siswa_id.namapanggilan', readonly=True, store=True)
    
    kamar_id    = fields.Many2one('cdn.kamar_santri', string='Kamar', related='siswa_id.kamar_id', readonly=True, store=True)
    musyrif_id  = fields.Many2one('hr.employee', string='Musyrif', related='siswa_id.musyrif_id', readonly=True, store=True)
    
    kehadiran_absen = fields.Selection([
        ('Hadir', 'Hadir'),
        ('Izin', 'Izin'),
        ('keluar', 'Izin Keluar'),
        ('Sakit', 'Sakit'),
        ('Alpa', 'Alpa'),
    ], string='Kehadiran', default="Hadir", required=True)
    
    keterangan                  = fields.Char(string='Keterangan')
    keterangan_izin             = fields.Binary(string="Foto", attachment=True)
    keterangan_izin_filename    = fields.Char(string="Nama File Foto")
    company_id                  = fields.Many2one('res.company', string='Lembaga', related='absen_id.company_id', readonly=True, store=True)
    row_number                  = fields.Integer(string='No', compute='_compute_row_number', store=False)

    def _compute_row_number(self):
        for index, record in enumerate(self):
            record.row_number = index + 1

    def action_view_permission(self):
        """Buka form perijinan untuk santri ini"""
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
                    'title': '❌ Tidak Dapat Menemukan Data!',
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