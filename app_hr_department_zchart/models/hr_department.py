# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class Department(models.Model):
    # 目录图片，可显示小图标，
    _name = "hr.department"
    _inherit = ['hr.department', 'image.mixin']

    # 目录图片，可显示小图标，odoo13 在 mixin 中处理了

