# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class TKIProvider(models.AbstractModel):
    """
    TKI (Teknologi Kartu Indonesia) Smart Billing Provider.

    TKI menyediakan Platform Sekolah Pintar yang mencakup:
    - Kartu multifungsi digital
    - Digital billing
    - Sistem absensi

    This is a placeholder implementation. When you get the TKI API documentation
    and credentials, implement the actual API calls here.

    Website: https://teknologikartu.com
    """
    _name = 'smart.billing.provider.tki'
    _inherit = 'smart.billing.provider'
    _description = 'TKI Smart Billing Provider'

    def get_provider_code(self):
        return 'tki'

    def get_provider_name(self):
        return 'TKI (Teknologi Kartu Indonesia)'

    def get_config(self):
        """Get TKI configuration from settings"""
        ICP = self.env['ir.config_parameter'].sudo()
        return {
            'api_key': ICP.get_param('smart_billing.server_key', ''),
            'secret_key': ICP.get_param('smart_billing.client_key', ''),
            'merchant_id': ICP.get_param('smart_billing.merchant_id', ''),
            'school_id': ICP.get_param('smart_billing.tki_school_id', ''),
            'is_production': ICP.get_param('smart_billing.is_production', 'False') == 'True',
            'va_bank': ICP.get_param('smart_billing.va_bank', 'bni'),
            'expiry_duration': int(ICP.get_param('smart_billing.expiry_hours', '24')),
        }

    def _validate_config(self):
        """Validate that required configuration is set"""
        config = self.get_config()
        if not config['api_key']:
            raise UserError(
                "TKI API Key belum dikonfigurasi.\n\n"
                "Silakan set di Settings > Keuangan > Smart Billing"
            )
        return config

    def _get_api_base_url(self):
        """Get TKI API base URL based on environment"""
        config = self.get_config()
        if config['is_production']:
            # Example - adjust based on actual API
            return 'https://api.teknologikartu.com/v1'
        else:
            return 'https://sandbox.teknologikartu.com/v1'  # Example sandbox URL

    def create_va_transaction(self, order_id, amount, customer_details, bank=None):
        """
        Create VA transaction via TKI API.

        TODO: Implement actual TKI API call when documentation is available.
        """
        self._validate_config()

        raise UserError(
            "TKI API belum diimplementasikan.\n\n"
            "Untuk menggunakan TKI, Anda perlu:\n"
            "1. Hubungi TKI (teknologikartu.com) untuk dokumentasi API\n"
            "2. Dapatkan credentials (API Key, Secret Key, School ID)\n"
            "3. Implementasikan API calls di file ini\n\n"
            "Sementara ini, gunakan 'Dummy Provider' untuk testing."
        )

    def create_permanent_va(self, partner, bank=None):
        """
        Create permanent VA via TKI API.

        TODO: Implement actual TKI API call.

        TKI might use different approach with their card system.
        """
        self._validate_config()

        raise UserError(
            "TKI Permanent VA belum diimplementasikan.\n\n"
            "TKI mungkin menggunakan sistem kartu untuk pembayaran.\n"
            "Hubungi TKI untuk informasi lebih lanjut tentang integrasi VA."
        )

    def create_payment_link(self, order_id, amount, item_details, customer_details):
        """
        Create payment link via TKI API.

        TODO: Implement if TKI supports payment links.
        """
        self._validate_config()

        raise UserError(
            "TKI Payment Link belum diimplementasikan.\n\n"
            "Fitur ini tergantung pada dukungan dari TKI API."
        )

    def check_transaction_status(self, order_id):
        """
        Check transaction status from TKI API.

        TODO: Implement actual TKI API call.
        """
        self._validate_config()

        raise UserError(
            "TKI Status Check belum diimplementasikan.\n\n"
            "Silakan cek status transaksi langsung di dashboard TKI."
        )

    def verify_notification_signature(self, notification_data):
        """
        Verify TKI webhook signature.

        TODO: Implement TKI signature verification based on their spec.
        """
        _logger.warning(
            "[TKI] Signature verification not implemented - accepting all notifications")
        return True

    def parse_notification(self, notification_data):
        """
        Parse TKI webhook notification.

        TODO: Adjust parsing based on actual TKI notification format.
        """
        return {
            'order_id': notification_data.get('order_id', notification_data.get('invoice_id', '')),
            'transaction_status': notification_data.get('status', 'pending'),
            'gross_amount': float(notification_data.get('amount', 0)),
            'va_number': notification_data.get('va_number', ''),
            'settlement_time': notification_data.get('paid_at'),
            'transaction_id': notification_data.get('transaction_id', ''),
        }

    def cancel_transaction(self, order_id):
        """
        Cancel TKI transaction.

        TODO: Implement if TKI API supports cancellation.
        """
        self._validate_config()

        raise UserError(
            "TKI Cancel Transaction belum diimplementasikan.\n\n"
            "Silakan batalkan transaksi langsung di dashboard TKI."
        )


# =============================================================================
# Implementation Guide for TKI Integration
# =============================================================================
#
# TKI (Teknologi Kartu Indonesia) - Platform Sekolah Pintar
# Website: https://teknologikartu.com
#
# When you receive TKI API documentation, follow these steps:
#
# 1. UNDERSTAND TKI SYSTEM
#    - TKI focuses on multi-functional cards for schools
#    - They might have different approach than traditional VA
#    - Understand their billing system first
#
# 2. AUTHENTICATION
#    - TKI might use API Key + Secret Key
#    - Or OAuth2 tokens
#    - Check their authentication method
#
# 3. API ENDPOINTS
#    - Look for endpoints related to:
#      * Create billing/invoice
#      * Create VA (if available)
#      * Check payment status
#      * Get student info
#
# 4. CARD INTEGRATION (if applicable)
#    - TKI might use student cards for payment
#    - Understand card-based payment flow
#    - Map card transactions to our system
#
# 5. WEBHOOK HANDLING
#    - Understand TKI notification format
#    - Implement signature verification
#    - Handle payment notifications
#
# 6. TESTING
#    - Request sandbox/testing environment from TKI
#    - Test all integration points
#
# Contact TKI:
# - Website: https://teknologikartu.com
# - Request API documentation and sandbox access
# - Ask about VA support and payment notification system
#
# =============================================================================
