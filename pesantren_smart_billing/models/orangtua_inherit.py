# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class CdnOrangtua(models.Model):
    """
    Extend cdn.orangtua to add Smart Billing integration.
    """
    _inherit = 'cdn.orangtua'

    # Computed fields for smart buttons
    tagihan_belum_lunas_count = fields.Integer(
        string='Tagihan Belum Lunas',
        compute='_compute_tagihan_count'
    )
    smart_billing_transaction_count = fields.Integer(
        string='Transaksi Smart Billing',
        compute='_compute_smart_billing_count'
    )

    @api.depends('siswa_ids')
    def _compute_tagihan_count(self):
        """Count unpaid invoices for all children"""
        for record in self:
            partner_ids = record.siswa_ids.mapped('partner_id').ids
            if partner_ids:
                count = self.env['account.move'].sudo().search_count([
                    ('partner_id', 'in', partner_ids),
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted'),
                    ('payment_state', 'in', ['not_paid', 'partial']),
                ])
                record.tagihan_belum_lunas_count = count
            else:
                record.tagihan_belum_lunas_count = 0

    @api.depends('siswa_ids')
    def _compute_smart_billing_count(self):
        """Count Smart Billing transactions for all children"""
        for record in self:
            partner_ids = record.siswa_ids.mapped('partner_id').ids
            if partner_ids:
                count = self.env['smart.billing.transaction'].sudo().search_count([
                    ('partner_id', 'in', partner_ids),
                ])
                record.smart_billing_transaction_count = count
            else:
                record.smart_billing_transaction_count = 0

    def action_view_tagihan_anak(self):
        """Open list of unpaid invoices for children"""
        self.ensure_one()
        partner_ids = self.siswa_ids.mapped('partner_id').ids

        if not partner_ids:
            raise UserError("Anda tidak memiliki data anak yang terdaftar.")

        return {
            'name': 'Tagihan Anak',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [
                ('partner_id', 'in', partner_ids),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
            ],
            'context': {
                'search_default_not_paid': 1,
                'create': False,
            },
            'target': 'current',
        }

    def action_view_transaksi_smart_billing(self):
        """Open list of Smart Billing transactions for children"""
        self.ensure_one()
        partner_ids = self.siswa_ids.mapped('partner_id').ids

        if not partner_ids:
            raise UserError("Anda tidak memiliki data anak yang terdaftar.")

        return {
            'name': 'Transaksi Smart Billing',
            'type': 'ir.actions.act_window',
            'res_model': 'smart.billing.transaction',
            'view_mode': 'list,form',
            'domain': [('partner_id', 'in', partner_ids)],
            'context': {'create': False},
            'target': 'current',
        }

    def action_topup_smart_billing_anak(self):
        """
        Open wizard untuk top-up saldo anak.
        Orang tua bisa pilih anak mana yang mau di-topup.
        """
        self.ensure_one()

        if not self.siswa_ids:
            raise UserError("Anda tidak memiliki data anak yang terdaftar.")

        # Filter children who have VA
        siswa_with_va = self.siswa_ids.filtered(
            lambda s: s.partner_id and s.partner_id.va_saku)

        if not siswa_with_va:
            raise UserError(
                "Belum ada anak yang memiliki Virtual Account.\n\n"
                "Silakan hubungi admin pesantren untuk mendaftarkan VA."
            )

        # If only 1 child with VA, open wizard directly
        if len(siswa_with_va) == 1:
            siswa = siswa_with_va[0]
            return {
                'name': f'Top-up Saldo {siswa.name}',
                'type': 'ir.actions.act_window',
                'res_model': 'smart.billing.topup.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_partner_id': siswa.partner_id.id,
                }
            }

        # If multiple children, open selection wizard
        return {
            'name': 'Pilih Anak untuk Top-up',
            'type': 'ir.actions.act_window',
            'res_model': 'smart.billing.pilih.anak.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_orangtua_id': self.id,
            }
        }

    def action_view_va_anak(self):
        """
        View VA information for all children.
        """
        self.ensure_one()

        if not self.siswa_ids:
            raise UserError("Anda tidak memiliki data anak yang terdaftar.")

        # Build VA information
        va_info = []
        for siswa in self.siswa_ids:
            if siswa.partner_id and siswa.partner_id.va_saku:
                va_info.append({
                    'name': siswa.name,
                    'va': siswa.partner_id.va_saku,
                    'bank': siswa.partner_id.va_saku_bank or '-',
                })

        if not va_info:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Informasi VA',
                    'message': 'Belum ada anak yang memiliki Virtual Account.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # Format message
        message = "Virtual Account Anak:\n\n"
        for info in va_info:
            message += f"👤 {info['name']}\n"
            message += f"🏦 Bank: {info['bank']}\n"
            message += f"💳 VA: {info['va']}\n\n"

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Informasi VA',
                'message': message,
                'type': 'info',
                'sticky': True,
            }
        }
