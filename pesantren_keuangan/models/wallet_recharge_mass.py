from datetime import datetime, timedelta
from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class WalletRechargeMass(models.TransientModel):
    _inherit = 'recharge.wallet.mass'

    def _get_partner_ids(self):
        context = self._context or {}
        active_ids = context.get('active_ids', [])
        active_model = context.get('active_model')
        
        if not active_ids:
            _logger.warning("Tidak ada active_ids dalam konteks.")
            return []

        partner_ids = []
        if active_model == 'res.partner':
            partner_ids = active_ids
        elif active_model == 'cdn.siswa':
            siswa_records = self.env['cdn.siswa'].browse(active_ids)
            partner_ids = siswa_records.mapped('partner_id.id')
        
        _logger.info("Id Dari Partner Select %s", partner_ids)
        return partner_ids

    siswa_ids = fields.Many2many(
        'res.partner', 
        string='Santri', 
        required=True,
        default=lambda self: self._get_partner_ids(),
        ondelete='cascade'
    )

    recharge_amount = fields.Float(
        string='Nominal Saldo', required=True, readonly=False, compute="_compute_recharge_amount", store=True
    )

    recharge_type = fields.Selection(selection=[
        ('manual_based', 'Isi Dompet Manual'),
        # ('saku_based', 'Isi Berdasarkan Saldo'),
        ('limit_hari', 'Isi dengan Limit Harian'),
        ('limit_minggu', 'Isi dengan Limit Mingguan'),
        ('limit_bulan', 'Isi dengan Limit Bulanan'),
    ], default='manual_based', string='Tipe Isi Saldo', 
       help="Untuk pilihan limit hanya bisa di isi satu kali dan akan ada waktu tunggu penggunaan.")
    
    siswa_id = fields.Many2one(
        comodel_name='res.partner',  
        string='Siswa', 
        readonly=True,
        default=lambda self: self._get_partner_ids(),
        ondelete='cascade'
    )
    
    wallet_balance = fields.Float(
        string='Saldo Dompet', 
        related='siswa_id.wallet_balance', 
        readonly=True
    )
    saldo_uang_saku = fields.Float(
        string='Saldo Santri', 
        related='siswa_id.saldo_uang_saku', 
        readonly=True
    )

    LIMITS = {
        'limit_hari': 50000,
        'limit_minggu': 200000,
        'limit_bulan': 600000,
    }

    def _get_reset_time(self, last_recharge_time, recharge_type):
        return {
            'limit_hari': last_recharge_time + timedelta(days=1),
            'limit_minggu': last_recharge_time + timedelta(weeks=1),
            'limit_bulan': last_recharge_time + timedelta(days=30),
        }.get(recharge_type, last_recharge_time)

    def _check_recharge_limit(self):
        now = datetime.now()
        santri_terkena_limit = []

        for partner in self.siswa_ids:
            last_recharge = self.env['cdn.uang_saku'].search([
                ('siswa_id', '=', partner.id),
                ('jns_transaksi', '=', 'keluar'),
                ('keterangan', 'ilike', self.recharge_type)
            ], order='tgl_transaksi desc', limit=1)

            if last_recharge:
                reset_time = self._get_reset_time(last_recharge.tgl_transaksi, self.recharge_type)
                if now < reset_time:
                    remaining_time = reset_time - now
                    days, remainder = divmod(remaining_time.total_seconds(), 86400)  # 1 hari = 86400 detik
                    hours, remainder = divmod(remainder, 3600)  # 1 jam = 3600 detik
                    minutes, _ = divmod(remainder, 60)  # 1 menit = 60 detik

                    santri_terkena_limit.append(
                        f"{partner.name} - {int(days)} hari {int(hours)} jam {int(minutes)} menit"
                    )
                    
        if santri_terkena_limit:
            raise UserError(
                "Santri berikut terkena limit pengisian ulang:\n- " + "\n- ".join(santri_terkena_limit)
            )

            #      if santri_terkena_limit:
            # raise models.UserError(
            #     f"⚠ Validasi\n\n"
            #     f"Santri berikut terkena limit pengisian ulang:\n- " + "\n- ".join(santri_terkena_limit)
            #     f"Silahkan coba lagi jika cooldown limit sudah berakhir."
            # )

    # @api.depends('recharge_type', 'siswa_ids')
    # def _compute_recharge_amount(self):
    #     for record in self:
    #         if record.recharge_type == 'manual_based':
    #             record.recharge_amount = 0  # Biarkan pengguna memasukkan secara manual
    #         else:
    #             batas_saldo = self.LIMITS.get(record.recharge_type, float('inf'))
    #             total_saldo = sum(record.siswa_ids.mapped('saldo_uang_saku'))  # Total saldo dari semua santri
    #             record.recharge_amount = min(batas_saldo, total_saldo)  # Pilih jumlah terkecil


    # @api.depends('recharge_type')
    # def _compute_recharge_amount(self):
    #     for record in self:
    #         if record.recharge_type == 'manual_based':
    #             record.recharge_amount = 0 
    #         else:
    #             batas_saldo = self.LIMITS.get(record.recharge_type, 0)
    #             record.recharge_amount = batas_saldo 
            
    #         _logger.info(f"Set Recharge Amount: {record.recharge_amount} untuk tipe {record.recharge_type}")


    @api.depends('recharge_type')
    def _compute_recharge_amount(self):
        for record in self:
            if record.recharge_type == 'manual_based':
                record.recharge_amount = 0  # Biarkan pengguna memasukkan secara manual
            elif record.recharge_type == 'saku_based':
                record.recharge_amount = record.saldo_uang_saku 
            else:
                record.recharge_amount = self.LIMITS.get(record.recharge_type, 0)  # Langsung gunakan limit tanpa mempertimbangkan saldo uang saku

    @api.model
    def default_get(self, fields):
        res = super(WalletRechargeMass, self).default_get(fields)

        # Cari jurnal yang sesuai dengan perusahaan aktif
        default_journal = self.env['account.journal'].search([
            ('name', '=', 'Jurnal Dompet Santri'),
            ('company_id', '=', self.env.company.id)  # Sesuai dengan perusahaan pengguna saat ini
        ], limit=1)

        if default_journal:
            res['journal_id'] = default_journal.id  # Set nilai default

        return res

    def post(self):

        self._check_recharge_limit()

        insufficient_balance_students = []
        
        # for partner in self.siswa_ids:
        #     if self.recharge_type (partner.saldo_uang_saku or 0) < self.recharge_amount:
        #         insufficient_balance_students.append(partner.name)

        for partner in self.siswa_ids:
            saldo_santri = partner.saldo_uang_saku or 0
            if saldo_santri <  self.recharge_amount:
                insufficient_balance_students.append(partner.name)


        if insufficient_balance_students:
            raise models.UserError(
                f"Saldo Uang Saku tidak mencukupi untuk santri berikut:\n- " + "\n- ".join(insufficient_balance_students)
            )

        if self.recharge_amount < 1000:
            raise models.UserError('Nilai recharge dompet harus lebih dari 1000 Rupiah.')

        if not self.journal_id:
            raise models.UserError("Journal tidak ditemukan, harap pilih journal yang valid.")

        AccountPayment = self.env['account.payment']
        date_now = datetime.strftime(datetime.now(), '%Y-%m-%d')
        timestamp = fields.Datetime.now()

        for partner in self.siswa_ids:
            payment_create = AccountPayment.sudo().create({
                'name': self.env['ir.sequence'].with_context(ir_sequence_date=date_now).next_by_code('account.payment.customer.invoice'),
                'payment_type': "inbound",
                'amount': self.recharge_amount,
                'date': datetime.now().date(),
                'journal_id': self.journal_id.id,
                'payment_method_id': 1,
                'partner_type': 'customer',
                'partner_id': partner.id,
            })
            payment_create.action_post()

            self.env['pos.wallet.transaction'].sudo().create({
                'wallet_type': 'kas',
                'reference': 'manual',
                'amount': self.recharge_amount,
                'partner_id': partner.id,
                'currency_id': partner.property_product_pricelist.currency_id.id,
            })

            partner.write({'wallet_balance': partner.calculate_wallet()})

            # Catat transaksi uang saku
            self.env['cdn.uang_saku'].sudo().create({
                'tgl_transaksi': timestamp,
                'siswa_id': partner.id,
                'jns_transaksi': 'keluar',
                'amount_out': self.recharge_amount,
                'validasi_id': self.env.user.id,
                'validasi_time': timestamp,
                'keterangan': f'Wallet Recharge - {self.recharge_type}',
                'state': 'confirm',
            })

            partner.write({'saldo_uang_saku': partner.calculate_saku()})

        return {'type': 'ir.actions.act_window_close'}
