from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from odoo.tools import format_date
import uuid
import pytz
import random
import string
import logging


class inheritKarywan(models.Model):
    _inherit = ['hr.employee']
    _description = 'Inherit Karyawan'

    tgl_pendaftaran = fields.Date(
        string='Tanggal Pendaftaran', default=fields.Date.context_today)

    token = fields.Char(string="Token")

    # Data Diri
    no_ktp = fields.Char(string="No KTP")
    tgl_lahir = fields.Date(string="Tanggal Lahir")
    tmp_lahir = fields.Char(string="Tempat Lahir")
    alamat = fields.Text(string="Alamat")
    jk = fields.Selection(selection=[
        ('L', 'Laki-laki'), ('P', 'Perempuan')],
        string="Jenis Kelamin",  help="")

    # Dokumen
    cv = fields.Binary(string="CV", help="CV mencakup:Identitas pribadi nama, alamat, nomor telepon, email. Pengalaman kerja sebelumnya. Pendidikan terakhir. Keterampilan yang relevan dengan pekerjaan yang dilamar. Sertifikat atau penghargaan jika ada")
    ktp = fields.Binary(
        string="Foto KTP", help="Untuk memverifikasi identitas Anda. Pastikan fotokopi identitas masih berlaku dan jelas.")
    pas_foto = fields.Binary(string="Pas Foto Berwarna",
                             help="Biasanya ukuran pas foto standar (3x4 cm atau 4x6 cm), sering kali diminta dalam format digital.")
    ijazah = fields.Binary(
        string="Ijazah", help="Fotokopi atau dari ijazah pendidikan terakhir Anda.")
    sertifikat = fields.Binary(string="Sertifikat/Dokumen Pendukung",
                               help="Sertifikat pelatihan, kursus, atau keterampilan lainnya yang relevan dengan pekerjaan. Misalnya sertifikat bahasa asing, pelatihan teknis, atau sertifikat keterampilan lain. Opsional(Jika Ada)")
    surat_pengalaman = fields.Binary(
        string="Surat Pengalaman Kerja", help="Jika Anda sudah memiliki pengalaman kerja sebelumnya, Anda mungkin perlu mengunggah surat pengalaman kerja dari perusahaan sebelumnya. Surat ini biasanya mencakup durasi kerja, jabatan, dan deskripsi pekerjaan. Opsional(Jika Ada)")
    surat_kesehatan = fields.Binary(string="Surat Keterangan Sehat",
                                    help="Dokumen terkait kesehatan, seperti surat keterangan sehat dari dokter atau hasil pemeriksaan medis. Opsional(Jika Ada)")
    npwp = fields.Binary(
        string="NPWP", help="Salinan NPWP Anda untuk keperluan administrasi perpajakan.")

    def _update_jns_pegawai(self):
        """Set jns_pegawai based on job_id."""
        if self.job_id:
            job_name = self.job_id.name.lower()
            # Mapping job names to role codes
            role_map = {
                'musyrif': ['musyrif'],
                'ustadz': ['ustadz'],
                'guru': ['guru'],
                'keamanan': ['keamanan'],
                'kesehatan': ['kesehatan'],
                'guruquran': ['guruquran'],
                'musyrif,guruquran': ['musyrif', 'guruquran'],
                'guru,guruquran': ['guru', 'guruquran'],
                'musyrif,guru': ['musyrif', 'guru'],
                'musyrif,guru,guruquran': ['musyrif', 'guru', 'guruquran'],
            }

            codes = role_map.get(job_name, [])
            if codes:
                roles = self.env['cdn.jenis_pegawai'].search(
                    [('code', 'in', codes)])
                if roles:
                    self.jns_pegawai_ids = [(6, 0, roles.ids)]
                    return

            # If no mapping found or no roles found, clear the field
            self.jns_pegawai_ids = [(5, 0, 0)]

    @api.model
    def create(self, vals):
        """Override create to set jns_pegawai."""
        employee = super(inheritKarywan, self).create(vals)
        employee._update_jns_pegawai()
        return employee

    def write(self, vals):
        """Override write to update jns_pegawai."""
        res = super(inheritKarywan, self).write(vals)
        if 'job_id' in vals:  # Update only if job_id is modified
            self._update_jns_pegawai()
        return res
