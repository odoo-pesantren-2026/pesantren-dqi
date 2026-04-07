from odoo import api, fields, models
import datetime
import random
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    virtual_account = fields.Char(string='Virtual Account', store=True)
    va_saku = fields.Char(string='No. VA Uang Saku', store=True)
    saldo_uang_saku = fields.Float(
        string='Saldo Santri', compute='_compute_saldo_uang_saku', store=True)
    wallet_balance = fields.Float(
        string='Saldo Dompet', compute='_compute_saldo_uang_saku', store=True)
    wallet_pin = fields.Char(string='PIN Dompet', store=True)
    has_wallet_pin = fields.Boolean(
        string='Apakah ada Wallet PIN', compute='_compute_has_wallet_pin', store=True, readonly=True)
    nis = fields.Char(string="No Induk Siswa",
                      related='siswa_id.nis', readonly=True)
    barcode_santri = fields.Char(
        string="Barcode Santri", related='siswa_id.barcode_santri', ondelete='cascade', store=True)
    siswa_id = fields.One2many('cdn.siswa', 'partner_id', string='Siswa')
    name = fields.Char(string='Siswa')

    def _generate_virtual_account(self, nis):
        """Generate Virtual Account untuk Partner."""
        kode_va_bank = "88810"
        account_type = "01"  # Tipe untuk akun utama
        nis2 = nis.replace(".", "")

        virtual_account = f"{kode_va_bank}{account_type}{nis2}"

        return virtual_account

    def _generate_va_uangsaku(self, nis):
        """Generate Virtual Account untuk Uang Saku."""
        kode_va_bank = "88810"
        account_type = "02"  # Tipe untuk VA Uang Saku
        nis2 = nis.replace(".", "")

        va_saku = f"{kode_va_bank}{account_type}{nis2}"

        return va_saku

    def create_data_account(self):
        """
        Method untuk auto-generate Virtual Account dan VA Uang Saku.
        """
        for partner in self:
            if not partner.nis:
                raise UserError(f"NIS untuk {partner.name} belum dibuat.")

            partner.virtual_account = partner._generate_virtual_account(
                partner.nis)
            partner.va_saku = partner._generate_va_uangsaku(partner.nis)

            # Generate PIN dompet jika belum ada
            if not partner.wallet_pin:
                partner.wallet_pin = str(random.randint(1000, 9999))
        return True

    @api.depends('siswa_id')
    def _compute_saldo_uang_saku(self):
        for partner in self:
            partner.saldo_uang_saku = partner.calculate_saku()

    def calculate_wallet(self):
        WalletTransaction = self.env['pos.wallet.transaction'].search(
            [('partner_id', '=', self.id)])
        total_amount = 0
        for transaction in WalletTransaction:
            if transaction.wallet_type == 'debit':
                total_amount = total_amount - float(transaction.amount)
            else:
                total_amount = total_amount + float(transaction.amount)
        return total_amount

    def calculate_saku(self, timestamp=None):
        self.ensure_one()
        domain = [('siswa_id', '=', self.id), ('state', '=', 'confirm')]
        if timestamp:
            domain.append(('validasi_time', '<', timestamp))

        # Menggunakan read_group untuk kalkulasi di atas database (lebih cepat)
        result = self.env['cdn.uang_saku'].read_group(
            domain, ['amount_in:sum', 'amount_out:sum'], ['siswa_id'])

        if result:
            total_in = result[0].get('amount_in', 0.0)
            total_out = result[0].get('amount_out', 0.0)
            return total_in - total_out

        return 0.0

    @api.depends('wallet_pin')
    def _compute_has_wallet_pin(self):
        for rec in self:
            rec.has_wallet_pin = rec.wallet_pin != False

    @api.model
    def check_wallet_pin(self, args):
        Partner = self.env['res.partner'].browse(args['partner_id'])
        return {'has_wallet_pin': Partner.has_wallet_pin, 'match': Partner.wallet_pin == args['wallet_pin']}
