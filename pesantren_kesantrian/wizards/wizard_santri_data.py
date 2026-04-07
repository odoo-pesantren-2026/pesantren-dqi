from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class getSantriData(models.Model):
    _inherit = "cdn.siswa"