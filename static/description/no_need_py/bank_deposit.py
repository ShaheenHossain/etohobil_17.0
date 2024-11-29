from odoo import models, fields

class BankDeposit(models.Model):
    _name = 'bank.deposit'
    _description = 'Bank and Cash Deposit'

    member_id = fields.Many2one('member.management', string='Member', required=True)
    bank_name = fields.Char(string='Bank Name')
    deposit_cash_in_hand = fields.Float(string='Cash in Hand')
    deposit_bank = fields.Float(string='Deposit in Bank')
    deposit_total = fields.Float(string='Total Deposit', compute='_compute_deposit_total')
    total_deposit = fields.Float(string="Total Deposit", compute="_compute_total_deposit")

    # @api.depends('deposit_cash_in_hand', 'deposit_bank')
    # def _compute_total_deposit(self):
    #     for record in self:
    #         record.total_deposit = record.deposit_cash_in_hand + record.deposit_bank
