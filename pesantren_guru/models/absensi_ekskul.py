from odoo import api, fields, models
from odoo.exceptions import UserError
import base64
import logging

_logger = logging.getLogger(__name__)


class AbsensiEkskul(models.Model):
    _name = 'cdn.absensi_ekskul'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Data Absensi Ekstrakurikuler'

    # Default & Domain Helper
    def _get_default_guru(self):
        user = self.env.user
        if user.has_group('base.group_system'):
            employee = self.env['hr.employee'].search(
                [('user_id', '=', user.id)], limit=1)
            return employee.id if employee else False
        if user.has_group('pesantren_guru.group_guru_staff') or user.has_group('pesantren_guru.group_guru_manager'):
            employee = self.env['hr.employee'].search(
                [('user_id', '=', user.id)], limit=1)
            if not employee:
                raise UserError(
                    "Akun Anda tidak terkait dengan data Guru. Silakan hubungi administrator.")
            return employee.id
        raise UserError(
            "Anda tidak memiliki izin untuk membuat absensi ekstrakurikuler.")

    def _get_domain_ekskul(self):
        if self.env.user.has_group('base.group_system'):
            return []  # No filter, access all ekskul records
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
        return [('penanggung_id', '=', employee.id)] if employee else [('id', '=', False)]

    # Fields
    search = fields.Char(string="Pencarian")
    name = fields.Date(
        string='Tanggal Absen',
        required=True,
        default=fields.Date.context_today,
        help="Tanggal pelaksanaan ekstrakurikuler"
    )

    fiscalyear_id = fields.Many2one(
        'cdn.ref_tahunajaran',
        string='Tahun Ajaran',
        readonly=True,
        default=lambda self: self.env.user.company_id.tahun_ajaran_aktif.id
    )
    guru = fields.Many2one(
        'hr.employee',
        string="Guru Pengampu",
        required=True,
        default=_get_default_guru,
        domain=lambda self: self.env['cdn.absensi_ekskul']._domain_guru(),
        compute='_compute_guru',
        readonly=True,
        store=True,
        help="Guru yang bertanggung jawab memimpin ekstrakurikuler ini"
    )

    def _domain_guru(self):
        admin_user_ids = self.env.ref('base.group_system').users.ids

        return [
            '|',
            ('user_id', 'in', admin_user_ids),
            ('jns_pegawai_ids.code', 'in', ['guru', 'superadmin'])
        ]

    @api.depends('ekskul_id')
    def _compute_guru(self):
        for record in self:
            if record.ekskul_id and record.ekskul_id.penanggung_id:
                record.guru = record.ekskul_id.penanggung_id.id
            elif not record.guru:
                employee = self.env['hr.employee'].search(
                    [('user_id', '=', self.env.uid)], limit=1)
                if employee:
                    record.guru = employee.id
                else:
                    raise UserError(
                        "Guru Pengampu tidak dapat ditentukan. Pastikan ekstrakurikuler memiliki Penanggung Jawab atau akun Anda terkait dengan data Guru.")

    penanggung_id = fields.Many2one(
        "hr.employee",
        string="Penanggung Jawab",
        readonly=True,
        help="Penanggung jawab ekskul, diisi otomatis dari ekskul"
    )
    ekskul_id = fields.Many2one(
        'cdn.pembagian_ekstra',
        string="Ekstrakurikuler",
        required=True,
        domain=lambda self: self._get_domain_ekskul()
    )
    absen_ids = fields.One2many(
        'cdn.absen_ekskul_line',
        'absen_id',
        string='Daftar Absensi'
    )
    states = fields.Selection([
        ('Proses', 'Proses'),
        ('Done', 'Selesai'),
    ], default='Proses', string='Status', tracking=True)
    row_number = fields.Integer(
        string='No', compute='_compute_row_number', store=False)
    company_id = fields.Many2one(
        'res.company', string='Lembaga', default=lambda self: self.env.company)

    def _compute_row_number(self):
        for index, record in enumerate(self):
            record.row_number = index + 1

    # Onchange: Filter ekskul berdasarkan guru
    @api.onchange('guru')
    def _onchange_guru(self):
        if self.guru:
            return {
                'domain': {
                    'ekskul_id': [('penanggung_id', '=', self.guru.id)]
                }
            }
        else:
            return {
                'domain': {
                    'ekskul_id': []
                }
            }

    # Onchange: Saat ekskul dipilih, isi siswa & sinkronkan guru/penanggung
    @api.onchange('ekskul_id')
    def _onchange_ekskul_id(self):
        """Mengisi absen_ids berdasarkan ekskul, hanya jika absen_ids kosong atau ekskul_id berubah."""
        if self.ekskul_id and (not self.absen_ids or self._origin.ekskul_id != self.ekskul_id):
            if not self.ekskul_id.penanggung_id:
                raise UserError(
                    "Ekstrakurikuler yang dipilih tidak memiliki Penanggung Jawab. Silakan lengkapi data ekstrakurikuler.")
            # Isi penanggung jawab dan pastikan guru terisi
            self.penanggung_id = self.ekskul_id.penanggung_id.id
            self.guru = self.ekskul_id.penanggung_id.id
            # Hapus semua baris absensi lama hanya jika perlu mengisi ulang
            absen_list = [(5, 0, 0)]
            siswa_list = self.ekskul_id.siswa_ids
            if not siswa_list:
                return {
                    'warning': {
                        'title': 'Perhatian',
                        'message': 'Tidak ada santri yang ditemukan untuk ekstrakurikuler tersebut.'
                    },
                    'value': {'absen_ids': [(5, 0, 0)]}
                }
            for siswa in siswa_list:
                permission = self.env['cdn.perijinan'].search([
                    ('siswa_id', '=', siswa.id),
                    ('state', '=', 'Permission')
                ], limit=1)
                if permission:
                    keperluan_name = permission.keperluan.name if permission.keperluan else 'Tidak ada keterangan'
                    waktu_keluar = self.format_datetime_indonesia(
                        permission.waktu_keluar) if permission.waktu_keluar else 'Tidak tercatat'
                    message = f"Santri Keluar pada {waktu_keluar}, karena {keperluan_name}"
                    # Validate foto_bukti
                    foto_bukti = False
                    try:
                        if permission.foto_bukti:
                            base64.b64decode(
                                permission.foto_bukti, validate=True)
                            foto_bukti = permission.foto_bukti
                    except Exception as e:
                        _logger.error(
                            f"Invalid foto_bukti for permission {permission.id} (siswa: {siswa.name}): {str(e)}"
                        )
                        foto_bukti = False
                    # Ambil nama file asli dari perijinan, atau generate jika kosong
                    if permission and permission.foto_bukti_filename:
                        nama_file = permission.foto_bukti_filename
                    elif permission and foto_bukti:
                        nama_file = f"Bukti_Izin_{siswa.nis}_{siswa.name}_{permission.name}.jpg"
                    else:
                        nama_file = False
                    absen_list.append((0, 0, {
                        'siswa_id': siswa.id,
                        'kehadiran': 'keluar',
                        'keterangan': message,
                        'keterangan_izin': foto_bukti,
                        'keterangan_izin_filename': nama_file,
                        'company_id': self.company_id.id,
                    }))
                else:
                    absen_list.append((0, 0, {
                        'siswa_id': siswa.id,
                        'kehadiran': 'Hadir',
                        'company_id': self.company_id.id,
                    }))
            return {'value': {'absen_ids': absen_list}}
        return {}

    # Override create to ensure guru is set
    @api.model
    def create(self, vals):
        if 'ekskul_id' in vals:
            ekskul = self.env['cdn.pembagian_ekstra'].browse(vals['ekskul_id'])
            if not ekskul.penanggung_id:
                raise UserError(
                    "Ekstrakurikuler yang dipilih tidak memiliki Penanggung Jawab.")
            vals['guru'] = ekskul.penanggung_id.id
            vals['penanggung_id'] = ekskul.penanggung_id.id
        elif 'guru' not in vals or not vals['guru']:
            raise UserError("Guru Pengampu harus diisi.")
        return super(AbsensiEkskul, self).create(vals)

    # Button Actions
    def action_proses(self):
        self.states = 'Proses'

    def action_done(self):
        self.states = 'Done'

    # Opsional: Cegah edit jika sudah Done
    def write(self, vals):
        for rec in self:
            if rec.states == 'Done' and any(field in vals for field in ['ekskul_id', 'absen_ids']):
                raise UserError(
                    "Tidak dapat mengubah absensi yang sudah Selesai.")
        return super(AbsensiEkskul, self).write(vals)

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


class AbsenEkskulLine(models.Model):
    _name = 'cdn.absen_ekskul_line'
    _description = 'Baris Absensi Ekstrakurikuler'

    absen_id = fields.Many2one(
        'cdn.absensi_ekskul', string='Absen', ondelete='cascade')
    tanggal = fields.Date(
        string='Tanggal', related='absen_id.name', readonly=True, store=True)
    siswa_id = fields.Many2one(
        'cdn.siswa',
        string='Siswa',
        ondelete='cascade',
        domain="[('id', 'in', allowed_siswa_ids)]"
    )
    allowed_siswa_ids = fields.Many2many(  # Diubah ke Many2many untuk konsistensi dengan domain
        'cdn.siswa',
        compute='_compute_allowed_siswa',
        string='Siswa yang Diizinkan'
    )
    name = fields.Char(string='Nama', related='siswa_id.name',
                       readonly=True, store=True)
    nis = fields.Char(string='NIS', related='siswa_id.nis',
                      readonly=True, store=True)
    panggilan = fields.Char(
        string='Nama Panggilan', related='siswa_id.namapanggilan', readonly=True, store=True)
    keterangan_izin = fields.Binary(string='Foto Bukti', attachment=True)
    keterangan_izin_filename = fields.Char(string="Nama File Foto")
    kehadiran = fields.Selection([
        ('Hadir', 'Hadir'),
        ('Izin', 'Izin'),
        ('keluar', 'Izin Keluar'),
        ('Sakit', 'Sakit'),
        ('Alpa', 'Alpa'),
    ], string='Kehadiran', required=True, default='Hadir')
    keterangan = fields.Char(string="Keterangan")
    guru = fields.Many2one('hr.employee', string="Guru",
                           related='absen_id.guru')
    ekskul = fields.Many2one('cdn.pembagian_ekstra',
                             string="Ekskul", related='absen_id.ekskul_id')
    row_number = fields.Integer(
        string='No', compute='_compute_row_number', store=False)
    company_id = fields.Many2one(
        'res.company', string='Lembaga', related='absen_id.company_id', store=True)

    def _compute_row_number(self):
        for index, record in enumerate(self):
            record.row_number = index + 1

    def action_view_permission(self):
        """Buka form perijinan aktif siswa"""
        self.ensure_one()
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
                    'title': '❌ Tidak Ditemukan',
                    'message': 'Santri tidak dalam status izin keluar.',
                    'type': 'warning',
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

    @api.depends('absen_id.ekskul_id')
    def _compute_allowed_siswa(self):
        for record in self:
            if record.absen_id.ekskul_id:
                siswa_ids = record.absen_id.ekskul_id.siswa_ids.ids
                record.allowed_siswa_ids = [(6, 0, siswa_ids)]
            else:
                record.allowed_siswa_ids = [(5, 0, 0)]

    @api.onchange('siswa_id')
    def _onchange_siswa_id(self):
        """Cek perijinan saat siswa dipilih"""
        if self.siswa_id:
            permission = self.env['cdn.perijinan'].search([
                ('siswa_id', '=', self.siswa_id.id),
                ('state', '=', 'Permission')
            ], limit=1)
            if permission:
                self.kehadiran = 'keluar'
                keperluan = permission.keperluan.name or 'Tidak ada keterangan'
                waktu_keluar = self.format_datetime_indonesia(
                    permission.waktu_keluar)
                self.keterangan = f"Santri Keluar pada {waktu_keluar}, karena {keperluan}"
            else:
                self.kehadiran = 'Hadir'
                self.keterangan = False

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
