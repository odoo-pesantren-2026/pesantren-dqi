from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from odoo.tools import format_date
import uuid
import pytz
import random
import string
import logging

class inheritRecruitment(models.Model):
    _inherit            = ['hr.candidate']
    _description        = 'Inherit Karyawan'

    tgl_pendaftaran     = fields.Date(string='Tanggal Pendaftaran', default=fields.Date.context_today, store=True)

    token               = fields.Char(string="Token", store=True)

    # kiri

    # kanan
    lembaga             = fields.Selection([
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
    job_id              = fields.Many2one('hr.job', string="Jabatan Kerja", store=True)

    # Data Diri
    no_ktp              = fields.Char(string="No KTP", store=True)
    tgl_lahir           = fields.Date(string="Tanggal Lahir", store=True)
    tmp_lahir           = fields.Char(string="Tempat Lahir", store=True)
    gender              = fields.Selection(selection=[
                            ('L','Laki-laki'),('P','Perempuan')],
                            string="Jenis Kelamin",  help="", store=True)
    alamat              = fields.Text(string="Alamat", store=True)

    # Dokumen
    cv                  = fields.Binary(string="CV", help="CV mencakup:Identitas pribadi nama, alamat, nomor telepon, email. Pengalaman kerja sebelumnya. Pendidikan terakhir. Keterampilan yang relevan dengan pekerjaan yang dilamar. Sertifikat atau penghargaan jika ada", store=True)
    ktp                 = fields.Binary(string="Foto KTP", help="Untuk memverifikasi identitas Anda. Pastikan fotokopi identitas masih berlaku dan jelas.", store=True)
    pas_foto            = fields.Binary(string="Pas Foto Berwarna", help="Biasanya ukuran pas foto standar (3x4 cm atau 4x6 cm), sering kali diminta dalam format digital.", store=True)
    ijazah              = fields.Binary(string="Ijazah", help="Fotokopi atau dari ijazah pendidikan terakhir Anda.", store=True)
    sertifikat          = fields.Binary(string="Sertifikat/Dokumen Pendukung", help="Sertifikat pelatihan, kursus, atau keterampilan lainnya yang relevan dengan pekerjaan. Misalnya sertifikat bahasa asing, pelatihan teknis, atau sertifikat keterampilan lain. Opsional(Jika Ada)", store=True)
    surat_pengalaman    = fields.Binary(string="Surat Pengalaman Kerja", help="Jika Anda sudah memiliki pengalaman kerja sebelumnya, Anda mungkin perlu mengunggah surat pengalaman kerja dari perusahaan sebelumnya. Surat ini biasanya mencakup durasi kerja, jabatan, dan deskripsi pekerjaan. Opsional(Jika Ada)", store=True)
    surat_kesehatan     = fields.Binary(string="Surat Keterangan Sehat", help="Dokumen terkait kesehatan, seperti surat keterangan sehat dari dokter atau hasil pemeriksaan medis. Opsional(Jika Ada)", store=True)
    npwp                = fields.Binary(string="NPWP", help="Salinan NPWP Anda untuk keperluan administrasi perpajakan.", store=True)
    
    def get_formatted_tanggal_lahir(self):
        if self.tgl_lahir:
            # Langsung gunakan strftime untuk format DD-MM-YYYY
            return self.tgl_lahir.strftime('%d-%m-%Y')
        return 'Tanggal tidak tersedia'
    
    @api.model
    def create(self, vals):
        # Generate UUID token
        vals['token'] = str(uuid.uuid4())

        record =  super(inheritRecruitment, self).create(vals)
        return record
    
    def create_employee_from_candidate(self):
        self.ensure_one()
        self._check_interviewer_access()

        if not self.partner_id:
            if not self.partner_name:
                raise UserError(_('Please provide an candidate name.'))

            self.partner_id = self.env['res.partner'].create({
                'is_company': False,
                'name': self.partner_name,
                'email': self.email_from,
            })

        action = self.env['ir.actions.act_window']._for_xml_id('hr.open_view_employee_list')
        employee = self.env['hr.employee'].create(self._get_employee_create_vals())
        employee.user_id.write({
            'phone': self.partner_phone,
            'mobile': self.partner_phone,
        })
        action['res_id'] = employee.id
        return action

    def _get_employee_create_vals(self):
        self.ensure_one()
        address_id   = self.partner_id.address_get(['contact'])['contact']
        address_sudo = self.env['res.partner'].sudo().browse(address_id)
        return {
            'name'                  : self.partner_name or self.partner_id.display_name,
            'work_contact_id'       : self.partner_id.id,
            'private_street'        : address_sudo.street,
            'private_street2'       : address_sudo.street2,
            'private_city'          : address_sudo.city,
            'private_state_id'      : address_sudo.state_id.id,
            'private_zip'           : address_sudo.zip,
            'private_country_id'    : address_sudo.country_id.id,
            'private_phone'         : address_sudo.phone,
            'private_email'         : address_sudo.email,
            'lang'                  : address_sudo.lang,
            'address_id'            : self.company_id.partner_id.id,
            'phone'                 : self.partner_phone,
            'candidate_id'          : self.ids,
            'work_email'            : self.email_from,
            'lembaga'               : self.lembaga,
            'no_ktp'                : self.no_ktp,
            'job_id'                : int(self.job_id),
            'tgl_lahir'             : self.tgl_lahir,
            'tmp_lahir'             : self.tmp_lahir,
            'jk'                    : self.gender,
            'alamat'                : self.alamat,
            'cv'                    : self.cv,
            'ktp'                   : self.ktp,
            'pas_foto'              : self.pas_foto,
            'ijazah'                : self.ijazah,
            'sertifikat'            : self.sertifikat,
            'surat_pengalaman'      : self.surat_pengalaman,
            'surat_kesehatan'       : self.surat_kesehatan,
            'npwp'                  : self.npwp
        }

class HrJob(models.Model):
    _inherit = 'hr.job'

    salary_range = fields.Char(
        string="Rate Gaji", 
        help="Format: Rp 10.000 - Rp 20.000"
    )
    color = fields.Integer(string='Color', default=0)

    @api.onchange('salary_range')
    def _onchange_salary_range(self):
        if self.salary_range:
            # Validasi sederhana untuk memastikan format yang benar
            if not self.salary_range.startswith('Rp'):
                self.salary_range = f"Rp {self.salary_range}"
