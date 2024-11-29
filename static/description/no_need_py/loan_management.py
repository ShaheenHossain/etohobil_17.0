from odoo import models, fields

class LoanManagement(models.Model):
    _name = 'loan.management'
    _description = 'Loan Management'

    member_id = fields.Many2one('member.management', string='Member', required=True)
    loan_from_bank = fields.Float(string='Loan from Bank')
    loan_from_person = fields.Float(string='Loan from Person')
    total_loan = fields.Float(string='Total Loan', compute='_compute_total_loan')

    # @api.depends('loan_from_bank', 'loan_from_person')
    # def _compute_total_loan(self):
    #     for record in self:
    #         record.total_loan = record.loan_from_bank + record.loan_from_person
