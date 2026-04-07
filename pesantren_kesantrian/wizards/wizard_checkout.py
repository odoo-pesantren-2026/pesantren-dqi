from odoo import api, fields, models
from odoo.exceptions import UserError
import logging
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

class PerijinanCheckOut(models.TransientModel):
    _name           = 'cdn.perijinan.checkout'
    _description    = 'Santri Keluar/Masuk'

    _last_keperluan_id = None
    _last_penjemput = None
    _last_tgl_kembali = None

    siswa_id = fields.Many2one(
        'cdn.siswa', 
        string='Santri', 
        ondelete='cascade',
        domain=[
            '|', 
            ('name', 'ilike', ''),
            ('nis', 'ilike', '')
        ],
    )

    tgl_ijin = fields.Datetime(string='Tgl Ijin', required=True, default=lambda self: fields.Datetime.now())
    tgl_kembali = fields.Datetime(string='Tgl Kembali', required=True, default=lambda self: fields.Datetime.now() + relativedelta(days=1))
    perijinan_id = fields.Many2one('cdn.perijinan', string='Perizinan')
    kelas_id    = fields.Many2one('cdn.ruang_kelas', string='Kelas', related='siswa_id.ruang_kelas_id', readonly=True)
    kamar_id    = fields.Many2one('cdn.kamar_santri', string='Kamar', related='siswa_id.kamar_id', readonly=True)
    halaqoh_id  = fields.Many2one('cdn.halaqoh', string='Halaqoh', related='siswa_id.halaqoh_id', readonly=True)
    musyrif_id  = fields.Many2one('hr.employee', string='Musyrif', related='siswa_id.musyrif_id', readonly=True)
    keperluan   = fields.Many2one('master.keterangan', string='Keperluan', readonly=False, required=False, tracking=True)
    lama_ijin   = fields.Char(string='Lama Izin', readonly=True, store=True, compute='_compute_lama_ijin')
    penjemput   = fields.Char(string='Penjemput', required=False)

    barcode     = fields.Char(string='Kartu Santri', readonly=False)

    has_permission = fields.Char(string="Has Permission", default='Tidak Ada')

    keluar_masuk = fields.Selection([
        ('keluar', 'Keluar'),
        ('masuk', 'Masuk'),
    ], string="Status Santri : ", required=True,)

    catatan_keamanan = fields.Text(string='Catatan', readonly=False)
    
    @api.onchange('keluar_masuk')
    def _onchange_keluar_masuk(self):
        """Mengubah tgl_kembali berdasarkan status keluar/masuk"""
        if self.keluar_masuk == 'masuk':
            out_permissions = False
            if self.siswa_id:
                out_permissions = self.env['cdn.perijinan'].search([
                    ('siswa_id', '=', self.siswa_id.id), 
                    ('state', '=', 'Permission'),
                    ('waktu_kembali', '=', False)
                ])
            
            if not out_permissions:
                self.tgl_kembali = self.tgl_ijin
            
                
        elif self.keluar_masuk == 'keluar':
            out_permissions = False
            if self.siswa_id:
                out_permissions = self.env['cdn.perijinan'].search([
                    ('siswa_id', '=', self.siswa_id.id), 
                    ('state', '=', 'Approved'),
                ])
            
            if not out_permissions:
                self.tgl_kembali = self.tgl_ijin + relativedelta(hours=5)


    @api.onchange('tgl_ijin', 'tgl_kembali', 'keperluan', 'penjemput')
    def _onchange_check_if_data_changed(self):
        if not self.perijinan_id:
            self.has_permission = 'Salah'
            return

        permission = self.perijinan_id
        if (self.tgl_ijin != permission.tgl_ijin or
            self.tgl_kembali != permission.tgl_kembali or
            self.keperluan != permission.keperluan or
            self.penjemput != permission.penjemput):
            self.has_permission = 'Salah'
        else:
            self.has_permission = 'Benar'

    @api.onchange('tgl_ijin', 'tgl_kembali')
    def _onchange_tanggal_ijin_kembali(self):
        if self.tgl_ijin and self.tgl_kembali and self.tgl_ijin > self.tgl_kembali:
            return {
                'warning': {
                    'title': "Perhatian!",
                    'message': "Tanggal kembali tidak boleh sebelum tanggal izin.",
                }
            }
            
    @api.depends('tgl_ijin', 'tgl_kembali')
    def _compute_lama_ijin(self):
        for record in self:
            if record.tgl_ijin and record.tgl_kembali:
                delta = record.tgl_kembali - record.tgl_ijin
                
                # Hitung hari, jam, dan menit
                total_menit = int(delta.total_seconds() / 60)
                hari = total_menit // (24 * 60)
                sisa_menit = total_menit % (24 * 60)
                jam = sisa_menit // 60
                menit = sisa_menit % 60
                
                # Format string untuk menampilkan hari, jam, menit
                record.lama_ijin = f"{hari} hari {jam} jam {menit} menit"    
    
    
    def action_button(self):
        self.penjemput = "-"
        self.has_permission = "Salah"
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'name': 'Santri Keluar/Masuk',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new', 
        }

    @api.onchange('barcode')
    def _onchange_barcode(self):
        """Mengisi data berdasarkan barcode yang diinput"""
        if self.barcode:
            siswa = self.env['cdn.siswa'].search([('barcode_santri', '=', self.barcode)], limit=1)
            if not siswa:
                siswa = self.env['cdn.siswa'].search([('barcode', '=', self.barcode)], limit=1)

            if siswa:
                self.siswa_id = siswa.id
                out_permissions = self.env['cdn.perijinan'].search([
                    ('siswa_id', '=', siswa.id),
                    ('state', '=', 'Permission'),
                    ('waktu_kembali', '=', False)
                ])

                if out_permissions:
                    permission = out_permissions[0]
                    self.perijinan_id = permission.id
                    self.tgl_ijin = permission.tgl_ijin
                    self.tgl_kembali = permission.tgl_kembali
                    self.penjemput = permission.penjemput
                    self.keperluan = permission.keperluan.id if permission.keperluan else False
                    self.keluar_masuk = 'masuk'

                else:
                    approved_permissions = self.env['cdn.perijinan'].search([
                        ('siswa_id', '=', siswa.id),
                        ('state', '=', 'Approved'),
                        ('waktu_keluar', '=', False)
                    ])

                    if approved_permissions:
                        permission = approved_permissions[0]
                        self.perijinan_id = permission.id
                        self.tgl_ijin = permission.tgl_ijin
                        self.tgl_kembali = permission.tgl_kembali
                        self.penjemput = permission.penjemput
                        self.keperluan = permission.keperluan.id if permission.keperluan else False
                        self.keluar_masuk = 'keluar'
                    else:
                        self.perijinan_id = False
                        self.keluar_masuk = 'keluar'

                        if self.__class__._last_keperluan_id:
                            keperluan = self.env['master.keterangan'].browse(self.__class__._last_keperluan_id)
                            self.keperluan = self.__class__._last_keperluan_id if keperluan.exists() else False
                        else:
                            self.keperluan = False
                        
                        if self.__class__._last_penjemput:
                            self.penjemput = self.__class__._last_penjemput
                        
                        if self.__class__._last_tgl_kembali:
                            self.tgl_kembali = self.__class__._last_tgl_kembali
                        else:
                            self.tgl_kembali = self.tgl_ijin + relativedelta(hours=5)

            else:
                # Jika barcode tidak ditemukan
                barcode_sementara = self.barcode
                self.barcode = False
                return {
                    'warning': {
                        'title': 'Perhatian !',
                        'message': f"Tidak dapat menemukan kartu santri dengan kode {barcode_sementara}"
                    }
                }


    @api.onchange('siswa_id')
    def _onchange_siswa_id(self):
        """Cek izin yang tersedia untuk santri"""

        if self.siswa_id:
            siswa = self.siswa_id 
            self.barcode = siswa.barcode_santri or siswa.barcode

            # 1. Cek dulu izin keluar yang belum kembali (masuk)
            out_permissions = self.env['cdn.perijinan'].search([
                ('siswa_id', '=', self.siswa_id.id), 
                ('state', '=', 'Permission'),
                ('waktu_kembali', '=', False)
            ])
            
            if out_permissions:
                permission = out_permissions[0]
                self.perijinan_id = permission.id
                self.tgl_ijin = permission.tgl_ijin
                self.tgl_kembali = permission.tgl_kembali
                self.penjemput = permission.penjemput
                self.keperluan = permission.keperluan.id if permission.keperluan else False
                self.keluar_masuk = 'masuk'
                self.has_permission = 'Benar'

            else:
                # 2. Jika tidak, cek izin yang sudah disetujui tapi belum keluar (keluar)
                approved_permissions = self.env['cdn.perijinan'].search([
                    ('siswa_id', '=', self.siswa_id.id), 
                    ('state', '=', 'Approved'),
                    ('waktu_keluar', '=', False)
                ])
                
                if approved_permissions:
                    permission = approved_permissions[0]
                    self.perijinan_id = permission.id
                    self.tgl_ijin = permission.tgl_ijin
                    self.tgl_kembali = permission.tgl_kembali
                    self.penjemput = permission.penjemput
                    self.keperluan = permission.keperluan.id if permission.keperluan else False
                    self.keluar_masuk = 'keluar'
                    self.has_permission = 'Benar' 
                else:
                    self.perijinan_id = False
                    self.keluar_masuk = 'keluar'
                    self.has_permission = 'Salah'

                    if self.__class__._last_keperluan_id:
                        keperluan = self.env['master.keterangan'].browse(self.__class__._last_keperluan_id)
                        self.keperluan = self.__class__._last_keperluan_id if keperluan.exists() else False
                    else:
                        self.keperluan = False
                    
                    if self.__class__._last_penjemput:
                        self.penjemput = self.__class__._last_penjemput

                    if self.__class__._last_tgl_kembali:
                        self.tgl_kembali = self.__class__._last_tgl_kembali
                    else:
                        self.tgl_kembali = self.tgl_ijin + relativedelta(hours=5)

        else:
            self.perijinan_id = False
            self.keluar_masuk = 'keluar'
            self.penjemput = False
            self.keperluan = False

            if self.keluar_masuk == 'masuk':
                self.tgl_kembali = self.tgl_ijin


    def toast_notification(self, pesan):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '❌ Gagal Menyimpan',
                'message': f'{pesan}',
                'type': 'danger',
                'sticky': False,
            }
        }
        
    def action_checkout(self):
        if not self.siswa_id:
            return self.toast_notification("Kolom Santri Belum Diisi")
        if not self.keperluan:
            return self.toast_notification("Kolom Keperluan Belum Diisi")
        if not self.penjemput:
            return self.toast_notification("Kolom Penjemput Belum Diisi")

        santri_name = self.siswa_id.name

        if self.keperluan:
            self.__class__._last_keperluan_id = self.keperluan.id
        if self.penjemput:
            self.__class__._last_penjemput = self.penjemput
        if self.tgl_kembali:
            self.__class__._last_tgl_kembali = self.tgl_kembali

        permission_vals = {
            'barcode': self.barcode,
            'siswa_id': self.siswa_id.id,
            'tgl_ijin': self.tgl_ijin,
            'tgl_kembali': self.tgl_kembali,
            'penjemput': self.penjemput or '-',
            'keperluan': self.keperluan.id,
            'catatan_keamanan': self.catatan_keamanan or '',
        }

        # Default tidak ada permission yang ditemukan
        existing_permission = False

        if self.keluar_masuk == 'keluar':
            existing_permission = self.env['cdn.perijinan'].search([
                ('siswa_id', '=', self.siswa_id.id),
                ('state', '=', 'Approved'),
                ('waktu_keluar', '=', False),
            ], limit=1)

            if existing_permission:
                # Bandingkan field apakah ada perubahan
                if (existing_permission.keperluan.id != self.keperluan.id or
                    existing_permission.penjemput != self.penjemput or
                    existing_permission.tgl_kembali != self.tgl_kembali):
                    # Field berbeda ➔ Buat baru
                    permission_vals.update({
                        'state': 'Permission',
                        'waktu_keluar': fields.Datetime.now(),
                    })
                    permission = self.env['cdn.perijinan'].create(permission_vals)
                    self.perijinan_id = permission
                else:
                    # Field sama ➔ Update existing
                    self.perijinan_id = existing_permission
                    self.perijinan_id.write({
                        'state': 'Permission',
                        'waktu_keluar': fields.Datetime.now(),
                    })
            else:
                # Tidak ada izin lama ➔ buat baru
                permission_vals.update({
                    'state': 'Permission',
                    'waktu_keluar': fields.Datetime.now(),
                })
                permission = self.env['cdn.perijinan'].create(permission_vals)
                self.perijinan_id = permission

            message = f"Santri dengan nama {santri_name} keluar dari kawasan pondok."

        elif self.keluar_masuk == 'masuk':
            existing_permission = self.env['cdn.perijinan'].search([
                ('siswa_id', '=', self.siswa_id.id),
                ('state', '=', 'Permission'),
                ('waktu_keluar', '!=', False),
                ('waktu_kembali', '=', False),
            ], limit=1)

            if existing_permission:
                # Tidak perlu cek perubahan field, cukup update waktu_kembali
                self.perijinan_id = existing_permission
                self.perijinan_id.write({
                    'waktu_kembali': fields.Datetime.now(),
                    'state': 'Return',
                    'catatan_keamanan': self.catatan_keamanan or '',
                })
            else:
                # Tidak ada izin keluar ➔ buat baru sebagai Return
                permission_vals.update({
                    'state': 'Return',
                    'waktu_keluar': fields.Datetime.now(),  # optional kalau mau
                    'waktu_kembali': fields.Datetime.now(),
                })
                permission = self.env['cdn.perijinan'].create(permission_vals)
                self.perijinan_id = permission

            message = f"Santri dengan nama {santri_name} masuk ke kawasan pondok."

        else:
            return self.toast_notification("Jenis keluar/masuk tidak valid!")

        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {
                'message': message,
                'title': '✅ Data Tersimpan!',
                'sticky': False,
                'type': 'success',
                'timeout': 150000,
            }
        )

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'cdn.perijinan.checkout',
            'view_mode': 'form',
            'name': 'Santri Keluar/Masuk',
            'target': 'new',
            'context': self.env.context,
            'tag': 'reload',
        }



