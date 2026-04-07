# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class generate_invoice(models.TransientModel):
    _name = "generate.invoice"
    _description = "Wizard Generate Invoice Santri"

    # Default Tahun Ajaran dari Company
    def _default_tahunajaran(self):
        return self.env['res.company'].search([('id', '=', 1)]).tahun_ajaran_aktif

    # === Fields ===
    tahunajaran_id = fields.Many2one(
        comodel_name="cdn.ref_tahunajaran",
        string="Tahun Ajaran",
        default=_default_tahunajaran,
        readonly=True,
        store=True
    )

    komponen_id = fields.Many2one(
        'cdn.komponen_biaya',
        'Komponen Biaya',
        required=True
    )

    period_from = fields.Many2one(
        'cdn.periode_tagihan',
        'Bulan Awal',
        required=True,
        domain="[('tahunajaran_id','=',tahunajaran_id)]"
    )

    period_to = fields.Many2one(
        'cdn.periode_tagihan',
        'Bulan Akhir',
        required=True,
        domain="[('tahunajaran_id','=',tahunajaran_id)]"
    )

    angkatan_id = fields.Many2one(
        'cdn.ref_tahunajaran',
        'Siswa Angkatan',
        required=True
    )

    partner_ids = fields.Many2many(
        'cdn.siswa',
        'partner_rel',
        'siswa_id',
        'partner_id',
        'Siswa',
        required=True,
        domain="[('bebasbiaya', '=', False), ('ruang_kelas_id.tahunajaran_id', '=', tahunajaran_id)]"
    )

    name = fields.Float('Harga')

    kelas_id = fields.Many2many(
        'cdn.ruang_kelas',
        string='Kelas',
        domain="[('tahunajaran_id','=',angkatan_id), ('aktif_tidak', '=', 'aktif'), ('status','=','konfirm')]"
    )

    # === Onchange Methods ===

    @api.onchange('komponen_id', 'name')
    def _onchange_komponen_id(self):
        if self.komponen_id:
            harga = self.env['cdn.biaya_tahunajaran'].search([
                ('tahunajaran_id', '=', self.tahunajaran_id.id),
                ('name', '=', self.komponen_id.id)
            ], limit=1)
            if not harga:
                return {
                    'value': {'partner_ids': False, 'komponen_id': False, 'name': 0},
                    'warning': {
                        'title': 'Perhatian',
                        'message': 'Harga komponen belum ditentukan pada tahun ajaran.'
                    }
                }
            self.name = harga.nominal

    @api.onchange('kelas_id')
    def _onchange_kelas_id(self):
        current_kelas_ids = self.kelas_id.ids if self.kelas_id else []
        if not current_kelas_ids:
            self.partner_ids = [(6, 0, [])]
            return

        all_santri = []
        for kelas in self.kelas_id:
            valid_santri = kelas.siswa_ids.filtered(lambda s:
                                                    s.active and
                                                    not s.bebasbiaya and
                                                    s.ruang_kelas_id.tahunajaran_id.id == self.tahunajaran_id.id
                                                    )
            all_santri.extend(valid_santri.ids)

        self.partner_ids = [(6, 0, all_santri)] if all_santri else [(6, 0, [])]

    @api.onchange('angkatan_id')
    def _onchange_angkatan_id(self):
        self.kelas_id = [(6, 0, [])]
        self.partner_ids = [(6, 0, [])]
        return {
            'domain': {
                'partner_ids': [
                    ('bebasbiaya', '=', False),
                    ('ruang_kelas_id.tahunajaran_id', '=', self.tahunajaran_id.id),
                    ('active', '=', True)
                ]
            }
        }

    # === Pembuatan Invoice ===

    def create_invoice(self):
        if self.period_from.id > self.period_to.id:
            raise UserError(_("Bulan Awal lebih besar daripada Bulan Akhir!"))

        if not self.partner_ids:
            raise UserError(_("Siswa belum dipilih!"))

        obj_period = self.env['cdn.periode_tagihan']
        obj_invoice = self.env['account.move']
        produk = self.komponen_id.product_id
        gen_invoice = self.env['ir.sequence'].next_by_code('gen.invoice')

        period_ids = obj_period.search([
            ('id', '>=', self.period_from.id),
            ('id', '<=', self.period_to.id)
        ])

        for period in period_ids:
            for siswa in self.partner_ids:
                # === Validasi: Cek tagihan ganda ===
                existing_invoice = obj_invoice.search([
                    ('siswa_id', '=', siswa.id),
                    ('periode_id', '=', period.id),
                    ('komponen_id', '=', self.komponen_id.id),
                    ('move_type', '=', 'out_invoice'),
                    ('state', '!=', 'cancel')
                ], limit=1)

                if existing_invoice:
                    raise UserError(_(
                        f"Tagihan untuk santri {siswa.name}, komponen '{self.komponen_id.name}', dan periode '{period.name}' sudah pernah dibuat."
                    ))

                # === Lewat Validasi ===
                if not siswa.ruang_kelas_id or siswa.ruang_kelas_id.tahunajaran_id.id != self.tahunajaran_id.id:
                    continue

                disc_amount = 0
                disc_persen = 0
                qty = 1

                if siswa.harga_komponen:
                    disc = self.env['cdn.harga_khusus'].search([
                        ('siswa_id', '=', siswa.id),
                        ('name', '=', self.komponen_id.id)
                    ])
                    if disc:
                        disc_amount = disc.disc_amount
                        disc_persen = disc.disc_persen

                invoice_vals = {
                    'name': '/',
                    'move_type': 'out_invoice',
                    'invoice_origin': siswa.name,
                    'student': True,
                    'generate_invoice': gen_invoice,
                    'invoice_payment_term_id': False,
                    'komponen_id': self.komponen_id.id,
                    'tahunajaran_id': self.tahunajaran_id.id,
                    'orangtua_id': siswa.orangtua_id.id,
                    'ruang_kelas_id': siswa.ruang_kelas_id.id,
                    'siswa_id': siswa.id,
                    'partner_id': siswa.partner_id.id,
                    'partner_shipping_id': siswa.partner_id.id,
                    'currency_id': self.env.user.company_id.currency_id.id,
                    'fiscal_position_id': siswa.partner_id.property_account_position_id.id,
                    'invoice_date': period.start_date,
                    'company_id': self.env.user.company_id.id,
                    'periode_id': period.id,
                    'user_id': self.env.uid
                }

                res_invoice = obj_invoice.create(invoice_vals)

                invoice_line_vals = {
                    'name': produk.partner_ref,
                    'product_id': produk.id or False,
                    'discount': disc_persen,
                    'discount_amount': disc_amount,
                    'account_id': produk.property_account_income_id.id or produk.categ_id.property_account_income_categ_id.id,
                    'price_unit': self.name - disc_amount,
                    'quantity': qty,
                    'product_uom_id': produk.uom_id.id,
                }

                res_invoice.write({
                    'invoice_line_ids': [(0, 0, invoice_line_vals)]
                })

        # Redirect ke daftar invoice yang baru dibuat
        action = self.env.ref(
            'pesantren_base.action_tagihan_inherit_view').read()[0]
        action['domain'] = [('generate_invoice', '=', gen_invoice)]
        return action
