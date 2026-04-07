# -*- coding: utf-8 -*-

from odoo import models, fields, api


class JenisPegawai(models.Model):
    _name = 'cdn.jenis_pegawai'
    _description = 'Employee Role Master'
    _order = 'sequence, name'

    name = fields.Char(string='Role Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True,
                       help='Unique code for this role (e.g., "musyrif", "guru", "guruquran")')
    description = fields.Text(string='Description', translate=True)
    sequence = fields.Integer(
        string='Sequence', default=10, help='Order in which roles appear')
    active = fields.Boolean(string='Active', default=True)
    color = fields.Integer(string='Color')

    # Security groups that will be assigned when this role is active
    security_group_ids = fields.Many2many(
        'res.groups',
        'jenis_pegawai_group_rel',
        'jenis_pegawai_id',
        'group_id',
        string='Security Groups',
        help='Security groups automatically assigned to employees with this role'
    )

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Role code must be unique!')
    ]
