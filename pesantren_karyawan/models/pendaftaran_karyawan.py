from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from odoo.tools import format_date
import uuid
import pytz
import random
import string
import logging

class rekrutKaryawan(models.Model):
    _name           = "ubig.karyawan"
    _description    = 'Draft Pendaftaran Karyawan'
    _inherit        = ['mail.thread', 'mail.activity.mixin']

    tgl_pendaftaran = fields.Date(string='Tanggal Pendaftaran', default=fields.Date.context_today)

    token           = fields.Char(string="Token")

    # kiri
    name            = fields.Char(string="Nama Lengkap Pelamar", required=True)
    email_kantor    = fields.Char(string="Email Kantor", required=True)
    no_telp         = fields.Char(string="Nomor HP")

    # kanan
    nip             = fields.Char(string="NIP")
    lembaga         = fields.Selection([
                        ('paud','PAUD'),
                        ('tk','TK'),
                        ('sdmi','SD / MI'),
                        ('smpmts','SMP / MTS'),
                        ('smama','SMA / MA'),
                        ('smk','SMK'),
                        ('nonformal','Non Formal'),
                        ('pondokputra','Pondok Putra'),
                        ('pondokputri','Pondok Putri'),
                        ('rtq','RTQ')], string='Lembaga')
    job_id   = fields.Many2one('hr.job', string="Jabatan Kerja", store=True)

    # Data Diri
    no_ktp          = fields.Char(string="No KTP")
    tgl_lahir       = fields.Date(string="Tanggal Lahir")
    tmp_lahir       = fields.Char(string="Tempat Lahir")
    gender          = fields.Selection(selection=[
                        ('L','Laki-laki'),('P','Perempuan')],
                        string="Jenis Kelamin",  help="")
    alamat          = fields.Text(string="Alamat")

    # Dokumen
    cv              = fields.Binary(string="CV", help="CV mencakup:Identitas pribadi nama, alamat, nomor telepon, email. Pengalaman kerja sebelumnya. Pendidikan terakhir. Keterampilan yang relevan dengan pekerjaan yang dilamar. Sertifikat atau penghargaan jika ada")
    ktp             = fields.Binary(string="Foto KTP", help="Untuk memverifikasi identitas Anda. Pastikan fotokopi identitas masih berlaku dan jelas.")
    pas_foto        = fields.Binary(string="Pas Foto Berwarna", help="Biasanya ukuran pas foto standar (3x4 cm atau 4x6 cm), sering kali diminta dalam format digital.")
    ijazah          = fields.Binary(string="Ijazah", help="Fotokopi atau dari ijazah pendidikan terakhir Anda.")
    sertifikat      = fields.Binary(string="Sertifikat/Dokumen Pendukung", help="Sertifikat pelatihan, kursus, atau keterampilan lainnya yang relevan dengan pekerjaan. Misalnya sertifikat bahasa asing, pelatihan teknis, atau sertifikat keterampilan lain. Opsional(Jika Ada)")
    surat_pengalaman= fields.Binary(string="Surat Pengalaman Kerja", help="Jika Anda sudah memiliki pengalaman kerja sebelumnya, Anda mungkin perlu mengunggah surat pengalaman kerja dari perusahaan sebelumnya. Surat ini biasanya mencakup durasi kerja, jabatan, dan deskripsi pekerjaan. Opsional(Jika Ada)")
    surat_kesehatan = fields.Binary(string="Surat Keterangan Sehat", help="Dokumen terkait kesehatan, seperti surat keterangan sehat dari dokter atau hasil pemeriksaan medis. Opsional(Jika Ada)")
    npwp            = fields.Binary(string="NPWP", help="Salinan NPWP Anda untuk keperluan administrasi perpajakan.")
    
    # State
    state = fields.Selection([
        ('draft', 'Draft'),
        ('terdaftar', 'Terdaftar'),
        ('seleksi', 'Seleksi'),
        ('diterima', 'Diterima'),
        ('ditolak', 'Ditolak'),
        ('batal', 'Batal'),
    ], string='Status', default='draft',
        track_visibility='onchange')
    
    @api.model
    def create(self, vals):
        # Generate UUID token
        vals['token'] = str(uuid.uuid4())

        record = super(rekrutKaryawan, self).create(vals)

        return record
    
    def action_terdaftar(self):
        self.state = 'terdaftar'

    def action_seleksi(self):
        self.state = 'seleksi'

    def action_diterima(self):
        self.state = 'diterima'

    def action_ditolak(self):
        self.state = 'ditolak'

    def action_batal(self):
        self.state = 'batal'

    def action_draft(self):
        # Optional: You can define additional actions for when "Draft" is clicked
        self.write({'state': 'draft'})

    def get_formatted_tanggal_lahir(self):
        if self.tgl_lahir:
            # Langsung gunakan strftime untuk format DD-MM-YYYY
            return self.tgl_lahir.strftime('%d-%m-%Y')
        return 'Tanggal tidak tersedia'






        