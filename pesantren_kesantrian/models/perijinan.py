from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class Perijinan(models.Model):
    _name = 'cdn.perijinan'
    _description = 'Data Perijinan Santri'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc' 

    name = fields.Char(string='Nama', readonly=True)
    tgl_ijin = fields.Datetime(string='Tgl Ijin', required=True,
        states={
            'Draft': [('readonly', False)],
            'Check': [('readonly', True)],
            'Approved': [('readonly', True)],
            'Rejected': [('readonly', True)],
            'Permission': [('readonly', True)],
            'Return': [('readonly', True)],
            'Overdue': [('readonly', True)],
        }, default=lambda self: fields.Datetime.now())

    tgl_kembali = fields.Datetime(string='Tgl Kembali', required=True,
        states={    
            'Draft': [('readonly', False)],
            'Check': [('readonly', False)],
            'Approved': [('readonly', True)],
            'Rejected': [('readonly', True)],
            'Permission': [('readonly', True)],
            'Return': [('readonly', True)],
            'Overdue': [('readonly', True)],
        },  default=lambda self: fields.Datetime.now() + relativedelta(days=1))
    
    waktu_keluar = fields.Datetime(string='Waktu Keluar', readonly=True)
    waktu_kembali = fields.Datetime(string='Waktu Kembali', readonly=True)

    penjemput = fields.Char(string='Penjemput', required=True,
        states={
            'Draft': [('readonly', False)],
            'Check': [('readonly', False)],
            'Approved': [('readonly', True)],
            'Rejected': [('readonly', True)],
            'Permission': [('readonly', True)],
            'Return': [('readonly', True)],
            'Overdue': [('readonly', True)],
        }) 
    siswa_id = fields.Many2one('cdn.siswa', string='Santri', required=True,
        states={
            'Draft': [('readonly', False)],
            'Check': [('readonly', True)],
            'Approved': [('readonly', True)],
            'Rejected': [('readonly', True)],
            'Permission': [('readonly', True)],
            'Return': [('readonly', True)],
            'Overdue': [('readonly', True)],
        }, ondelete='cascade')
    
    barcode = fields.Char(string='Kartu Santri', states= {
        'Draft': [('readonly', False)],
        'Check': [('readonly', True)],  
        'Approved': [('readonly', True)],
        'Rejected': [('readonly', True)],
        'Permission': [('readonly', True)],
        'Return': [('readonly', True)],
        'Overdue': [('readonly', True)],
    })
    
    kelas_id = fields.Many2one('cdn.ruang_kelas', string='Kelas',related='siswa_id.ruang_kelas_id', readonly=True)
    kamar_id = fields.Many2one('cdn.kamar_santri', string='Kamar', related='siswa_id.kamar_id', readonly=True)
    halaqoh_id = fields.Many2one('cdn.halaqoh', string='Halaqoh', related='siswa_id.halaqoh_id', readonly=True)
    musyrif_id = fields.Many2one('hr.employee', string='Musyrif', related='siswa_id.musyrif_id', readonly=True)
    
    foto_bukti = fields.Binary(string="Foto Bukti", attachment=True, readonly=False,states={
        'Draft': [('readonly', False)],
        'Check': [('readonly', False)],
        'Approved': [('readonly', True)],
        'Rejected': [('readonly', True)],
        'Permission': [('readonly', True)],
        'Return': [('readonly', True)],
        'Overdue': [('readonly', True)],
    })
    
    foto_bukti_filename = fields.Char(string="Nama File Foto Bukti", states={
        'Draft': [('readonly', False)],
        'Check': [('readonly', False)],
        'Approved': [('readonly', True)],
        'Rejected': [('readonly', True)],
        'Permission': [('readonly', True)],
        'Return': [('readonly', True)],
        'Overdue': [('readonly', True)],
    })

    catatan = fields.Text(string='Catatan', readonly=False,
        states={
            'Draft': [('readonly', False)],
            'Check': [('readonly', False)],
            'Approved': [('readonly', True)],
            'Rejected': [('readonly', True)],
            'Permission': [('readonly', True)],
            'Return': [('readonly', True)],
            'Overdue': [('readonly', True)],
        }) 
    
    catatan_keamanan = fields.Text(string='Catatan', readonly=False, 
        states={
            'Draft': [('readonly', False)],
            'Check': [('readonly', False)],
            'Approved': [('readonly', False)],
            'Rejected': [('readonly', False)],
            'Permission': [('readonly', False)],
            'Return': [('readonly', False)],
            'Overdue': [('readonly', True)],
        })
    
    keperluan = fields.Many2one('master.keterangan',string='Keperluan', required=True ,states={
            'Draft': [('readonly', False)], 
            'Check': [('readonly', False)],
            'Approved': [('readonly', True)],
            'Rejected': [('readonly', True)],
            'Permission': [('readonly', True)],
            'Return': [('readonly', True)],
            'Overdue': [('readonly', True)],
        }, tracking=True )
    
    company_id      = fields.Many2one('res.company', string='Lembaga', default=lambda self: self.env.company)

     # --- fields for overdue evidence ---
    # keterangan_terlambat = fields.Text("Keterangan Terlambat", states={
    #     # editable hanya saat Overdue (juga bisa diizinkan di Permission jika ingin)
    #     'Overdue': [('readonly', False)],
    # })
    # bukti_file = fields.Binary("Bukti Terlambat", attachment=True, states={
    #     'Overdue': [('readonly', False)],
    # })
    # bukti_filename = fields.Char("Nama File", states={
    #     'Overdue': [('readonly', False)],
    # })
    # is_bukti_submitted = fields.Boolean("Bukti Dikirim", default=False, readonly=True)

    lama_ijin = fields.Char(string='Lama Ijin', readonly=True, compute='_compute_lama_ijin', store=True)
    # jatuh_tempo = fields.Char(string='Terlambat', readonly=True, compute='_compute_jatuh_tempo', store=True)
    # cek_terlambat = fields.Boolean(string='Cek Terlambat', default=False, compute='_compute_jatuh_tempo', store=True)


    lama_ijin = fields.Char(
        string='Lama Ijin', 
        readonly=True, 
        compute='_compute_lama_ijin', 
        store=True
    )

    jatuh_tempo = fields.Char(
        string='Terlambat', 
        readonly=True, 
        compute='_compute_jatuh_tempo', 
        store=True
    )

    # cek_terlambat = fields.Boolean(string='Cek Terlambat', default=False, compute='_compute_jatuh_tempo', store=True)

    state = fields.Selection([
        ('Draft', 'Pengajuan'),
        ('Check', 'Diperiksa'),
        ('Approved', 'Disetujui'),
        ('Rejected', 'Ditolak'),
        ('Permission', 'Ijin Keluar'),
        ('Return', 'Kembali'),
        ('Overdue', 'Terlambat'),
    ], string='Status', default='Draft',
        track_visibility='onchange')
    
    musyrif_id = fields.Many2one(
        comodel_name='hr.employee', 
        string='Musyrif', 
        related='siswa_id.musyrif_id', 
        readonly=True, 
        store=True
    )   

    show_button_santri_masuk = fields.Boolean(compute='_compute_show_button_santri_masuk', store=False)

    @api.depends('state')
    def _compute_show_button_santri_masuk(self):
        for record in self:
            record.show_button_santri_masuk = record.state in ['Permission']

    def action_save_record(self):
        self.state = 'Draft'

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

    @api.onchange('waktu_kembali')
    def _onchange_waktu_kembali(self):
        for record in self:
            if record.waktu_kembali and not record.waktu_keluar:
                # Jika hanya ada waktu_kembali tanpa waktu_keluar
                # Maka isi tgl_kembali dengan nilai yang sama dengan tgl_ijin
                record.tgl_kembali = record.tgl_ijin


    @api.depends('tgl_ijin', 'tgl_kembali')
    def _compute_lama_ijin(self):
        for record in self:
            if record.tgl_ijin and record.tgl_kembali:
                # Hitung selisih waktu
                delta = record.tgl_kembali - record.tgl_ijin
                
                # Hitung hari, jam, dan menit
                total_menit = int(delta.total_seconds() / 60)
                hari = total_menit // (24 * 60)
                sisa_menit = total_menit % (24 * 60)
                jam = sisa_menit // 60
                menit = sisa_menit % 60
                
                # Format string untuk menampilkan hari, jam, menit
                record.lama_ijin = f"{hari} hari {jam} jam {menit} menit"

    # @api.depends('waktu_kembali', 'tgl_kembali')
    # def _compute_jatuh_tempo(self):
    #     for record in self:
    #         if record.waktu_kembali:
    #             # Hitung selisih waktu
    #             if record.tgl_kembali < record.waktu_kembali and record.tgl_kembali < record.waktu_kembali:
    #                 delta = record.waktu_kembali - record.tgl_kembali
                    
    #                 # Hitung hari, jam, dan menit
    #                 total_menit = int(delta.total_seconds() / 60)
    #                 hari = total_menit // (24 * 60)
    #                 sisa_menit = total_menit % (24 * 60)
    #                 jam = sisa_menit // 60
    #                 menit = sisa_menit % 60
                    
    #                 # Format string untuk menampilkan hari, jam, menit
    #                 record.jatuh_tempo = f"{hari} hari {jam} jam {menit} menit"
    #                 record.cek_terlambat = True
    #             else:
    #                 record.jatuh_tempo = "0 hari 0 jam 0 menit"
    #                 record.cek_terlambat = False

    @api.depends('waktu_kembali', 'tgl_kembali')
    def _compute_jatuh_tempo(self):
        for record in self:
            record.jatuh_tempo = "0 hari 0 jam 0 menit"
            if record.waktu_kembali and record.tgl_kembali:
                if record.waktu_kembali > record.tgl_kembali:
                    delta = record.waktu_kembali - record.tgl_kembali
                    total_menit = int(delta.total_seconds() / 60)
                    hari = total_menit // (24 * 60)
                    sisa_menit = total_menit % (24 * 60)
                    jam = sisa_menit // 60
                    menit = sisa_menit % 60
                    record.jatuh_tempo = f"{hari} hari {jam} jam {menit} menit"

    def action_checked(self):
        self.state = 'Check'
    def action_approved(self):
        self.state = 'Approved'
        
        # Cari user orang tua dari siswa terkait
        parent_user = self.env['res.users'].search([
            ('partner_id.child_ids', 'in', self.siswa_id.partner_id.id),
            ('groups_id', 'in', self.env.ref('pesantren_kesantrian.group_kesantrian_orang_tua').id),
        ], limit=1)

        if parent_user:
            self.message_post(
                body=f"Izin santri atas nama <b>{self.siswa_id.name}</b> telah <b>disetujui</b>.",
                partner_ids=[parent_user.partner_id.id],
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )

    def action_rejected(self):
        self.state = 'Rejected'
    def action_permission(self):
        self.state = 'Permission'
        self.waktu_keluar = fields.Datetime.now()
    def action_return(self):
        """Santri kembali ke pesantren"""
        for rec in self:
            rec.waktu_kembali = fields.Datetime.now()

            # kalau tidak ada waktu keluar, fallback ke tgl_ijin
            if not rec.waktu_keluar:
                rec.tgl_kembali = rec.tgl_ijin

            # langsung set Return, tanpa cek terlambat
            rec.state = 'Return'
            # rec.jatuh_tempo = "0 hari 0 jam 0 menit"
            # rec.cek_terlambat = False

       # action musyrif: upload/submit bukti (set is_bukti_submitted)
    # def action_submit_bukti(self):
    #     for rec in self:
    #         if rec.state != 'Overdue':
    #             raise UserError(_("Hanya record dengan status Terlambat yang bisa mengunggah bukti."))
    #         if not rec.keterangan_terlambat or not rec.bukti_file:
    #             raise UserError(_("Harap lengkapi keterangan dan bukti sebelum mengirim untuk verifikasi admin."))
    #         rec.is_bukti_submitted = True
    #         # kirim notifikasi ke admin (ganti group jika anda punya group admin lain)
    #         try:
    #             admin_users = self.env.ref('base.group_system').users
    #         except Exception:
    #             admin_users = self.env['res.users'].search([])  # fallback
    #         for user in admin_users:
    #             rec.message_post(
    #                 body=f"Musyrif telah mengunggah bukti keterlambatan santri {rec.siswa_id.name}. Mohon verifikasi.",
    #                 partner_ids=[user.partner_id.id],
    #                 message_type='notification',
    #                 subtype_xmlid='mail.mt_note',
    #             )
                
        # action admin: verifikasi bukti -> ubah status ke Return
    # def action_verify_by_admin(self):
    #     # hanya admin (group_system) yang bisa verifikasi — ganti sesuai kebutuhan
    #     if not self.env.user.has_group('base.group_system'):
    #         raise UserError(_("Hanya admin yang dapat melakukan verifikasi ini."))

    #     for rec in self:
    #         if rec.state != 'Overdue':
    #             raise UserError(_("Hanya izin dengan status Terlambat yang dapat diverifikasi."))
    #         # pastikan bukti dan keterangan ada
    #         if not rec.keterangan_terlambat or not rec.bukti_file:
    #             raise UserError(_("Tidak dapat memverifikasi: keterangan atau bukti belum lengkap."))
    #         # jika sudah lengkap, ubah jadi Return
    #         rec.state = 'Return'
    #         rec.message_post(body=f"Admin {self.env.user.name} menyetujui bukti keterlambatan. Status diubah menjadi Kembali.")            

    def _validate_tanggal_izin_kembali(self, vals=None):
        for record in self:
            tgl_ijin = vals.get('tgl_ijin') if vals and 'tgl_ijin' in vals else record.tgl_ijin
            tgl_kembali = vals.get('tgl_kembali') if vals and 'tgl_kembali' in vals else record.tgl_kembali

            # Jika string, konversi ke datetime
            if isinstance(tgl_ijin, str):
                tgl_ijin = fields.Datetime.from_string(tgl_ijin)
            if isinstance(tgl_kembali, str):
                tgl_kembali = fields.Datetime.from_string(tgl_kembali)

            if tgl_ijin and tgl_kembali and tgl_ijin > tgl_kembali:
                raise UserError("Tanggal kembali tidak boleh sebelum tanggal izin!.")


    def _validate_duplicate_tanggal_izin(self, vals=None):
        for record in self:
            # Ambil tgl_ijin dan siswa_id dari vals atau record
            tgl_ijin = vals.get('tgl_ijin') if vals and 'tgl_ijin' in vals else record.tgl_ijin
            siswa_id = vals.get('siswa_id') if vals and 'siswa_id' in vals else record.siswa_id.id

            # Jika tgl_ijin dalam bentuk string, konversi ke datetime
            if isinstance(tgl_ijin, str):
                try:
                    tgl_ijin = fields.Datetime.from_string(tgl_ijin)
                except Exception:
                    continue  # Lewati jika parsing gagal

            if not siswa_id or not tgl_ijin:
                continue  # Data tidak lengkap

            domain = [
                ('siswa_id', '=', siswa_id),
                ('tgl_ijin', '>=', tgl_ijin - timedelta(hours=1)),
                ('tgl_ijin', '<=', tgl_ijin + timedelta(hours=1)),
                ('id', '!=', record.id),
            ]

            duplicate = self.env['cdn.perijinan'].search(domain, limit=1)
            if duplicate:
                raise UserError(
                    f"Santri sudah memiliki izin lain dalam rentang waktu ±1 jam dari {tgl_ijin.strftime('%d-%m-%Y %H:%M')}."
                )

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('cdn.perijinan')
        temp_record = super(Perijinan, self).create(vals)
        temp_record._validate_duplicate_tanggal_izin(vals)
        temp_record._validate_tanggal_izin_kembali(vals)
        return temp_record


    # def write(self, vals):
    #     # proteksi: kalau ada permintaan ubah state Overdue -> Return, pastikan user admin & bukti lengkap
    #     for record in self:
    #         if 'state' in vals and vals.get('state') == 'Return' and record.state == 'Overdue':
    #             if not self.env.user.has_group('base.group_system'):
    #                 raise UserError(_("Hanya admin yang dapat merubah status Terlambat menjadi Kembali."))
    #             # cek apakah bukti/keterangan disertakan baik di vals atau record
    #             keterangan = vals.get('keterangan_terlambat', record.keterangan_terlambat)
    #             bukti = vals.get('bukti_file', record.bukti_file)
    #             if not keterangan or not bukti:
    #                 raise UserError(_("Tidak bisa ubah ke Kembali: keterangan atau bukti belum lengkap."))

    #         # juga jalankan validasi tanggal yang sudah ada
    #         if vals:
    #             record._validate_duplicate_tanggal_izin(vals)
    #             record._validate_tanggal_izin_kembali(vals)
    #     return super(Perijinan, self).write(vals)
    
    # @api.model
    # def cron_check_santri_terlambat(self):
    #     """Scheduled task to check if any students have not returned on time"""
    #     now = fields.Datetime.now()
    #     perijinan_terlambat = self.search([
    #         ('state', '=', 'Permission'),             # Masih dalam status "izin keluar"
    #         ('tgl_kembali', '<', now),                # Sudah melewati batas waktu kembali
    #         ('waktu_kembali', '=', False)             # Belum kembali
    #     ])
    #     try:
    #         admin_users = self.env.ref('base.group_system').users  # Ganti dengan group keamanan jika ada
    #     except Exception:
    #             admin_users = self.env['res.users'].search([])
                
    #     for rec in perijinan_terlambat:
    #         # Tandai terlambat
    #         # rec.cek_terlambat = True
    #         rec.write({
    #         'cek_terlambat': True,
    #         'state': 'Overdue'
    #         })
    #         # Kirim notifikasi ke semua admin
    #         for user in admin_users:
    #             rec.message_post(
    #                 body=f"Santri {rec.siswa_id.name} belum kembali sesuai jadwal!\nRencana Kembali: {rec.tgl_kembali.strftime('%d-%m-%Y %H:%M')}",
    #                 partner_ids=[user.partner_id.id],
    #                 message_type='notification',
    #                 subtype_xmlid='mail.mt_note',
    #             )
            
            
