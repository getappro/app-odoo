# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_app_cn_po = fields.Boolean('SaaS Chinese PO', help="Checked to Sync Odoo Chinese from www.odooapp.cn")
