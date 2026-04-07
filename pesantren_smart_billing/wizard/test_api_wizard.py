# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import requests
import logging
import json

_logger = logging.getLogger(__name__)


class SmartBillingTestWizard(models.TransientModel):
    """Wizard untuk test API SmartBilling (Mockup atau Production)"""
    _name = 'smart.billing.test.wizard'
    _description = 'Smart Billing API Test Wizard'

    # Configuration
    api_mode = fields.Selection([
        ('mockup', 'Mockup API (Local)'),
        ('sandbox', 'BSI Sandbox'),
        ('production', 'BSI Production'),
    ], string='API Mode', default='mockup', required=True)

    mockup_url = fields.Char(
        string='Mockup API URL',
        default='http://localhost:8001',
        help='URL untuk API mockup yang berjalan lokal'
    )

    # Test Parameters
    test_customer_no = fields.Char(
        string='Customer No',
        default='111222333444',
        help='Nomor pelanggan untuk testing (lihat sample_bills.json)'
    )

    test_amount = fields.Float(
        string='Amount',
        default=15000,
        help='Nominal pembayaran untuk testing'
    )

    # Results
    auth_result = fields.Text(string='Auth Result', readonly=True)
    inquiry_result = fields.Text(string='Inquiry Result', readonly=True)
    payment_result = fields.Text(string='Payment Result', readonly=True)

    # Status
    auth_status = fields.Selection([
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ], string='Auth Status', default='pending')

    inquiry_status = fields.Selection([
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ], string='Inquiry Status', default='pending')

    payment_status = fields.Selection([
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ], string='Payment Status', default='pending')

    access_token = fields.Char(string='Access Token', readonly=True)

    def _get_api_url(self):
        """Get API base URL based on mode"""
        if self.api_mode == 'mockup':
            return self.mockup_url

        # Check global config for mockup override
        try:
            config = self.env['smart.billing.provider.bsi'].get_config()
            if config.get('use_mockup') and self.api_mode == 'sandbox':
                return config.get('mockup_url', self.mockup_url)
        except Exception:
            pass

        if self.api_mode == 'sandbox':
            return 'https://sandbox.api.bpi.co.id'
        else:
            return 'https://api.bpi.co.id'

    def action_test_auth(self):
        """Test Authentication endpoint"""
        self.ensure_one()

        base_url = self._get_api_url()
        url = f"{base_url}/api/v1.0/access-token/b2b"

        headers = {
            'Content-Type': 'application/json',
            'X-Client-Key': 'SBI0001',
            'X-Timestamp': fields.Datetime.now().strftime('%Y-%m-%dT%H:%M:%S+07:00'),
        }

        _logger.info(f"[Test] Auth request to: {url}")

        try:
            response = requests.post(url, headers=headers, timeout=30)
            result = response.json()

            self.auth_result = json.dumps(result, indent=2)

            if result.get('responseCode') == '2000000':
                self.auth_status = 'success'
                self.access_token = result.get('accessToken', '')
                return self._show_notification('Auth Test', 'Authentication berhasil!', 'success')
            else:
                self.auth_status = 'failed'
                return self._show_notification('Auth Test', f"Authentication gagal: {result.get('responseMessage')}", 'danger')

        except Exception as e:
            self.auth_status = 'failed'
            self.auth_result = str(e)
            return self._show_notification('Auth Test', f"Error: {str(e)}", 'danger')

    def action_test_inquiry(self):
        """Test Inquiry endpoint"""
        self.ensure_one()

        if not self.access_token:
            # Get new token first
            self.action_test_auth()
            if not self.access_token:
                return self._show_notification('Inquiry Test', 'Gagal mendapatkan access token', 'danger')

        base_url = self._get_api_url()
        url = f"{base_url}/api/v1.0/transfer-va/inquiry"

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}',
            'X-Partner-Id': 'SBI0001',
            'X-External-Id': f'INQ-{fields.Datetime.now().strftime("%Y%m%d%H%M%S")}',
            'X-Timestamp': fields.Datetime.now().strftime('%Y-%m-%dT%H:%M:%S+07:00'),
        }

        payload = {
            'customerNo': self.test_customer_no,
            'partnerServiceId': 'SBI0001',
        }

        _logger.info(f"[Test] Inquiry request to: {url}")
        _logger.info(f"[Test] Inquiry payload: {payload}")

        try:
            response = requests.post(
                url, json=payload, headers=headers, timeout=30)
            result = response.json()

            self.inquiry_result = json.dumps(result, indent=2)

            if result.get('responseCode') == '2002400':
                self.inquiry_status = 'success'
                va_data = result.get('virtualAccountData', {})
                msg = f"Inquiry berhasil!\n\nNama: {va_data.get('virtualAccountName')}\nTotal: Rp {va_data.get('totalAmount', {}).get('value', 0):,.0f}"
                return self._show_notification('Inquiry Test', msg, 'success')
            else:
                self.inquiry_status = 'failed'
                return self._show_notification('Inquiry Test', f"Inquiry gagal: {result.get('responseMessage')}", 'danger')

        except Exception as e:
            self.inquiry_status = 'failed'
            self.inquiry_result = str(e)
            return self._show_notification('Inquiry Test', f"Error: {str(e)}", 'danger')

    def action_test_payment(self):
        """Test Payment Notification endpoint"""
        self.ensure_one()

        # Get new token for payment
        self.action_test_auth()
        if not self.access_token:
            return self._show_notification('Payment Test', 'Gagal mendapatkan access token', 'danger')

        base_url = self._get_api_url()
        url = f"{base_url}/api/v1.0/transfer-va/payment"

        timestamp = fields.Datetime.now().strftime('%Y-%m-%dT%H:%M:%S+07:00')
        payment_id = f'PAY-{fields.Datetime.now().strftime("%Y%m%d%H%M%S")}'

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}',
            'X-Partner-Id': 'SBI0001',
            'X-External-Id': payment_id,
            'X-Timestamp': timestamp,
        }

        payload = {
            'customerNo': self.test_customer_no,
            'partnerServiceId': 'SBI0001',
            'paymentRequestId': payment_id,
            'paidAmount': {
                'value': self.test_amount,
                'currency': 'IDR'
            },
            'trxDateTime': timestamp,
        }

        _logger.info(f"[Test] Payment request to: {url}")
        _logger.info(f"[Test] Payment payload: {payload}")

        try:
            response = requests.post(
                url, json=payload, headers=headers, timeout=30)
            result = response.json()

            self.payment_result = json.dumps(result, indent=2)

            if result.get('responseCode') == '2002500':
                self.payment_status = 'success'
                va_data = result.get('virtualAccountData', {})
                paid = va_data.get('paidAmount', {})
                msg = f"Payment berhasil!\n\nNama: {va_data.get('virtualAccountName')}\nDibayar: Rp {paid.get('value', 0):,.0f}"
                return self._show_notification('Payment Test', msg, 'success')
            else:
                self.payment_status = 'failed'
                return self._show_notification('Payment Test', f"Payment gagal: {result.get('responseMessage')}", 'danger')

        except Exception as e:
            self.payment_status = 'failed'
            self.payment_result = str(e)
            return self._show_notification('Payment Test', f"Error: {str(e)}", 'danger')

    def action_test_all(self):
        """Run all tests sequentially"""
        self.ensure_one()

        # Reset status
        self.auth_status = 'pending'
        self.inquiry_status = 'pending'
        self.payment_status = 'pending'
        self.access_token = False

        results = []

        # Test Auth
        self.action_test_auth()
        results.append(f"Auth: {self.auth_status}")

        if self.auth_status == 'success':
            # Test Inquiry (need new token because mockup uses one-time tokens)
            self.action_test_auth()  # Get new token
            self.action_test_inquiry()
            results.append(f"Inquiry: {self.inquiry_status}")

            # Test Payment
            self.action_test_payment()
            results.append(f"Payment: {self.payment_status}")

        summary = "\n".join(results)
        notification_type = 'success' if all(s == 'success' for s in [
                                             self.auth_status, self.inquiry_status, self.payment_status]) else 'warning'

        return self._show_notification('Test All', f"Test selesai:\n{summary}", notification_type)

    def action_reset(self):
        """Reset all test results"""
        self.ensure_one()
        self.write({
            'auth_result': False,
            'inquiry_result': False,
            'payment_result': False,
            'auth_status': 'pending',
            'inquiry_status': 'pending',
            'payment_status': 'pending',
            'access_token': False,
        })
        return self._show_notification('Reset', 'Test results telah direset', 'info')

    def _show_notification(self, title, message, notification_type='info'):
        """Show notification to user"""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': notification_type,
                'sticky': False,
            }
        }
