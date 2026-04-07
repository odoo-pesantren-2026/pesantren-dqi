# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Provider Selection
    smart_billing_provider = fields.Selection([
        ('dummy', 'Dummy Provider (Testing)'),
        ('bsi', 'BSI (Bank Syariah Indonesia)'),
        ('tki', 'TKI (Teknologi Kartu Indonesia)'),
    ], string='Smart Billing Provider',
        config_parameter='smart_billing.provider',
        default='dummy',
        help='Pilih provider untuk Smart Billing'
    )

    # Common Configuration
    smart_billing_server_key = fields.Char(
        string='Server Key / API Key',
        config_parameter='smart_billing.server_key',
        help='Server Key atau API Key dari provider'
    )
    smart_billing_client_key = fields.Char(
        string='Client Key / Secret Key',
        config_parameter='smart_billing.client_key',
        help='Client Key atau Secret Key dari provider'
    )
    smart_billing_merchant_id = fields.Char(
        string='Merchant ID / School ID',
        config_parameter='smart_billing.merchant_id',
        help='Merchant ID atau School ID dari provider'
    )
    smart_billing_is_production = fields.Boolean(
        string='Production Mode',
        config_parameter='smart_billing.is_production',
        default=False,
        help='Aktifkan untuk mode production. Nonaktifkan untuk sandbox/testing.'
    )

    # BSI Specific Configuration
    smart_billing_bsi_client_id = fields.Char(
        string='BSI Client ID',
        config_parameter='smart_billing.bsi_client_id',
        help='Client ID dari BSI Smart Billing (BPI)'
    )
    smart_billing_bsi_client_secret = fields.Char(
        string='BSI Client Secret',
        config_parameter='smart_billing.bsi_client_secret',
        help='Client Secret untuk CRUD API dan signature verification'
    )
    smart_billing_bsi_partner_id = fields.Char(
        string='BSI Partner ID',
        config_parameter='smart_billing.bsi_partner_id',
        help='Partner ID (prefix VA number, biasanya sama dengan Client ID)'
    )
    smart_billing_bsi_use_mockup = fields.Boolean(
        string='Use Mockup API',
        config_parameter='smart_billing.bsi_use_mockup',
        default=False,
        help='Aktifkan untuk testing dengan mockup API lokal (FastAPI)'
    )
    smart_billing_bsi_mockup_url = fields.Char(
        string='Mockup API URL',
        config_parameter='smart_billing.bsi_mockup_url',
        default='http://localhost:8001',
        help='URL mockup API untuk testing (contoh: http://localhost:8001)'
    )

    # VA Configuration
    smart_billing_va_bank = fields.Selection([
        ('bsi', 'BSI'),
        ('bni', 'BNI'),
        ('bri', 'BRI'),
        ('bca', 'BCA'),
        ('permata', 'Permata'),
        ('cimb', 'CIMB'),
        ('mandiri', 'Mandiri'),
    ], string='Default VA Bank',
        config_parameter='smart_billing.va_bank',
        default='bsi',
        help='Bank default untuk Virtual Account (BSI untuk Smart Billing BSI)'
    )
    smart_billing_expiry_hours = fields.Integer(
        string='VA Expiry Duration (Hours)',
        config_parameter='smart_billing.expiry_hours',
        default=24,
        help='Durasi berlakunya VA tagihan dalam jam'
    )
    smart_billing_permanent_va_expiry_days = fields.Integer(
        string='Permanent VA Expiry (Days)',
        config_parameter='smart_billing.permanent_va_expiry_days',
        default=365,
        help='Durasi berlakunya VA permanen dalam hari (default 1 tahun)'
    )

    # Webhook Configuration
    smart_billing_webhook_url = fields.Char(
        string='Webhook URL (Generic)',
        compute='_compute_webhook_url',
        help='URL untuk diset di dashboard provider'
    )
    smart_billing_bsi_auth_url = fields.Char(
        string='BSI Auth URL',
        compute='_compute_webhook_url',
        help='URL untuk BSI SNAP BI Authentication'
    )
    smart_billing_bsi_inquiry_url = fields.Char(
        string='BSI Inquiry URL',
        compute='_compute_webhook_url',
        help='URL untuk BSI SNAP BI Inquiry'
    )
    smart_billing_bsi_payment_url = fields.Char(
        string='BSI Payment URL',
        compute='_compute_webhook_url',
        help='URL untuk BSI SNAP BI Payment Notification'
    )

    # Feature Toggles
    smart_billing_auto_reconcile = fields.Boolean(
        string='Auto Reconcile Invoice',
        config_parameter='smart_billing.auto_reconcile',
        default=True,
        help='Otomatis rekonsiliasi invoice saat pembayaran diterima'
    )
    smart_billing_auto_topup_saldo = fields.Boolean(
        string='Auto Top-up Saldo',
        config_parameter='smart_billing.auto_topup_saldo',
        default=True,
        help='Otomatis tambah saldo uang saku saat transfer ke VA permanen'
    )
    smart_billing_send_notification = fields.Boolean(
        string='Send Payment Notification',
        config_parameter='smart_billing.send_notification',
        default=True,
        help='Kirim notifikasi ke orang tua saat pembayaran berhasil'
    )

    @api.depends('smart_billing_provider')
    def _compute_webhook_url(self):
        base_url = self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        for record in self:
            provider = record.smart_billing_provider or 'dummy'
            record.smart_billing_webhook_url = f"{base_url}/smart-billing/notification/{provider}"
            # BSI SNAP BI endpoints (Standard Standard - SNAP BI)
            record.smart_billing_bsi_auth_url = f"{base_url}/api/v1.0/access-token/b2b"
            record.smart_billing_bsi_inquiry_url = f"{base_url}/api/v1.0/transfer-va/inquiry"
            record.smart_billing_bsi_payment_url = f"{base_url}/api/v1.0/transfer-va/payment"

    def action_test_connection(self):
        """Test connection to the selected provider"""
        self.ensure_one()

        provider = self._get_billing_provider()
        config = provider.get_config()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Connection Test',
                'message': f"Provider: {provider.get_provider_name()}\nConfig loaded successfully.",
                'type': 'success',
                'sticky': False,
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
