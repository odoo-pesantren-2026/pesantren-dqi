
from odoo import http, fields
from odoo.http import request
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class SiswaController(http.Controller):

    @http.route('/siswa/get_data', type='json', auth='user')
    def get_data(self, domain=None):
        """
        Mengambil data dari model `res.partner` dengan filter domain opsional.

        :param domain: List berisi filter domain Odoo untuk memfilter data siswa (opsional).
        :return: List berisi data siswa sesuai filter yang diberikan.
        """
        try:
            # Jika tidak ada domain, gunakan list kosong agar semua data diambil
            domain = domain or []

            # Jika domain diberikan, batasi hasil pencarian menjadi satu data
            limit = 1 if domain else None

            # Cari data sesuai domain yang diberikan dengan limit jika diperlukan
            siswa_records = request.env['res.partner'].sudo().search(
                domain, limit=limit)

            data = [{
                'partner_id': record.id,
                'name': record.name,
                'nis': record.nis,
                'saldo_uang_saku': record.saldo_uang_saku,
                'pin': record.wallet_pin,
            } for record in siswa_records]

            return data
        except Exception as e:
            return {'error': str(e)}

    @http.route('/siswa/deduct_wallet', type='json', auth='user')
    def deduct_wallet(self, partner_id, amount, order_details=None):
        """
        Mengurangi wallet_balance pada partner yang diberikan dengan amount tertentu.

        :param partner_id: ID dari partner (siswa) yang wallet_balance-nya akan dikurangi.
        :param amount: Jumlah yang akan dikurangi dari wallet_balance.
        :return: Status sukses atau error.
        """
        try:
            if amount <= 0:
                raise UserError(
                    "Jumlah yang dikurangi harus lebih besar dari nol.")

            # Cari partner berdasarkan ID
            partner = request.env['res.partner'].sudo().browse(partner_id)
            santri = request.env['cdn.siswa'].sudo().search(
                [('partner_id', '=', partner_id)], limit=1)
            timestamp = fields.Datetime.now()

            santri = request.env['cdn.siswa'].sudo().search(
                [('partner_id', '=', partner_id)], limit=1)

            if santri.status_akun in ['nonaktif', 'blokir']:
                return {'error': "Pembayaran ini tidak dapat diproses karena statusnya sedang tidak aktif atau telah diblokir. Silakan hubungi pihak pengurus pesantren untuk informasi lebih lanjut."}

            if santri:
                # 1. Pengecekan Limit (Centralized)
                # Ini akan raise UserError jika limit tercapai, yang ditangkap oleh 'except UserError'
                santri._check_limit(amount)

            # Validasi jika partner ditemukan
            if not partner.exists():
                raise UserError("Siswa dengan ID tersebut tidak ditemukan.")

            # Validasi jika saldo mencukupi
            if partner.saldo_uang_saku < amount:
                raise UserError(
                    "Saldo tidak mencukupi untuk melakukan pengurangan.")

            nama_santri = santri.name or "Santri"

            keterangan = self._generate_transaction_description(
                order_details, amount, santri_name=nama_santri)

            transaksi_terbaru = request.env['pos.wallet.transaction'].search([
                ('partner_id', '=', partner_id)
            ], order="create_date desc", limit=1)

            # transaksi_saldo_saku = request.env['cdn_uang_saku'].search([
            #     ('partner_id', '=', partner_id)
            # ], order="create_date desc", limit=1)

            partner.sudo().write(
                {'saldo_uang_saku': partner.saldo_uang_saku - amount})

            request.env['cdn.uang_saku'].sudo().create({
                'tgl_transaksi': timestamp,
                'siswa_id': partner.id,
                'jns_transaksi': 'keluar',
                'amount_out': amount,
                'validasi_id': request.env.user.id,
                'validasi_time': timestamp,
                'keterangan': keterangan,
                'state': 'confirm',
            })

            if transaksi_terbaru:
                transaksi_terbaru.sudo().write({
                    'amount': transaksi_terbaru.amount - amount
                })

            return {'success': True, 'new_balance': partner.saldo_uang_saku}
        except UserError as e:
            return {'error': str(e)}
        except Exception as e:
            return {'error': 'Terjadi kesalahan: ' + str(e)}

    def _generate_transaction_description(self, order_details, amount, santri_name="Santri"):
        """
        Generate deskripsi transaksi pendek, cocok untuk dashboard.
        Contoh hasil: "Transaksi POS atas nama Ahmad: Pembelian 2x Nasi Goreng, 1x Nasi Pecel. Total Rp 30.000"
        """
        try:
            total_amount = order_details.get(
                'total_amount', amount) if order_details else amount
            items = order_details.get('items', []) if order_details else []

            # Susun deskripsi item maksimal 3 biar pendek
            product_lines = []
            for item in items[:3]:
                product_name = item.get('product_name', 'Produk')
                qty = item.get('quantity', 0)
                product_lines.append(f"{qty}x {product_name}")
            if len(items) > 3:
                product_lines.append("dll.")

            return f"Transaksi POS atas nama {santri_name}: Pembelian {', '.join(product_lines)}. Total Rp {total_amount:,.0f}"
        except Exception as e:
            return f"Transaksi POS - Total: Rp {amount:,.0f} (Error: {str(e)})"

    @http.route('/siswa/get_data/bar', type='json', auth='user')
    def get_data_bar(self, barcode=None):
        """
        Mengambil data dari model `res.partner` berdasarkan barcode.

        :param barcode: String berisi barcode untuk memfilter data siswa (opsional).
        :return: Dictionary berisi data siswa sesuai barcode yang diberikan.
        """
        try:
            # Jika barcode tidak diberikan, kembalikan None
            if not barcode:
                return None

            # Cari data siswa berdasarkan barcode, virtual_account, atau va_saku
            siswa_record = request.env['res.partner'].sudo().search([
                '|', '|',
                ('barcode', '=', barcode),
                ('virtual_account', '=', barcode),
                ('va_saku', '=', barcode)
            ], limit=1)

            # Jika tidak ditemukan, kembalikan None
            if not siswa_record:
                return None

            data = {
                'partner_id': siswa_record.id,
                'name': siswa_record.name,
                'nis': siswa_record.nis,
                'wallet_balance': siswa_record.saldo_uang_saku,
                'pin': siswa_record.wallet_pin,
            }

            return data
        except Exception as e:
            _logger.error(
                f"Error fetching data for barcode {barcode}: {str(e)}")
            return None

    @http.route('/siswa/search', type='json', auth='user')
    def search_siswa(self, query=None, no_limit=False, **kw):
        """
        Mencari data siswa berdasarkan query pencariannya.

        :param query: String berisi kata kunci pencarian.
        :param no_limit: Boolean yang menentukan apakah ada batasan jumlah hasil atau tidak.
        :return: Dictionary berisi list data siswa yang cocok dengan pencarian.
        """
        if not query:
            return {'partners': []}

        # Tentukan limit berdasarkan parameter no_limit
        limit = None if no_limit else 100  # Default 100 jika no_limit tidak diaktifkan

        # Cari di database lokal Odoo
        local_partners = request.env['res.partner'].search([
            '|', '|', '|', '|', '|',
            ('name', 'ilike', query),
            ('barcode', 'ilike', query),
            ('nis', 'ilike', query),
            ('phone', 'ilike', query),
            ('virtual_account', 'ilike', query),
            ('va_saku', 'ilike', query)
        ], limit=limit)

        partners_list = local_partners.read(
            ['id', 'name', 'barcode', 'nis', 'saldo_uang_saku', 'virtual_account', 'va_saku', 'street', 'email', 'phone'])

        # Format wallet_balance untuk tampilan
        for partner in partners_list:
            if 'saldo_uang_saku' in partner:
                partner['wallet_balance_display'] = f"Rp {partner['saldo_uang_saku']:,.0f}"

        # Return combined results
        return {
            'partners': partners_list
        }
