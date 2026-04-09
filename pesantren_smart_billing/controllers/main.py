# -*- coding: utf-8 -*-

from odoo import http, fields
from odoo.http import request
from datetime import datetime
import logging
import json
import hashlib
import hmac
import base64

_logger = logging.getLogger(__name__)

# DEBUG: Log when controller module is imported
_logger.info("========================================")
_logger.info("[SMART BILLING] Controller module LOADED")
_logger.info("========================================")

# BSI Public Key for signature verification
BSI_PUBLIC_KEY = '''-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA8IpXqI86bzWnD/6T4odb
12YCrRX2I/4WGmFvQuOe4hpFPLMh+bjeGbbgoIUUiWcK0QHUzPh3rE+kZGK5N71a
kr/bMfZHBsepz1vrkSSVF9SafTTZNWlM48Nxf71Pxw1F3+5xiOzOVbJ5mOyzVKVM
lxOtUzkPLp7H22bncaJjUUueCUtJ2KNN0SEh45oOQuhgfcoiwR996z38fv9edLNO
DLrcmpJGBXD4XtOLgqkxRnUv2WaBg7CsPbtQhAw8+u33/F+MMHfPn05bZk/lCv2F
frCZceEQmWLFs+YSUYtmfptRfqOwRunSTF+UVUJclSmZ7g5yyE6s87FYBh/8iFeR
2wIDAQAB
-----END PUBLIC KEY-----'''


class SmartBillingController(http.Controller):
    """
    Controller for Smart Billing webhooks and callbacks.
    """

    # =========================================================================
    # BSI SNAP BI H2H Endpoints
    # =========================================================================

    @http.route('/api/v1.0/access-token/b2b', type='http', auth='public', methods=['POST'], csrf=False)
    def bsi_auth(self):
        """
        BSI SNAP BI Authentication endpoint.
        Path: /api/v1.0/access-token/b2b
        """
        try:
            all_headers = dict(request.httprequest.headers)
            _logger.info(f"[BSI AUTH] Headers: {all_headers}")

            x_signature = all_headers.get('X-Signature', '')
            x_client_key = all_headers.get('X-Client-Key', '')
            x_timestamp = all_headers.get('X-Timestamp', '')

            # Verify signature using BSI public key
            data_to_verify = f"{x_client_key}|{x_timestamp}"

            if self._verify_bsi_auth_signature(data_to_verify, x_signature):
                token = self._generate_access_token()
                response = {
                    'responseCode': '2000000',
                    'responseMessage': 'Auth Success',
                    'accessToken': token,
                    'tokenType': 'BearerToken',
                    'expiresIn': 900
                }
                _logger.info(f"[BSI AUTH] Success")
                return request.make_response(json.dumps(response), headers=[('Content-Type', 'application/json')])
            else:
                _logger.warning("[BSI AUTH] Invalid signature")
                return request.make_response(json.dumps({
                    'responseCode': '4010000',
                    'responseMessage': 'Unauthorized'
                }), status=401, headers=[('Content-Type', 'application/json')])
        except Exception as e:
            _logger.error(f"[BSI AUTH] Error: {e}")
            return request.make_response(json.dumps({
                'responseCode': '5002400',
                'responseMessage': f'General Error: {str(e)}'
            }), status=500, headers=[('Content-Type', 'application/json')])

    @http.route('/api/v1.0/transfer-va/inquiry', type='http', auth='public', methods=['POST'], csrf=False)
    def bsi_inquiry(self):
        """
        BSI SNAP BI Inquiry endpoint.
        Path: /api/v1.0/transfer-va/inquiry
        """
        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
            all_headers = dict(request.httprequest.headers)

            _logger.info(
                f"[BSI INQUIRY] Request: {json.dumps(data, indent=2)}")

            # Extract headers
            x_signature = all_headers.get('X-Signature', '')
            x_partner_id = all_headers.get('X-Partner-Id', '')
            x_external_id = all_headers.get('X-External-Id', '')
            x_timestamp = all_headers.get('X-Timestamp', '')
            authorization = all_headers.get('Authorization', '')

            access_token = authorization[7:] if authorization.startswith(
                'Bearer ') else ''

            # Verify signature & token
            if not self._verify_snap_signature('POST', '/api/v1.0/transfer-va/inquiry', data, access_token, x_timestamp, x_signature):
                return request.make_response(json.dumps({'responseCode': '4012400', 'responseMessage': 'Invalid Signature'}), status=401, headers=[('Content-Type', 'application/json')])

            if not self._is_token_valid(access_token):
                return request.make_response(json.dumps({'responseCode': '4012401', 'responseMessage': 'Invalid Token'}), status=401, headers=[('Content-Type', 'application/json')])

            customer_no = data.get('customerNo', '')
            result = self._find_tagihan_by_customer_no(
                customer_no, x_partner_id)

            if result:
                response = {
                    'responseCode': '2002400',
                    'responseMessage': 'Success',
                    'virtualAccountData': {
                        'partnerServiceId': x_partner_id.rjust(8),
                        'customerNo': customer_no,
                        'virtualAccountNo': x_partner_id.rjust(8) + customer_no,
                        'virtualAccountName': result['customer_name'],
                        'inquiryRequestId': x_external_id,
                        'totalAmount': {'value': str(int(result['amount'])), 'currency': 'IDR'},
                        'additionalInfo': result.get('additional_info', [])
                    }
                }
                return request.make_response(json.dumps(response), headers=[('Content-Type', 'application/json')])
            else:
                return request.make_response(json.dumps({'responseCode': '4042412', 'responseMessage': 'Tagihan Tidak Ditemukan'}), status=404, headers=[('Content-Type', 'application/json')])
        except Exception as e:
            _logger.error(f"[BSI INQUIRY] Error: {e}")
            return request.make_response(json.dumps({'responseCode': '5002400', 'responseMessage': f'General Error: {str(e)}'}), status=500, headers=[('Content-Type', 'application/json')])

    @http.route('/api/v1.0/transfer-va/payment', type='http', auth='public', methods=['POST'], csrf=False)
    def bsi_payment(self):
        """
        BSI SNAP BI Payment notification endpoint.
        Path: /api/v1.0/transfer-va/payment
        """
        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
            all_headers = dict(request.httprequest.headers)

            _logger.info(
                f"[BSI PAYMENT] Request: {json.dumps(data, indent=2)}")

            # Extract headers
            x_signature = all_headers.get('X-Signature', '')
            x_partner_id = all_headers.get('X-Partner-Id', '')
            x_external_id = all_headers.get('X-External-Id', '')
            x_timestamp = all_headers.get('X-Timestamp', '')
            authorization = all_headers.get('Authorization', '')

            access_token = authorization[7:] if authorization.startswith(
                'Bearer ') else ''

            # Verify signature & token
            if not self._verify_snap_signature('POST', '/api/v1.0/transfer-va/payment', data, access_token, x_timestamp, x_signature):
                return request.make_response(json.dumps({'responseCode': '4012500', 'responseMessage': 'Invalid Signature'}), status=401, headers=[('Content-Type', 'application/json')])

            if not self._is_token_valid(access_token):
                return request.make_response(json.dumps({'responseCode': '4012401', 'responseMessage': 'Invalid Token'}), status=401, headers=[('Content-Type', 'application/json')])

            customer_no = data.get('customerNo', '')
            paid_amount = data.get('paidAmount', {})
            payment_request_id = data.get('paymentRequestId', x_external_id)
            trx_datetime = data.get('trxDateTime', '')

            amount = float(paid_amount.get('value', 0)) if isinstance(
                paid_amount, dict) else float(paid_amount or 0)

            result = self._process_bsi_payment(
                customer_no, amount, payment_request_id, trx_datetime, x_partner_id)

            if result['success']:
                response = {
                    'responseCode': '2002500',
                    'responseMessage': 'Success'
                }
                return request.make_response(json.dumps(response), headers=[('Content-Type', 'application/json')])
            else:
                return request.make_response(json.dumps({'responseCode': '5002500', 'responseMessage': result.get('message', 'Payment processing failed')}), status=500, headers=[('Content-Type', 'application/json')])
        except Exception as e:
            _logger.error(f"[BSI PAYMENT] Error: {e}")
            return request.make_response(json.dumps({'responseCode': '5002500', 'responseMessage': f'General Error: {str(e)}'}), status=500, headers=[('Content-Type', 'application/json')])

    @http.route('/api/v1.0/transfer-va/advice', type='http', auth='public', methods=['POST'], csrf=False)
    def bsi_advice(self):
        """
        BSI SNAP BI Advice endpoint.
        Path: /api/v1.0/transfer-va/advice
        Used to verify status of a previous payment.
        """
        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
            all_headers = dict(request.httprequest.headers)
            _logger.info(f"[BSI ADVICE] Request: {json.dumps(data)}")

            x_signature = all_headers.get('X-Signature', '')
            x_timestamp = all_headers.get('X-Timestamp', '')
            authorization = all_headers.get('Authorization', '')
            access_token = authorization[7:] if authorization.startswith('Bearer ') else ''

            if not self._verify_snap_signature('POST', '/api/v1.0/transfer-va/advice', data, access_token, x_timestamp, x_signature):
                return request.make_response(json.dumps({'responseCode': '4012500', 'responseMessage': 'Invalid Signature'}), status=401, headers=[('Content-Type', 'application/json')])

            payment_request_id = data.get('paymentRequestId', '')
            customer_no = data.get('customerNo', '')

            # Advice should return same success as Payment if record exists
            transaction = request.env['smart.billing.transaction'].sudo().search([
                ('provider_transaction_id', '=', payment_request_id),
                ('provider', '=', 'bsi')
            ], limit=1)

            if transaction and transaction.state == 'settlement':
                if customer_no and transaction.va_number and customer_no not in transaction.va_number:
                    return request.make_response(json.dumps({'responseCode': '4002500', 'responseMessage': 'Customer number mismatch'}), status=400, headers=[('Content-Type', 'application/json')])

                return request.make_response(json.dumps({'responseCode': '2002500', 'responseMessage': 'Success'}), headers=[('Content-Type', 'application/json')])
            else:
                return request.make_response(json.dumps({'responseCode': '4042512', 'responseMessage': 'Payment record not found'}), status=404, headers=[('Content-Type', 'application/json')])
        except Exception as e:
            _logger.error(f"[BSI ADVICE] Error: {e}")
            return request.make_response(json.dumps({'responseCode': '5002500', 'responseMessage': f'General Error: {str(e)}'}), status=500, headers=[('Content-Type', 'application/json')])

    @http.route('/api/bpi-bi-snap/reconciliation', type='http', auth='public', methods=['POST'], csrf=False)
    def bsi_reconciliation(self):
        """
        BSI Web Service Reconciliation endpoint.
        Path: /api/bpi-bi-snap/reconciliation
        """
        try:
            payload = json.loads(request.httprequest.data.decode('utf-8'))
            _logger.info(f"[BSI RECON] Action: {payload.get('action')}")

            data_list = payload.get('data', [])
            bsi_provider = request.env['smart.billing.provider.bsi'].sudo()
            results = bsi_provider.process_reconciliation(data_list)

            return request.make_response(json.dumps(results), headers=[('Content-Type', 'application/json')])
        except Exception as e:
            _logger.error(f"[BSI RECON] Error: {e}")
            return request.make_response(json.dumps([{'rc': False, 'message': str(e)}]), status=500, headers=[('Content-Type', 'application/json')])

    # =========================================================================
    # BSI Helper Methods
    # =========================================================================

    def _verify_bsi_auth_signature(self, data, signature):
        """Verify BSI auth signature using their public key"""
        try:
            ICP = request.env['ir.config_parameter'].sudo()
            is_production = ICP.get_param(
                'smart_billing.is_production', 'False') == 'True'
            use_mockup = ICP.get_param(
                'smart_billing.bsi_use_mockup', 'False') == 'True'

            # Mockup mode hanya diizinkan di NON-PRODUKSI
            if use_mockup and not is_production:
                _logger.info(
                    "[BSI AUTH] Mockup mode enabled (non-production), skipping signature verification")
                return True

            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.backends import default_backend

            public_key = serialization.load_pem_public_key(
                BSI_PUBLIC_KEY.encode(),
                backend=default_backend()
            )

            public_key.verify(
                base64.b64decode(signature),
                data.encode(),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return True
        except ImportError:
            _logger.error(
                "[BSI] Critical: cryptography library not installed. Cannot verify signature.")
            return False
        except Exception as e:
            _logger.error(f"[BSI] Signature verification error: {e}")
            return False

    def _verify_snap_signature(self, http_method, endpoint_url, body, access_token, timestamp, signature):
        """Verify SNAP BI signature using HMAC-SHA512"""
        try:
            ICP = request.env['ir.config_parameter'].sudo()
            is_production = ICP.get_param(
                'smart_billing.is_production', 'False') == 'True'
            use_mockup = ICP.get_param(
                'smart_billing.bsi_use_mockup', 'False') == 'True'

            # Mockup mode hanya diizinkan di NON-PRODUKSI
            if use_mockup and not is_production:
                _logger.info(
                    "[BSI] Mockup mode enabled (non-production), skipping signature verification")
                return True

            client_secret = ICP.get_param(
                'smart_billing.bsi_client_secret', '')

            if not client_secret:
                _logger.warning(
                    "[BSI] Client secret not configured. Failing verification.")
                return False

            # Hash of request body
            body_str = json.dumps(body) if isinstance(
                body, dict) else str(body)
            hash_body = hashlib.sha256(body_str.encode()).hexdigest().lower()

            # String to sign
            string_to_sign = f"{http_method}:{endpoint_url}:{access_token}:{hash_body}:{timestamp}"

            # HMAC-SHA512 signature
            expected_sig = hmac.new(
                client_secret.encode(),
                string_to_sign.encode(),
                hashlib.sha512
            ).digest()
            expected_sig_b64 = base64.b64encode(expected_sig).decode()

            return expected_sig_b64 == signature

        except Exception as e:
            _logger.error(f"[BSI] SNAP signature verification error: {e}")
            return False

    def _generate_access_token(self):
        """Generate simple access token"""
        import secrets
        token = secrets.token_hex(32)

        # Store token in config parameter with expiry
        ICP = request.env['ir.config_parameter'].sudo()
        tokens_str = ICP.get_param('smart_billing.bsi_tokens', '{}')
        try:
            tokens = json.loads(tokens_str)
        except:
            tokens = {}

        # Add new token with expiry (15 minutes)
        expiry = (datetime.now().timestamp() + 900)
        tokens[token] = expiry

        # Clean expired tokens
        now = datetime.now().timestamp()
        tokens = {k: v for k, v in tokens.items() if v > now}

        ICP.set_param('smart_billing.bsi_tokens', json.dumps(tokens))

        return token

    def _is_token_valid(self, token):
        """Check if access token is valid"""
        # Skip token validation if mockup mode is enabled
        ICP = request.env['ir.config_parameter'].sudo()
        use_mockup = ICP.get_param(
            'smart_billing.bsi_use_mockup', 'False') == 'True'
        if use_mockup:
            _logger.info(
                "[BSI] Mockup mode enabled, skipping token validation")
            return True

        tokens_str = ICP.get_param('smart_billing.bsi_tokens', '{}')
        try:
            tokens = json.loads(tokens_str)
        except:
            tokens = {}

        if token not in tokens:
            return False

        # Check expiry
        if tokens[token] < datetime.now().timestamp():
            return False

        return True

    def _find_tagihan_by_customer_no(self, customer_no, partner_id):
        """
        Find tagihan by customer number.

        customerNo could be:
        - NIS santri (for permanent VA / top-up)
        - Invoice reference number
        - Smart billing transaction customer_no
        """
        _logger.info(f"[BSI] Finding tagihan for customer_no: {customer_no}")
        
        # Get BSI Client ID to reconstruct exact VA Number
        bsi_provider = request.env['smart.billing.provider.bsi'].sudo()
        config = bsi_provider.get_config()
        client_id = config.get('client_id', partner_id)

        # First, try to find by smart billing transaction (most specific)
        # Search by name (contains customer_no in format) or va_number
        # Gunakan '=' untuk pencocokan persis agar tidak salah menemukan transaksi lain
        transaction = request.env['smart.billing.transaction'].sudo().search([
            '|', '|',
            ('name', '=', customer_no),
            ('va_number', '=', customer_no),
            ('va_number', '=', f"{client_id}{customer_no}"),
        ], limit=1)

        if transaction:
            _logger.info(f"[BSI] Found transaction: {transaction.name}")
            return {
                'customer_name': transaction.partner_id.name,
                'amount': transaction.gross_amount,
                'type': 'transaction',
                'transaction_id': transaction.id,
                'partner_id': transaction.partner_id.id,
                'invoice_id': transaction.move_id.id if transaction.move_id else None,
                'client_id': client_id,
                'additional_info': [
                    {'label': 'ORDER', 'value': transaction.name},
                ]
            }

        # Try to find by siswa NIS
        siswa = request.env['cdn.siswa'].sudo().search([
            '|',
            ('nis', '=', customer_no),
            ('nis', '=', customer_no.lstrip('0'))
        ], limit=1)

        if siswa and siswa.partner_id:
            _logger.info(f"[BSI] Found siswa by NIS: {siswa.name}")
            # Check for permanent VA (top-up mode)
            if siswa.partner_id.va_saku:
                # This is a top-up request, return open amount
                return {
                    'customer_name': siswa.name,
                    'amount': 0,  # Open amount
                    'type': 'topup',
                    'siswa_id': siswa.id,
                    'partner_id': siswa.partner_id.id,
                    'additional_info': [
                        {'label': 'NAMA SANTRI', 'value': siswa.name},
                        {'label': 'NIS', 'value': siswa.nis or ''},
                        {'label': 'KELAS',
                            'value': siswa.ruang_kelas_id.name if siswa.ruang_kelas_id else ''},
                    ]
                }

            # Check for unpaid invoices
            invoices = request.env['account.move'].sudo().search([
                ('partner_id', '=', siswa.partner_id.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial'])
            ], order='invoice_date asc', limit=1)

            if invoices:
                invoice = invoices[0]
                return {
                    'customer_name': siswa.name,
                    'amount': invoice.amount_residual,
                    'type': 'invoice',
                    'invoice_id': invoice.id,
                    'siswa_id': siswa.id,
                    'partner_id': siswa.partner_id.id,
                    'additional_info': [
                        {'label': 'NAMA SANTRI', 'value': siswa.name},
                        {'label': 'NIS', 'value': siswa.nis or ''},
                        {'label': 'INVOICE', 'value': invoice.name},
                    ]
                }

        _logger.warning(
            f"[BSI] No tagihan found for customer_no: {customer_no}")
        return None

    def _process_bsi_payment(self, customer_no, amount, payment_request_id, trx_datetime, partner_id):
        """
        Process BSI payment notification.

        - Update transaction status
        - Create uang saku for top-up
        - Reconcile invoice for tagihan
        """
        try:
            # Find tagihan info
            tagihan = self._find_tagihan_by_customer_no(
                customer_no, partner_id)

            if not tagihan:
                return {'success': False, 'message': 'Tagihan tidak ditemukan'}

            # Create or find transaction
            transaction = None

            # Check if this specific payment ID already exists (to avoid duplicates)
            existing_by_pid = request.env['smart.billing.transaction'].sudo().search([
                ('provider_transaction_id', '=', payment_request_id)
            ], limit=1)

            if existing_by_pid:
                _logger.info(
                    f"[BSI PAYMENT] Payment {payment_request_id} already processed in transaction {existing_by_pid.name}")
                transaction = existing_by_pid
            elif tagihan.get('type') == 'transaction':
                transaction = request.env['smart.billing.transaction'].sudo().browse(
                    tagihan['transaction_id'])
                # If the found transaction is already settled and we have a NEW payment ID,
                # it means it's another payment for the same "Permanent VA" ref.
                # In this case, we should create a NEW transaction record.
                if transaction.state == 'settlement' and transaction.transaction_type == 'va_topup':
                    _logger.info(
                        f"[BSI PAYMENT] Existing top-up transaction {transaction.name} is already settled. Creating a NEW record for this payment.")
                    tagihan['force_new_topup'] = True
                    transaction = None  # Force creation below

            if not transaction:
                # Determine transaction type
                is_topup = tagihan.get(
                    'type') == 'topup' or tagihan.get('force_new_topup')

                client_id = tagihan.get('client_id', partner_id)
                # Create new transaction for this payment
                # NOTE: For va_topup, set to settlement immediately
                # For va_tagihan, keep pending - let _on_payment_settled() decide based on full/partial
                initial_state = 'settlement' if is_topup else 'pending'

                transaction = request.env['smart.billing.transaction'].sudo().create({
                    'name': payment_request_id or f"BSI-{customer_no}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    'provider': 'bsi',
                    'transaction_type': 'va_topup' if is_topup else 'va_tagihan',
                    'state': initial_state,
                    'partner_id': tagihan['partner_id'],
                    'move_id': tagihan.get('invoice_id'),
                    'va_number': f"{client_id}{customer_no}",
                    'va_bank': 'BSI',
                    'gross_amount': amount,
                    'transaction_time': fields.Datetime.now(),
                    'settlement_time': fields.Datetime.now(),
                    'provider_transaction_id': payment_request_id,
                    'provider_status': 'settlement',
                })

            elif transaction.state == 'pending' and transaction.transaction_type == 'va_tagihan':
                # For existing tagihan transaction, update with actual paid amount
                # CRITICAL: Must update gross_amount so _reconcile_invoice_payment uses correct amount
                transaction.write({
                    'state': 'settlement',  # Explicitly set to settlement!
                    'gross_amount': amount,
                    'settlement_time': fields.Datetime.now(),
                    'provider_transaction_id': payment_request_id,
                    'provider_status': 'settlement',
                })
            elif transaction.state != 'settlement':
                # For other types (va_topup, active), set settlement
                transaction.write({
                    'state': 'settlement',
                    'settlement_time': fields.Datetime.now(),
                    'gross_amount': amount,
                    'provider_transaction_id': payment_request_id,
                    'provider_status': 'settlement',
                })

            # Process based on type
            if transaction:
                # Use model logic to handle reconcile (va_tagihan) or top-up (va_topup)
                # Add from_webhook context to prevent circular call when updating billing
                transaction.with_context(
                    from_webhook=True)._on_payment_settled()
                _logger.info(
                    f"[BSI PAYMENT] Triggered model logic for {transaction.name}")
            else:
                # Fallback for old/legacy flow without transaction records
                if tagihan.get('type') == 'topup':
                    siswa = request.env['cdn.siswa'].sudo().browse(
                        tagihan.get('siswa_id'))
                    if siswa:
                        uang_saku = request.env['cdn.uang_saku'].sudo().create({
                            'siswa_id': siswa.partner_id.id,
                            'jns_transaksi': 'masuk',
                            'amount_in': amount,
                            'keterangan': f'Top-up via BSI VA (Legacy) - {payment_request_id}',
                            'tgl_transaksi': fields.Datetime.now(),
                        })
                        uang_saku.action_confirm()
                        _logger.info(
                            f"[BSI PAYMENT] Created and confirmed legacy uang saku for {siswa.name}")

                elif tagihan.get('type') == 'invoice':
                    # Reconcile invoice manually
                    invoice = request.env['account.move'].sudo().browse(
                        tagihan.get('invoice_id'))
                    if invoice and invoice.payment_state != 'paid':
                        try:
                            payment_register = request.env['account.payment.register'].sudo().with_context(
                                active_model='account.move',
                                active_ids=invoice.ids,
                            ).create({
                                'amount': amount,
                                'payment_date': fields.Date.today(),
                                'communication': f'BSI Smart Billing (Legacy): {payment_request_id}',
                            })
                            payment = payment_register._create_payments()
                            _logger.info(
                                f"[BSI PAYMENT] Legacy flow: Payment created for invoice {invoice.name}")
                        except Exception as e:
                            _logger.error(
                                f"[BSI PAYMENT] Legacy flow error: {e}")

            return {
                'success': True,
                'customer_name': tagihan['customer_name'],
                'additional_info': tagihan.get('additional_info', [])
            }

        except Exception as e:
            _logger.error(f"[BSI PAYMENT] Processing error: {e}")
            return {'success': False, 'message': str(e)}

    # =========================================================================
    # Generic Webhook Endpoints (for Dummy and other providers)
    # =========================================================================

    @http.route('/smart-billing/notification/dummy', type='json', auth='public', methods=['POST'], csrf=False)
    def dummy_notification(self):
        """Handle Dummy provider notifications (for testing)."""
        return self._process_notification('dummy')

    @http.route('/smart-billing/notification/bsi', type='json', auth='public', methods=['POST'], csrf=False)
    def bsi_notification(self):
        """Handle BSI payment notifications (legacy endpoint)."""
        return self._process_notification('bsi')

    @http.route('/smart-billing/notification/tki', type='json', auth='public', methods=['POST'], csrf=False)
    def tki_notification(self):
        """Handle TKI payment notifications."""
        return self._process_notification('tki')

    def _process_notification(self, provider_code):
        """Process payment notification from any provider."""
        try:
            data = request.jsonrequest
            _logger.info(
                f"[{provider_code.upper()}] Notification: {json.dumps(data, indent=2)}")

            provider = self._get_provider(provider_code)

            if not provider.verify_notification_signature(data):
                return {'status': 'error', 'message': 'Invalid signature'}

            parsed = provider.parse_notification(data)
            order_id = parsed.get('order_id')

            if not order_id:
                return {'status': 'error', 'message': 'Missing order_id'}

            transaction = request.env['smart.billing.transaction'].sudo().search([
                ('name', '=', order_id)
            ], limit=1)

            if transaction:
                transaction._process_notification(data)
                return {'status': 'ok', 'message': 'Transaction updated'}

            return {'status': 'error', 'message': 'Transaction not found'}

        except Exception as e:
            _logger.error(f"[{provider_code.upper()}] Error: {e}")
            return {'status': 'error', 'message': str(e)}

    def _get_provider(self, provider_code):
        """Get provider instance by code"""
        provider_map = {
            'dummy': 'smart.billing.provider.dummy',
            'bsi': 'smart.billing.provider.bsi',
            'tki': 'smart.billing.provider.tki',
        }
        model_name = provider_map.get(
            provider_code, 'smart.billing.provider.dummy')
        return request.env[model_name].sudo()

    # =========================================================================
    # Utility Endpoints
    # =========================================================================

    @http.route('/smart-billing/test', type='http', auth='public', methods=['GET'])
    def test_endpoint(self):
        """Test endpoint to verify webhook is reachable."""
        return "Smart Billing webhook is active!"
