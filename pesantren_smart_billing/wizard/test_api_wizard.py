# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import requests
import logging
import json
import hashlib
import hmac
import base64
import pytz
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

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

    # Configuration overrides
    override_credentials = fields.Boolean(
        string='Override Kredensial (Custom)', default=False)
    bsi_client_id = fields.Char(string='BSI Client ID')
    bsi_client_secret = fields.Char(string='BSI Client Secret')
    bsi_partner_id = fields.Char(string='BSI Partner ID')
    bsi_private_key = fields.Text(string='BSI Private Key (PEM)')

    # Test Parameters
    test_customer_no = fields.Char(
        string='Customer No',
        default='111222333444',
        help='Nomor pelanggan untuk testing (lihat sample_bills.json)'
    )

    test_amount = fields.Float(
        string='Amount',
        default=150000.0,
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
            bsi_provider = self.env['smart.billing.provider.bsi'].sudo()
            config = bsi_provider.get_config()
            if config.get('use_mockup'):
                return config.get('mockup_url', self.mockup_url)
        except Exception:
            pass

        if self.api_mode == 'sandbox':
            return 'https://sandbox.api.bpi.co.id'
        else:
            return 'https://api.bpi.co.id'

    def _get_bsi_config(self):
        """Get BSI configuration from wizard fields or system settings"""
        ICP = self.env['ir.config_parameter'].sudo()
        if self.override_credentials:
            config = {
                'client_id': self.bsi_client_id or ICP.get_param('smart_billing.bsi_client_id', ''),
                'client_secret': self.bsi_client_secret or ICP.get_param('smart_billing.bsi_client_secret', ''),
                'partner_id': self.bsi_partner_id or ICP.get_param('smart_billing.bsi_partner_id', ''),
                'private_key': self.bsi_private_key or ''
            }
        else:
            config = {
                'client_id': ICP.get_param('smart_billing.bsi_client_id', ''),
                'client_secret': ICP.get_param('smart_billing.bsi_client_secret', ''),
                'partner_id': ICP.get_param('smart_billing.bsi_partner_id', ''),
                'private_key': ''
            }
        return config

    def _generate_auth_signature(self, client_id, timestamp, private_key_pem):
        """Generate RSA-SHA256 signature for Auth request"""
        if not private_key_pem or self.api_mode == 'mockup':
            return "simulated-auth-signature"

        try:
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode(),
                password=None,
                backend=default_backend()
            )
            data_to_sign = f"{client_id}|{timestamp}"
            signature = private_key.sign(
                data_to_sign.encode(),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return base64.b64encode(signature).decode()
        except Exception as e:
            _logger.error(f"Failed to generate auth signature: {e}")
            return f"Error: {str(e)}"

    def _generate_snap_signature(self, method, endpoint, body, access_token, timestamp, client_secret):
        """Generate HMAC-SHA512 signature for transaction requests"""
        if not client_secret or self.api_mode == 'mockup':
            return "simulated-snap-signature"

        try:
            # Hash of request body
            body_str = json.dumps(body) if isinstance(
                body, dict) else str(body)
            hash_body = hashlib.sha256(body_str.encode()).hexdigest().lower()

            # String to sign
            string_to_sign = f"{method}:{endpoint}:{access_token}:{hash_body}:{timestamp}"

            # HMAC-SHA512 signature
            signature = hmac.new(
                client_secret.encode(),
                string_to_sign.encode(),
                hashlib.sha512
            ).digest()
            return base64.b64encode(signature).decode()
        except Exception as e:
            _logger.error(f"Failed to generate snap signature: {e}")
            return f"Error: {str(e)}"

    def action_test_auth(self):
        """Test Authentication endpoint"""
        self.ensure_one()

        base_url = self._get_api_url()
        url = f"{base_url}/api/v1.0/access-token/b2b"
        config = self._get_bsi_config()
        tz = pytz.timezone('Asia/Jakarta')
        timestamp = datetime.now(tz).strftime('%Y-%m-%dT%H:%M:%S+07:00')

        signature = self._generate_auth_signature(
            config['client_id'], timestamp, config['private_key'])

        headers = {
            'Content-Type': 'application/json',
            'X-Signature': signature,
            'X-Client-Key': config['client_id'] or 'SBI0001',
            'X-Timestamp': timestamp,
        }

        _logger.info(f"[Test] Auth request to: {url}")

        try:
            response = requests.post(url, headers=headers, timeout=30)
            try:
                result = response.json()
                self.auth_result = json.dumps(result, indent=2)
            except Exception:
                self.auth_result = f"Non-JSON Response (HTTP {response.status_code}):\n{response.text}"
                self.auth_status = 'failed'
                return self._show_notification('Auth Test', f"Server returned non-JSON response (HTTP {response.status_code})", 'danger')

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
        url = "/api/v1.0/transfer-va/inquiry"
        full_url = f"{base_url}{url}"
        config = self._get_bsi_config()
        tz = pytz.timezone('Asia/Jakarta')
        timestamp = datetime.now(tz).strftime('%Y-%m-%dT%H:%M:%S+07:00')

        # Send simulation flag if hitting mockup to prevent state persistence
        is_mockup = (self.api_mode == 'mockup')
        if not is_mockup:
            try:
                is_mockup = self.env['smart.billing.provider.bsi'].sudo().get_config().get('use_mockup')
            except Exception:
                pass

        payload = {
            'customerNo': self.test_customer_no,
            'partnerServiceId': config['partner_id'] or 'SBI0001',
            'additionalInfo': {
                'simulation': is_mockup
            }
        }

        signature = self._generate_snap_signature(
            'POST', url, payload, self.access_token, timestamp, config['client_secret'])

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}',
            'X-Signature': signature,
            'X-Partner-Id': config['partner_id'] or 'SBI0001',
            'X-External-Id': f'INQ-{fields.Datetime.now().strftime("%Y%m%d%H%M%S")}',
            'X-Timestamp': timestamp,
        }

        _logger.info(f"[Test] Inquiry request to: {full_url}")
        _logger.info(f"[Test] Inquiry payload: {payload}")

        try:
            response = requests.post(
                full_url, json=payload, headers=headers, timeout=30)
            try:
                result = response.json()
                self.inquiry_result = json.dumps(result, indent=2)
            except Exception:
                self.inquiry_result = f"Non-JSON Response (HTTP {response.status_code}):\n{response.text}"
                self.inquiry_status = 'failed'
                return self._show_notification('Inquiry Test', f"Server returned non-JSON response (HTTP {response.status_code})", 'danger')

            if result.get('responseCode') == '2002400':
                self.inquiry_status = 'success'
                va_data = result.get('virtualAccountData', {})
                # Handle string amount from v3.2 spec
                amount_raw = va_data.get('totalAmount', {}).get('value', 0)
                amount = float(amount_raw) if isinstance(
                    amount_raw, (str, int, float)) else 0
                msg = f"Inquiry berhasil!\n\nNama: {va_data.get('virtualAccountName')}\nTotal: Rp {amount:,.0f}"
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
        url = "/api/v1.0/transfer-va/payment"
        full_url = f"{base_url}{url}"
        config = self._get_bsi_config()
        tz = pytz.timezone('Asia/Jakarta')
        timestamp = datetime.now(tz).strftime('%Y-%m-%dT%H:%M:%S+07:00')
        payment_id = f'PAY-{fields.Datetime.now().strftime("%Y%m%d%H%M%S")}'

        # Send simulation flag if hitting mockup to prevent state persistence
        is_mockup = (self.api_mode == 'mockup')
        if not is_mockup:
            try:
                is_mockup = self.env['smart.billing.provider.bsi'].sudo().get_config().get('use_mockup')
            except Exception:
                pass

        payload = {
            'customerNo': self.test_customer_no,
            'partnerServiceId': config['partner_id'] or 'SBI0001',
            'paymentRequestId': payment_id,
            'paidAmount': {
                'value': str(int(self.test_amount)),  # Send as string per spec
                'currency': 'IDR'
            },
            'trxDateTime': timestamp,
            'additionalInfo': {
                'simulation': is_mockup
            }
        }

        signature = self._generate_snap_signature(
            'POST', url, payload, self.access_token, timestamp, config['client_secret'])

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}',
            'X-Signature': signature,
            'X-Partner-Id': config['partner_id'] or 'SBI0001',
            'X-External-Id': payment_id,
            'X-Timestamp': timestamp,
        }

        _logger.info(f"[Test] Payment request to: {full_url}")
        _logger.info(f"[Test] Payment payload: {payload}")

        try:
            response = requests.post(
                full_url, json=payload, headers=headers, timeout=30)
            try:
                result = response.json()
                self.payment_result = json.dumps(result, indent=2)
            except Exception:
                self.payment_result = f"Non-JSON Response (HTTP {response.status_code}):\n{response.text}"
                self.payment_status = 'failed'
                return self._show_notification('Payment Test', f"Server returned non-JSON response (HTTP {response.status_code})", 'danger')

            if result.get('responseCode') == '2002500':
                self.payment_status = 'success'
                # Handle minimal spec response (Ack-only)
                va_data = result.get('virtualAccountData')
                if va_data:
                    paid = va_data.get('paidAmount', {})
                    msg = f"Payment berhasil!\n\nNama: {va_data.get('virtualAccountName') or 'N/A'}\nDibayar: Rp {float(paid.get('value', 0)):,.0f}"
                else:
                    msg = "Payment berhasil! (ACK Received)"
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
