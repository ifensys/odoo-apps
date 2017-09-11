# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import amount_to_text_en

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    @api.depends('order_line.price_total','order_line.total_sale_tol','order_line.cgst_amt_tol','order_line.sgst_rate_tol','order_line.igst_amt_tol')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = cgst_amt = sgst_amt = igst_amt = total_sale = discount = total_tax_amt = total_befor_round_amt = 0.0;
            convert_str = ''; convert_int_amout = 0;rount_of_int_amt = 0.0;convert_float_round_off=0.0;convert_float_ro_amt = 0.0;
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                # FORWARDPORT UP TO 10.0
                if order.company_id.tax_calculation_rounding_method == 'round_globally':
                    price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                    # Added new fields in this object 
                    total_sale += line.total_sale
                    cgst_amt += line.cgst_amt
                    sgst_amt += line.sgst_amt
                    igst_amt += line.igst_amt
                    discount += line.gst_discount
                else:
                    # Added new fields in this object 
                    amount_tax += line.price_tax
                    total_sale += line.total_sale
                    cgst_amt += line.cgst_amt
                    sgst_amt += line.sgst_amt
                    igst_amt += line.igst_amt
                    discount += line.gst_discount
            total_tax_amt = cgst_amt + sgst_amt + igst_amt
            total_befor_round_amt = amount_untaxed + total_tax_amt
            convert_str = str(total_befor_round_amt)
            if convert_str:
                round_of_amt = format(total_befor_round_amt, '.2f')
                rount_of_int_amt = int(round_of_amt.split('.')[-1])
            else:
                round_of_amt = 0
            convert_int_amout = int(total_befor_round_amt)
#             if rount_of_int_amt <= 50:
#                 total_befor_round_amt = convert_int_amout
#             else:
#                 total_befor_round_amt = convert_int_amout + 1
            if convert_int_amout:
                # converted amount in words in Indian format
                order.amt_in_words = self.amount_to_text(total_befor_round_amt,currency='INR')
            if rount_of_int_amt:
                convert_float_round_off = float(rount_of_int_amt)
                convert_float_ro_amt = (convert_float_round_off / 100.00)
            order.update({
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'cgst_amt':cgst_amt,
                'total_sale':total_sale,
                'sgst_amt':sgst_amt,
                'igst_amt':igst_amt,
                'discount':discount,
                
                'total_tax_amount':total_tax_amt,
                'total_before_bound_off':amount_untaxed + total_tax_amt,
                'round_off':convert_float_ro_amt,
                
                'amount_total': convert_int_amout,
            })
    
    cgst_amt = fields.Monetary(string='Total CGST', store=True, readonly=True, compute='_amount_all', track_visibility='always')
    sgst_amt = fields.Monetary(string='Total SGST', store=True, readonly=True, compute='_amount_all', track_visibility='always')
    igst_amt = fields.Monetary(string='Total IGST', store=True, readonly=True, compute='_amount_all', track_visibility='always')
    
    total_tax_amount = fields.Monetary(string='Total Tax Amount', store=True, readonly=True, compute='_amount_all')
    total_before_bound_off = fields.Monetary(string='Total Before Round off', store=True, readonly=True, compute='_amount_all')
    round_off = fields.Monetary(string='Round Off(-)', store=True, readonly=True, compute='_amount_all')
    
    gst_number_id = fields.Many2one('gst.configuration', 'GST Number')
    our_gst_number_id = fields.Many2one('our.gst.configuration', 'Our GST Number')
    total_sale = fields.Monetary(string='Total Sale', store=True, readonly=True, compute='_amount_all')
    discount = fields.Monetary(string='Total Discounts', store=True, readonly=True, compute='_amount_all')
    amt_in_words = fields.Text('Amount In Words')
    transport_mode = fields.Selection([('air','AIR'), ('road','ROAD'), ('rail','RAIL'), ('other','OTHER')], string="Transport Mode")
    transport_company = fields.Char('Transport By')
    
    
    @api.multi
    def amount_to_text(self, amount, currency=''):
        amount_in_words = amount_to_text_en.amount_to_text(amount, lang='en', currency=currency)
        if currency == 'INR':
            amount_in_words = str(amount_in_words).replace('INR', 'rupees')
            amount_in_words = str(amount_in_words).replace('Cents', 'paise')
            amount_in_words = str(amount_in_words).replace('Cent', 'paise')
        amount_in_words += '\tonly'
        return amount_in_words
    
    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))
        invoice_vals = {
            'name': self.client_order_ref or '',
            'origin': self.name,
            # Added new fields in this object 
            'gst_number_id': self.gst_number_id.id,
            'our_gst_number_id': self.our_gst_number_id.id,
            'amt_in_words' : self.amt_in_words,
            'transport_mode': self.transport_mode,
            'transport_company' : self.transport_company,
            
            'type': 'out_invoice',
            'account_id': self.partner_invoice_id.property_account_receivable_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'journal_id': journal_id,
            'currency_id': self.pricelist_id.currency_id.id,
            'comment': self.note,
            'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
            'company_id': self.company_id.id,
            'user_id': self.user_id and self.user_id.id,
            'team_id': self.team_id.id,
        }
        return invoice_vals

class InheritedSaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    hsn_sac_code = fields.Char('HSN/SAC Code')
    total_sale = fields.Float(compute='_total_sale', string='Total Sale', readonly=True, store=True)
    cgst_rate = fields.Float('CGST Rate %')
    cgst_amt = fields.Float(compute='_cgst_rate', string='CGST Amount', readonly=True, store=True)
    sgst_rate = fields.Float('SGST Rate %')
    sgst_amt = fields.Float(compute='_sgst_rate', string='SGST Amount', readonly=True, store=True)
    igst_rate = fields.Float('IGST Rate %')
    igst_amt = fields.Float(compute='_igst_rate', string='IGST Amount', readonly=True, store=True)
    gst_discount = fields.Float('Discount')
    
    total_sale_tol = fields.Monetary(compute='_compute_amount', string='Total Sale', readonly=True, store=True)
    cgst_amt_tol = fields.Monetary(compute='_compute_amount', string='Total CGST Amount', readonly=True, store=True)
    sgst_rate_tol = fields.Monetary(compute='_compute_amount', string='Total SGST Amount', readonly=True, store=True)
    igst_amt_tol = fields.Monetary(compute='_compute_amount', string='Total IGST Amount', readonly=True, store=True)
    
    
    @api.depends('price_unit', 'product_uom_qty')
    def _total_sale(self):
        for record in self:
            if record.price_unit:
                record.total_sale = record.price_unit * record.product_uom_qty
            
    @api.depends('cgst_rate','price_unit', 'product_uom_qty')
    def _cgst_rate(self):
        amt = 0.0;
        for record in self:
            if record.cgst_rate:
                amt =  record.total_sale - record.gst_discount
                record.cgst_amt = (record.cgst_rate * amt)/100
            else:
                record.cgst_amt = 0.0
             
    @api.depends('sgst_rate','price_unit', 'product_uom_qty')
    def _sgst_rate(self):
        amt = 0.0;
        for record in self:
            if record.sgst_rate:
                amt =  record.total_sale - record.gst_discount
                record.sgst_amt = (record.sgst_rate * amt)/100
            else:
                record.sgst_amt = 0.0
            
    @api.depends('igst_rate','price_unit', 'product_uom_qty')
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
            amt = self.price_subtotal - self.gst_discount
            self.price_subtotal = amt
        else:
            self.price_subtotal = self.price_subtotal
            
    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id','total_sale','cgst_amt','sgst_amt','igst_amt')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'] - line.gst_discount ,
                # Added new fields in this object 
                'total_sale_tol': line.total_sale,
                'cgst_amt_tol': line.cgst_amt,
                'sgst_rate_tol': line.sgst_amt,
                'igst_amt_tol': line.igst_amt,
            })
            
    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {}
        account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id
        if not account:
            raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
                (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)

        res = {
            'name': self.name,
            'sequence': self.sequence,
            'origin': self.order_id.name,
            'account_id': account.id,
            'price_unit': self.price_unit,
            'price_subtotal':self.price_subtotal,
            'quantity': qty,
            'discount': self.discount,
            'uom_id': self.product_uom.id,
            'product_id': self.product_id.id or False,
            'layout_category_id': self.layout_category_id and self.layout_category_id.id or False,
            'product_id': self.product_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            'account_analytic_id': self.order_id.project_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            # Added new fields in this object 
            'hsn_sac_code': self.hsn_sac_code,
            'total_sale': self.total_sale,
            'cgst_rate': self.cgst_rate,
            'cgst_amt': self.cgst_amt,
            'sgst_rate': self.sgst_rate,
            'sgst_amt': self.sgst_amt,
            'igst_rate': self.igst_rate,
            'igst_amt': self.igst_amt,
            'gst_discount': self.gst_discount,
        }
        return res
    
class GstConfiguration(models.Model):
    _name = "gst.configuration"
    
    name = fields.Char('GST Name', required=True)
    
class OurGstConfiguration(models.Model):
    _name = "our.gst.configuration"
    
    name = fields.Char('Our GST Name', required=True)
    