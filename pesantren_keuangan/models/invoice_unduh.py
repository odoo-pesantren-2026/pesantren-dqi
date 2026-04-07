# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.http import request
import werkzeug.urls
import base64
from odoo.exceptions import UserError

class InvoiceDownloadWizard(models.TransientModel):
    _name = 'invoice.download.wizard'
    _description = 'Wizard Konfirmasi Unduh Faktur'

    invoice_id = fields.Many2one('account.move', string='Faktur', required=True)
    invoice_name = fields.Char(string='Nomor Faktur')
    user_type = fields.Selection([('finance', 'Pengguna Keuangan'),('parent', 'Orang Tua')], string='Tipe Pengguna', compute='_compute_user_type', store=True)
    message_text = fields.Char(string='Pesan', compute='_compute_message_text')
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        finance_group = self.env.ref('account.group_account_user', False) or self.env.ref('account.group_account_manager', False)
        if finance_group and finance_group.id in self.env.user.groups_id.ids:
            res['user_type'] = 'finance'
        else:
            res['user_type'] = 'parent'
        return res

    @api.depends()
    def _compute_user_type(self):
        """Menentukan tipe pengguna saat ini (keuangan atau orang tua)"""
        finance_group = self.env.ref('account.group_account_user', False) or self.env.ref('account.group_account_manager', False)
        for record in self:
            if finance_group and finance_group.id in self.env.user.groups_id.ids:
                record.user_type = 'finance'
            else:
                record.user_type = 'parent'
    
    @api.depends('user_type')
    def _compute_message_text(self):
        """Menghitung pesan yang akan ditampilkan berdasarkan tipe pengguna"""
        for record in self:
            if record.user_type == 'finance':
                record.message_text = 'Apakah Anda ingin membuka bukti transaksi ini sekarang?'
            else:
                record.message_text = 'Apakah Anda ingin mengunduh bukti transaksi ini sekarang?'
    
    def action_preview(self):
        """Aksi untuk melihat pratinjau faktur"""
        self.ensure_one()
        return self.invoice_id.with_context(force_website=True).preview_invoice()
    
    def action_download(self):
        """Aksi untuk mengunduh faktur"""
        self.ensure_one()
        
        # Jika pengguna keuangan, tampilkan PDF tanpa opsi unduh
        if self.user_type == 'finance':
            return {
                'type': 'ir.actions.act_url',
                'url': '/my/invoices/%s?report_type=pdf' % (self.invoice_id.id),
                'target': 'new',  # Membuka di tab/jendela baru
            }
        # Jika orang tua/pengguna lain, unduh PDF langsung
        else:
            return {
                'type': 'ir.actions.act_url',
                'url': '/my/invoices/%s?report_type=pdf&download=true' % (self.invoice_id.id),
                'target': 'self',
            }