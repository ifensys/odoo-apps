# -*- coding: utf-8 -*-

from openerp import api, fields, models

class GstConfiguration(models.Model):
    _name = "gst.configuration"
    
    name = fields.Char('Number', required=True)
    
class OurGstConfiguration(models.Model):
    _name = "our.gst.configuration"
    
    name = fields.Char('Number', required=True)