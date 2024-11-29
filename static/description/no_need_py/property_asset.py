from odoo import models, fields

class PropertyAsset(models.Model):
    _name = 'property.asset'
    _description = 'Property Asset Management'

    member_id = fields.Many2one('member.management', string='Member', required=True)
    land_quantity = fields.Integer(string='Land Quantity')
    land_area_each = fields.Float(string='Each Land Area')
    land_value_each = fields.Float(string='Each Land Value (Current Year)')
    total_land_area = fields.Float(string='Total Land Area (Katha)', compute='_compute_total_land_area')
    total_land_value = fields.Float(string='Total Land Value', compute='_compute_total_land_value')

    # @api.depends('land_quantity', 'land_area_each')
    # def _compute_total_land_area(self):
    #     for record in self:
    #         record.total_land_area = record.land_quantity * record.land_area_each
    #
    # @api.depends('land_quantity', 'land_value_each')
    # def _compute_total_land_value(self):
    #     for record in self:
    #         record.total_land_value = record.land_quantity * record.land_value_each
