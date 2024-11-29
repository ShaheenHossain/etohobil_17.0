from odoo import models, fields

class PaymentStructure(models.Model):
    _name = 'payment.structure'
    _description = 'Payment Structure'

    name = fields.Char(string='Payment Structure', required=True)
    deposit_amount = fields.Float(string='Deposit Amount', required=True)
    subscription_amount = fields.Float(string='Subscription Amount', required=True)
