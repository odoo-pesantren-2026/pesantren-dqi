from odoo import api, fields, models
from datetime import timedelta, datetime
import logging

_logger = logging.getLogger(__name__)


class UangSaku(models.Model):
    _name = 'cdn.uang_saku'
    _description = 'Uang Saku Santri'
    _order = 'tgl_transaksi desc'

    name = fields.Char(string='Name', readonly=True)
    tgl_transaksi = fields.Datetime(
        string='Tgl Transaksi', required=True, default=fields.Datetime.now, widget="date")
    siswa_id = fields.Many2one(comodel_name='res.partner', string='Santri', required=True, domain=[
                               ('siswa_id', '!=', False)], ondelete='cascade')
    siswa = fields.Many2one(comodel_name='cdn.siswa', compute='_compute_siswa',
                            string='Siswa', store=True, ondelete='cascade')
    va_saku = fields.Char(string='No. VA Saku',
                          related='siswa_id.va_saku', readonly=True, store=True)
    saldo_awal = fields.Float(
        string='Saldo Awal', readonly=True, store=True, compute='_compute_saldo_awal')
    status_akun = fields.Selection(related='siswa.status_akun')
    barcode_santri = fields.Char(
        string='Kartu Santri', related='siswa.barcode_santri', store=True, readonly=False)

    kelas_id = fields.Many2one('cdn.ruang_kelas', string='Kelas',
                               related='siswa.ruang_kelas_id', readonly=True, store=True)
    kamar_id = fields.Many2one(
        'cdn.kamar_santri', string='Kamar', related='siswa.kamar_id', readonly=True)
    halaqoh_id = fields.Many2one(
        'cdn.halaqoh', string='Halaqoh', related='siswa.halaqoh_id', readonly=True)
    musyrif_id = fields.Many2one(
        'hr.employee', string='Musyrif', related='siswa.musyrif_id', readonly=True)

    jns_transaksi = fields.Selection(string='Jenis Transaksi', selection=[
        ('masuk', 'Uang Masuk'),
        ('keluar', 'Uang Keluar'),
    ], required=True, default='masuk')
    amount_in = fields.Float(string='Nominal Masuk')
    amount_out = fields.Float(string='Nominal Keluar')

    validasi_id = fields.Many2one(
        comodel_name='res.users', string='Validasi', readonly=True)
    validasi_time = fields.Datetime(string='Tgl Validasi', readonly=False)
    keterangan = fields.Text(string='Keterangan', states={
                             'confirm': [('readonly', True)]})

    state = fields.Selection(string='State', selection=[
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
    ], default='draft', readonly=True)

    orangtua_id = fields.Many2one(
        comodel_name='cdn.orangtua',
        string='Orang Tua',
        related='siswa.orangtua_id',
        readonly=True,
        store=True
    )
    # musyrif_id = fields.Many2one('hr.employee', string='Musyrif', related='siswa.musyrif_id', readonly=True)

    # Perbaiki fungsi _compute_siswa

    @api.depends('siswa_id')
    def _compute_siswa(self):
        for record in self:
            Siswa = self.env['cdn.siswa'].search(
                [('partner_id', '=', record.siswa_id.id)])
            if Siswa:
                record.siswa = Siswa[0].id
            else:
                record.siswa = False

    # Perbaiki fungsi _onchange_barcode
    @api.onchange('barcode_santri')
    def _onchange_barcode(self):
        if self.barcode_santri:
            partner = self.env['res.partner'].search(
                [('barcode_santri', '=', self.barcode_santri)], limit=1)
            if partner:
                self.siswa_id = partner.id
            else:
                self.siswa_id = False
                barcode_sementara = self.barcode_santri
                self.barcode_santri = False
                return {
                    'warning': {
                        'title': "Perhatian !",
                        'message': f"Data Santri dengan Kartu Santri {barcode_sementara} tidak ditemukan."
                    }
                }
        else:
            self.barcode_santri = False
            self.siswa_id = False

    @api.onchange('amount_in', 'jns_transaksi')
    def _onchange_amount_in_warning(self):
        if self.jns_transaksi == 'masuk' and self.amount_in is not None and self.amount_in < 0:
            self.amount_in = 0  # reset ke 0 biar jelas
            return {
                'warning': {
                    'title': 'Perhatian!',
                    'message': 'Nominal uang masuk tidak boleh kurang dari 0.'
                }
            }

    @api.onchange('amount_out', 'jns_transaksi')
    def _onchange_amount_out_warning(self):
        if self.jns_transaksi == 'keluar' and self.amount_out is not None and self.amount_out < 0:
            self.amount_out = 0  # reset ke 0 biar jelas
            return {
                'warning': {
                    'title': 'Perhatian!',
                    'message': 'Nominal uang keluar tidak boleh kurang dari 0.'
                }
            }

    @api.onchange('siswa_id')
    def _check_virtual_account_and_status(self):
        if self.siswa_id:
            siswa = self.siswa_id.name

            if not self.siswa_id.va_saku:
                self.siswa_id = False
                return {
                    'warning': {
                        'title': 'Perhatian!',
                        'message': f"Santri bernama {siswa} belum memiliki Virtual Account."
                    }
                }

            siswa_obj = self.env['cdn.siswa'].search(
                [('partner_id', '=', self.siswa_id.id)], limit=1)
            if siswa_obj and siswa_obj.status_akun in ['nonaktif', 'blokir']:
                self.siswa_id = False
                status = siswa_obj.status_akun.capitalize()
                return {
                    'warning': {
                        'title': 'Akses Ditolak!',
                        'message': f"Transaksi tidak dapat diproses karena akun santri bernama {siswa} saat ini berstatus {status}. Mohon hubungi pengurus pesantren untuk informasi lebih lanjut."
                    }
                }

    # # Field untuk Group By per minggu
    # week_tgl_transaksi = fields.Char(string='Minggu Transaksi', compute='_compute_week_tgl_transaksi', store=True)

    # @api.depends('tgl_transaksi')
    # def _compute_week_tgl_transaksi(self):
    #     for record in self:
    #         if record.tgl_transaksi:
    #             record.week_tgl_transaksi = record.tgl_transaksi.strftime('%Y-W%U')
    #             # Contoh hasil: '2025-W11' (Tahun 2025, Minggu ke-11)

    # override
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'cdn.uang_saku') or 'New'

        # Pengecekan Limit jika di-create langsung confirm
        if vals.get('state') == 'confirm' and vals.get('jns_transaksi') == 'keluar':
            siswa_id = vals.get('siswa_id')
            amount_out = vals.get('amount_out', 0)
            if siswa_id and amount_out > 0:
                # Cari santri (siswa_id di model ini merujuk ke res.partner)
                siswa_obj = self.env['cdn.siswa'].sudo().search(
                    [('partner_id', '=', siswa_id)], limit=1)
                if siswa_obj:
                    # 1. Pengecekan
                    siswa_obj._check_limit(amount_out)
                    # 2. Update Penggunaan
                    siswa_obj._apply_limit_usage(amount_out)

        result = super(UangSaku, self).create(vals)
        return result

    @api.model
    def _read_group_process_groupby(self, gb, query):
        """Override untuk mengatur format tampilan grup minggu"""
        result = super(UangSaku, self)._read_group_process_groupby(gb, query)

        # Jika pengelompokan berdasarkan minggu, ubah formatnya
        if gb == 'tgl_transaksi:week' or (gb.startswith('tgl_transaksi') and gb.endswith('week')):
            # Mengubah format default menjadi format yang diinginkan
            # Format default: W1 2025
            # Format baru: Minggu 1 2025 (dengan spasi setelah Minggu)
            result['display_format'] = 'Minggu %W %Y'
            result['interval_type'] = 'week'

            # Logging untuk debugging
            _logger.info(f"Mengubah format minggu: {result}")

        return result

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """Override method read_group untuk menangani format minggu"""
        result = super(UangSaku, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)

        # Cek jika terdapat pengelompokan berdasarkan minggu
        week_groupby = False
        for gb in groupby:
            if gb == 'tgl_transaksi:week' or (gb.startswith('tgl_transaksi') and gb.endswith('week')):
                week_groupby = True
                break

        if week_groupby:
            # Iterasi semua hasil dan ubah format minggu
            for item in result:
                if 'tgl_transaksi:week' in item:
                    week_value = item['tgl_transaksi:week']
                    if isinstance(week_value, str) and week_value.startswith('W'):
                        item['tgl_transaksi:week'] = week_value.replace(
                            'W', 'Minggu ')

                # Juga ubah display_name jika menggunakan format minggu
                if 'display_name' in item and isinstance(item['display_name'], str) and item['display_name'].startswith('W'):
                    item['display_name'] = item['display_name'].replace(
                        'W', 'Minggu ')

        return result

    # actions

    def action_confirm(self):
        for rec in self:
            Partner = rec.siswa_id

            # Pengecekan Limit jika transaksi Keluar
            if rec.jns_transaksi == 'keluar' and rec.siswa:
                # 1. Pengecekan (akan raise UserError jika gagal)
                rec.siswa._check_limit(rec.amount_out)

                # 2. Update penggunaan limit
                rec.siswa._apply_limit_usage(rec.amount_out)

            rec.state = 'confirm'
            rec.validasi_id = self.env.user.id
            rec.validasi_time = fields.Datetime.now()
            rec.siswa_id.write({
                'saldo_uang_saku': rec.siswa_id.calculate_saku(),
            })

            # rec.env['pos.wallet.transaction'].sudo().create({
            #     'wallet_type': 'kas',
            #     'reference': 'manual',
            #     'amount': rec.amount_in,
            #     'partner_id': Partner.id,
            #     'currency_id': Partner.property_product_pricelist.currency_id.id,
            # })
            rec.kirim_email_pemberitahuan()

    def kirim_email_pemberitahuan(self):
        for record in self:
            if record.siswa and record.siswa.orangtua_id and record.siswa.orangtua_id.partner_id.email:
                parent_email = record.siswa.orangtua_id.partner_id.email

                sender_name = "Pengurus Pondok Dqi"
                sender_mail = "ponpesdqi@gmail.com"
                email_from = f'"{sender_name}" <{sender_mail}>'

                amount_in_formatted = f"Rp{'{:,.0f}'.format(record.amount_in).replace(',', '.')}"
                saldo_formatted = f"Rp{'{:,.0f}'.format(record.siswa_id.saldo_uang_saku).replace(',', '.')}"

                subject = f"Saldo sudah masuk ke santri bernama {record.siswa.name}"
                body_html = f"""
                   <div style="background-color: #f5f8fa; padding: 30px; font-family: 'Arial', sans-serif;">
                        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden;">
                            <!-- Header -->
                            <div style="background-color: #005299; color: #ffffff; text-align: center; padding: 30px;">
                                <img src="https://i.ibb.co.com/SmWmBTW/SAVE-20220114-075750-removebg-preview-4.png" alt="Logo" style="margin:0 0 15px 0;box-sizing:border-box;vertical-align:middle;width: 80px; height: 80px; margin-bottom: 15px;" width="80">
                                <h1 style="margin: 0; font-size: 24px; font-weight: 600;">Pesantren Daarul Qur'an Istiqomah</h1>
                            </div>
                            
                            <!-- Content -->
                            <div style="padding: 30px;">
                                <p style="font-size: 16px; line-height: 1.6; color: #333333; margin-top: 0;">Assalamualaikum,</p>
                                
                                <p style="font-size: 16px; line-height: 1.6; color: #333333;">Dengan ini kami informasikan bahwa saldo uang saku sudah masuk ke akun santri:</p>
                                
                                <div style="background-color: #f8f9fa; border-left: 4px solid #005299; padding: 15px; margin: 20px 0; border-radius: 4px;">
                                    <p style="margin: 8px 0; font-size: 15px; color: #333333;"><strong>Nama Santri:</strong> {record.siswa.name}</p>
                                    <p style="margin: 8px 0; font-size: 15px; color: #333333;"><strong>Virtual Account:</strong> {record.va_saku}</p>
                                    <p style="margin: 8px 0; font-size: 15px; color: #333333;"><strong>Jumlah:</strong> {amount_in_formatted}</p>
                                    <p style="margin: 8px 0; font-size: 15px; color: #333333;"><strong>Tanggal:</strong> {record.tgl_transaksi}</p>
                                    <p style="margin: 8px 0; font-size: 15px; color: #333333;"><strong>Saldo Sekarang:</strong> {saldo_formatted}</p>
                                </div>
                                
                                <p style="font-size: 16px; line-height: 1.6; color: #333333;">Terima kasih.</p>
                            </div>
                            
                            <!-- Footer -->
                            <div style="background-color: #f0f4f8; text-align: center; padding: 15px; color: #666666; font-size: 14px; border-top: 1px solid #e7eaec;">
                                <p style="margin: 5px 0;">Pesantren Daarul Qur'an Istiqomah</p>
                            </div>
                        </div>
                    </div>
                """
                email_values = {
                    'subject': subject,
                    'email_to': parent_email,
                    'reply_to': email_from,
                    'body_html': body_html,
                    'body': f"""Assalamualaikum,
                    Dengan ini kami informasikan bahwa saldo uang saku sudah masuk ke akun santri:
                    
                        Nama Santri: {record.siswa.name}
                        Virtual Account: {record.va_saku}
                        Jumlah: {amount_in_formatted}
                        Tanggal: {record.tgl_transaksi}
                        Saldo Sekarang: {saldo_formatted}

                    Terima kasih.

                    Pesantren Daarul Qur'an Istiqomah
                    """
                }

                self.env['mail.mail'].create(email_values).send()

    # compute
    @api.depends('siswa_id')
    def _compute_saldo_awal(self):
        for record in self:
            if record.siswa_id:
                record.saldo_awal = record.siswa_id.calculate_saku(
                    record.validasi_time)
