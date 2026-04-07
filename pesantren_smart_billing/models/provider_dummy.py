# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging
import random
import string

_logger = logging.getLogger(__name__)


class DummyProvider(models.AbstractModel):
    """
    Dummy provider for testing Smart Billing without real API.

    This provider simulates all API calls and can be used for:
    - Development and testing
    - Demo purposes
    - Validating integration before getting real API credentials
    """
    _name = 'smart.billing.provider.dummy'
    _inherit = 'smart.billing.provider'
    _description = 'Dummy Smart Billing Provider (Testing)'

    def get_provider_code(self):
        return 'dummy'

    def get_provider_name(self):
        return 'Dummy Provider (Testing)'

    def get_config(self):
        """Dummy config - no real credentials needed"""
        return {
            'server_key': 'DUMMY-SERVER-KEY',
            'client_key': 'DUMMY-CLIENT-KEY',
            'is_production': False,
            'va_bank': 'bsi',  # Default BSI for Smart Billing
            'expiry_duration': 24,
        }

    def _generate_dummy_va(self, bank='bsi'):
        """Generate a random VA number for testing"""
        bank_prefixes = {
            'bsi': '7188',
            'bni': '8808',
            'bri': '8877',
            'bca': '7007',
            'permata': '8625',
            'cimb': '7001',
        }
        prefix = bank_prefixes.get(bank, '7188')
        random_suffix = ''.join(random.choices(string.digits, k=12))
        return f"{prefix}{random_suffix}"

    def _generate_order_id(self, prefix, partner):
        """Generate order ID for VA creation"""
        siswa = self.env['cdn.siswa'].search(
            [('partner_id', '=', partner.id)], limit=1)
        nis = siswa.nis.replace('.', '').replace(
            '-', '') if siswa and siswa.nis else str(partner.id)
        return f"{prefix}-{nis}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def _generate_dummy_transaction_id(self):
        """Generate dummy transaction ID"""
        return f"DUMMY-TXN-{''.join(random.choices(string.ascii_uppercase + string.digits, k=16))}"

    def create_va_transaction(self, order_id, amount, customer_details, bank=None):
        """
        Create dummy VA transaction
        """
        config = self.get_config()
        bank = bank or config['va_bank']
        expiry_hours = config['expiry_duration']

        va_number = self._generate_dummy_va(bank)
        transaction_id = self._generate_dummy_transaction_id()
        expiry_time = datetime.now() + timedelta(hours=expiry_hours)

        _logger.info(
            f"[DUMMY] Created VA transaction: {order_id}, VA: {va_number}")

        return {
            'success': True,
            'va_number': va_number,
            'va_bank': bank.upper(),
            'expiry_time': expiry_time,
            'transaction_id': transaction_id,
            'order_id': order_id,
            'gross_amount': amount,
            'raw_response': {
                'status_code': '201',
                'status_message': 'Success, Bank Transfer transaction is created',
                'transaction_id': transaction_id,
                'order_id': order_id,
                'gross_amount': str(amount),
                'currency': 'IDR',
                'payment_type': 'bank_transfer',
                'transaction_status': 'pending',
                'va_numbers': [{'bank': bank, 'va_number': va_number}],
                'expiry_time': expiry_time.strftime('%Y-%m-%d %H:%M:%S'),
            }
        }

    def create_permanent_va(self, partner, bank=None):
        """
        Create dummy permanent VA for santri
        """
        config = self.get_config()
        bank = bank or config['va_bank']

        va_number = self._generate_dummy_va(bank)
        order_id = self._generate_order_id('PERMVA', partner)
        transaction_id = self._generate_dummy_transaction_id()
        expiry_time = datetime.now() + timedelta(days=365)  # 1 year expiry

        _logger.info(
            f"[DUMMY] Created permanent VA for {partner.name}: {va_number}")

        return {
            'success': True,
            'va_number': va_number,
            'va_bank': bank.upper(),
            'expiry_time': expiry_time,
            'order_id': order_id,
            'transaction_id': transaction_id,
            'raw_response': {
                'status_code': '201',
                'status_message': 'Success, Permanent VA created',
                'transaction_id': transaction_id,
                'order_id': order_id,
                'va_numbers': [{'bank': bank, 'va_number': va_number}],
                'expiry_time': expiry_time.strftime('%Y-%m-%d %H:%M:%S'),
            }
        }

    def create_payment_link(self, order_id, amount, item_details, customer_details):
        """
        Create dummy payment link
        """
        config = self.get_config()
        expiry_hours = config['expiry_duration']

        token = ''.join(random.choices(
            string.ascii_lowercase + string.digits, k=32))
        payment_url = f"https://app.sandbox.dummy-payment.com/snap/v4/redirect/{token}"
        expiry_time = datetime.now() + timedelta(hours=expiry_hours)

        _logger.info(
            f"[DUMMY] Created payment link: {order_id}, URL: {payment_url}")

        return {
            'success': True,
            'payment_url': payment_url,
            'token': token,
            'expiry_time': expiry_time,
            'raw_response': {
                'token': token,
                'redirect_url': payment_url,
            }
        }

    def check_transaction_status(self, order_id):
        """
        Check dummy transaction status - always returns pending
        """
        _logger.info(f"[DUMMY] Checking status for: {order_id}")

        return {
            'success': True,
            'status': 'pending',
            'settlement_time': None,
            'gross_amount': 0,
            'raw_response': {
                'status_code': '201',
                'transaction_status': 'pending',
                'order_id': order_id,
            }
        }

    def verify_notification_signature(self, notification_data):
        """
        Dummy signature verification - always returns True for testing
        """
        _logger.info(f"[DUMMY] Verifying signature (always True for testing)")
        return True

    def parse_notification(self, notification_data):
        """
        Parse dummy notification data
        """
        return {
            'order_id': notification_data.get('order_id', ''),
            'transaction_status': notification_data.get('transaction_status', 'pending'),
            'gross_amount': float(notification_data.get('gross_amount', 0)),
            'va_number': notification_data.get('va_number', ''),
            'settlement_time': notification_data.get('settlement_time'),
            'transaction_id': notification_data.get('transaction_id', ''),
        }

    def update_billing(self, order_id, amount, customer_details=None):
        """
        Update dummy billing - simulates updating amount or customer info
        """
        _logger.info(
            f"[DUMMY] Updating billing: {order_id}, new amount: {amount}")

        return {
            'success': True,
            'message': 'Billing updated successfully',
            'raw_response': {
                'status_code': '200',
                'status_message': 'Success, billing is updated',
                'order_id': order_id,
                'gross_amount': str(amount),
            }
        }

    def cancel_transaction(self, order_id):
        """
        Cancel dummy transaction
        """
        _logger.info(f"[DUMMY] Cancelling transaction: {order_id}")

        return {
            'success': True,
            'message': 'Transaction cancelled successfully',
            'raw_response': {
                'status_code': '200',
                'status_message': 'Success, transaction is canceled',
                'order_id': order_id,
            }
        }

    def simulate_payment(self, order_id, amount):
        """
        Special method to simulate a payment for testing.
        This can be called manually to test webhook processing.

        Args:
            order_id: Order ID to simulate payment for
            amount: Amount paid

        Returns:
            dict: Simulated notification payload
        """
        _logger.info(
            f"[DUMMY] Simulating payment for {order_id}, amount: {amount}")

        return {
            'order_id': order_id,
            'transaction_status': 'settlement',
            'gross_amount': str(amount),
            'transaction_id': self._generate_dummy_transaction_id(),
            'settlement_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'payment_type': 'bank_transfer',
            'signature_key': 'dummy_signature_for_testing',
        }
