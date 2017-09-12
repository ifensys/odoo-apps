# -*- coding: utf-8 -*-

from openerp import fields, models, api, _ 
from datetime import datetime
from datetime import date, timedelta
from openerp.tools import amount_to_text_en
from lxml import etree

class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    _description = 'Account Invoice Details'
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = models.Model.fields_view_get(self, cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            for sheet in doc.xpath("//sheet"):
                parent = sheet.getparent()
                index = parent.index(sheet)
                for child in sheet:
                    parent.insert(index, child)
                    index += 1
                parent.remove(sheet)
            res['arch'] = etree.tostring(doc)
        return res
    
    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id', 'date_invoice')
    def _compute_amount(self):
        amount_untaxed = cgst_amt = sgst_amt = igst_amt = total_sale = discount = convert_float_round_off = convert_float_ro_amt = 0.0;
        convert_str = '';
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
        self.amount_tax = sum(line.amount for line in self.tax_line_ids)
        for line in self.invoice_line_ids:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            # Added new fields in this object
            cgst_amt += line.cgst_amt
            sgst_amt += line.sgst_amt
            igst_amt += line.igst_amt
            total_sale += line.total_sale
            discount += line.gst_discount
        # Added new fields in this object    
        self.cgst_amt  = cgst_amt
        self.sgst_amt  = sgst_amt
        self.igst_amt  = igst_amt
        self.total_sale  = total_sale
        self.discount  = discount
        # Added new fields in this object
        self.total_tax_amount = cgst_amt + sgst_amt + igst_amt
        self.amount_untaxed = self.total_sale - self.discount
        self.total_before_bound_off = self.amount_untaxed + self.total_tax_amount
        
        convert_str = str(self.total_before_bound_off)
        if convert_str:
            round_of_amt = format(self.total_before_bound_off, '.2f')
            rount_of_int_amt = int(round_of_amt.split('.')[-1])
        if rount_of_int_amt:
                convert_float_round_off = float(rount_of_int_amt)
                convert_float_ro_amt = (convert_float_round_off / 100.00)
        
        self.round_off = convert_float_ro_amt
        self.amount_total = int(self.total_before_bound_off)
        
        if self.amount_total:
            # converted amount in words in Indian format
            self.amt_in_words = self.amount_to_text(self.amount_total,currency='INR')
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id.with_context(date=self.date_invoice)
            amount_total_company_signed = currency_id.compute(self.amount_total, self.company_id.currency_id)
            amount_untaxed_signed = currency_id.compute(self.amount_untaxed, self.company_id.currency_id)
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign
#     
    cgst_amt = fields.Monetary(string='Total CGST', store=True, readonly=True, compute='_compute_amount', track_visibility='always')
    sgst_amt = fields.Monetary(string='Total SGST', store=True, readonly=True, compute='_compute_amount', track_visibility='always')
    igst_amt = fields.Monetary(string='Total IGST', store=True, readonly=True, compute='_compute_amount', track_visibility='always')
    
    total_tax_amount = fields.Monetary(string='Total Tax Amount', store=True, readonly=True, compute='_compute_amount')
    total_before_bound_off = fields.Monetary(string='Total Before Round off', store=True, readonly=True, compute='_compute_amount')
    round_off = fields.Monetary(string='Round Off(-)', store=True, readonly=True, compute='_compute_amount')
    
    gst_number_id = fields.Many2one('gst.configuration', 'GST Number')
    our_gst_number_id = fields.Many2one('our.gst.configuration', 'Our GST Number')
    total_sale = fields.Monetary(string='Total Sale', store=True, readonly=True, compute='_compute_amount')
    discount = fields.Monetary(string='Total Discounts', store=True, readonly=True, compute='_compute_amount')
    amt_in_words = fields.Text('Amount In Words')
    
    transport_mode = fields.Selection([('air','AIR'), ('road','ROAD'), ('rail','RAIL'), ('other','OTHER')], string="Transport Mode")
    transport_company = fields.Char('Transport By')
    contact_number = fields.Char('Contact Number')
        
    @api.model
    def invoice_line_move_line_get(self):
        res = []
        for line in self.invoice_line_ids:
            tax_ids = []
            for tax in line.invoice_line_tax_ids:
                tax_ids.append((4, tax.id, None))
                for child in tax.children_tax_ids:
                    if child.type_tax_use != 'none':
                        tax_ids.append((4, child.id, None))

            move_line_dict = {
                'invl_id': line.id,
                'type': 'src',
                'name': line.name.split('\n')[0][:64],
                'price_unit': line.price_unit,
                'quantity': line.quantity,
                 'price': int(line.price_subtotal + line.cgst_amt + line.sgst_amt + line.igst_amt),
                'account_id': line.account_id.id,
                'product_id': line.product_id.id,
                'uom_id': line.uom_id.id,
                'account_analytic_id': line.account_analytic_id.id,
                'tax_ids': tax_ids,
                'invoice_id': self.id,
            }
            if line['account_analytic_id']:
                move_line_dict['analytic_line_ids'] = [(0, 0, line._get_analytic_line())]
            res.append(move_line_dict)
        return res
    
    @api.multi
    def amount_to_text(self, amount, currency=''):
        amount_in_words = amount_to_text_en.amount_to_text(amount, lang='en', currency=currency)
        if currency == 'INR':
            amount_in_words = str(amount_in_words).replace('INR', 'rupees')
            amount_in_words = str(amount_in_words).replace('Cents', 'paise')
            amount_in_words = str(amount_in_words).replace('Cent', 'paise')
        amount_in_words += '\tonly'
        return amount_in_words
    
class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    
    hsn_sac_code = fields.Char('HSN/SAC Code')
    total_sale = fields.Float(compute='_total_sale', string='Total Sale', readonly=True, store=True)
    cgst_rate = fields.Float('CGST Rate %')
    cgst_amt = fields.Float(compute='_cgst_rate', string='CGST Amount', readonly=True, store=True)
    sgst_rate = fields.Float('SGST Rate %')
    sgst_amt = fields.Float(compute='_sgst_rate', string='SGST Amount', readonly=True, store=True)
    igst_rate = fields.Float('IGST Rate %')
    igst_amt = fields.Float(compute='_igst_rate', string='IGST Amount', readonly=True, store=True)
    gst_discount = fields.Float('Discount')
    
    @api.depends('price_unit', 'quantity')
    def _total_sale(self):
        for record in self:
            if record.price_unit:
                record.total_sale = record.price_unit * record.quantity
            
    @api.depends('cgst_rate','price_unit', 'quantity')
    def _cgst_rate(self):
        amt = 0.0;
        for record in self:
            if record.cgst_rate:
                amt =  record.total_sale - record.gst_discount
                record.cgst_amt = (record.cgst_rate * amt)/100
            else:
                record.cgst_amt = 0.0
             
    @api.depends('sgst_rate','price_unit', 'quantity')
    def _sgst_rate(self):
        amt = 0.0;
        for record in self:
            if record.sgst_rate:
                amt =  record.total_sale - record.gst_discount
                record.sgst_amt = (record.sgst_rate * amt)/100
            else:
                record.sgst_amt = 0.0
            
    @api.depends('igst_rate','price_unit', 'quantity')
    def _igst_rate(self):
        amt = 0.0;
        for record in self:
            if record.igst_rate:
                amt =  record.total_sale - record.gst_discount
                record.igst_amt = (record.igst_rate * amt)/100
            else:
                record.igst_amt = 0.0
            
    @api.onchange('gst_discount')
    def onchange_gst_discount(self):
        amt = 0.0;
        if self.gst_discount:
            amt = self.total_sale - self.gst_discount
            self.price_subtotal = amt
        else:
            self.price_subtotal = self.price_subtotal
    
    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
        'invoice_id.date_invoice')
    def _compute_price(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
        self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
        # Subtract discount amount from price subtotal
        self.price_subtotal =  self.price_subtotal - self.gst_discount
        if self.invoice_id.currency_id and self.invoice_id.company_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            price_subtotal_signed = self.invoice_id.currency_id.with_context(date=self.invoice_id.date_invoice).compute(price_subtotal_signed, self.invoice_id.company_id.currency_id)
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign