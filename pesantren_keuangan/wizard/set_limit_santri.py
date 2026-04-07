from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SetLimitSantri(models.TransientModel):
    _name = 'set.limit.santri'

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
            if not Siswa:
                _logger.error(
                    f"Tidak ditemukan partner_id untuk siswa {active_id}")
                return False
            partner_id = Siswa
            _logger.info("Id Dari Partner %s", partner_id)
        return partner_id

    santri_id = fields.Many2one('cdn.siswa', string="Santri", required=True,
                                default=lambda self: self._get_partner_id(), ondelete='cascade')
    musyrif = fields.Many2one(related='santri_id.musyrif_id', string="Musyrif")
    kelas = fields.Many2one(related='santri_id.ruang_kelas_id', string="Kelas")
    kamar = fields.Many2one(related='santri_id.kamar_id')
    halaqoh = fields.Many2one(related='santri_id.halaqoh_id')
    kartu = fields.Char(string="Kartu Santri",
                        related='santri_id.barcode_santri')
    limit = fields.Selection(selection=[
        ('hari', 'Perhari'),
        ('minggu', 'Perminggu'),
        ('bulan', 'Bulan'),
    ], default='hari', string='Periode')

    amount = fields.Float(string="Total", digits=(16, 0),
                          default=lambda self: self.env.company.standard_limit_amount)

    def action_set_limit(self):
        self.ensure_one()
        if not self.amount:
            raise UserError("Mohon masukkan jumlah limit!")

        now = fields.Datetime.now()

        reset_date = self.santri_id._get_next_limit_reset_date(self.limit)

        # Update data santri
        self.sudo().santri_id.write({
            'limit': self.limit,
            'amount': self.amount,
            'used_amount': 0,
            'limit_reset_date': reset_date,
            'is_limit_active': True
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Pengaturan Limit Berhasil!',
                'message': f'Limit {self.limit} sebesar Rp {self.amount:,.0f} telah diatur untuk {self.santri_id.name}',
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            },
        }
