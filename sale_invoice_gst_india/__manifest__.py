# -*- coding: utf-8 -*-
##############################################################################
#
#    iFenSys Software Solutions Pvt. Ltd.
#    Copyright (C) 2017 iFenSys Software Solutions(<http://www.ifensys.com>).
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Sale Invoice GST India',
    'version': "10.0.1.0.0",
    'summary': 'Sale Invoice GST India',
    'category': 'Sales',
    'author':'iFenSys Software Solutions',
    'company':'iFenSys Software Solutions Pvt. Ltd',
    'website': 'http://www.ifensys.com',
    'depends': ['base','sale','account'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale/inherited_sale_views.xml',
        'views/account/inherited_account_views.xml',
        'views/sale/gst_configuration_views.xml',
        'report/inherited_invoice_report_template.xml',
        'report/inherited_sale_report_template.xml',
        'views/menus.xml'
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
}
