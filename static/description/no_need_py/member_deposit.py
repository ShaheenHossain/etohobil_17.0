from odoo import models, fields, api
from datetime import date

class MemberDeposit(models.Model):
    _name = 'member.deposit'
    _description = 'Member Deposit and Payment Management'

    member_id = fields.Many2one('res.partner', string='Member', required=True)
    deposit_amount = fields.Float(string='Deposit Amount', required=True)
    due_amount = fields.Float(string='Due Amount', compute='_compute_due_amount')
    payment_date = fields.Date(string='Payment Date', default=date.today())
    total_amount_due = fields.Float(string='Total Due Amount', compute='_compute_total_due')

    @api.depends('deposit_amount', 'due_amount')
    def _compute_total_due(self):
        for record in self:
            record.total_amount_due = record.deposit_amount + record.due_amount

    @api.model
    def generate_monthly_invoices(self):
        """Auto-generate invoices for all members and send emails."""
        members = self.env['res.partner'].search([('is_member', '=', True)])
        for member in members:
            due_amount = member.due_amount
            current_month_deposit = self.get_monthly_deposit_structure(member)
            total_amount = current_month_deposit + due_amount

            # Create invoice
            invoice_vals = {
                'partner_id': member.id,
                'amount_total': total_amount,
                'due_amount': due_amount,
                'date_invoice': fields.Date.today(),
                'state': 'draft',
            }
            invoice = self.env['account.move'].create(invoice_vals)

            # Send invoice via email
            template = self.env.ref('your_module.mail_template_member_invoice')
            template.send_mail(invoice.id, force_send=True)

            # Update due amount
            member.due_amount += current_month_deposit

    def get_monthly_deposit_structure(self, member):
        """Define the deposit structure here."""
        # Assuming you have predefined deposit structures
        # You can customize this logic based on your data model.
        return 1000  # Replace this logic to calculate the correct amount

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_member = fields.Boolean(string='Is Member', default=False)
    due_amount = fields.Float(string='Due Amount')
