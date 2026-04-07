# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class PilihAnakWizard(models.TransientModel):
    """
    Wizard untuk memilih anak (santri) untuk top-up saldo.
    Digunakan ketika orang tua memiliki lebih dari satu anak.
    """
    _name = 'smart.billing.pilih.anak.wizard'
    _description = 'Pilih Anak untuk Top-up'

    orangtua_id = fields.Many2one(
        'cdn.orangtua',
        string='Orang Tua',
        required=True
    )
    siswa_id = fields.Many2one(
        'cdn.siswa',
        string='Pilih Anak',
        required=True,
        domain="[('id', 'in', available_siswa_ids)]"
    )
    available_siswa_ids = fields.Many2many(
        'cdn.siswa',
        string='Available Siswa',
        compute='_compute_available_siswa'
    )

    # Selected siswa info
    siswa_va = fields.Char(
        string='VA Saku',
        compute='_compute_siswa_info'
    )
    siswa_saldo = fields.Char(
        string='Saldo Saat Ini',
        compute='_compute_siswa_info'
    )
    has_va = fields.Boolean(
        string='Has VA',
        compute='_compute_siswa_info'
    )

    @api.depends('orangtua_id')
    def _compute_available_siswa(self):
        for record in self:
            if record.orangtua_id:
                # Only show children who have VA
                siswa_with_va = record.orangtua_id.siswa_ids.filtered(
                    lambda s: s.partner_id and s.partner_id.va_saku
                )
                record.available_siswa_ids = siswa_with_va
            else:
                record.available_siswa_ids = False

    @api.depends('siswa_id')
    def _compute_siswa_info(self):
        for record in self:
            if record.siswa_id and record.siswa_id.partner_id:
                partner = record.siswa_id.partner_id
                record.siswa_va = partner.va_saku or '-'
                record.has_va = bool(partner.va_saku)

                saldo = record.siswa_id.saldo_uang_saku or 0
                record.siswa_saldo = f"Rp{saldo:,.0f}".replace(',', '.')
            else:
                record.siswa_va = '-'
                record.siswa_saldo = 'Rp0'
                record.has_va = False

    def action_continue(self):
        """Continue to top-up wizard with selected child"""
        self.ensure_one()

        if not self.siswa_id:
            raise UserError("Silakan pilih anak terlebih dahulu.")

        if not self.has_va:
            raise UserError(
                f"Anak {self.siswa_id.name} belum memiliki Virtual Account.\n"
                "Silakan hubungi admin pesantren."
            )

        return {
            'name': f'Top-up Saldo {self.siswa_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'smart.billing.topup.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.siswa_id.partner_id.id,
            }
        }
