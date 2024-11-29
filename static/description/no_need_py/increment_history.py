from odoo import models, fields

class IncrementHistory(models.Model):
    _name = 'payment.increment.history'
    _description = 'Increment History for Members'

    member_id = fields.Many2one('res.partner', string='Member', required=True)
    increment_amount = fields.Float(string='Increment Amount', required=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date')


class Member(models.Model):
    _inherit = 'res.partner'

    def _compute_current_amount(self):
        for record in self:
            base_amount = record.base_amount
            months = 0
            increment_history = self.env['payment.increment.history'].search([('member_id', '=', record.id)],
                                                                            order="start_date")

            for history in increment_history:
                # Calculate time period within each increment history
                start = history.start_date
                end = history.end_date if history.end_date else fields.Date.today()
                time_period = (end.year - start.year) * 12 + (end.month - start.month)

                # Accumulate total increment over time periods
                base_amount += time_period * history.increment_amount

            record.current_amount = base_amount
