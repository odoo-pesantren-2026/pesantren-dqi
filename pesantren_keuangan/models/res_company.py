from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    max_wallet = fields.Float(string='Saldo Dompet Maksimal')
    limit_weekly_reset_day = fields.Selection([
        ('0', 'Senin'),
        ('1', 'Selasa'),
        ('2', 'Rabu'),
        ('3', 'Kamis'),
        ('4', 'Jumat'),
        ('5', 'Sabtu'),
        ('6', 'Minggu')
    ], string='Hari Reset Mingguan', default='0')
    limit_monthly_reset_day = fields.Integer(
        string='Tanggal Reset Bulanan', default=1)
    limit_reset_hour = fields.Integer(
        string='Jam Reset Limit (0-23)', default=0)
    standard_limit_amount = fields.Float(
        string='Default Nominal Limit', default=30000.0)
