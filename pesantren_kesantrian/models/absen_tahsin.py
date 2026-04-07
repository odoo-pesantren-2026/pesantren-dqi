from odoo import api, fields, models
from datetime import date, datetime
from odoo.exceptions import UserError


class AbsenTahsinQuran(models.Model):
    _name = 'cdn.absen_tahsin_quran'
    _description = 'Tabel Absen Tahsin Quran'

    # get domain
    def _domain_halaqoh_id(self):
        tahun_ajaran = self.env.user.company_id.tahun_ajaran_aktif.id
        user = self.env.user

        # Jika user adalah Manager Kesantrian -> lihat semua halaqoh di tahun ajaran aktif
        if self.env.user.has_group('pesantren_kesantrian.group_kesantrian_manager'):
            return [
                ('fiscalyear_id', '=', tahun_ajaran)
            ]
    # Cari employee dari user
        employee = self.env['hr.employee'].search(
            [('user_id', '=', user.id)], limit=1)

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

    def _get_domain_guru(self):
        return [
            ('jns_pegawai_ids.code', 'in', ['guruquran', 'guru'])
        ]

    def _get_default_guru(self):
        user = self.env.user
        if user.has_group('pesantren_guru.group_guru_staff'):
            user = self.env['hr.employee'].search([('user_id', '=', user.id)])
            return user.id
        return False

    name = fields.Date(string='Tgl Absen', required=True,
                       default=fields.Date.context_today, states={'Done': [('readonly', True)]})
    halaqoh_id = fields.Many2one('cdn.halaqoh', string='Halaqoh', required=True,
                                 domain=_domain_halaqoh_id, ondelete='cascade', states={'Done': [('readonly', True)]})
    ustadz_id = fields.Many2one('hr.employee', string='Ustadz', domain=_get_domain_guru,
                                default=_get_default_guru, required=True, states={'Done': [('readonly', True)]})
    fiscalyear_id = fields.Many2one('cdn.ref_tahunajaran', string='Tahun Ajaran', readonly=True,
                                    default=lambda self: self.env.user.company_id.tahun_ajaran_aktif.id, states={'Done': [('readonly', True)]})
    absen_ids = fields.One2many('cdn.absen_tahsin_quran_line', 'absen_id', string='Absen', states={
                                'Done': [('readonly', True)]})
    state = fields.Selection([
        ('Draft', 'Draft'),
        ('Proses', 'Proses'),
        ('Done', 'Selesai'),
    ], default='Draft', string='Status')
    penanggung_jawab_id = fields.Many2one(
        'hr.employee', string='Penanggung Jawab', related='halaqoh_id.penanggung_jawab_id', readonly=True, store=True)
    sesi_id = fields.Many2one('cdn.sesi_tahsin', string='Sesi', states={
                              'Done': [('readonly', True)]})
    keterangan = fields.Char(string='Keterangan')

    def action_proses(self):
        self.state = 'Proses'
        for absen in self.absen_ids:
            if absen.kehadiran == 'Hadir':
                tahsin_quran_vals = {
                    'tanggal': self.name,
                    'siswa_id': absen.siswa_id.id,
                    'halaqoh_id': self.halaqoh_id.id,
                    'ustadz_id': self.ustadz_id.id,
                    'sesi_tahsin_id': self.sesi_id.id,
                    'state': 'draft',
                }
                self.env['cdn.tahsin_quran'].create(tahsin_quran_vals)

    def action_confirm(self):
        self.state = 'Done'

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
                    waktu_keluar = self.format_datetime_indonesia(
                        permission.waktu_keluar) if permission.waktu_keluar else 'Tidak tercatat'
                    message = f"Santri Keluar pada {waktu_keluar}, karena {keperluan_name}".encode(
                    )

                    absen_ids.append((0, 0, {
                        'siswa_id': siswa.id,
                        'kehadiran': 'keluar',
                        'keterangan': message,
                    }))

                else:
                    absen_ids.append((0, 0, {
                        'siswa_id': siswa.id,
                        'kehadiran': 'Hadir'
                    }))

            ustadz = halaqoh.penanggung_jawab_id | halaqoh.pengganti_ids

            if not self.env.user.has_group('pesantren_kesantrian.group_kesantrian_manager'):
                ustadz = ustadz.filtered(lambda x: x.user_id == self.env.user)

            return {
                'domain': {
                    'ustadz_id': [('id', 'in', ustadz.ids)]
                },
                'value': {
                    'absen_ids': absen_ids,
                    'ustadz_id': ustadz[0].id if ustadz else False
                }
            }

    @api.model
    def default_get(self, fields_tree):
        tahun_ajaran = self.env['res.company'].search(
            [('id', '=', self.env.ref('base.main_company').id)]).tahun_ajaran_aktif.id
        if not tahun_ajaran:
            raise models.UserError('Tahun ajaran belum di set')
        return super().default_get(fields_tree)


class AbsenTahsinQuranLine(models.Model):
    _name = 'cdn.absen_tahsin_quran_line'
    _description = 'Tabel Absen Tahsin Quran Line'

    absen_id = fields.Many2one(
        'cdn.absen_tahsin_quran', string='Absen', ondelete='cascade')
    tanggal = fields.Date(string='Tgl Absen',
                          related='absen_id.name', readonly=True, store=True)
    halaqoh_id = fields.Many2one('cdn.halaqoh', string='Halaqoh',
                                 related='absen_id.halaqoh_id', readonly=True, store=True)
    siswa_id = fields.Many2one('cdn.siswa', string='Siswa', ondelete='cascade')
    name = fields.Char(string='Nama', related='siswa_id.name',
                       readonly=True, store=True)
    nis = fields.Char(string='NIS', related='siswa_id.nis',
                      readonly=True, store=True)
    panggilan = fields.Char(
        string='Nama Panggilan', related='siswa_id.namapanggilan', readonly=True, store=True)
    keterangan = fields.Char(string='Keterangan')
    keterangan_izin = fields.Char(string='Foto', store=True)
    kehadiran = fields.Selection([
        ('Hadir', 'Hadir'),
        ('Izin', 'Izin'),
        ('keluar', 'Izin Keluar'),
        ('Sakit', 'Sakit'),
        ('Alpa', 'Alpa'),
    ], string='Kehadiran', required=True)
    penanggung_jawab_id = fields.Many2one(
        'hr.employee', string='Penanggung Jawab', related='halaqoh_id.penanggung_jawab_id', readonly=True, store=True)

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
                    'title': '❌ Tidak Dapat Menemukan Data !',
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
