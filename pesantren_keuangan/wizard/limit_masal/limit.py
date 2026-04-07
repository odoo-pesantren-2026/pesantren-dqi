from odoo import api, fields, models
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

class MassLimit(models.TransientModel):
    _name = 'mass.limit'
    _description = 'Wizard Limit Masal'

    name = fields.Many2one('cdn.ref_tahunajaran',string="Santri Angkatan")
    limit  = fields.Selection(selection=[
            ('hari', 'Perhari'),
            ('minggu', 'Perminggu'),
            ('bulan', 'Bulan'),
        ], default='hari', string='Periode')
    limit_amount = fields.Float(string="Jumlah Limit", required=True, digits=(16, 0),
                                default=lambda self: self.env.company.standard_limit_amount)

    kelas = fields.Many2many('cdn.ruang_kelas')

    def action_set_limit(self):
        self.ensure_one()

        if not self.limit_amount:
            raise UserError("Mohon massukkan jumlah limit!")
        
        if not self.kelas:
            raise UserError("Pilih minimal satu kelas terlebih dahulu !")
        
        now = fields.Datetime.now()

        # Menggunakan helper dari model cdn.siswa untuk konsistensi perhitungan
        # ambil satu record dummy untuk memanggil method _get_next_limit_reset_date
        dummy_santri = self.env['cdn.siswa'].new({})
        reset_date = dummy_santri._get_next_limit_reset_date(self.limit)

        all_santri = self.env['cdn.siswa']
        for kelas in self.kelas:
            all_santri |= kelas.siswa_ids
        
        if not all_santri:
            raise UserError("Tidak ada santri ditemukan di kelas yang dipilih")

        limit_data = {
            'limit' : self.limit,
            'amount' : self.limit_amount,
            'used_amount': 0,
            'limit_reset_date': reset_date,
            'is_limit_active': True
        }

        self.sudo().write({})
        all_santri.sudo().write(limit_data)

        kelas_names = ', '.join(self.kelas.mapped('name.name'))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Limit berhasil diatur untuk {len(all_santri)} santri di kelas: {kelas_names}',
                'type': 'success',
                'sticky': False,
            }
        }

    