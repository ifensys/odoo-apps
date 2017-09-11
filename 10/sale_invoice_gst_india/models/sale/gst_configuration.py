# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class GstConfiguration(models.Model):
    _name = "gst.configuration"
    
    name = fields.Char('Number', required=True)
    
class OurGstConfiguration(models.Model):
    _name = "our.gst.configuration"
    
    name = fields.Char('Number', required=True)