# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models, api
from datetime import date, datetime
from odoo.exceptions import ValidationError

class AccountJournal(models.Model): 
    """Adding fields to account journal"""
    _inherit = "account.journal"

    wallet_journal = fields.Boolean(string="Jurnal Dompet",
                                    help="Jurnal Dompet")
class Donation(models.Model):
    _name = 'cdn.donation'
    _description = 'Tabel Donasi'

    name = fields.Char(string='Judul Sumbangan', required=True)
    description = fields.Html(string='Deskripsi')
    target_amount = fields.Float(
        string='Target Donasi', 
        help='Jumlah target donasi yang ingin dicapai'
    )
    collected_amount = fields.Float(
        string='Donasi Terkumpul', 
        compute='_compute_collected_amount', 
        store=True, 
        help='Jumlah donasi yang sudah terkumpul'
    )
    start_date = fields.Date(
        string='Tgl Mulai', 
        help='Tgl dimulainya penggalangan donasi'
    )
    end_date = fields.Date(
        string='Tgl Berakhir', 
        help='Tgl berakhirnya penggalangan donasi'
    )
    is_active = fields.Boolean(
        string='Masih Aktif', 
        compute='_compute_is_active', 
        store=False, 
        help='Status apakah penggalangan donasi masih aktif'
    )
    qr_image = fields.Binary(
        string='QR Code', 
        help='Upload QR Code yang akan digunakan untuk donasi'
    )
    bank_account = fields.Char(
        string='Rekening Bank', 
        help='Nomor rekening bank untuk menerima donasi jika tidak menggunakan QR Code',
        required=True
    )

    # Relasi ke donasi yang masuk
    donation_detail_ids = fields.One2many(
        'cdn.donation.detail', 
        'donation_id', 
        string='Detail Donasi', 
        help='Daftar donasi yang masuk untuk penggalangan ini'
    )

    @api.depends('donation_detail_ids.amount', 'donation_detail_ids.state')
    def _compute_collected_amount(self):
        """Menghitung jumlah donasi yang terkumpul hanya untuk status 'terverifikasi'."""
        for record in self:
            # Filter donation_detail_ids yang memiliki state = 'terverifikasi'
            verified_donations = record.donation_detail_ids.filtered(lambda d: d.state == 'terverifikasi')
            record.collected_amount = sum(verified_donations.mapped('amount'))

    @api.depends('start_date', 'end_date')
    def _compute_is_active(self):
        """Menghitung apakah donasi masih aktif berdasarkan tanggal mulai dan berakhir."""
        today = fields.Date.today()
        for record in self:
            record.is_active = bool(record.start_date and record.end_date and record.start_date <= today <= record.end_date)
    
    @api.onchange('start_date', 'end_date')
    def _onchange_dates(self):
        today = fields.Date.today()
        if self.start_date and self.start_date < today:
            self.start_date = False
            return {
                'warning': {
                    'title': "Invalid Tanggal",
                    'message': "Tanggal Mulai tidak boleh kurang dari hari ini.",
                }
            }

        if self.start_date and self.end_date and self.start_date >= self.end_date:
            self.end_date = False
            return {
                'warning': {
                    'title': "Invalid Tanggal",
                    'message': "Tanggal Mulai harus lebih awal dari Tanggal Berakhir.",
                }
            }

    # @api.model
    # def update_is_active(self):
    #     """Dijalankan secara otomatis setiap hari untuk memperbarui status is_active."""
    #     today = date.today()
    #     records = self.search([])
        
    #     for record in records:
    #         is_active = bool(record.start_date and record.end_date and record.start_date <= today <= record.end_date)
    #         if record.is_active != is_active:
    #             record.write({'is_active': is_active})
    
    # @api.model
    # def _search(self, domain, offset=0, limit=None, order=None, count=False):
    #     # Handle empty domain
    #     if not domain:
    #         return super(Donation, self)._search(domain, offset=offset, limit=limit, order=order, )
        
    #     # Periksa domain untuk mencegah error
    #     if isinstance(domain, list):
    #         new_domain = []
    #         for item in domain:
    #             if isinstance(item, (list, tuple)) and len(item) == 3:
    #                 field, operator, value = item
                            
    #                 # Handle tanggal
    #                 if field in ['start_date','end_date'] and operator == 'ilike' and value:
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
    #         valid_domain = []
    #         or_count = 0
            
    #         for item in domain:
    #             if isinstance(item, (list, tuple)) and len(item) == 3:
    #                 valid_domain.append(item)
    #             elif isinstance(item, str) and item in ['&', '|', '!']:
    #                 if item == '|':
    #                     or_count += 1
    #                 valid_domain.append(item)
            
    #         # Ensure proper balancing for OR operators
    #         if or_count > 0 and len(valid_domain) < (or_count * 2 + 1):
    #             # Domain is invalid, fall back to simple name search
    #             return super(Donation, self)._search([('name', 'ilike', '')], offset=offset, limit=limit, order=order, )
            
    #         domain = valid_domain if valid_domain else domain
        
    #     return super(Donation, self)._search(domain, offset=offset, limit=limit, order=order, )



class DonationDetail(models.Model):
    _name = 'cdn.donation.detail'
    _description = 'Detail Donasi'

    name = fields.Char(string='Nama Donatur', required=True)
    amount = fields.Float(string='Jumlah Donasi', required=True, help="Jumlah donasi yang diberikan")
    date = fields.Date(string='Tgl Donasi', default=fields.Date.today, required=True)
    donation_id = fields.Many2one(
    'cdn.donation',
    string='Terkait Sumbangan',
    help='Penggalangan donasi yang terkait dengan detail donasi ini',
    domain="[('start_date', '<=', date), ('end_date', '>=', date)]"
    )

    state = fields.Selection(
        string='Status',
        selection=[('draft', 'Draft'), ('terverifikasi', 'Terverifikasi')],
        default='draft'
    )
    bukti_image = fields.Binary(
        string='Bukti Transaksi', 
        help='Upload Bukti donasi anda'
    )
    # Field Related
    qr_image = fields.Binary(
        string='QR Code',
        related='donation_id.qr_image',
        readonly=True,
        store=False,
    )
    bank_account = fields.Char(
        string='Rekening Bank',
        related='donation_id.bank_account',
        readonly=True,
        store=False,
    )
    created_by = fields.Many2one(
        'res.users', 
        string='Dibuat Oleh', 
        default=lambda self: self.env.user, 
        readonly=True,
        help='Pengguna yang membuat detail donasi'
    )

    def action_set_to_terverifikasi(self):
        """Ubah status menjadi 'Terverifikasi'"""
        for record in self:
            record.state = 'terverifikasi'

    def action_set_to_draft(self):
        """Ubah status menjadi 'Draft'"""
        for record in self:
            record.state = 'draft'
            
    # @api.constrains('donation_id')
    # def _check_donation_active(self):
    #     """Cek apakah donasi masih aktif sebelum menambahkan donasi baru."""
    #     for record in self:
    #         if record.donation_id and not record.donation_id.is_active:
    #             raise ValidationError("Donasi ini sudah tidak aktif. Anda tidak dapat menambahkan donasi baru.")
    @api.onchange('date')
    def _onchange_date(self):
        """Update domain donation_id sesuai tanggal donasi"""
        if self.date:
            return {
                'domain': {
                    'donation_id': [
                        ('start_date', '<=', self.date),
                        ('end_date', '>=', self.date),
                    ]
                }
            }
        return {'domain': {'donation_id': []}}  
         

    # @api.model
    # def _search(self, domain, offset=0, limit=None, order=None, count=False):
    #     # Handle empty domain
    #     if not domain:
    #         return super(DonationDetail, self)._search(domain, offset=offset, limit=limit, order=order, )
        
    #     # Periksa domain untuk mencegah error
    #     if isinstance(domain, list):
    #         new_domain = []
    #         for item in domain:
    #             if isinstance(item, (list, tuple)) and len(item) == 3:
    #                 field, operator, value = item
                            
    #                 # Handle tanggal
    #                 if field in ['date'] and operator == 'ilike' and value:
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
    #         valid_domain = []
    #         or_count = 0
            
    #         for item in domain:
    #             if isinstance(item, (list, tuple)) and len(item) == 3:
    #                 valid_domain.append(item)
    #             elif isinstance(item, str) and item in ['&', '|', '!']:
    #                 if item == '|':
    #                     or_count += 1
    #                 valid_domain.append(item)
            
    #         # Ensure proper balancing for OR operators
    #         if or_count > 0 and len(valid_domain) < (or_count * 2 + 1):
    #             # Domain is invalid, fall back to simple name search
    #             return super(DonationDetail, self)._search([('name', 'ilike', '')], offset=offset, limit=limit, order=order, )
            
    #         domain = valid_domain if valid_domain else domain
        
    #     return super(DonationDetail, self)._search(domain, offset=offset, limit=limit, order=order, )