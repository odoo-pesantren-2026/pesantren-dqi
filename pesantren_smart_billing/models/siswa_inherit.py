# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """
    Extend res.partner to add permanent VA fields for santri.
    """
    _inherit = 'res.partner'

    # Permanent VA for top-up (uang saku)
    va_saku = fields.Char(
        string='VA Saku (Permanen)',
        help='Nomor Virtual Account permanen untuk top-up saldo uang saku'
    )
    va_saku_bank = fields.Char(
        string='Bank VA Saku',
        help='Bank untuk VA permanen'
    )
    va_saku_provider = fields.Selection([
        ('dummy', 'Dummy'),
        ('bsi', 'BSI'),
        ('tki', 'TKI'),
    ], string='VA Provider')
    va_saku_expiry = fields.Date(
        string='VA Expiry',
        help='Tanggal kadaluarsa VA permanen'
    )
    va_saku_order_id = fields.Char(
        string='VA Order ID',
        help='Order ID saat VA dibuat'
    )


class CdnSiswa(models.Model):
    """
    Extend cdn.siswa to add smart billing integration.
    """
    _inherit = 'cdn.siswa'

    # Related VA fields from partner
    va_saku = fields.Char(
        related='partner_id.va_saku',
        string='VA Saku',
        readonly=False
    )
    va_saku_bank = fields.Char(
        related='partner_id.va_saku_bank',
        string='Bank VA Saku',
        readonly=False
    )
    va_saku_expiry = fields.Date(
        related='partner_id.va_saku_expiry',
        string='VA Expiry',
        readonly=False
    )

    # Transaction count for smart button
    smart_billing_transaction_count = fields.Integer(
        string='Smart Billing Transactions',
        compute='_compute_smart_billing_count'
    )

    @api.depends('partner_id')
    def _compute_smart_billing_count(self):
        for record in self:
            if record.partner_id:
                count = self.env['smart.billing.transaction'].search_count([
                    ('partner_id', '=', record.partner_id.id)
                ])
                record.smart_billing_transaction_count = count
            else:
                record.smart_billing_transaction_count = 0

    def action_create_permanent_va(self):
        """
        Create permanent VA for this santri.
        This VA can be used by parents to top-up any amount at any time.

        Requirements:
        - Santri must have NIS (used as customer_no for VA)
        - Santri must have partner_id
        """
        self.ensure_one()

        if not self.partner_id:
            raise UserError(
                "Santri harus memiliki data partner terlebih dahulu.")

        # Validate NIS - required for VA creation (used as customer number)
        if not self.nis:
            raise UserError(
                "Santri harus memiliki NIS terlebih dahulu.\n\n"
                "NIS digunakan sebagai nomor customer untuk Virtual Account.\n"
                "Silakan generate NIS dengan klik tombol 'Buat NIS' di header form."
            )

        # Check if already has VA
        if self.va_saku:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'VA Sudah Ada',
                    'message': f'Santri sudah memiliki VA: {self.va_saku} ({self.va_saku_bank})',
                    'type': 'warning',
                    'sticky': True,
                }
            }

        # Get provider
        provider = self._get_billing_provider()

        try:
            result = provider.create_permanent_va(self.partner_id)

            if result.get('success'):
                # Save VA to partner
                self.partner_id.write({
                    'va_saku': result['va_number'],
                    'va_saku_bank': result['va_bank'],
                    'va_saku_provider': provider.get_provider_code(),
                    'va_saku_expiry': result.get('expiry_time').date() if result.get('expiry_time') else False,
                    'va_saku_order_id': result.get('order_id'),
                })

                # Create transaction record
                self.env['smart.billing.transaction'].create({
                    'name': result.get('order_id', f"PERMVA-{self.nis}"),
                    'provider': provider.get_provider_code(),
                    'transaction_type': 'va_topup',
                    'state': 'active',  # 'pending', # Permanent VA is active immediately
                    'partner_id': self.partner_id.id,
                    'va_number': result['va_number'],
                    'va_bank': result['va_bank'],
                    'expiry_time': result.get('expiry_time'),
                    'provider_transaction_id': result.get('transaction_id'),
                    'provider_response': str(result.get('raw_response', {})),
                })

                _logger.info(
                    f"Permanent VA created for {self.name}: {result['va_number']}")

                # Show notification and reload form to display VA info
                self.env['bus.bus']._sendone(
                    self.env.user.partner_id,
                    'simple_notification',
                    {
                        'title': 'VA Permanen Berhasil Dibuat',
                        'message': f"Bank: {result['va_bank']}\nNo. VA: {result['va_number']}\nBerlaku hingga: {result.get('expiry_time').strftime('%d/%m/%Y') if result.get('expiry_time') else '1 Tahun'}\n\nOrang tua dapat top-up kapan saja dengan nominal bebas.",
                        'type': 'success',
                        'sticky': True,
                    }
                )
                # Reload form to show updated VA data
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'cdn.siswa',
                    'res_id': self.id,
                    'view_mode': 'form',
                    'target': 'current',
                }
            else:
                raise UserError(
                    f"Gagal membuat VA: {result.get('message', 'Unknown error')}")

        except Exception as e:
            _logger.error(f"Error creating permanent VA for {self.name}: {e}")
            raise UserError(f"Gagal membuat VA Permanen: {str(e)}")

    def action_renew_permanent_va(self):
        """
        Renew expired permanent VA.
        Creates a new VA with new expiry date.
        """
        self.ensure_one()

        if not self.va_saku:
            raise UserError(
                "Santri belum memiliki VA. Silakan buat VA terlebih dahulu.")

        # Check if really expired
        if self.va_saku_expiry and self.va_saku_expiry > fields.Date.today():
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'VA Masih Berlaku',
                    'message': f"VA masih berlaku hingga {self.va_saku_expiry.strftime('%d/%m/%Y')}.\n\nTidak perlu diperpanjang.",
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # Get provider
        provider = self._get_billing_provider()

        try:
            # Create new VA (will get new number and expiry)
            result = provider.create_permanent_va(self.partner_id)

            if result.get('success'):
                # Update VA on partner
                self.partner_id.write({
                    'va_saku': result['va_number'],
                    'va_saku_bank': result['va_bank'],
                    'va_saku_provider': provider.get_provider_code(),
                    'va_saku_expiry': result.get('expiry_time').date() if result.get('expiry_time') else False,
                    'va_saku_order_id': result.get('order_id'),
                })

                _logger.info(
                    f"Permanent VA renewed for {self.name}: {result['va_number']}")

                # Show notification and reload form to display updated VA info
                self.env['bus.bus']._sendone(
                    self.env.user.partner_id,
                    'simple_notification',
                    {
                        'title': 'VA Berhasil Diperpanjang',
                        'message': f"Bank: {result['va_bank']}\nNo. VA Baru: {result['va_number']}\nBerlaku hingga: {result.get('expiry_time').strftime('%d/%m/%Y') if result.get('expiry_time') else '1 Tahun'}\n\nJangan lupa kirim informasi VA baru ke orang tua!",
                        'type': 'success',
                        'sticky': True,
                    }
                )
                # Reload form to show updated VA data
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'cdn.siswa',
                    'res_id': self.id,
                    'view_mode': 'form',
                    'target': 'current',
                }
            else:
                raise UserError(
                    f"Gagal memperpanjang VA: {result.get('message', 'Unknown error')}")

        except Exception as e:
            _logger.error(f"Error renewing permanent VA for {self.name}: {e}")
            raise UserError(f"Gagal memperpanjang VA: {str(e)}")

    def is_va_expired(self):
        """Check if VA is expired"""
        self.ensure_one()
        if not self.va_saku_expiry:
            return False
        return self.va_saku_expiry < fields.Date.today()

    def action_view_smart_billing_transactions(self):
        """Open list of smart billing transactions for this santri"""
        self.ensure_one()

        return {
            'name': f'Transaksi Smart Billing - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'smart.billing.transaction',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.partner_id.id)],
            'context': {'create': False},
            'target': 'current',
        }

    def action_topup_smart_billing(self):
        """Open top-up wizard for this santri"""
        self.ensure_one()

        if not self.va_saku:
            raise UserError(
                f"Santri {self.name} belum memiliki Virtual Account (VA Saku).\n\n"
                "Silakan klik tombol 'Buat VA Permanen' terlebih dahulu."
            )

        return {
            'name': f'Top-up Saldo - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'smart.billing.topup.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.partner_id.id,
            }
        }

    def action_send_va_whatsapp(self):
        """
        Send VA information to parent via WhatsApp.
        Opens WhatsApp with pre-filled message containing VA details.
        """
        self.ensure_one()

        if not self.va_saku:
            raise UserError(
                f"Santri {self.name} belum memiliki Virtual Account.\n\n"
                "Silakan buat VA terlebih dahulu."
            )

        # Get parent phone number - cdn.orangtua uses _inherits from res.partner
        # so phone/mobile fields are accessed directly
        phone = None
        if self.orangtua_id:
            # orangtua_id inherits res.partner, so phone/mobile are direct fields
            phone = self.orangtua_id.mobile or self.orangtua_id.phone

        # Fallback to siswa's parent data (ayah_telp, ibu_telp, wali_telp)
        if not phone:
            phone = self.ayah_telp or self.ibu_telp or self.wali_telp

        if not phone:
            raise UserError(
                "Nomor telepon orang tua tidak ditemukan.\n\n"
                "Silakan lengkapi data orang tua terlebih dahulu."
            )

        # Clean phone number
        phone = phone.replace(' ', '').replace('-', '').replace('+', '')
        if phone.startswith('0'):
            phone = '62' + phone[1:]
        elif not phone.startswith('62'):
            phone = '62' + phone

        # Get school name
        company_name = self.env.company.name or 'Pesantren'

        # Format saldo
        saldo_str = f"Rp{self.saldo_uang_saku:,.0f}".replace(
            ',', '.') if self.saldo_uang_saku else "Rp0"

        # Create WhatsApp message
        message = f"""Assalamu'alaikum Wr. Wb.

Bapak/Ibu Orang Tua/Wali dari *{self.name}*,

Berikut informasi Virtual Account (VA) untuk top-up saldo uang saku:

*BANK:* {self.va_saku_bank or 'BSI'}
*NO. VA:* {self.va_saku}
*BERLAKU HINGGA:* {self.va_saku_expiry.strftime('%d/%m/%Y') if self.va_saku_expiry else '1 Tahun'}

*Saldo saat ini:* {saldo_str}

*Cara Top-up:*
1. Buka aplikasi BSI Mobile / M-Banking
2. Pilih menu Transfer > Virtual Account
3. Masukkan nomor VA: {self.va_saku}
4. Masukkan nominal top-up
5. Konfirmasi dan selesaikan pembayaran

Saldo akan otomatis bertambah setelah pembayaran berhasil.

Jazakumullah khairan katsira.
_Tim Keuangan {company_name}_"""

        # URL encode the message
        import urllib.parse
        encoded_message = urllib.parse.quote(message)
        whatsapp_url = f"https://wa.me/{phone}?text={encoded_message}"

        return {
            'type': 'ir.actions.act_url',
            'url': whatsapp_url,
            'target': 'new',
        }

    def action_send_va_bulk_whatsapp(self):
        """
        Send VA information to all selected santri's parents via WhatsApp.
        This is called from list view with multiple selections.
        """
        for record in self:
            if record.va_saku:
                try:
                    record.action_send_va_whatsapp()
                except UserError as e:
                    _logger.warning(
                        f"Could not send WA for {record.name}: {e}")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Kirim WhatsApp',
                'message': f'Membuka WhatsApp untuk {len(self.filtered(lambda s: s.va_saku))} santri yang memiliki VA.',
                'type': 'info',
            }
        }

    def _get_billing_provider(self):
        """Get the currently configured billing provider"""
        provider_code = self.env['ir.config_parameter'].sudo().get_param(
            'smart_billing.provider', 'dummy'
        )

        provider_map = {
            'dummy': 'smart.billing.provider.dummy',
            'bsi': 'smart.billing.provider.bsi',
            'tki': 'smart.billing.provider.tki',
        }

        model_name = provider_map.get(
            provider_code, 'smart.billing.provider.dummy')
        return self.env[model_name]
