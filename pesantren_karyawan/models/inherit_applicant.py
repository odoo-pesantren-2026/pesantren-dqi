from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta, timezone
from odoo.tools import format_date
import uuid
import pytz
import random
import string
import logging
from datetime import date

_logger = logging.getLogger(__name__)

class inheritRecruitment(models.Model):
    _inherit            = ['hr.applicant']
    _description        = 'Inherit Karyawan'

    tgl_pendaftaran     = fields.Date(string='Tanggal Pendaftaran', default=fields.Date.context_today)

    token               = fields.Char(related="candidate_id.token")

    # kiri

    # kanan
    lembaga             = fields.Selection(related="candidate_id.lembaga")
    job_id              = fields.Many2one(related="candidate_id.job_id")
    nip                 = fields.Char(string='Nip')
    tgl_masuk           = fields.Date(string= "Tanggal Masuk", default=fields.Date.context_today)
    no_masuk            = fields.Integer(string= "No Masuk")

    # Data Diri
    no_ktp              = fields.Char(related="candidate_id.no_ktp")
    tgl_lahir           = fields.Date(related="candidate_id.tgl_lahir")
    tmp_lahir           = fields.Char(related="candidate_id.tmp_lahir")
    gender              = fields.Selection(related="candidate_id.gender")
    alamat              = fields.Text(related="candidate_id.alamat")

    # Dokumen
    cv                  = fields.Binary(string="CV", help="CV mencakup:Identitas pribadi nama, alamat, nomor telepon, email. Pengalaman kerja sebelumnya. Pendidikan terakhir. Keterampilan yang relevan dengan pekerjaan yang dilamar. Sertifikat atau penghargaan jika ada")
    ktp                 = fields.Binary(string="Foto KTP", help="Untuk memverifikasi identitas Anda. Pastikan fotokopi identitas masih berlaku dan jelas.")
    pas_foto            = fields.Binary(string="Pas Foto Berwarna", help="Biasanya ukuran pas foto standar (3x4 cm atau 4x6 cm), sering kali diminta dalam format digital.")
    ijazah              = fields.Binary(string="Ijazah", help="Fotokopi atau dari ijazah pendidikan terakhir Anda.")
    sertifikat          = fields.Binary(string="Sertifikat/Dokumen Pendukung", help="Sertifikat pelatihan, kursus, atau keterampilan lainnya yang relevan dengan pekerjaan. Misalnya sertifikat bahasa asing, pelatihan teknis, atau sertifikat keterampilan lain. Opsional(Jika Ada)")
    surat_pengalaman    = fields.Binary(string="Surat Pengalaman Kerja", help="Jika Anda sudah memiliki pengalaman kerja sebelumnya, Anda mungkin perlu mengunggah surat pengalaman kerja dari perusahaan sebelumnya. Surat ini biasanya mencakup durasi kerja, jabatan, dan deskripsi pekerjaan. Opsional(Jika Ada)")
    surat_kesehatan     = fields.Binary(string="Surat Keterangan Sehat", help="Dokumen terkait kesehatan, seperti surat keterangan sehat dari dokter atau hasil pemeriksaan medis. Opsional(Jika Ada)")
    npwp                = fields.Binary(string="NPWP", help="Salinan NPWP Anda untuk keperluan administrasi perpajakan.")

    tgl_wawancara_p_m   = fields.Datetime("Wawancara Dimulai", store=True)
    tgl_wawancara_p_a   = fields.Datetime("Wawancara Berakhir", store=True)
    tgl_wawancara_k_m   = fields.Datetime("Wawancara Dimulai", store=True)
    tgl_wawancara_k_a   = fields.Datetime("Wawancara Berakhir", store=True)

    batas_waktu_m       = fields.Datetime("Batas Waktu Mulai", store=True)
    batas_waktu_a       = fields.Datetime("Batas Waktu Berakhir", store=True)

    def get_formatted_tanggal_lahir(self):
        if self.tgl_lahir:
            # Langsung gunakan strftime untuk format DD-MM-YYYY
            return self.tgl_lahir.strftime('%d-%m-%Y')
        return 'Tanggal tidak tersedia'

    def convert_to_utc(self, vals):
        utc_tz = pytz.utc

        def convert_datetime(dt):
            if dt:
                # Pastikan datetime memiliki zona waktu (tzinfo)
                if not dt.tzinfo:
                    # Jika datetime tidak memiliki informasi zona waktu, anggap sudah dalam UTC
                    dt = utc_tz.localize(dt)  # Localize ke UTC jika datetime naive
                # Konversi ke UTC jika sudah ada zona waktu
                dt_utc = dt.astimezone(utc_tz)
                # Hapus informasi zona waktu (jadikan naive datetime)
                return dt_utc.replace(tzinfo=None)

        # Lakukan konversi untuk setiap field datetime yang ada
        for field_name in ['tgl_wawancara_p_m', 'tgl_wawancara_p_a', 'tgl_wawancara_k_m', 
                            'tgl_wawancara_k_a', 'batas_waktu_m', 'batas_waktu_a']:
            if field_name in vals:
                dt = vals[field_name]
                if dt:
                    # Pastikan datetime dalam format datetime
                    if isinstance(dt, str):
                        dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
                    # Konversi datetime ke UTC dan pastikan menjadi naive datetime
                    vals[field_name] = convert_datetime(dt)

        return vals

    def create(self, vals):
        # Generate UUID token
        vals['token'] = str(uuid.uuid4())
        vals = self.convert_to_utc(vals)

        return super(inheritRecruitment, self).create(vals)
    

    def write(self, vals):
        # Tambahkan user yang login jika belum ada di interviewer_ids
        if 'stage_id' in vals:
            # Jika stage_id berubah, tambahkan user yang mengubah ke interviewer_ids jika belum ada
            if self.env.uid not in self.interviewer_ids.ids:
                if 'interviewer_ids' not in vals:
                    vals['interviewer_ids'] = [(4, self.env.uid)]
                else:
                    vals['interviewer_ids'] = vals['interviewer_ids'] + [(4, self.env.uid)]

         # Pastikan user_id diisi dengan user yang sedang login jika belum ada
        if 'user_id' not in vals:
            vals['user_id'] = self.env.uid

        # Pastikan user_id yang ada di record adalah user yang login
        if self.user_id.id != self.env.uid:
            vals['user_id'] = self.env.uid
        vals = self.convert_to_utc(vals)


        return super(inheritRecruitment, self).write(vals)


    def aturMeeting(self):
        for record in self:
            if not record.active:
                continue  # Skip record yang tidak aktif

            allowed_stage_ids = [3, 4, 5]  # Tahapan wawancara pertama, wawancara kedua, penandatanganan kontrak
            if record.stage_id.id not in allowed_stage_ids:
                raise UserError("Pertemuan Hanya bisa dilakukan pada tahap Wawancara Pertama, Wawancara Kedua, atau Penandatanganan Kontrak.")

            
            # Ambil perusahaan yang aktif (current company)
            company = self.env.user.company_id

            # Ambil alamat perusahaan
            alamat_perusahaan = {
                'street'    : company.street or '',
                'street2'   : company.street2 or '',
                'city'      : company.city or '',
                'state'     : company.state_id.name if company.state_id else '',
                'zip'       : company.zip or '',
                'country'   : company.country_id.name if company.country_id else '',
            }

            # Gabungkan alamat menjadi satu string (opsional)
            alamat_lengkap = ', '.join(filter(None, [
                alamat_perusahaan['street'],
                alamat_perusahaan['street2'],
                alamat_perusahaan['city'],
                alamat_perusahaan['state'],
                alamat_perusahaan['zip'],
                alamat_perusahaan['country']
            ]))
            
            thn_sekarang = datetime.now().year

            # Inisialisasi tanggal dan waktu
            tgl_wawancara_m = ''
            tgl_wawancara_a = ''
            
            # Menentukan tanggal dan waktu berdasarkan stage_id
            if record.stage_id.id == 3:
                tgl_wawancara_m = record.tgl_wawancara_p_m
                tgl_wawancara_a = record.tgl_wawancara_p_a
            elif record.stage_id.id == 4:
                tgl_wawancara_m = record.tgl_wawancara_k_m
                tgl_wawancara_a = record.tgl_wawancara_k_a
            elif record.stage_id.id == 5:
                tgl_wawancara_m = record.batas_waktu_m
                tgl_wawancara_a = record.batas_waktu_a

            existing_event = None

            if tgl_wawancara_m and tgl_wawancara_a:
                # Cek apakah event dengan nama, tanggal mulai, dan tanggal selesai sudah ada
                existing_event = self.env['calendar.event'].search([
                    ('name', '=', record.stage_id.name),
                    ('start', '=', tgl_wawancara_m),
                    ('stop', '=', tgl_wawancara_a)
                ], limit=1)

            if existing_event:
                # Jika event sudah ada, periksa apakah partner sudah ada di dalam event tersebut
                existing_partner_ids = existing_event.partner_ids.mapped('id')
                
                if record.candidate_id.partner_id.id not in existing_partner_ids:
                    # Jika partner belum ada, tambahkan partner_id ke event yang ada
                    existing_event.write({
                        'partner_ids': [(4, record.candidate_id.partner_id.id)]  # Menambahkan partner baru
                    })
                    _logger.info(f"Partner {record.candidate_id.partner_id.name} ditambahkan ke event {existing_event.name}")
                else:
                    _logger.info(f"Partner {record.candidate_id.partner_id.name} sudah ada di event {existing_event.name}")
            else:
                # Jika event belum ada, buat event baru
                event_values = {
                    'name': record.stage_id.name,  # Judul acara
                    'start': tgl_wawancara_m,  # Tanggal mulai (mulai wawancara)
                    'stop': tgl_wawancara_a,  # Tanggal akhir (selesai wawancara)
                    'allday': False,  # Jika kamu ingin acara ini sepanjang hari
                    'user_id': record.user_id.id,  # Bisa diisi dengan user yang terkait (jika ada)
                    'partner_ids': [(4, record.candidate_id.partner_id.id)],  # Peserta acara (calon peserta)
                    'location': alamat_lengkap,  # Lokasi wawancara (jika diperlukan)
                }

                # Menambahkan event baru ke kalender
                calendar_event = self.env['calendar.event'].create(event_values)
                _logger.info(f"Event baru dibuat untuk {calendar_event.name} dengan partner {record.candidate_id.partner_id.name}")


  
    def kirim_email_applicant(self):
        for record in self:

            allowed_stage_ids = [3, 4, 5]  # Tahapan wawancara pertama, wawancara kedua, penandatanganan kontrak
            if record.stage_id.id not in allowed_stage_ids:
                raise UserError("Email hanya dapat dikirim pada tahapan Wawancara Pertama, Wawancara Kedua, atau Penandatanganan Kontrak.")

            # Ambil perusahaan yang aktif (current company)
            company = self.env.user.company_id

            # Ambil alamat perusahaan
            alamat_perusahaan = {
                'street'    : company.street or '',
                'street2'   : company.street2 or '',
                'city'      : company.city or '',
                'state'     : company.state_id.name if company.state_id else '',
                'zip'       : company.zip or '',
                'country'   : company.country_id.name if company.country_id else '',
            }

            # Gabungkan alamat menjadi satu string (opsional)
            alamat_lengkap = ', '.join(filter(None, [
                alamat_perusahaan['street'],
                alamat_perusahaan['street2'],
                alamat_perusahaan['city'],
                alamat_perusahaan['state'],
                alamat_perusahaan['zip'],
                alamat_perusahaan['country']
            ]))
            
            thn_sekarang = datetime.now().year

            # Inisialisasi tanggal dan waktu
            tgl_wawancara_m = ''
            tgl_wawancara_a = ''
            
            # Menentukan tanggal dan waktu berdasarkan stage_id
            if record.stage_id.id == 3:
                tgl_wawancara_m = record.tgl_wawancara_p_m
                tgl_wawancara_a = record.tgl_wawancara_p_a
            elif record.stage_id.id == 4:
                tgl_wawancara_m = record.tgl_wawancara_k_m
                tgl_wawancara_a = record.tgl_wawancara_k_a
            elif record.stage_id.id == 5:
                tgl_wawancara_m = record.batas_waktu_m
                tgl_wawancara_a = record.batas_waktu_a

            existing_event = None

            if tgl_wawancara_m and tgl_wawancara_a:
                # Cek apakah event dengan nama, tanggal mulai, dan tanggal selesai sudah ada
                existing_event = self.env['calendar.event'].search([
                    ('name', '=', record.stage_id.name),
                    ('start', '=', tgl_wawancara_m),
                    ('stop', '=', tgl_wawancara_a)
                ], limit=1)

            if existing_event:
                # Jika event sudah ada, periksa apakah partner sudah ada di dalam event tersebut
                existing_partner_ids = existing_event.partner_ids.mapped('id')
                
                if record.candidate_id.partner_id.id not in existing_partner_ids:
                    # Jika partner belum ada, tambahkan partner_id ke event yang ada
                    existing_event.write({
                        'partner_ids': [(4, record.candidate_id.partner_id.id)]  # Menambahkan partner baru
                    })
                    _logger.info(f"Partner {record.candidate_id.partner_id.name} ditambahkan ke event {existing_event.name}")
                else:
                    _logger.info(f"Partner {record.candidate_id.partner_id.name} sudah ada di event {existing_event.name}")
            else:
                # Jika event belum ada, buat event baru
                event_values = {
                    'name': record.stage_id.name,  # Judul acara
                    'start': tgl_wawancara_m,  # Tanggal mulai (mulai wawancara)
                    'stop': tgl_wawancara_a,  # Tanggal akhir (selesai wawancara)
                    'allday': False,  # Jika kamu ingin acara ini sepanjang hari
                    'user_id': record.user_id.id,  # Bisa diisi dengan user yang terkait (jika ada)
                    'partner_ids': [(4, record.candidate_id.partner_id.id)],  # Peserta acara (calon peserta)
                    'location': alamat_lengkap,  # Lokasi wawancara (jika diperlukan)
                }

                # Menambahkan event baru ke kalender
                calendar_event = self.env['calendar.event'].create(event_values)
                _logger.info(f"Event baru dibuat untuk {calendar_event.name} dengan partner {record.candidate_id.partner_id.name}")

            # Fungsi untuk memeriksa dan memformat tanggal
            def format_tanggal(tanggal):
                # Pastikan tanggal adalah objek datetime
                if isinstance(tanggal, datetime):
                    # Tentukan zona waktu Indonesia (WIB - UTC+7)
                    local_tz = pytz.timezone('Asia/Jakarta')

                    # Jika waktu tidak memiliki informasi zona waktu (naive datetime), anggap itu UTC
                    if tanggal.tzinfo is None:
                        utc_tz = pytz.utc
                        tanggal = utc_tz.localize(tanggal)

                    # Konversi waktu ke zona waktu Indonesia (WIB)
                    tanggal_local = tanggal.astimezone(local_tz)

                    # Format tanggal dan waktu
                    return tanggal_local.strftime('%d-%b-%Y pukul %H:%M')
                else:
                    return "Tanggal tidak diisi"


            # Format tanggal jika ada
            tgl_wawancara_m = format_tanggal(tgl_wawancara_m)
            tgl_wawancara_a = format_tanggal(tgl_wawancara_a)

            if record.stage_id.id == 3:
                # Jika stage_id adalah 3 (Wawancara)
                email_body_intro = "Selamat! Anda telah dijadwalkan untuk wawancara. Berikut adalah informasi wawancara Anda:"
                email_subject = "Wawancara"
            elif record.stage_id.id == 4:
                email_body_intro = "Selamat! Anda telah dijadwalkan untuk wawancara kedua. Berikut adalah informasi wawancara Anda:"
                email_subject = "Wawancara"
            elif record.stage_id.id == 5:
                email_body_intro = "Selamat! Anda telah memenuhi persyaratan untuk bekerja di pesantren kami. Kami menantikan kehadiran Anda untuk menghadiri wawancara dan membahas kontrak."
                email_subject = "Pertemuan"

            if record.gender == 'L':
                # Tindakan jika gender adalah Laki-laki
                # Misalnya, lakukan sesuatu atau set nilai tertentu
                gender = "Yth. Bpk "
            elif record.gender == 'P':
                # Tindakan jika gender adalah Perempuan
                gender = "Yth. Ibu "
            else:
                # Tindakan jika gender tidak memiliki nilai yang valid
                gender = "Yth "

   
            email_values = {
                'subject': "Informasi Perekrutan Pesantren Daarul Qur'an Istiqomah",
                'email_to': record.email_from,
                'body_html': f'''
                    <div style="background-color: #f5f8fa; padding: 30px; font-family: 'Arial', sans-serif;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden;">
                        <!-- Header -->
                        <div style="background-color: #005299; color: #ffffff; text-align: center; padding: 30px;">
                            <img src="https://i.ibb.co.com/SmWmBTW/SAVE-20220114-075750-removebg-preview-4.png" alt="Logo" style="margin:0 0 15px 0;box-sizing:border-box;vertical-align:middle;width: 80px; height: 80px; margin-bottom: 15px;" width="80">
                            <h1 style="margin: 0; font-size: 24px; font-weight: 600;">Pesantren Daarul Qur'an Istiqomah</h1>
                        </div>

                        <!-- Body -->
                        <div style="padding: 30px; color: #2d3748;">
                            <p style="margin: 0 0 20px; font-size: 16px; line-height: 1.6;">
                                Assalamualaikum Wr. Wb,
                            </p>
                            <p style="margin: 0 0 25px; font-size: 16px; line-height: 1.6;">
                                {gender}<strong>{record.candidate_id.partner_name}</strong>,<br>
                                {email_body_intro}
                            </p>

                            <div style="background-color: #f8fafc; padding: 25px; border-radius: 8px; margin: 25px 0; border: 1px solid #e2e8f0;">
                                <h3 style="margin: 0 0 15px; color: #005299; font-size: 18px;">Jadwal {email_subject}</h3>
                                <table style="width: 100%; border-collapse: collapse;">
                                    <tr>
                                        <td style="padding: 12px 8px; font-weight: 600; color: #4a5568; width: 120px;">Mulai:</td>
                                        <td style="padding: 12px 8px; color: #2d3748;">
                                            {tgl_wawancara_m}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 12px 8px; font-weight: 600; color: #4a5568;">Berakhir:</td>
                                        <td style="padding: 12px 8px; color: #2d3748;">
                                            {tgl_wawancara_a}
                                        </td>
                                    </tr>
                                </table>

                                <h3 style="margin: 25px 0 15px; color: #005299; font-size: 18px;">Posisi</h3>
                                <table style="width: 100%; border-collapse: collapse;">
                                    <tr>
                                        <td style="padding: 12px 8px; font-weight: 600; color: #4a5568; width: 120px;">Jabatan:</td>
                                        <td style="padding: 12px 8px; color: #2d3748;">
                                           {record.job_id.name if record.job_id else 'Belum diisi'}
                                        </td>
                                    </tr>
                                </table>

                                <h3 style="margin: 25px 0 15px; color: #005299; font-size: 18px;">Lembaga Pendidikan</h3>
                                <table style="width: 100%; border-collapse: collapse;">
                                    <tr>
                                        <td style="padding: 12px 8px; font-weight: 600; color: #4a5568; width: 120px;">Lembaga:</td>
                                        <td style="padding: 12px 8px; color: #2d3748;">
                                             { 
                                                'paud' if record.lembaga == 'paud' else
                                                'TK' if record.lembaga == 'tk' else
                                                'SD / MI' if record.lembaga == 'sdmi' else
                                                'SMP / MTS' if record.lembaga == 'smpmts' else
                                                'SMA / MA' if record.lembaga == 'smama' else
                                                'SMK' if record.lembaga == 'smk' else
                                                'Non Formal' if record.lembaga == 'nonformal' else
                                                'Pondok Putra' if record.lembaga == 'pondokputra' else
                                                'Pondok Putri' if record.lembaga == 'pondokputri' else
                                                'RTQ' if record.lembaga == 'rtq' else
                                                'Belum diisi' }
                                        </td>
                                    </tr>
                                </table>
                            </div>

                            <!-- Company Address Section -->
                            <div style="background-color: #f8fafc; padding: 25px; border-radius: 8px; margin: 25px 0; border: 1px solid #e2e8f0;">
                                <h3 style="margin: 0 0 15px; color: #005299; font-size: 18px;">Lokasi Wawancara</h3>
                                <p style="margin: 0; color: #4a5568; line-height: 1.6;">
                                   {alamat_lengkap}
                                </p>
                            </div>

                            <div style="margin: 30px 0; padding: 20px; background-color: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
                                <p style="margin: 0 0 15px; font-size: 16px; line-height: 1.6;">
                                    Jika Anda memerlukan bantuan atau informasi tambahan, silakan menghubungi tim kami di:
                                </p>
                                <ul style="margin: 0; padding-left: 20px; color: #4a5568; font-size: 16px; line-height: 1.6;">
                                    <li>0822 5207 9785</li>
                                </ul>
                            </div>
                        </div>

                        <!-- Footer -->
                        <div style="background-color: #f8fafc; text-align: center; padding: 20px; border-top: 1px solid #e2e8f0;">
                            <p style="font-size: 14px; color: #718096; margin: 0;">
                                &copy; {thn_sekarang} Pesantren Tahfizh Daarul Qur'an Istiqomah. All rights reserved.
                            </p>
                        </div>
                    </div>
                </div>
                ''',
                
            }

            # Kirim email
            mail = self.env['mail.mail'].sudo().create(email_values)
            mail.send()
            
    
   
    @api.model
    def create(self, vals):
        if 'no_masuk' not in vals or vals['no_masuk'] == 0:
            last_entry = self.search([], order='id desc', limit=1)
            vals['no_masuk'] = (last_entry.no_masuk or 0) + 1
        return super(inheritRecruitment, self).create(vals)


    def _generate_nip(self):
        if not self.tgl_lahir:
            _logger.warning("NIP tidak bisa dibuat: Tanggal Lahir kosong.")
            return False

        try:
            tahun_daftar = self.tgl_masuk.strftime('%m') if self.tgl_masuk else fields.Date.today().strftime('%m')
            tahun = self.tgl_masuk.strftime('%y') if self.tgl_masuk else fields.Date.today().strftime('%y')
            tgl_lahir_str = self.tgl_lahir.strftime('%d%m')
            tgl_pok = self.tgl_lahir.strftime('%Y')[-2:]
            nomor = str(self.no_masuk).zfill(3)
            nip = f"{nomor}.{tahun_daftar}.{tahun}.{tgl_lahir_str}{tgl_pok}"
            _logger.info(f"NIP yang dihasilkan: {nip}")
            return nip
        except Exception as e:
            _logger.error(f"Gagal membuat NIP: {e}")
            return False

    def create_employee_from_applicant(self):
        self.ensure_one()
        self._check_interviewer_access()

        if not self.partner_id:
            if not self.partner_name:
                raise UserError(_('Please provide a candidate name.'))

            self.partner_id = self.env['res.partner'].create({
                'is_company': False,
                'name': self.partner_name,
                'email': self.email_from,
            })

        nip = self._generate_nip()
        if not nip:
            raise UserError(_('Gagal membuat NIP. Periksa kembali tanggal lahir dan tanggal masuk.'))

        self.nip = nip

        employee_vals = self._get_employee_create_vals()
        employee_vals['nip'] = self.nip

        employee = self.env['hr.employee'].create(employee_vals)

        if employee.user_id:
            employee.user_id.write({
                'phone': self.partner_phone,
                'mobile': self.partner_phone,
            })

        action = self.env['ir.actions.act_window']._for_xml_id('hr.open_view_employee_list')
        action['res_id'] = employee.id
        return action


    def _get_employee_create_vals(self):
        self.ensure_one()
        address_id   = self.partner_id.address_get(['contact'])['contact']
        address_sudo = self.env['res.partner'].sudo().browse(address_id)
        return {
            'name'                  : self.partner_name or self.partner_id.display_name,
            'nip'                   : self.nip,
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
            'candidate_id'          : self.candidate_id,
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
            'npwp'                  : self.npwp,
        }

    def _check_interviewer_access(self):
        if self.env.user.has_group('hr_recruitment.group_hr_recruitment_interviewer') and not self.env.user.has_group('hr_recruitment.group_hr_recruitment_user'):
            raise UserError(_('You are not allowed to perform this action.'))
