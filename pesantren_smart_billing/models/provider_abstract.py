# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SmartBillingProvider(models.AbstractModel):
    """
    Abstract class for Smart Billing providers.

    All payment providers (BSI, TKI, etc.) must inherit from this class
    and implement the required methods.
    """
    _name = 'smart.billing.provider'
    _description = 'Smart Billing Provider Interface'

    # -------------------------------------------------------------------------
    # Abstract Methods - Must be implemented by each provider
    # -------------------------------------------------------------------------

    def get_provider_code(self):
        """
        Return the unique provider code (e.g., 'bsi', 'tki', 'dummy')

        Returns:
            str: Provider code
        """
        raise NotImplementedError(
            "Provider must implement get_provider_code()")

    def get_provider_name(self):
        """
        Return the display name of the provider

        Returns:
            str: Provider display name
        """
        raise NotImplementedError(
            "Provider must implement get_provider_name()")

    def get_config(self):
        """
        Get provider configuration from settings

        Returns:
            dict: Configuration dictionary with keys like server_key, client_key, etc.
        """
        raise NotImplementedError("Provider must implement get_config()")

    def create_va_transaction(self, order_id, amount, customer_details, bank=None):
        """
        Create Virtual Account transaction for specific amount (for invoice payment)

        Args:
            order_id (str): Unique order ID
            amount (float): Transaction amount
            customer_details (dict): Customer info with first_name, email, phone
            bank (str, optional): Bank code (bni, bri, bca, etc.)

        Returns:
            dict: {
                'success': bool,
                'va_number': str,
                'va_bank': str,
                'expiry_time': datetime,
                'transaction_id': str,
                'raw_response': dict
            }
        """
        raise NotImplementedError(
            "Provider must implement create_va_transaction()")

    def create_permanent_va(self, partner, bank=None):
        """
        Create Permanent/Open Amount Virtual Account for a santri.
        This VA can receive any amount and is valid for extended period.

        Args:
            partner (res.partner): Partner record (santri)
            bank (str, optional): Bank code

        Returns:
            dict: {
                'success': bool,
                'va_number': str,
                'va_bank': str,
                'expiry_time': datetime,
                'order_id': str,
                'raw_response': dict
            }
        """
        raise NotImplementedError(
            "Provider must implement create_permanent_va()")

    def create_payment_link(self, order_id, amount, item_details, customer_details):
        """
        Create Payment Link that customer can use to pay

        Args:
            order_id (str): Unique order ID
            amount (float): Transaction amount
            item_details (list): List of items [{id, name, price, quantity}]
            customer_details (dict): Customer info

        Returns:
            dict: {
                'success': bool,
                'payment_url': str,
                'token': str,
                'expiry_time': datetime,
                'raw_response': dict
            }
        """
        raise NotImplementedError(
            "Provider must implement create_payment_link()")

    def check_transaction_status(self, order_id):
        """
        Check transaction status from provider

        Args:
            order_id (str): Order ID to check

        Returns:
            dict: {
                'success': bool,
                'status': str (pending, settlement, expired, cancelled),
                'settlement_time': datetime or None,
                'gross_amount': float,
                'raw_response': dict
            }
        """
        raise NotImplementedError(
            "Provider must implement check_transaction_status()")

    def verify_notification_signature(self, notification_data):
        """
        Verify webhook notification signature

        Args:
            notification_data (dict): Full notification payload

        Returns:
            bool: True if signature is valid
        """
        raise NotImplementedError(
            "Provider must implement verify_notification_signature()")

    def parse_notification(self, notification_data):
        """
        Parse webhook notification data into standardized format

        Args:
            notification_data (dict): Raw notification from provider

        Returns:
            dict: {
                'order_id': str,
                'transaction_status': str,
                'gross_amount': float,
                'va_number': str,
                'settlement_time': datetime or None,
                'transaction_id': str,
            }
        """
        raise NotImplementedError(
            "Provider must implement parse_notification()")

    def cancel_transaction(self, order_id):
        """
        Cancel a pending transaction

        Args:
            order_id (str): Order ID to cancel

        Returns:
            dict: {
                'success': bool,
                'message': str,
                'raw_response': dict
            }
        """
        raise NotImplementedError(
            "Provider must implement cancel_transaction()")

    # -------------------------------------------------------------------------
    # Helper Methods - Common utilities for all providers
    # -------------------------------------------------------------------------

    def _get_base_url(self):
        """Get base URL for webhooks"""
        return self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')

    def _generate_order_id(self, prefix, partner=None):
        """Generate unique order ID"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

        if partner:
            siswa = self.env['cdn.siswa'].search(
                [('partner_id', '=', partner.id)], limit=1)
            if siswa and siswa.nis:
                nis = siswa.nis.replace('.', '').replace('-', '')
                return f"{prefix}-{nis}-{timestamp}"

        return f"{prefix}-{timestamp}"

    def _prepare_customer_details(self, partner):
        """Prepare standard customer details from partner"""
        siswa = self.env['cdn.siswa'].search(
            [('partner_id', '=', partner.id)], limit=1)

        email = partner.email or ''
        if siswa and siswa.orangtua_id and siswa.orangtua_id.partner_id.email:
            email = siswa.orangtua_id.partner_id.email

        return {
            'first_name': partner.name or 'Customer',
            'email': email or 'noemail@pesantren.id',
            'phone': partner.phone or partner.mobile or '',
        }

    def _log_api_call(self, method, request_data, response_data, success=True):
        """Log API call for debugging"""
        provider = self.get_provider_code()
        if success:
            _logger.info(f"[{provider}] {method} - Success: {response_data}")
        else:
            _logger.error(f"[{provider}] {method} - Error: {response_data}")
