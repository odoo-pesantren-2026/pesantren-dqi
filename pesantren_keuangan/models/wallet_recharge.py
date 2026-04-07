from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError
from lxml import etree
import logging

_logger = logging.getLogger(__name__)


class WalletRecharge(models.TransientModel):
    _inherit = 'recharge.wallet'

    def _get_partner_id(self):
        context = self._context or {}
        active_id = context.get('active_id', False)
        model = self._context.get('active_model')
        if not active_id:
            _logger.warning("Tidak ada active_id dalam konteks.")
            return False

        partner_id = active_id
        if model == 'cdn.siswa':
            Siswa = self.env['cdn.siswa'].browse(active_id)
            if not Siswa.partner_id:
                _logger.error(
                    f"Tidak ditemukan partner_id untuk siswa {active_id}")
                return False
            partner_id = Siswa.partner_id.id
            _logger.info("Id Dari Partner %s", partner_id)
        return partner_id

    def _default_amount(self):
        if not self.siswa_id:
            return 0

        Partner = self.siswa_id
        dompet = Partner.wallet_balance
        max_wallet = self.env.user.company_id.max_wallet
        return max(0, max_wallet - dompet)

    recharge_amount = fields.Float(
        string='Nominal Saldo', required=True, readonly=False, compute="_compute_recharge_amount", store=True
    )
    siswa_id = fields.Many2one(
        comodel_name='res.partner', string='Siswa', readonly=True, default=lambda self: self._get_partner_id(), ondelete='cascade'
    )
    wallet_balance = fields.Float(
        string='Saldo Dompet', related='siswa_id.wallet_balance', readonly=True)
    saldo_uang_saku = fields.Float(
        string='Saldo Santri', related='siswa_id.saldo_uang_saku', readonly=True)
    recharge_type = fields.Selection(selection=[
        ('manual_based', 'Isi Dompet Manual'),
        ('saku_based', 'Isi Berdasarkan Saldo'),
        ('limit_hari', 'Isi dengan Limit Harian'),
        ('limit_minggu', 'Isi dengan Limit Mingguan'),
        ('limit_bulan', 'Isi dengan Limit Bulanan'),
    ], default='manual_based', string='Tipe Isi Saldo',
        help="Untuk pilihan limit hanya bisa di isi satu kali dan akan ada waktu tunggu penggunaan, untuk isi berdasaarkan saldo akan mengambil keseluruhan saldo yang ada untuk isi dompet.")

    # Batas maksimal saldo yang bisa diisi ulang
    LIMITS = {
        'limit_hari': 50000,
        'limit_minggu': 200000,
        'limit_bulan': 600000,
    }

    def _get_reset_time(self, last_recharge_time):
        """ Menentukan kapan reset saldo terjadi berdasarkan jenis recharge """
        return {
            # 24 jam dari transaksi terakhir
            'limit_hari': last_recharge_time + timedelta(days=1),
            # 7 hari dari transaksi terakhir
            'limit_minggu': last_recharge_time + timedelta(weeks=1),
            # 30 hari dari transaksi terakhir
            'limit_bulan': last_recharge_time + timedelta(days=30),
        }.get(self.recharge_type, last_recharge_time)

    def _check_recharge_limit(self):
        """ Memeriksa apakah transaksi masih dalam periode pembatasan waktu dan saldo """
        now = datetime.now()

        if not self.siswa_id:
            return  # Jika tidak ada siswa, abaikan pengecekan

        last_recharge = self.env['cdn.uang_saku'].search([
            ('siswa_id', '=', self.siswa_id.id),
            ('jns_transaksi', '=', 'keluar'),
            ('keterangan', 'ilike', self.recharge_type)
        ], order='tgl_transaksi desc', limit=1)

        # Jika belum ada transaksi sebelumnya, langsung izinkan
        if not last_recharge:
            return

        # Hitung kapan saldo bisa diisi ulang kembali
        reset_time = self._get_reset_time(last_recharge.tgl_transaksi)

        # **PERUBAHAN DI SINI**: Jika masih dalam cooldown, langsung raise error tanpa lanjut ke pengecekan saldo
        if now < reset_time:
            remaining_time = reset_time - now
            days, remainder = divmod(
                remaining_time.total_seconds(), 86400)  # Konversi ke hari
            hours, remainder = divmod(remainder, 3600)
            minutes, _ = divmod(remainder, 60)

            limit_labels = {
                'limit_hari': 'Waktu limit harian Anda :',
                'limit_minggu': 'Waktu limit mingguan Anda :',
                'limit_bulan': 'Waktu limit bulanan Anda :',
            }
            limit_message = limit_labels.get(
                self.recharge_type, "Waktu limit tidak diketahui")

            raise UserError(
                f"⚠️ Validasi\n\n"
                f"Anda tidak bisa melakukan pengisian ulang sekarang.\n"
                f"{limit_message} {int(days)} hari {int(hours)} jam {int(minutes)} menit\n"
                f"Silahkan coba lagi jika cooldown limit sudah berakhir."
            )

        # **PERBAIKAN LAINNYA**: Pastikan hanya transaksi dalam periode yang sama dihitung
        batas_saldo = self.LIMITS.get(self.recharge_type, float('inf'))
        total_pengisian = sum(self.env['cdn.uang_saku'].search([
            ('siswa_id', '=', self.siswa_id.id),
            ('jns_transaksi', '=', 'keluar'),
            ('keterangan', 'ilike', self.recharge_type),
            # Hanya transaksi dalam periode ini
            ('tgl_transaksi', '>=', now - timedelta(days=1))
        ]).mapped('amount_out')) + self.recharge_amount

        if total_pengisian > batas_saldo:
            raise models.UserError(
                f"Total pengisian untuk {self.recharge_type} melebihi batas Rp {batas_saldo}. Sisa yang bisa diisi: Rp {batas_saldo - (total_pengisian - self.recharge_amount)}."
            )

    @api.depends('recharge_type')
    def _compute_recharge_amount(self):
        for record in self:
            if record.recharge_type == 'manual_based':
                record.recharge_amount = 0  # Biarkan pengguna memasukkan secara manual
            elif record.recharge_type == 'saku_based':
                record.recharge_amount = record.saldo_uang_saku
            else:
                # Langsung gunakan limit tanpa mempertimbangkan saldo uang saku
                record.recharge_amount = self.LIMITS.get(
                    record.recharge_type, 0)

    @api.model
    def default_get(self, fields):
        res = super(WalletRecharge, self).default_get(fields)

        # Cari jurnal yang sesuai dengan perusahaan aktif
        default_journal = self.env['account.journal'].search([
            ('name', '=', 'Jurnal Dompet Santri'),
            # Sesuai dengan perusahaan pengguna saat ini
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        if default_journal:
            res['journal_id'] = default_journal.id  # Set nilai default

        return res

    def post(self):
        """ Proses pengisian ulang """
        self._check_recharge_limit()

        if self.recharge_amount < 1000:
            raise UserError(
                '⚠️Nilai recharge dompet harus lebih dari 1000 Rupiah.')

        if (self.saldo_uang_saku or 0) < self.recharge_amount:
            raise UserError('⚠️Saldo Uang Saku Tidak Cukup!')

        if not self.journal_id:
            raise UserError(
                "⚠️Journal tidak ditemukan, harap pilih journal yang valid.")

        AccountPayment = self.env['account.payment']
        Partner = self.siswa_id
        date_now = datetime.strftime(datetime.now(), '%Y-%m-%d')
        timestamp = fields.Datetime.now()

        payment_create = AccountPayment.sudo().create({
            'name': self.env['ir.sequence'].with_context(ir_sequence_date=date_now).next_by_code('account.payment.customer.invoice'),
            'payment_type': "inbound",
            'amount': self.recharge_amount,
            'date': datetime.now().date(),
            'journal_id': self.journal_id.id,
            'payment_method_id': 1,
            'partner_type': 'customer',
            'partner_id': Partner.id,
        })
        payment_create.action_post()

        # Buat transaksi dompet
        self.env['pos.wallet.transaction'].sudo().create({
            'wallet_type': 'kas',
            'reference': 'manual',
            'amount': self.recharge_amount,
            'partner_id': Partner.id,
            'currency_id': Partner.property_product_pricelist.currency_id.id,
        })

        Partner.write({'wallet_balance': Partner.calculate_wallet()})

        # Catat transaksi uang saku
        self.env['cdn.uang_saku'].sudo().create({
            'tgl_transaksi': timestamp,
            'siswa_id': Partner.id,
            'jns_transaksi': 'keluar',
            'amount_out': self.recharge_amount,
            'validasi_id': self.env.user.id,
            'validasi_time': timestamp,
            'keterangan': f'Wallet Recharge - {self.recharge_type}',
            'state': 'confirm',
        })

        Partner.write({'saldo_uang_saku': Partner.calculate_saku()})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Pengisian Saldo Berhasil !',
                'message': f'Nominal Rp {self.recharge_amount:,.0f} telah berhasil ditambahkan ke dompet {Partner.name}.',
                'type': 'success',
                'sticky': False,
                # Menutup form setelah notifikasi
                'next': {'type': 'ir.actions.act_window_close'}
            },
        }
