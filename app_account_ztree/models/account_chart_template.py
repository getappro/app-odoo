# -*- coding: utf-8 -*-

# Created on 2022-07-08
# author: 欧度智能，https://www.odooai.cn
# email: 300883@qq.com
# resource of odooai
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# Odoo16在线用户手册（长期更新）
# https://www.odooai.cn/documentation/16.0/zh_CN/index.html

# Odoo16在线开发者手册（长期更新）
# https://www.odooai.cn/documentation/16.0/zh_CN/developer.html

# Odoo13在线用户手册（长期更新）
# https://www.odooai.cn/documentation/user/13.0/zh_CN/index.html

# Odoo13在线开发者手册（长期更新）
# https://www.odooai.cn/documentation/13.0/index.html

# Odoo在线中文用户手册（长期更新）
# https://www.odooai.cn/documentation/user/10.0/zh_CN/index.html

# Odoo10离线中文用户手册下载
# https://www.odooai.cn/odoo10_user_manual_document_offline/
# Odoo10离线开发手册下载-含python教程，jquery参考，Jinja2模板，PostgresSQL参考（odoo开发必备）
# https://www.odooai.cn/odoo10_developer_document_offline/
# description:

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountChartTemplate(models.Model):
    # 会计科目表模板，使用此模板的会生成一样的会计科目表
    _inherit = "account.chart.template"

    # 科目分隔符
    delimiter = fields.Char(string='Code Delimiter', default='.',
                            help='Delimiter after parent account chart')

    @api.model
    def _prepare_transfer_account_template(self):
        # 分隔符，用友为""，金蝶为 "."，注意odoo中一级科目，现金默认定义是4位头，银行是6位头
        # 我们使用 用友的多级科目方式，自动生成下级，此处直接覆盖原生
        digits = self.code_digits
        prefix = self.transfer_account_code_prefix or ''
        # Flatten the hierarchy of chart templates.
        chart_template = self
        chart_templates = self
        while chart_template.parent_id:
            chart_templates += chart_template.parent_id
            chart_template = chart_template.parent_id
        delimiter = chart_template.delimiter
        new_code = ''
        for num in range(1, 100):
            new_code = str(prefix.ljust(digits - 1, '0')) + delimiter + '%02d' % (num)
            rec = self.env['account.account.template'].search(
                [('code', '=', new_code), ('chart_template_id', 'in', chart_templates.ids)], limit=1)
            if not rec:
                break
        parent = self.env['account.account.template'].search(
            [('code', '=', prefix), ('chart_template_id', 'in', chart_templates.ids)], limit=1)
        if new_code == '':
            raise UserError(_('Cannot generate an unused account code.'))
        res = {
            'name': _('Liquidity Transfer'),
            'code': new_code,
            'parent_id': parent.id if parent else False,
            'account_type': 'asset_current',
            'reconcile': True,
            'chart_template_id': self.id,
        }
        return res

    def _load(self, company):
        # 这个是加载预制模板，在此方法中调用 _install_template ，再从中调用 _load_template 来生成会计科目
        res = super(AccountChartTemplate, self)._load(company)
        # 先整体load完，再按template中的设置更新父级
        acc_ids = self.env['account.account'].sudo().search([('company_id', '=', company.id)])
        for acc in acc_ids:
            code = acc.code
            todo_account = self.env['account.account.template'].sudo().search([
                ('code', '=', code),
                ('chart_template_id', '=', self.id),
                ('parent_id', '!=', False)
            ], limit=1)
            if len(todo_account) or code == '2221.01.01':
                parent_code = todo_account[0].parent_id.code
                if parent_code:
                    parent = self.env['account.account'].sudo().search([
                        ('company_id', '=', company.id),
                        ('code', '=', parent_code),
                    ], limit=1).exists()
                    if parent and acc.parent_id != parent:
                        acc.write({
                            'parent_id': parent.id,
                        })
        return res


