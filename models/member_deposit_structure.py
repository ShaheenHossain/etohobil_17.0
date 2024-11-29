from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta

import logging

_logger = logging.getLogger(__name__)

from odoo.exceptions import UserError

class MemberDepositStructure(models.Model):
    _name = 'member.deposit.structure'
    _description = 'Member Payment Structure'

    payment_id = fields.Many2one('member.payment', string="Payment Record", ondelete='cascade')
    sequence = fields.Integer(required=True, default=10)
    sl_no = fields.Integer(string="Sl")
    subscription_fee = fields.Float(string="Fee")
    deposit_amount = fields.Float(string="Monthly Amount")
    extra_amount = fields.Float(string="Extra Amount")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    total_years = fields.Integer(string="Total Years", compute='_compute_total_years_months', store=True)
    total_months = fields.Integer(string="Total Months", compute='_compute_total_years_months', store=True)
    subtotal_amount = fields.Float(string="Subtotal Amount", compute='_compute_totals', store=True)
    subtotal_subscription_amount = fields.Float(string="Subtotal Fee", compute='_compute_totals', store=True)
    total_amount_with_subscription = fields.Float(string="Total with Fee", compute='_compute_totals', store=True)
    total_with_extra_amount = fields.Float(string="Total with Extra", compute='_compute_totals', store=True)
    is_selected = fields.Boolean(string="Is Selected", default=False)
    selected_total = fields.Float(string="Selected Total", compute="_compute_selected_total", store=True)
    payment_info = fields.Many2one('product.product', string="Payment Info", domain=[('type', '=', 'service')])
    sale_order_line_id = fields.Many2one('sale.order.line', string="Sale Order Line", ondelete='cascade')
    currency_id = fields.Many2one('res.currency', string="Currency", default=lambda self: self.env.company.currency_id)
    grand_total = fields.Monetary(string="Grand Total", compute="_compute_grand_total", store=False,
                                  currency_field='currency_id')
    base_current_amount = fields.Float(string="Base Current Amount")
    partner_id = fields.Many2one('res.partner', string="Partner")

    member_transaction_ids = fields.One2many('member.deposit.structure', 'account_move_id', string="Member Deposit Transactions")
    account_move_id = fields.Many2one('account.move', string="Related Account Move")
    member_deposit_structure_id = fields.Many2one('account.move', string="Account Move", ondelete='cascade')
    taxes_id = fields.Many2many('account.tax', 'member_deposit_structure_tax_rel', 'deposit_structure_id', 'tax_id',
                                string="Taxes")
    supplier_taxes_id = fields.Many2many('account.tax', 'member_deposit_structure_account_tax_rel', 'member_id',
                                         'tax_id', string="Supplier Taxes")

    @api.depends('total_with_extra_amount')
    def _compute_grand_total(self):
        for record in self:
            total = sum(self.search([]).mapped('total_with_extra_amount'))
            record.grand_total = total

    @api.depends('deposit_amount', 'subscription_fee', 'extra_amount')
    def _compute_selected_total(self):
        for record in self:
            record.selected_total = record.deposit_amount + record.subscription_fee + record.extra_amount

    @api.depends('start_date', 'end_date')
    def _compute_total_years_months(self):
        for record in self:
            if record.start_date and record.end_date:
                delta = relativedelta(record.end_date, record.start_date)
                if delta.days > 0:
                    delta = relativedelta(years=delta.years, months=delta.months + 1)
                record.total_years = delta.years
                record.total_months = delta.years * 12 + delta.months
            else:
                record.total_years = 0
                record.total_months = 1

    @api.depends('deposit_amount', 'subscription_fee', 'total_months', 'extra_amount')
    def _compute_totals(self):
        for record in self:
            record.subtotal_amount = record.deposit_amount * record.total_months
            record.subtotal_subscription_amount = record.subscription_fee * record.total_months
            record.total_amount_with_subscription = record.subtotal_amount + record.subtotal_subscription_amount
            record.total_with_extra_amount = record.total_amount_with_subscription + record.extra_amount

    def convert_to_product(self):
        for record in self:
            if record.payment_info:
                raise UserError("This record has already been converted to a product.")

            record._compute_totals()
            record._compute_total_years_months()

            payment_name = record.payment_id.name if record.payment_id and hasattr(record.payment_id,
                                                                                   'name') else 'Payment'
            product_vals = {
                'name': f"{payment_name} - {record.sl_no}",
                'type': 'service',
                'list_price': record.total_with_extra_amount,  # Set from total_with_extra_amount
                'standard_price': record.total_amount_with_subscription,  # Set from total_amount_with_subscription
                'sl_no': record.sl_no,
                'subscription_fee': record.subscription_fee,
                'deposit_amount': record.deposit_amount,
                'extra_amount': record.extra_amount,
                'start_date': record.start_date,
                'end_date': record.end_date,
                'total_years': record.total_years,
                'total_months': record.total_months,
                'subtotal_amount': record.subtotal_amount,
                'subtotal_subscription_amount': record.subtotal_subscription_amount,
                'total_amount_with_subscription': record.total_amount_with_subscription,
                'total_with_extra_amount': record.total_with_extra_amount,
                'taxes_id': [(5, 0, 0)],  # Clear out any sales taxes
                'supplier_taxes_id': [(5, 0, 0)],  # Clear out any purchase taxes
            }
            product = self.env['product.product'].create(product_vals)
            record.payment_info = product.id

    def update_last_line_end_date(self):
        last_record = self.search([], order="sequence desc", limit=1)
        if last_record and last_record.end_date:
            last_record.end_date += relativedelta(months=1)
            last_record._compute_total_years_months()
            last_record._compute_totals()

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    sl_no = fields.Integer(string="Sl")
    subscription_fee = fields.Float(string="Fee")
    deposit_amount = fields.Float(string="Monthly")
    extra_amount = fields.Float(string="Extra")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    total_years = fields.Integer(string="Total Years", compute='_compute_total_years_months', store=True)
    total_months = fields.Integer(string="Total Months", compute='_compute_total_years_months', store=True)
    subtotal_amount = fields.Float(string="Subtotal Amount", compute='_compute_totals', store=True)
    subtotal_subscription_amount = fields.Float(string="Subtotal Fee", compute='_compute_totals', store=True)
    total_amount_with_subscription = fields.Float(string="Total with Fee", compute='_compute_totals', store=True)
    total_with_extra_amount = fields.Float(string="Total with Extra", compute='_compute_totals', store=True)

    @api.depends('deposit_amount', 'subscription_fee', 'extra_amount')
    def _compute_selected_total(self):
        for record in self:
            record.selected_total = record.deposit_amount + record.subscription_fee + record.extra_amount

    def action_calculate_selected_total(self):
        for record in self:
            record._compute_selected_total()

    @api.depends('start_date', 'end_date')
    def _compute_total_years_months(self):
        for record in self:
            if record.start_date and record.end_date:
                delta = relativedelta(record.end_date, record.start_date)
                if delta.days > 0:
                    delta = relativedelta(years=delta.years, months=delta.months + 1)
                record.total_years = delta.years
                record.total_months = delta.years * 12 + delta.months
            else:
                record.total_years = 0
                record.total_months = 1


    @api.depends('deposit_amount', 'subscription_fee', 'total_months', 'extra_amount')
    def _compute_totals(self):
        for record in self:
            record.subtotal_amount = record.deposit_amount * record.total_months
            record.subtotal_subscription_amount = record.subscription_fee * record.total_months
            record.total_amount_with_subscription = record.subtotal_amount + record.subtotal_subscription_amount
            record.total_with_extra_amount = record.total_amount_with_subscription + record.extra_amount
            record.list_price = record.total_with_extra_amount


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    deposit_amount = fields.Float(string="Monthly Amount")
    subscription_fee = fields.Float(string="Subscription Fee")
    extra_amount = fields.Float(string="Extra Amount")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    total_years = fields.Integer(string="Total Years", compute='_compute_total_years_months', store=True)
    total_months = fields.Integer(string="Total Months", compute='_compute_total_years_months', store=True)
    subtotal_amount = fields.Float(string="Subtotal Amount", compute='_compute_totals', store=True)
    subtotal_subscription_amount = fields.Float(string="Subtotal Fee", compute='_compute_totals', store=True)
    total_amount_with_subscription = fields.Float(string="Total with Fee", compute='_compute_totals', store=True)
    total_with_extra_amount = fields.Float(string="Total with Extra", compute='_compute_totals', store=True)
    authorized_transaction_ids = fields.One2many('member.deposit.structure', 'sale_order_line_id',  string="Authorized Transactions")

    partner_credit_warning = fields.Boolean("Partner Credit Warning")

    @api.onchange('product_id')
    def _onchange_product_id_custom(self):
        """Update custom fields based on selected product."""
        if self.product_id:
            # Fetch product values
            self.deposit_amount = self.product_id.deposit_amount
            self.subscription_fee = self.product_id.subscription_fee
            self.extra_amount = self.product_id.extra_amount
            self.start_date = self.product_id.start_date
            self.end_date = self.product_id.end_date
            self.total_years = self.product_id.total_years
            self.total_months = self.product_id.total_months
            self.subtotal_amount = self.product_id.subtotal_amount
            self.subtotal_subscription_amount = self.product_id.subtotal_subscription_amount
            self.total_amount_with_subscription = self.product_id.total_amount_with_subscription
            self.total_with_extra_amount = self.product_id.total_with_extra_amount
            self.product_uom_qty = self.product_id.total_months

    @api.depends('start_date', 'end_date')
    def _compute_total_years_months(self):
        for record in self:
            if record.start_date and record.end_date:
                # Calculate the difference between dates
                delta = relativedelta(record.end_date, record.start_date)
                # Add 1 to include the end month
                total_months = delta.years * 12 + delta.months + 1
                record.total_years = delta.years
                record.total_months = max(total_months, 1)  # Ensure minimum 1 month
            else:
                record.total_years = 0
                record.total_months = 1



    @api.depends('deposit_amount', 'subscription_fee', 'total_months', 'extra_amount')
    def _compute_totals(self):
        for line in self:
            line.subtotal_amount = line.deposit_amount * line.total_months
            line.subtotal_subscription_amount = line.subscription_fee * line.total_months
            line.total_amount_with_subscription = line.subtotal_amount + line.subtotal_subscription_amount
            line.total_with_extra_amount = line.total_amount_with_subscription + line.extra_amount
            line.price_subtotal = line.total_with_extra_amount
            # _logger.debug(f"Computed subtotal: {line.price_subtotal}, Total with Extra: {line.total_with_extra_amount}")
            line.product_uom_qty = line.total_months

    @api.depends('total_with_extra_amount', 'product_uom_qty')
    def _compute_amount(self):
        for line in self:
            line.price_subtotal = line.total_with_extra_amount
            line.product_uom_qty = 1
            line.price_unit = line.total_with_extra_amount

    @api.model
    def create(self, vals):
        if 'start_date' in vals and 'end_date' in vals:
            start_date = fields.Date.from_string(vals.get('start_date'))
            end_date = fields.Date.from_string(vals.get('end_date'))
            if start_date and end_date:
                delta = relativedelta(end_date, start_date)
                vals['total_months'] = delta.years * 12 + delta.months + 1
        return super(SaleOrderLine, self).create(vals)

    def write(self, vals):
        if 'start_date' in vals or 'end_date' in vals:
            for record in self:
                start_date = vals.get('start_date', record.start_date)
                end_date = vals.get('end_date', record.end_date)
                if start_date and end_date:
                    delta = relativedelta(end_date, start_date)
                    vals['total_months'] = delta.years * 12 + delta.months + 1
        return super(SaleOrderLine, self).write(vals)

    def _prepare_invoice_line(self, **optional_values):
        invoice_line_vals = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)

        invoice_line_vals.update({
            'deposit_amount': self.deposit_amount,
            'subscription_fee': self.subscription_fee,
            'extra_amount': self.extra_amount,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'total_years': self.total_years,
            'total_months': self.total_months,
            'subtotal_amount': self.subtotal_amount,
            'subtotal_subscription_amount': self.subtotal_subscription_amount,
            'total_amount_with_subscription': self.total_amount_with_subscription,
            'total_with_extra_amount': self.total_with_extra_amount,
            # 'amount_total': self.amount_total,
        })
        return invoice_line_vals

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_compute_amount')

    def _prepare_invoice_line(self, line):
        res = super(SaleOrder, self)._prepare_invoice_line(line)
        res.update({
            'deposit_amount': line.deposit_amount,
            'subscription_fee': line.subscription_fee,
            'extra_amount': line.extra_amount,
            'start_date': line.start_date,
            'end_date': line.end_date,
            'total_years': line.total_years,
            'total_months': line.total_months,
            'subtotal_amount': line.subtotal_amount,
            'subtotal_subscription_amount': line.subtotal_subscription_amount,
            'total_amount_with_subscription': line.total_amount_with_subscription,
            'total_with_extra_amount': line.total_with_extra_amount,
            'price_unit': line.total_with_extra_amount,
            'quantity': 1,
        })
        return res

    @api.depends('order_line.price_total', 'currency_id')
    def _compute_amount(self):
        for order in self:
            order.amount_total = sum(order.order_line.mapped('price_total'))


    customer_invoice_total = fields.Monetary(
        string="Total Invoice Amount",
        compute='_compute_customer_invoice_total',
        currency_field='currency_id'
    )

    @api.depends('partner_id')
    def _compute_customer_invoice_total(self):
        for order in self:
            if order.partner_id:
                invoices = self.env['account.move'].search([
                    ('partner_id', '=', order.partner_id.id),
                    ('move_type', '=', 'out_invoice'),
                    # ('state', '=', 'posted')  # Only consider posted invoices
                ])
                order.customer_invoice_total = sum(invoices.mapped('amount_total'))
            else:
                order.customer_invoice_total = 0.0

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    deposit_amount = fields.Float(string="Monthly Amount")
    subscription_fee = fields.Float(string="Subscription Fee")
    extra_amount = fields.Float(string="Extra Amount")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    total_years = fields.Integer(string="Total Years", compute='_compute_total_years_months', store=True)
    total_months = fields.Integer(string="Total Months", compute='_compute_total_years_months', store=True)
    subtotal_amount = fields.Float(string="Subtotal Amount", compute='_compute_totals', store=True, readonly=True)
    subtotal_subscription_amount = fields.Float(string="Subtotal Fee", compute='_compute_totals', store=True, readonly=True)
    total_amount_with_subscription = fields.Float(string="Total with Fee", compute='_compute_totals', store=True, readonly=True)
    total_with_extra_amount = fields.Float(string="Total with Extra", compute='_compute_totals', store=True, readonly=True)
    member_deposit_structure_id = fields.Many2one('member.deposit.structure', string="Member Deposit Structure", ondelete='cascade')

    @api.onchange('product_id')
    def _onchange_product_id_custom(self):
        """ Update custom fields based on the selected product. """
        if self.product_id:
            self.deposit_amount = self.product_id.deposit_amount
            self.subscription_fee = self.product_id.subscription_fee
            self.extra_amount = self.product_id.extra_amount
            self.start_date = self.product_id.start_date
            self.end_date = self.product_id.end_date

    @api.depends('deposit_amount', 'subscription_fee', 'total_months', 'extra_amount')
    def _compute_totals(self):
        """ Recompute all custom total fields. """
        for line in self:
            line.subtotal_amount = line.deposit_amount * line.total_months
            line.subtotal_subscription_amount = line.subscription_fee * line.total_months
            line.total_amount_with_subscription = line.subtotal_amount + line.subtotal_subscription_amount
            line.total_with_extra_amount = line.total_amount_with_subscription + line.extra_amount
            line.price_subtotal = line.total_with_extra_amount
            line.price_unit = line.price_subtotal / (line.quantity or 1)

    @api.depends('start_date', 'end_date')
    def _compute_total_years_months(self):
        """ Calculate total years and months between start_date and end_date. """
        for record in self:
            if record.start_date and record.end_date:
                delta = relativedelta(record.end_date, record.start_date)
                total_months = delta.years * 12 + delta.months + 1
                record.total_years = delta.years
                record.total_months = max(total_months, 1)
            else:
                record.total_years = 0
                record.total_months = 1

    @api.model
    def create(self, vals):
        """ Set default quantity for new lines. """
        if 'quantity' not in vals:
            vals['quantity'] = 1
        return super(AccountMoveLine, self).create(vals)

    @api.depends('quantity', 'price_unit')
    def _compute_price_unit(self):
        """ Ensure price_unit is recalculated when needed. """
        for line in self:
            if line.price_subtotal and line.quantity:
                line.price_unit = line.price_subtotal / line.quantity

class AccountMove(models.Model):
    _inherit = 'account.move'

    sl_no = fields.Integer(string="Sl")
    subscription_fee = fields.Float(string="Fee")
    deposit_amount = fields.Float(string="Monthly")
    extra_amount = fields.Float(string="Extra")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    total_years = fields.Integer(string="Total Years", compute='_compute_total_years_months', store=True)
    total_months = fields.Integer(string="Total Months", compute='_compute_total_years_months', store=True)
    subtotal_amount = fields.Float(string="Subtotal Amount", compute='_compute_totals', store=True)
    subtotal_subscription_amount = fields.Float(string="Subtotal Fee", compute='_compute_totals', store=True)
    total_amount_with_subscription = fields.Float(string="Total with Fee", compute='_compute_totals', store=True)
    total_with_extra_amount = fields.Float(string="Total with Extra", compute='_compute_totals', store=True)
    total_base_current_amount = fields.Float(string="Total Base Current Amount", compute="_compute_total_base_current_amount", store=True)
    partner_ids = fields.One2many('res.partner', 'related_account_move_id', string="Related Partners")

    current_base_amount = fields.Float(string="Current Base Amount", compute="_compute_current_base_amount", store=False, readonly=True)

    move_type = fields.Selection(selection_add=[
        ('out_invoice', 'Payment Invoice')  # Replace the label for 'out_invoice'
    ])

    # deducted_amount = fields.Float(string="Deducted Amount", readonly=True )
    #
    # @api.depends('deducted_amount')
    # def _compute_current_base_amount(self):
    #     """Compute the current base amount after deducting confirmed invoice totals."""
    #     for record in self:
    #         # Fetch the grand total from member.deposit.structure
    #         grand_total = self.env['member.deposit.structure'].search([]).mapped('total_with_extra_amount')
    #         total_grand = sum(grand_total)
    #
    #         # Deduct the total confirmed invoice line amounts
    #         record.current_base_amount = total_grand - record.deducted_amount

    amount_due = fields.Float(
        string="Amount Due",
        compute="_compute_amount_due",
        store=False,
        readonly=True
    )

    # @api.depends('amount_due', 'amount_residual')
    # def _compute_payment_state(self):
    #     for record in self:
    #         if record.amount_due > 0 and record.amount_due < record.current_base_amount:
    #             record.payment_state = 'in_payment'
    #         elif record.amount_due == 0:
    #             record.payment_state = 'paid'
    #         else:
    #             record.payment_state = 'not_paid'

    @api.depends('current_base_amount', 'line_ids.amount_currency')
    def _compute_amount_due(self):
        for record in self:
            total_payments = sum(
                record.line_ids.filtered(
                    lambda l: l.account_id.internal_group == 'asset'
                ).mapped('amount_currency')
            )
            record.amount_due = record.current_base_amount - total_payments

            if record.amount_due <= 0:
                record.amount_due = 0.0

    #
    #
    # @api.depends(...)
    # def _compute_amount_due(self):
    #     for record in self:
    #         _logger.info(f"Current Base Amount: {record.current_base_amount}")
    #         _logger.info(
    #             f"Total Payments: {sum(record.line_ids.filtered(lambda l: l.account_id.internal_group == 'asset').mapped('amount_currency'))}")

    # def action_post(self):
    #     """Override the action_post method to update deducted_amount and deduct it from current_base_amount."""
    #     super(AccountMove, self).action_post()
    #     for record in self:
    #         # Calculate the total of all invoice line price_totals
    #         total_price_total = sum(record.invoice_line_ids.mapped('price_total'))
    #
    #         # Update the deducted amount field
    #         record.deducted_amount = total_price_total
    #
    #         # Trigger recompute for current_base_amount
    #         record._compute_current_base_amount()


    @api.depends()
    def _compute_current_base_amount(self):
        for record in self:
            grand_total = self.env['member.deposit.structure'].search([]).mapped('total_with_extra_amount')
            record.current_base_amount = sum(grand_total)

    @api.depends('partner_id')
    def _compute_total_base_current_amount(self):
        for record in self:
            member_payment_records = self.env['member.deposit.structure'].search([
                ('partner_id', '=', record.partner_id.id)  # Ensure partner_id exists
            ])
            record.total_base_current_amount = sum(member_payment_records.mapped('base_current_amount'))


    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for record in self:
            if record.partner_id:
                deposit_structure = self.env['member.deposit.structure'].search([
                    ('partner_id', '=', record.partner_id.id)
                ], limit=1)
                record.current_base_amount = deposit_structure.base_current_amount if deposit_structure else 0.0



    @api.depends('deposit_amount', 'subscription_fee', 'extra_amount')
    def _compute_selected_total(self):
        for record in self:
            record.selected_total = record.deposit_amount + record.subscription_fee + record.extra_amount

    def action_calculate_selected_total(self):
        for record in self:
            record._compute_selected_total()

    @api.depends('start_date', 'end_date')
    def _compute_total_years_months(self):
        for record in self:
            if record.start_date and record.end_date:
                delta = relativedelta(record.end_date, record.start_date)
                if delta.days > 0:
                    delta = relativedelta(years=delta.years, months=delta.months + 1)
                record.total_years = delta.years
                record.total_months = delta.years * 12 + delta.months
            else:
                record.total_years = 0
                record.total_months = 1

    @api.depends('deposit_amount', 'subscription_fee', 'total_months', 'extra_amount')
    def _compute_totals(self):
        for record in self:
            record.subtotal_amount = record.deposit_amount * record.total_months
            record.subtotal_subscription_amount = record.subscription_fee * record.total_months
            record.total_amount_with_subscription = record.subtotal_amount + record.subtotal_subscription_amount
            record.total_with_extra_amount = record.total_amount_with_subscription + record.extra_amount



class ResPartner(models.Model):
    _inherit = 'res.partner'

    deposit_structure_ids = fields.One2many('member.deposit.structure', 'partner_id', string="Deposit Structures")
    total_with_extra_amount = fields.Float(string="Total with Extra Amount", default=0.0)
    related_account_move_id = fields.Many2one('account.move', string="Related Account Move")

