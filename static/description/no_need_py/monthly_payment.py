from odoo import models, fields, api, _

class MonthlyPayment(models.Model):
    _name = 'monthly.payment'
    _description = 'Monthly Payment'