from odoo import models, fields, api, _
from datetime import datetime


class PaymentRecord(models.Model):
    _name = 'payment.record'
    _description = 'Payment Record'

    member_id = fields.Many2one('res.partner', string='Member', required=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    month_name = fields.Char(string='Month')
    year = fields.Char(string='Year')

    # Reference to member.payment model to access base_amount
    # member_payment_id = fields.Many2one('member.payment', string='Member Payment', required=True)
    # base_amount = fields.Float(string="Base Amount", store=True)
    # base_amount = fields.Float(string="Base Amount", compute='_compute_from_deposit_amount', store=True)

    deposit_amount = fields.Float(string='Deposit Amount', required=True)
    subscription_amount = fields.Float(string='Subscription Amount', required=True)
    extra_amount = fields.Float(string='Extra Amount', default=0.0)
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)
    grand_total = fields.Float(string='Grand Total', compute='_compute_total_amount', store=True)
    due_amount = fields.Float(string='Due Amount')
    receipt = fields.Binary(string='Payment Receipt')

    # payment_structure_ids = fields.One2many('member.deposit.structure', 'total_with_extra_amount', string="Payment Structures")



    #
    # @api.depends('payment_structure_ids.total_with_extra_amount')
    # def _compute_base_amount(self):
    #     for record in self:
    #         # Sum total_with_extra_amount of related payment_structure_ids
    #         record.base_amount = sum(line.total_with_extra_amount for line in record.payment_structure_ids)

    #
    # @api.depends('deposit_amount', 'subscription_amount', 'extra_amount', 'base_amount')
    # def _compute_total_amount(self):
    #     for record in self:
    #         # Calculate total as deposit + subscription
    #         record.total_amount = record.deposit_amount + record.subscription_amount
    #
    #         # Calculate grand total by including the extra amount and base amount
    #         record.grand_total = record.total_amount + record.extra_amount + record.base_amount
