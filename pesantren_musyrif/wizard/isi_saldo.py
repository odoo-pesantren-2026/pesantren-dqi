# from odoo import api, fields, models
# from odoo.exceptions import UserError

# class isiSaldo(models.Model):

#     _name               = "recharge.wallet.scan"
#     _description        = "Modul isi saldo santri dengan menggunakan barcode"

#     barcode             = fields.Char(string="Barcode Santri")
#     siswa_id            = fields.Many2one('cdn.siswa', string='Siswa', required=True, readonly=False)
#     journal_id          = fields.Many2one("account.journal", string="Jurnal Pembayaran", help="Pilih jenis jurnal")
#     recharge_amount     = fields.Float(string="Nominal Saldo", required=True, readonly=False, help="Jumlah pengisian ulang di dompet", compute="_compute_recharge_amount")
#     recharge_type       = fields.Selection(selection=[
#                             ('manual_based', 'Isi Dompet Manual'),
#                             ('saku_based', 'Isi Berdasarkan Saldo'),
#                             ('limit_hari', 'Isi dengan Limit Harian'),
#                             ('limit_minggu', 'Isi dengan Limit Mingguan'),
#                             ('limit_bulan', 'Isi dengan Limit Bulanan'),
#                             ], default='manual_based', string='Tipe Isi Saldo', 
#                             help="Untuk pilihan limit hanya bisa di isi satu kali dan akan ada waktu tunggu penggunaan, untuk isi berdasaarkan saldo akan mengambil keseluruhan saldo yang ada untuk isi dompet.")
#     wallet_balance      = fields.Float(string='Saldo Dompet', related='siswa_id.wallet_balance', readonly=True)
#     saldo_uang_saku     = fields.Float(string='Saldo Uang Saku', related='siswa_id.saldo_uang_saku', readonly=True)

#     tgl_transaksi       = fields.Date(string='Tanggal Transaksi', required=True, default=fields.Date.context_today)

#     LIMITS = {
#         'limit_hari': 50000,
#         'limit_minggu': 200000,
#         'limit_bulan': 600000,
#     }
                 
#     @api.onchange('barcode')
#     def _onchange_barcode(self):
#         if self.barcode:
#             siswa = self.env['cdn.siswa'].search([('barcode', '=', self.barcode)], limit=1)
#             if siswa:
#                 self.siswa_id = siswa.id
#             else:
#                 self.siswa_id = False  # Kosongkan jika tidak ditemukan
#                 return {'warning': {'title': "Perhatian!", 'message': f"Tidak ada santri dengan barcode {self.barcode}"}}

            
#     @api.depends('recharge_type')
#     def _compute_recharge_amount(self):
#         for record in self:
#             if record.recharge_type == 'manual_based':
#                 record.recharge_amount = 0
#             elif record.recharge_type == 'saku_based':
#                 record.recharge_amount = record.saldo_uang_saku
#             else:
#                 record.recharge_amount = self.LIMITS.get(record.recharge_type, 0)
    

#     def action_recharge(self):
#         for record in self:
#             if not record.siswa_id:
#                 raise UserError("Silahkan pilih siswa terlebih dahulu")
#             if record.recharge_type == 'manual_based' and record.recharge_amount <=0:
#                 raise UserError("Nominal pengisian saldo harus lebih daru 0")
#             # if record.recharge_type == 'saku_based' and record.saldo_uang_saku <=0:
#             #     raise UserError("Saldo uang saku tidak cukup untuk pengisian !")

#             partner = self.env["res.partner"].search([('id','=', record.siswa_id.id)], limit=1)

#             vals = {
#                 'recharge_amount' : record.recharge_amount,
#                 'recharge_type': record.recharge_type,
#                 'siswa_id' : partner.id if partner else record.siswa_id.id,
#                 'journal_id' : record.journal_id.id,
#             }

#             new_recharge = self.env['recharge.wallet'].write(vals)

#             return {
#                 'name'          : 'Pengisian Saldo Dompet Santri',
#                 'type'          : 'ir.actions.act_window',
#                 'res_id'        :  new_recharge.id,
#                 'view_mode'     : 'form',
#                 'target'        : 'current',
#             }

#         # return {
#         #     'type': 'ir.actions.act_window',
#         #     'res_model': 'cdn.perijinan',
#         #     'view_mode': 'form',
#         #     'res_id': self.perijinan_id.id,
#         #     'target': 'current',
#         # }

#     # @api.depends('barcode')
#     # def _onchange_barcode(self):
#     #     if self.barcode:
#     #         siswa = self.env['cdn.siswa'].search([('barcode', '=', self.barcode)], limit=1)
#     #         if siswa:
#     #             self.siswa_id = siswa.id
#     #     else:
#     #         raise UserError(f"Tidak ada santri dengan barcode {self.barcode}")
    


# from odoo import api, fields, models
# from odoo.exceptions import UserError
# from datetime import datetime, timedelta
# import logging

# _logger = logging.getLogger(__name__)

# class isiSaldo(models.Model):
#     _name = "recharge.wallet.scan"
#     _description = "Isi Saldo Dompet dengan Scan Barcode"

#     barcode = fields.Char(string="Barcode Santri")
#     siswa_id = fields.Many2one('cdn.siswa', string='Siswa', required=True, readonly=False)
#     journal_id = fields.Many2one("account.journal", string="Jurnal Pembayaran", help="Pilih jenis jurnal")
#     recharge_amount = fields.Float(string="Nominal Saldo", required=True, readonly=False, 
#                                   help="Jumlah pengisian ulang di dompet", 
#                                   compute="_compute_recharge_amount", store=True)
#     recharge_type = fields.Selection(selection=[
#                         ('manual_based', 'Isi Dompet Manual'),
#                         ('saku_based', 'Isi Berdasarkan Saldo'),
#                         ('limit_hari', 'Isi dengan Limit Harian'),
#                         ('limit_minggu', 'Isi dengan Limit Mingguan'),
#                         ('limit_bulan', 'Isi dengan Limit Bulanan'),
#                         ], default='manual_based', string='Tipe Isi Saldo',
#                         help="Untuk pilihan limit hanya bisa di isi satu kali dan akan ada waktu tunggu penggunaan, untuk isi berdasaarkan saldo akan mengambil keseluruhan saldo yang ada untuk isi dompet.")
#     wallet_balance = fields.Float(string='Saldo Dompet', related='siswa_id.wallet_balance', readonly=True)
#     saldo_uang_saku = fields.Float(string='Saldo Uang Saku', related='siswa_id.saldo_uang_saku', readonly=True)
#     tgl_transaksi = fields.Date(string='Tanggal Transaksi', required=True, default=fields.Date.context_today)

#     # Batas maksimal saldo yang bisa diisi ulang (sama dengan model WalletRecharge)
#     LIMITS = {
#         'limit_hari': 50000,
#         'limit_minggu': 200000,
#         'limit_bulan': 600000,
#     }
    
#     @api.onchange('barcode')
#     def _onchange_barcode(self):
#         if self.barcode:
#             siswa = self.env['cdn.siswa'].search([('barcode', '=', self.barcode)], limit=1)
#             if siswa:
#                 self.siswa_id = siswa.id
#             else:
#                 self.siswa_id = False  # Kosongkan jika tidak ditemukan
#                 return {'warning': {'title': "Perhatian!", 'message': f"Tidak ada santri dengan barcode {self.barcode}"}}
    

#     def _get_reset_time(self, last_recharge_time):
#         """ Menentukan kapan reset saldo terjadi berdasarkan jenis recharge """
#         return {
#             'limit_hari': last_recharge_time + timedelta(days=1),  # 24 jam dari transaksi terakhir
#             'limit_minggu': last_recharge_time + timedelta(weeks=1),  # 7 hari dari transaksi terakhir
#             'limit_bulan': last_recharge_time + timedelta(days=30),  # 30 hari dari transaksi terakhir
#         }.get(self.recharge_type, last_recharge_time)
    
    
#     def _check_recharge_limit(self):
#         """ Memeriksa apakah transaksi masih dalam periode pembatasan waktu dan saldo """
#         now = datetime.now()

#         if not self.siswa_id:
#             return  # Jika tidak ada siswa, abaikan pengecekan

#         last_recharge = self.env['cdn.uang_saku'].search([
#             ('siswa_id', '=', self.siswa_id.id),
#             ('jns_transaksi', '=', 'keluar'),
#             ('keterangan', 'ilike', self.recharge_type)
#         ], order='tgl_transaksi desc', limit=1)

#         # Jika belum ada transaksi sebelumnya, langsung izinkan
#         if not last_recharge:
#             return  

#         # Hitung kapan saldo bisa diisi ulang kembali
#         reset_time = self._get_reset_time(last_recharge.tgl_transaksi)

#         # **PERUBAHAN DI SINI**: Jika masih dalam cooldown, langsung raise error tanpa lanjut ke pengecekan saldo
#         if now < reset_time:
#             remaining_time = reset_time - now
#             days, remainder = divmod(remaining_time.total_seconds(), 86400)  # Konversi ke hari
#             hours, remainder = divmod(remainder, 3600)
#             minutes, _ = divmod(remainder, 60)

#             limit_labels = {
#                 'limit_hari': 'Waktu limit harian Anda :',
#                 'limit_minggu': 'Waktu limit mingguan Anda :',
#                 'limit_bulan': 'Waktu limit bulanan Anda :',
#             }
#             limit_message = limit_labels.get(self.recharge_type, "Waktu limit tidak diketahui")

#             raise UserError(
#                 f"⚠️ Validasi\n\n"
#                 f"Anda tidak bisa melakukan pengisian ulang sekarang.\n"
#                 f"{limit_message} {int(days)} hari {int(hours)} jam {int(minutes)} menit\n"
#                 f"Silahkan coba lagi jika cooldown limit sudah berakhir."
#             )

#         # **PERBAIKAN LAINNYA**: Pastikan hanya transaksi dalam periode yang sama dihitung
#         batas_saldo = self.LIMITS.get(self.recharge_type, float('inf'))
#         total_pengisian = sum(self.env['cdn.uang_saku'].search([
#             ('siswa_id', '=', self.siswa_id.id),
#             ('jns_transaksi', '=', 'keluar'),
#             ('keterangan', 'ilike', self.recharge_type),
#             ('tgl_transaksi', '>=', now - timedelta(days=1))  # Hanya transaksi dalam periode ini
#         ]).mapped('amount_out')) + self.recharge_amount

#         if total_pengisian > batas_saldo:
#             raise models.ValidationError(
#                 f"Total pengisian untuk {self.recharge_type} melebihi batas Rp {batas_saldo}. Sisa yang bisa diisi: Rp {batas_saldo - (total_pengisian - self.recharge_amount)}."
#             )

#     @api.depends('recharge_type')
#     def _compute_recharge_amount(self):
#         for record in self:
#             if record.recharge_type == 'manual_based':
#                 record.recharge_amount = 0
#             elif record.recharge_type == 'saku_based':
#                 record.recharge_amount = record.saldo_uang_saku
#             else:
#                 record.recharge_amount = self.LIMITS.get(record.recharge_type, 0)
    
    
#     def action_recharge(self):
#         """
#         Execute recharge directly without showing another form
#         """
#         self._check_recharge_limit()

#         for record in self:
#             if not record.siswa_id:
#                 raise UserError("Silahkan pilih siswa terlebih dahulu")
            
#             if record.recharge_type == 'manual_based' and record.recharge_amount <= 0:
#                 raise UserError("Nominal pengisian saldo harus lebih dari 0")
            
#             if not record.siswa_id.partner_id:
#                 raise UserError(f"Santri {record.siswa_id.name} tidak memiliki partner_id yang terkait")
            
#             if record.recharge_amount < 1000:
#                 raise UserError('⚠️Nilai recharge dompet harus lebih dari 1000 Rupiah.')
            
#             if record.recharge_type == 'saku_based' and (record.saldo_uang_saku or 0) < record.recharge_amount:
#                 raise UserError('⚠️Saldo Uang Saku Tidak Cukup!')
            
#             if not record.journal_id:
#                 raise UserError("⚠️Journal tidak ditemukan, harap pilih journal yang valid.")
            
#             partner = record.siswa_id.partner_id
            
#             AccountPayment = self.env['account.payment']
#             date_now = datetime.now().strftime('%Y-%m-%d')
#             timestamp = fields.Datetime.now()
            
#             payment_create = AccountPayment.sudo().create({
#                 'name': self.env['ir.sequence'].with_context(ir_sequence_date=date_now).next_by_code('account.payment.customer.invoice'),
#                 'payment_type': "inbound",
#                 'amount': record.recharge_amount,
#                 'date': datetime.now().date(),
#                 'journal_id': record.journal_id.id,
#                 'payment_method_id': 1,
#                 'partner_type': 'customer',
#                 'partner_id': partner.id,
#             })
#             payment_create.action_post()
            
#             self.env['pos.wallet.transaction'].sudo().create({
#                 'wallet_type': 'kas',
#                 'reference': 'manual',
#                 'amount': record.recharge_amount,
#                 'partner_id': partner.id,
#                 'currency_id': partner.property_product_pricelist.currency_id.id,
#             })
            

#             partner.write({'wallet_balance': partner.calculate_wallet()})
            
#             self.env['cdn.uang_saku'].sudo().create({
#                 'tgl_transaksi': timestamp,
#                 'siswa_id': partner.id,
#                 'jns_transaksi': 'keluar',
#                 'amount_out': record.recharge_amount,
#                 'validasi_id': self.env.user.id,
#                 'validasi_time': timestamp,
#                 'keterangan': f'Wallet Recharge - {record.recharge_type}',
#                 'state': 'confirm',
#             })
            
#             partner.write({'saldo_uang_saku': partner.calculate_saku()})
            
#             return {
#                 'type': 'ir.actions.client',
#                 'tag': 'display_notification',
#                 'params': {
#                     'title': 'Pengisian Berhasil',
#                     'message': f'Pengisian saldo untuk {partner.name} sebesar Rp {record.recharge_amount:,.0f} berhasil.',
#                     'type': 'success',
#                     'sticky': False,
#                 },
#             }


from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class isiSaldo(models.Model):
    _name = "recharge.wallet.scan"
    _description = "Isi Saldo Dompet dengan Scan Barcode"

    barcode = fields.Char(string="Kartu Santri")
    siswa_id = fields.Many2one('cdn.siswa', string='Siswa', ondelete='cascade' ,readonly=False)
    journal_id = fields.Many2one("account.journal", string="Jurnal Pembayaran", help="Pilih jenis jurnal")
    recharge_amount = fields.Float(string="Nominal Saldo", required=True, readonly=False, 
                                  help="Jumlah pengisian ulang di dompet", 
                                  compute="_compute_recharge_amount", store=True, digits=(16, 0))
    recharge_type = fields.Selection(selection=[
                        ('manual_based', 'Isi Dompet Manual'),
                        ('saku_based', 'Isi Berdasarkan Saldo'),
                        ('limit_hari', 'Isi dengan Limit Harian'),
                        ('limit_minggu', 'Isi dengan Limit Mingguan'),
                        ('limit_bulan', 'Isi dengan Limit Bulanan'),
                        ], default='manual_based', string='Tipe Isi Saldo',
                        help="Untuk pilihan limit hanya bisa di isi satu kali dan akan ada waktu tunggu penggunaan, untuk isi berdasaarkan saldo akan mengambil keseluruhan saldo yang ada untuk isi dompet.")
    wallet_balance = fields.Float(string='Saldo Dompet', related='siswa_id.wallet_balance', readonly=True, digits=(16, 0))
    saldo_uang_saku = fields.Float(string='Saldo Santri', related='siswa_id.saldo_uang_saku', readonly=True, digits=(16, 0))
    tgl_transaksi = fields.Date(string='Tanggal Transaksi', required=True, default=fields.Date.context_today)

    kelas_id    = fields.Many2one('cdn.ruang_kelas', string='Kelas', related='siswa_id.ruang_kelas_id', readonly=True, store=True)
    kamar_id    = fields.Many2one('cdn.kamar_santri', string='Kamar', related='siswa_id.kamar_id', readonly=True)
    halaqoh_id  = fields.Many2one('cdn.halaqoh', string='Halaqoh', related='siswa_id.halaqoh_id', readonly=True)
    musyrif_id  = fields.Many2one('hr.employee', string='Musyrif', related='siswa_id.musyrif_id', readonly=True)


    # Batas maksimal saldo yang bisa diisi ulang (sama dengan model WalletRecharge)
    LIMITS = {
        'limit_hari': 50000,
        'limit_minggu': 200000,
        'limit_bulan': 600000,
    }
    
    @api.onchange('barcode')
    def _onchange_barcode(self):
        if self.barcode:
            siswa = self.env['cdn.siswa'].search([('barcode', '=', self.barcode)], limit=1)
            if siswa:
                self.siswa_id = siswa.id
            else:
                self.siswa_id = False  # Kosongkan jika tidak ditemukan
                return {'warning': {'title': "Perhatian!", 'message': f"Tidak ada santri dengan barcode {self.barcode}"}}
    
    @api.onchange('siswa_id')
    def _onchange_santri(self):
        if self.siswa_id and self.siswa_id.barcode:
            self.barcode = self.siswa_id.barcode
        elif self.siswa_id:
            santri = self.siswa_id.name
            self.siswa_id = False
            return {
                'warning': {
                    'title' : 'Perhatian !',
                    'message' : f"Santri bernama {santri}, belum memiliki Kartu Santri"
                }
            }
        elif self.siswa_id and not self.siswa_id.va_saku:
            siswa = self.siswa_id.name
            self.siswa_id = False
            return {
                'warning' : {
                    'title' : 'Perhatian !',
                    'message': f"Santri bernama {siswa} belum memiliki Virtual Account"
                }
            }


    def _get_reset_time(self, last_recharge_time):
        """ Menentukan kapan reset saldo terjadi berdasarkan jenis recharge """
        return {
            'limit_hari': last_recharge_time + timedelta(days=1),  # 24 jam dari transaksi terakhir
            'limit_minggu': last_recharge_time + timedelta(weeks=1),  # 7 hari dari transaksi terakhir
            'limit_bulan': last_recharge_time + timedelta(days=30),  # 30 hari dari transaksi terakhir
        }.get(self.recharge_type, last_recharge_time)
        
    # def action_clear():
    #     siswa_id = False
        
    
    def _check_recharge_limit(self):
        """ Memeriksa apakah transaksi masih dalam periode pembatasan waktu dan saldo """
        now = datetime.now()

        if not self.siswa_id or not self.siswa_id.partner_id:
            return  # Jika tidak ada siswa atau partner_id, abaikan pengecekan
            
        partner_id = self.siswa_id.partner_id.id
        
        # Cari transaksi terakhir menggunakan partner_id bukan siswa_id
        last_recharge = self.env['cdn.uang_saku'].search([
            ('siswa_id', '=', partner_id),
            ('jns_transaksi', '=', 'keluar'),
            ('keterangan', 'ilike', self.recharge_type)
        ], order='tgl_transaksi desc', limit=1)

        # Jika belum ada transaksi sebelumnya, langsung izinkan
        if not last_recharge:
            return  

        # Hitung kapan saldo bisa diisi ulang kembali
        reset_time = self._get_reset_time(last_recharge.tgl_transaksi)

        if now < reset_time:
            remaining_time = reset_time - now
            days, remainder = divmod(remaining_time.total_seconds(), 86400)  # Konversi ke hari
            hours, remainder = divmod(remainder, 3600)
            minutes, _ = divmod(remainder, 60)

            limit_labels = {
                'limit_hari': 'Waktu limit harian Anda :',
                'limit_minggu': 'Waktu limit mingguan Anda :',
                'limit_bulan': 'Waktu limit bulanan Anda :',
            }
            limit_message = limit_labels.get(self.recharge_type, "Waktu limit tidak diketahui")

            raise UserError(
                f"⚠️ Validasi\n\n"
                f"Anda tidak bisa melakukan pengisian ulang sekarang.\n"
                f"{limit_message} {int(days)} hari {int(hours)} jam {int(minutes)} menit\n"
                f"Silahkan coba lagi jika cooldown limit sudah berakhir."
            )

        # Tentukan periode pengecekan berdasarkan tipe limit
        period_days = {
            'limit_hari': 1,
            'limit_minggu': 7,
            'limit_bulan': 30
        }.get(self.recharge_type, 1)  # Default 1 hari jika tidak diketahui
        
        # Hitung total pengisian dalam periode yang relevan sesuai dengan tipe limit
        batas_saldo = self.LIMITS.get(self.recharge_type, float('inf'))
        total_pengisian = sum(self.env['cdn.uang_saku'].search([
            ('siswa_id', '=', partner_id),  # Gunakan partner_id, bukan siswa_id
            ('jns_transaksi', '=', 'keluar'),
            ('keterangan', 'ilike', self.recharge_type),
            ('tgl_transaksi', '>=', now - timedelta(days=period_days))  # Sesuaikan periode dengan tipe limit
        ]).mapped('amount_out')) + self.recharge_amount

        if total_pengisian > batas_saldo:
            raise models.UserError(
                f"Total pengisian untuk {self.recharge_type} melebihi batas Rp {batas_saldo}. Sisa yang bisa diisi: Rp {batas_saldo - (total_pengisian - self.recharge_amount)}."
            )

    @api.depends('recharge_type')
    def _compute_recharge_amount(self):
        for record in self:
            if record.recharge_type == 'manual_based':
                record.recharge_amount = 0
            elif record.recharge_type == 'saku_based':
                record.recharge_amount = record.saldo_uang_saku
            else:
                record.recharge_amount = self.LIMITS.get(record.recharge_type, 0)
    
    # def action_reset_fields(self):
    #     for record in self:
    #         record.barcode = False
    #          return {
    #             'type': 'ir.actions.act_window',
    #             'res_model': 'recharge.wallet.scan',
    #             'view_mode': 'form',
    #             'target': 'new', 
    #             'context': {
    #                 'default_barcode': '',
    #                 'default_siswa_id': False,
    #                 'default_journal_id': False,
    #                 'default_recharge_amount': 0,
    #                 'default_recharge_type': 'manual_based',
    #                 'default_wallet_balance': 0,
    #                 'default_saldo_uang_saku': 0,
    #                 'default_tgl_transaksi': fields.Date.context_today(self),
    #             }
    #          }
            
    @api.model
    def default_get(self, fields):
        res = super(isiSaldo, self).default_get(fields)

        # Cari jurnal yang sesuai dengan perusahaan aktif
        default_journal = self.env['account.journal'].search([
            ('name', '=', 'Jurnal Dompet Santri'),
            ('company_id', '=', self.env.company.id)  # Sesuai dengan perusahaan pengguna saat ini
        ], limit=1)

        if default_journal:
            res['journal_id'] = default_journal.id  # Set nilai default

        return res    
    
    def action_recharge(self):
        """
        Execute recharge directly without showing another form
        """
        self._check_recharge_limit()

        for record in self:
            if not record.siswa_id:
                raise UserError("Silahkan pilih siswa terlebih dahulu")
            
            if (self.saldo_uang_saku or 0) < self.recharge_amount:
                raise UserError(f"⚠️Saldo {record.siswa_id.name} saat ini Rp {record.saldo_uang_saku:,.0f}, tidak cukup untuk melakukan pengisian")
            
            if not record.siswa_id.partner_id:
                raise UserError(f"Santri {record.siswa_id.name} tidak memiliki partner_id yang terkait")
            
            if record.recharge_amount < 1000:
                raise UserError('⚠️Nilai recharge dompet harus lebih dari 1000 Rupiah.')
            
            if not record.journal_id:
                raise UserError("⚠️Journal tidak ditemukan, harap pilih journal yang valid.")
            
            partner = record.siswa_id.partner_id
            
            AccountPayment = self.env['account.payment']
            date_now = datetime.now().strftime('%Y-%m-%d')
            timestamp = fields.Datetime.now()
            
            payment_create = AccountPayment.sudo().create({
                'name': self.env['ir.sequence'].with_context(ir_sequence_date=date_now).next_by_code('account.payment.customer.invoice'),
                'payment_type': "inbound",
                'amount': record.recharge_amount,
                'date': datetime.now().date(),
                'journal_id': record.journal_id.id,
                'payment_method_id': 1,
                'partner_type': 'customer',
                'partner_id': partner.id,
            })
            payment_create.action_post()
            
            self.env['pos.wallet.transaction'].sudo().create({
                'wallet_type': 'kas',
                'reference': 'manual',
                'amount': record.recharge_amount,
                'partner_id': partner.id,
                'currency_id': partner.property_product_pricelist.currency_id.id,
            })
            

            partner.write({'wallet_balance': partner.calculate_wallet()})
            
            self.env['cdn.uang_saku'].sudo().create({
                'tgl_transaksi': timestamp,
                'siswa_id': partner.id,
                'jns_transaksi': 'keluar',
                'amount_out': record.recharge_amount,
                'validasi_id': self.env.user.id,
                'validasi_time': timestamp,
                'keterangan': f'Wallet Recharge - {record.recharge_type}',
                'state': 'confirm',
            })
            
            partner.write({'saldo_uang_saku': partner.calculate_saku()})
            
            # message = f"✅ Saldo sebesar {record.recharge_amount} telah berhasil ditambahkan ke akun {partner.name}!"
            # self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {'message': message, 'title': 'Recharge Berhasil'})
            message = f"✅ Saldo sebesar {record.recharge_amount} telah berhasil ditambahkan ke akun {partner.name}!"
            self.env['bus.bus']._sendone(
                self.env.user.partner_id,  
                'simple_notification',
                {
                    'message': message,
                    'title': 'Recharge Berhasil',
                    'sticky': False, 
                    'type': 'success',
                    'timeout': 50000  
                }
            )
            
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'recharge.wallet.scan',
                'view_mode': 'form',
                'target': 'new', 
                'context': {
                    'default_name': 'Isi Saldo Santri'
                }   
                # 'context': {
                #     'default_barcode': '',
                #     'default_siswa_id': False,
                #     'default_journal_id': False,
                #     'default_recharge_amount': 0,
                #     'default_recharge_type': 'manual_based',
                #     'default_wallet_balance': 0,
                #     'default_saldo_uang_saku': 0,
                #     'default_tgl_transaksi': fields.Date.context_today(self),
                # }
            }
                       
            # return {
            #     'type': 'ir.actions.client',
            #     'tag': 'display_notification',
            #     'params': {
            #         'title': 'Pengisian Berhasil',
            #         'message': f'Pengisian saldo untuk {partner.name} sebesar Rp {record.recharge_amount:,.0f} berhasil.',
            #         'type': 'success',
            #         'sticky': False,
            #     },
            # }
    
    # def action_recharge(self):
    #     """
    #     Execute recharge directly without showing another form
    #     """
    #     self._check_recharge_limit()

    #     for record in self:
    #         if not record.siswa_id:
    #             raise UserError("Silahkan pilih siswa terlebih dahulu")
            
    #         if record.recharge_type == 'manual_based' and record.recharge_amount <= 0:
    #             raise UserError("Nominal pengisian saldo harus lebih dari 0")
            
    #         if not record.siswa_id.partner_id:
    #             raise UserError(f"Santri {record.siswa_id.name} tidak memiliki partner_id yang terkait")
            
    #         if record.recharge_amount < 1000:
    #             raise UserError('⚠️Nilai recharge dompet harus lebih dari 1000 Rupiah.')
            
    #         if record.recharge_type == 'saku_based' and (record.saldo_uang_saku or 0) < record.recharge_amount:
    #             raise UserError('⚠️Saldo Uang Saku Tidak Cukup!')
            
    #         if not record.journal_id:
    #             raise UserError("⚠️Journal tidak ditemukan, harap pilih journal yang valid.")
            
    #         partner = record.siswa_id.partner_id
            
    #         AccountPayment = self.env['account.payment']
    #         date_now = datetime.now().strftime('%Y-%m-%d')
    #         timestamp = fields.Datetime.now()
            
    #         payment_create = AccountPayment.sudo().create({
    #             'name': self.env['ir.sequence'].with_context(ir_sequence_date=date_now).next_by_code('account.payment.customer.invoice'),
    #             'payment_type': "inbound",
    #             'amount': record.recharge_amount,
    #             'date': datetime.now().date(),
    #             'journal_id': record.journal_id.id,
    #             'payment_method_id': 1,
    #             'partner_type': 'customer',
    #             'partner_id': partner.id,
    #         })
    #         payment_create.action_post()
            
    #         self.env['pos.wallet.transaction'].sudo().create({
    #             'wallet_type': 'kas',
    #             'reference': 'manual',
    #             'amount': record.recharge_amount,
    #             'partner_id': partner.id,
    #             'currency_id': partner.property_product_pricelist.currency_id.id,
    #         })

    #         partner.write({'wallet_balance': partner.calculate_wallet()})
            
    #         self.env['cdn.uang_saku'].sudo().create({
    #             'tgl_transaksi': timestamp,
    #             'siswa_id': partner.id,
    #             'jns_transaksi': 'keluar',
    #             'amount_out': record.recharge_amount,
    #             'validasi_id': self.env.user.id,
    #             'validasi_time': timestamp,
    #             'keterangan': f'Wallet Recharge - {record.recharge_type}',
    #             'state': 'confirm',
    #         })
            
    #         partner.write({'saldo_uang_saku': partner.calculate_saku()})

    #         nama_santri = partner.name
    #         jumlah_topup = record.recharge_amount

    #         self.clear_form_fields()

    #         return {
    #             'type': 'ir.actions.act_window',
    #             'res_model': recharge.wallet.scan,
    #             'view_mode': 'form',
    #             'view_id': self.env.ref('pesantren_musyrif.wizard_isi_saldo_menu_categ').id,
    #             'target': 'new',
    #             'context': {
    #                 'default_tgl_transaksi': fields.Date.context_today(self),
    #                 'show_success_message': True,
    #                 'success_title': 'Pengisian Saldo Berhasil ✅',
    #                 'success_message': f'Saldo {nama_santri} berhasil diisi Rp {jumlah_topup:,.0f}.',
    #             },
    #         }

    # def clear_form_fields(self):
    #     """
    #     Method alternatif untuk reset field
    #     """
    #     self.write({
    #         'barcode': False,
    #         'siswa_id': False,
    #         'journal_id': False,
    #         'recharge_amount': 0.0,
    #         'recharge_type': 'manual_based',
    #         'tgl_transaksi': fields.Date.context_today(self),
    #     })
    #     return True