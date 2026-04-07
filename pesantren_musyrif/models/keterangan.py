from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import timedelta, datetime
import logging



class MasterKeterangan(models.Model):
    _name = 'master.keterangan'
    
    name = fields.Char("Keterangan Ijin")