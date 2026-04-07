# -*- coding: utf-8 -*-

from asyncio.log import logger
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from datetime import date


class harga_khusus(models.Model):
    _name = 'cdn.harga_khusus'
    _description = 'Harga Khusus / Diskon Keringanan Biaya'

    name = fields.Many2one(comodel_name='cdn.komponen_biaya',
                           string='Komponen Biaya', required=True)
    siswa_id = fields.Many2one(
        comodel_name='cdn.siswa', string='Nama Siswa', required=True, ondelete='cascade')
    price = fields.Float(string='Harga', compute='_compute_price', store=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Partner ID', related='siswa_id.partner_id', store=True)
    disc_amount = fields.Integer(string='Diskon Rupiah', default=0)
    disc_persen = fields.Integer(string='Diskon Persen %', default=0)
    keterangan = fields.Char(string='Keterangan')

    @api.constrains('name', 'partner_id')
    def _check_unique_komponen_partner(self):
        for record in self:
            domain = [
                ('name', '=', record.name.id),
                ('partner_id', '=', record.partner_id.id),
                ('id', '!=', record.id)
            ]
            if self.search_count(domain):
                raise UserError(
                    'Data Komponen Biaya untuk Siswa tersebut sudah pernah dibuat!')

    # Pastikan expired_date juga menjadi dependensi
    @api.depends('name', 'expired_date')
    def _compute_price(self):
        for record in self:
            # Mengecek apakah harga berlaku berdasarkan tanggal kadaluarsa
            if record.expired_date and record.expired_date < date.today():
                record.price = 0  # Set harga menjadi 0 jika sudah kadaluarsa
            else:
                TahunAjaran = self.env.user.company_id.tahun_ajaran_aktif
                # Pastikan hanya satu record yang dikembalikan
                Biaya = TahunAjaran.biaya_ids.search(
                    [('name', '=', record.name.id)], limit=1)
                if Biaya:
                    record.price = Biaya.nominal
                else:
                    record.price = 0

    state = fields.Selection(
        string='Status',
        selection=[('berlaku', 'Berlaku'), ('expired', 'Kadaluarsa')],
        compute='_compute_state',
        store=True,
    )

    expired_date = fields.Date(
        string='Kadaluarsa',
        required=True,
        default=fields.Date.context_today,
    )

    @api.depends('expired_date')
    def _compute_state(self):
        for record in self:
            if record.expired_date and record.expired_date >= date.today():
                record.state = 'berlaku'
            else:
                record.state = 'expired'


class account_invoice(models.Model):
    _inherit = 'account.move'

    def _default_tahunajaran(self):
        return self.env['res.company'].search([('id', '=', 1)]).tahun_ajaran_aktif

    siswa_id = fields.Many2one(
        comodel_name='cdn.siswa', string='Santri', ondelete='cascade')
    invoice_date = fields.Date(
        string='Tgl Tagihan', required=True, default=fields.Date.context_today)
    student = fields.Boolean('Siswa')
    generate_invoice = fields.Char(string='Buat Tagihan')

    orangtua_id = fields.Many2one(comodel_name='cdn.orangtua', string='Orang Tua',
                                  related='siswa_id.orangtua_id', readonly=True, store=True)
    tahunajaran_id = fields.Many2one(comodel_name="cdn.ref_tahunajaran",
                                     string="Tahun Ajaran", default=_default_tahunajaran, readonly=True, store=True)
    komponen_id = fields.Many2one(comodel_name='cdn.komponen_biaya', string='Komponen Tagihan',
                                  readonly=True,  states={'draft': [('readonly', False)]})
    ruang_kelas_id = fields.Many2one(
        comodel_name='cdn.ruang_kelas', string='Ruang Kelas', readonly=True, store=True)
    periode_id = fields.Many2one(comodel_name='cdn.periode_tagihan', string='Periode Tagihan', readonly=True,  states={
                                 'draft': [('readonly', False)]}, domain="[('tahunajaran_id','=',tahunajaran_id)]")
    vendor_id = fields.Many2one(
        comodel_name='res.partner', string='Nama Vendor')
    vendor = fields.Boolean('Vendor', default=False)

    @api.onchange('vendor_id')
    def _onchange_vendor_id(self):
        if self.vendor_id:
            self.siswa_id = False
            self.tahunajaran_id = False
            self.ruang_kelas_id = False
            self.periode_id = False
            self.orangtua_id = False
            self.partner_id = self.vendor_id

    @api.onchange('siswa_id')
    def _onchange_siswa_id(self):
        if self.siswa_id:
            self.partner_id = self.siswa_id.partner_id
            self.ruang_kelas_id = self.siswa_id.ruang_kelas_id

    @api.depends('invoice_line_ids')
    def _add_line(self):
        for record in self:
            record.info_line = ', '.join(
                [line.name for line in record.invoice_line_ids])

    info_line = fields.Char(compute='_add_line', string='Invoice Line')

    _sql_constraints = [
        ('unique_invoice', 'unique(komponen_id, partner_id, periode_id)',
         'Invoice sudah pernah dibuat!')
    ]

    @api.onchange('periode_id')
    def _onchange_periode_id(self):
        if self.periode_id.end_date:
            self.invoice_date_due = self.periode_id.end_date


class account_move_line_inherit(models.Model):
    _inherit = 'account.move.line'

    discount_amount = fields.Float(string='Discount Nominal')

    @api.onchange('product_id')
    def _onchange_diskon_siswa(self):
        siswa = self.move_id.siswa_id
        komponen = self.product_id

        if siswa and komponen:
            harga_khusus = self.env['cdn.harga_khusus'].search([
                ('siswa_id', '=', siswa.id),
                ('name.product_id', '=', komponen.id),
                ('state', '=', 'berlaku')
            ], limit=1)

            if harga_khusus:
                harga_asli = self.price_unit
                if harga_khusus.disc_persen:
                    self.price_unit = harga_asli * \
                        (1 - (harga_khusus.disc_persen / 100))
                    self.discount_amount = harga_asli - self.price_unit
                elif harga_khusus.disc_amount:
                    self.price_unit = max(
                        harga_asli - harga_khusus.disc_amount, 0)
                    self.discount_amount = harga_khusus.disc_amount
