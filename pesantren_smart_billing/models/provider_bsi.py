# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging
import json
import requests
import base64
import hashlib
import hmac
import time

_logger = logging.getLogger(__name__)


class BnisEnc:
    """
    BSI Smart Billing encryption class.
    Ported from PHP implementation in BSI documentation.

    Used for P2H VA API communication (create/update/delete billing).
    """

    TIME_DIFF_LIMIT = 480  # 8 minutes

    @staticmethod
    def encrypt(json_data: dict, cid: str, secret: str) -> str:
        """
        Encrypt data for BSI API request.

        Args:
            json_data: Dictionary to encrypt
            cid: Client ID
            secret: Secret key

        Returns:
            Encrypted string safe for URL
        """
        data_str = str(int(time.time()))[::-1] + '.' + json.dumps(json_data)
        return BnisEnc._double_encrypt(data_str, cid, secret)

    @staticmethod
    def decrypt(hashed_string: str, cid: str, secret: str) -> dict:
        """
        Decrypt response from BSI API.

        Args:
            hashed_string: Encrypted string from BSI
            cid: Client ID
            secret: Secret key

        Returns:
            Decrypted dictionary or None if invalid
        """
        try:
            parsed_string = BnisEnc._double_decrypt(hashed_string, cid, secret)
            parts = parsed_string.split('.', 1)
            if len(parts) < 2:
                return None

            timestamp = parts[0][::-1]
            data = parts[1]

            if BnisEnc._ts_diff(int(timestamp)):
                return json.loads(data)
            return None
        except Exception as e:
            _logger.error(f"BnisEnc decrypt error: {e}")
            return None

    @staticmethod
    def _ts_diff(ts: int) -> bool:
        """Check if timestamp is within allowed time difference"""
        return abs(ts - int(time.time())) <= BnisEnc.TIME_DIFF_LIMIT

    @staticmethod
    def _double_encrypt(string: str, cid: str, secret: str) -> str:
        """Double encryption using cid and secret"""
        result = BnisEnc._enc(string, cid)
        result = BnisEnc._enc(result, secret)
        # Base64 encode and make URL safe
        b64 = base64.b64encode(result.encode('latin-1')).decode('ascii')
        b64 = b64.rstrip('=')
        return b64.replace('+', '-').replace('/', '_')

    @staticmethod
    def _enc(string: str, key: str) -> str:
        """Single encryption pass"""
        result = []
        key_len = len(key)
        for i, char in enumerate(string):
            key_char = key[(i % key_len) - 1] if key_len > 0 else ''
            new_char = chr((ord(char) + ord(key_char)) % 128)
            result.append(new_char)
        return ''.join(result)

    @staticmethod
    def _double_decrypt(string: str, cid: str, secret: str) -> str:
        """Double decryption using cid and secret"""
        # Pad and decode
        padding = (4 - len(string) % 4) % 4
        string = string.replace('-', '+').replace('_', '/')
        string = string + '=' * padding
        decoded = base64.b64decode(string).decode('latin-1')

        result = BnisEnc._dec(decoded, cid)
        result = BnisEnc._dec(result, secret)
        return result

    @staticmethod
    def _dec(string: str, key: str) -> str:
        """Single decryption pass"""
        result = []
        key_len = len(key)
        for i, char in enumerate(string):
            key_char = key[(i % key_len) - 1] if key_len > 0 else ''
            new_char = chr(((ord(char) - ord(key_char)) + 256) % 128)
            result.append(new_char)
        return ''.join(result)


class BSIProvider(models.AbstractModel):
    """
    BSI (Bank Syariah Indonesia) Smart Billing Provider.

    Implements two API approaches:
    1. P2H VA API - We call BSI to create/update/delete billing
    2. SNAP BI H2H - BSI calls our endpoints for inquiry and payment notification
    """
    _name = 'smart.billing.provider.bsi'
    _inherit = 'smart.billing.provider'
    _description = 'BSI Smart Billing Provider'

    # BSI API URLs
    SANDBOX_URL = 'https://sandbox.api.bpi.co.id'
    PRODUCTION_URL = 'https://api.bpi.co.id'

    def get_provider_code(self):
        return 'bsi'

    def get_provider_name(self):
        return 'BSI (Bank Syariah Indonesia)'

    def get_config(self):
        """Get BSI configuration from settings"""
        ICP = self.env['ir.config_parameter'].sudo()
        return {
            'client_id': ICP.get_param('smart_billing.bsi_client_id', ''),
            'client_secret': ICP.get_param('smart_billing.bsi_client_secret', ''),
            'partner_id': ICP.get_param('smart_billing.bsi_partner_id', ''),
            'is_production': ICP.get_param('smart_billing.is_production', 'False') == 'True',
            'expiry_duration': int(ICP.get_param('smart_billing.expiry_hours', '24')),
            'use_mockup': ICP.get_param('smart_billing.bsi_use_mockup', 'False') == 'True',
            'mockup_url': ICP.get_param('smart_billing.bsi_mockup_url', 'http://localhost:8001'),
        }

    def _get_api_base_url(self):
        """Get BSI API base URL based on environment"""
        config = self.get_config()
        # Use mockup URL if enabled
        if config.get('use_mockup'):
            return config.get('mockup_url', 'http://localhost:8001')
        # Otherwise use BSI sandbox or production
        if config['is_production']:
            return self.PRODUCTION_URL
        return self.SANDBOX_URL

    def _validate_config(self):
        """Validate that required configuration is set"""
        config = self.get_config()
        if not config['client_id']:
            raise UserError(
                "BSI Client ID belum dikonfigurasi.\n\n"
                "Silakan set di Settings > Accounting > Smart Billing"
            )
        if not config['client_secret']:
            raise UserError(
                "BSI Client Secret belum dikonfigurasi.\n\n"
                "Silakan set di Settings > Accounting > Smart Billing"
            )
        return config

    def _format_datetime_expired(self, hours=24):
        """Format datetime for BSI API"""
        expired = datetime.now() + timedelta(hours=hours)
        return expired.strftime('%Y-%m-%dT%H:%M:%S+0700')

    def _generate_virtual_account(self, customer_no: str) -> str:
        """Generate full VA number: client_id + customer_no"""
        config = self.get_config()
        client_id = config['client_id']
        return f"{client_id}{customer_no}"

    def _call_p2h_api(self, data: dict):
        """
        Call BSI P2H VA API.

        Args:
            data: Request data dictionary

        Returns:
            dict: Decrypted response
        """
        config = self._validate_config()
        base_url = self._get_api_base_url()
        url = f"{base_url}/ext/bnis/?fungsi=vabilling"

        # Encrypt the data
        encrypted_data = BnisEnc.encrypt(
            data, config['client_id'], config['client_secret'])

        payload = {
            'client_id': config['client_id'],
            'data': encrypted_data
        }

        headers = {'Content-Type': 'application/json'}

        _logger.info(f"[BSI] P2H API Request to {url}")
        _logger.debug(f"[BSI] Request data: {data}")

        try:
            response = requests.post(
                url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            response_json = response.json()
            _logger.info(f"[BSI] P2H API Response: {response_json}")

            # Decrypt the response
            if 'data' in response_json:
                decrypted = BnisEnc.decrypt(
                    response_json['data'],
                    config['client_id'],
                    config['client_secret']
                )
                return decrypted

            return response_json

        except requests.exceptions.RequestException as e:
            _logger.error(f"[BSI] P2H API Error: {e}")
            raise UserError(f"BSI API Error: {str(e)}")

    def create_va_transaction(self, order_id, amount, customer_details, bank=None):
        """
        Create VA transaction via BSI P2H API.

        Args:
            order_id: Unique order ID
            amount: Transaction amount
            customer_details: Customer info dict
            bank: Not used for BSI (always BSI)

        Returns:
            dict with va_number, expiry_time, etc.
        """
        config = self._validate_config()

        # Generate customer_no from order_id (remove non-alphanumeric)
        # Menghasilkan customer_no dari order_id (hanya angka untuk VA)
        # Jika order_id tidak memiliki cukup angka unik, gunakan hash numerik
        digits_only = ''.join(filter(str.isdigit, order_id))
        if len(digits_only) < 6:
            # Gunakan 12 digit terakhir dari hash MD5 (numerik) untuk menjamin keunikan
            customer_no = str(
                int(hashlib.md5(order_id.encode()).hexdigest(), 16))[-12:]
        else:
            customer_no = digits_only[-12:]
        virtual_account = self._generate_virtual_account(customer_no)

        expiry_time = self._format_datetime_expired(config['expiry_duration'])

        data = {
            'type': 'createbilling',
            'client_id': config['client_id'],
            'trx_id': order_id,
            'trx_amount': str(int(amount)),
            'billing_type': 'c',  # c = closed (fixed amount)
            'customer_name': customer_details.get('first_name', 'Customer'),
            'customer_email': customer_details.get('email', ''),
            'customer_phone': customer_details.get('phone', ''),
            'virtual_account': virtual_account,
            'datetime_expired': expiry_time,
            'description': f'Pembayaran {order_id}'
        }

        response = self._call_p2h_api(data)

        if response and response.get('status') == '000':
            expiry_dt = datetime.strptime(
                expiry_time[:19], '%Y-%m-%dT%H:%M:%S')
            return {
                'success': True,
                'va_number': virtual_account,
                'va_bank': 'BSI',
                'expiry_time': expiry_dt,
                'transaction_id': response.get('trx_id', order_id),
                'order_id': order_id,
                'customer_no': customer_no,
                'raw_response': response
            }
        else:
            error_msg = response.get(
                'message', 'Unknown error') if response else 'No response'
            raise UserError(f"BSI Create VA Error: {error_msg}")

    def create_permanent_va(self, partner, bank=None):
        """
        Create Permanent/Open Amount VA for a santri.

        Uses NIS as customer_no and billing_type='o' for open amount.
        """
        config = self._validate_config()

        # Get siswa data
        siswa = self.env['cdn.siswa'].search(
            [('partner_id', '=', partner.id)], limit=1)
        if siswa and siswa.nis:
            customer_no = siswa.nis.replace('.', '').replace('-', '')[-12:]
        else:
            customer_no = str(partner.id).zfill(12)

        virtual_account = self._generate_virtual_account(customer_no)
        order_id = f"PERMVA-{customer_no}-{datetime.now().strftime('%Y%m%d')}"

        # Permanent VA expires in 1 year
        expiry_time = (datetime.now() + timedelta(days=365)
                       ).strftime('%Y-%m-%dT%H:%M:%S+0700')

        data = {
            'type': 'createbilling',
            'client_id': config['client_id'],
            'trx_id': order_id,
            'trx_amount': '0',  # Open amount based on BSI-BPI-SPEC.md requirement
            'billing_type': 'o',  # o = open (free amount)
            'customer_name': partner.name or 'Santri',
            'customer_email': partner.email or '',
            'customer_phone': partner.phone or partner.mobile or '',
            'virtual_account': virtual_account,
            'datetime_expired': expiry_time,
            'description': f'Top-up Saldo {partner.name}'
        }

        response = self._call_p2h_api(data)

        if response and response.get('status') == '000':
            expiry_dt = datetime.strptime(
                expiry_time[:19], '%Y-%m-%dT%H:%M:%S')
            return {
                'success': True,
                'va_number': virtual_account,
                'va_bank': 'BSI',
                'expiry_time': expiry_dt,
                'order_id': order_id,
                'customer_no': customer_no,
                'transaction_id': response.get('trx_id', order_id),
                'raw_response': response
            }
        else:
            error_msg = response.get(
                'message', 'Unknown error') if response else 'No response'
            raise UserError(f"BSI Create Permanent VA Error: {error_msg}")

    def create_payment_link(self, order_id, amount, item_details, customer_details):
        """
        BSI doesn't have payment link feature.
        Use VA instead.
        """
        raise UserError(
            "BSI tidak mendukung Payment Link.\n\n"
            "Gunakan Virtual Account (VA) untuk pembayaran."
        )

    def check_transaction_status(self, order_id):
        """
        Check transaction status via BPI P2H API (inquirybilling).
        """
        config = self._validate_config()

        data = {
            'type': 'inquirybilling',
            'client_id': config['client_id'],
            'trx_id': order_id
        }

        try:
            response = self._call_p2h_api(data)

            if response and response.get('status') == '000':
                resp_data = response.get('data', {})
                va_status = resp_data.get('va_status', '')
                
                status_str = 'pending'
                # Check for explicit payment amount within 000
                payment_amount = float(resp_data.get('payment_amount', 0))
                if payment_amount > 0:
                    status_str = 'settlement'
                elif str(va_status) == '2':
                    # Inactive status could be manual cancel or expired
                    dt_exp_str = resp_data.get('datetime_expired', '')
                    if dt_exp_str:
                        try:
                            # BSI datetime format: %Y-%m-%dT%H:%M:%S+0700
                            dt_exp = datetime.strptime(dt_exp_str[:19], '%Y-%m-%dT%H:%M:%S')
                            if datetime.now() > dt_exp:
                                status_str = 'expire'
                            else:
                                status_str = 'cancel'
                        except Exception:
                            status_str = 'cancel'
                    else:
                        status_str = 'cancel'

                return {
                    'success': True,
                    'status': status_str,
                    'va_status': va_status,
                    'settlement_time': None,
                    'gross_amount': float(resp_data.get('trx_amount', 0)),
                    'raw_response': response
                }
            elif response and response.get('status') == '111':
                # BSI code 111 = Already paid
                return {
                    'success': True,
                    'status': 'settlement',
                    'settlement_time': None,
                    'raw_response': response
                }
            elif response and response.get('status') == '103':
                # BSI code 103 = Billing expired
                return {
                    'success': True,
                    'status': 'expire',
                    'settlement_time': None,
                    'raw_response': response
                }
            else:
                error_msg = response.get('message', 'Unknown error') if response else 'No response'
                return {
                    'success': False,
                    'status': 'pending', # fallback
                    'message': error_msg,
                    'raw_response': response or {}
                }
        except Exception as e:
            return {
                'success': False,
                'status': 'error',
                'message': str(e),
                'raw_response': {}
            }

    def verify_notification_signature(self, notification_data):
        """
        Verify BSI SNAP BI webhook signature.

        This is called by the controller when receiving webhook from BSI.
        The signature verification is more complex and done in the controller.
        """
        # Signature verification is done in controller
        return True

    def parse_notification(self, notification_data):
        """
        Parse BSI webhook notification data.

        Handles both BSI SNAP BI format and P2H Callback format.
        """
        # 1. Try to parse as P2H Callback format first (BSI-BPI-SPEC.md)
        if 'trx_id' in notification_data and 'payment_amount' in notification_data:
            return {
                'order_id': notification_data.get('trx_id', ''),
                'customer_no': notification_data.get('virtual_account', '')[-12:], # Approximate
                'transaction_status': 'settlement',
                'gross_amount': float(notification_data.get('payment_amount', 0)),
                'va_number': notification_data.get('virtual_account', ''),
                'settlement_time': fields.Datetime.now(), # P2H doesn't provide time
                'transaction_id': notification_data.get('trx_id', ''),
            }

        # 2. Parse as SNAP BI format
        customer_no = notification_data.get('customerNo', '')
        paid_amount = notification_data.get('paidAmount', {})

        return {
            'order_id': notification_data.get('paymentRequestId', ''),
            'customer_no': customer_no,
            'transaction_status': 'settlement',
            'gross_amount': float(paid_amount.get('value', 0)) if isinstance(paid_amount, dict) else float(paid_amount or 0),
            'va_number': notification_data.get('virtualAccountNo', ''),
            'settlement_time': notification_data.get('trxDateTime'),
            'transaction_id': notification_data.get('paymentRequestId', ''),
        }

    def cancel_transaction(self, order_id):
        """
        Delete billing via BSI P2H API.
        """
        config = self._validate_config()

        data = {
            'type': 'deletebilling',
            'client_id': config['client_id'],
            'trx_id': order_id,
        }

        try:
            response = self._call_p2h_api(data)

            if response and response.get('status') == '000':
                return {
                    'success': True,
                    'message': 'Billing deleted successfully',
                    'raw_response': response
                }
            else:
                error_msg = response.get(
                    'message', 'Unknown error') if response else 'No response'
                return {
                    'success': False,
                    'message': error_msg,
                    'raw_response': response
                }
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
                'raw_response': {}
            }

    def update_billing(self, order_id, amount, customer_details, expiry_time=None):
        """
        Update existing billing via BSI P2H API.
        """
        config = self._validate_config()

        customer_no = ''.join(filter(str.isalnum, order_id))[-12:]
        virtual_account = self._generate_virtual_account(customer_no)

        if not expiry_time:
            expiry_time = self._format_datetime_expired(
                config['expiry_duration'])

        data = {
            'type': 'updatebilling',
            'client_id': config['client_id'],
            'trx_id': order_id,
            'trx_amount': str(int(amount)),
            'customer_name': customer_details.get('first_name', 'Customer'),
            'customer_email': customer_details.get('email', ''),
            'customer_phone': customer_details.get('phone', ''),
            'virtual_account': virtual_account,
            'datetime_expired': expiry_time,
            'description': f'Updated billing {order_id}'
        }

        response = self._call_p2h_api(data)

        if response and response.get('status') == '000':
            return {
                'success': True,
                'message': 'Billing updated successfully',
                'raw_response': response
            }
        else:
            error_msg = response.get(
                'message', 'Unknown error') if response else 'No response'
            raise UserError(f"BSI Update Billing Error: {error_msg}")

    def process_reconciliation(self, data_list):
        """
        Process BSI reconciliation data (from POST /api/bpi-bi-snap/reconciliation).

        Each item in data_list should contain transaction details.
        """
        _logger.info(f"[BSI] Processing reconciliation for {len(data_list)} items")
        results = []

        for item in data_list:
            # Expected fields: id_rekon, kode_biller, total_pembayaran, nama, wkt_transaksi, status
            rekon_id = item.get('id_rekon') or item.get('trxId')
            amount = float(item.get('total_pembayaran', 0))
            status = item.get('status', '').lower()

            if not rekon_id:
                continue

            # Find matching transaction by provider_transaction_id or name
            transaction = self.env['smart.billing.transaction'].sudo().search([
                '|',
                ('provider_transaction_id', '=', rekon_id),
                ('name', '=', rekon_id)
            ], limit=1)

            if not transaction:
                # If not found, it might be a missing record. Let's try to find by customer info or skip
                _logger.warning(
                    f"[BSI RECON] Transaction {rekon_id} not found in Odoo. Skipping.")
                results.append({'rc': False, 'idRekon': rekon_id,
                               'message': 'Transaction not found'})
                continue

            # Update status if needed
            if status in ['success', 'settlement', 'paid'] and transaction.state != 'settlement':
                _logger.info(
                    f"[BSI RECON] Updating transaction {transaction.name} to settlement via reconciliation")
                transaction.write({
                    'state': 'settlement',
                    'gross_amount': amount or transaction.gross_amount,
                    'provider_status': status,
                    'settlement_time': fields.Datetime.now()
                })
                transaction._on_payment_settled()

            results.append({'rc': True, 'idRekon': rekon_id})

        return results

    # =========================================================================
    # SNAP BI H2H Helper Methods (used by controller)
    # =========================================================================

    def generate_signature(self, http_method, endpoint_url, body, access_token, timestamp):
        """
        Generate HMAC-SHA512 signature for SNAP BI H2H.

        Used to sign our responses back to BSI.
        """
        config = self.get_config()
        client_secret = config['client_secret']

        # Hash of request body (SNAP BI requires minified JSON string without spaces)
        body_str = json.dumps(body, separators=(',', ':')) if isinstance(body, dict) else str(body)
        hash_body = hashlib.sha256(body_str.encode()).hexdigest().lower()

        # String to sign
        string_to_sign = f"{http_method}:{endpoint_url}:{access_token}:{hash_body}:{timestamp}"

        # HMAC-SHA512 signature
        signature = hmac.new(
            client_secret.encode(),
            string_to_sign.encode(),
            hashlib.sha512
        ).digest()

        return base64.b64encode(signature).decode()

    def verify_signature(self, http_method, endpoint_url, body, access_token, timestamp, signature):
        """
        Verify incoming SNAP BI H2H signature from BSI.
        """
        expected = self.generate_signature(
            http_method, endpoint_url, body, access_token, timestamp)
        return expected == signature
