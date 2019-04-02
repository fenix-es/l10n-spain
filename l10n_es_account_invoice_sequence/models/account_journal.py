# -*- coding: utf-8 -*-
# Copyright 2011 NaN Projectes de Programari Lliure, S.L.
# Copyright 2013-2017 Pedro M. Baeza
# Copyright 2019 Jose F. Fernandez

from odoo import _, api, fields, exceptions, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    invoice_sequence_id = fields.Many2one(
        comodel_name='ir.sequence', string='Invoice sequence',
        domain="[('company_id', '=', company_id)]", ondelete='restrict',
        help="The sequence used for invoice numbers in this journal.",
    )
    refund_inv_sequence_id = fields.Many2one(
        comodel_name='ir.sequence', string='Refund sequence',
        domain="[('company_id', '=', company_id)]", ondelete='restrict',
        help="The sequence used for refund invoices numbers in this journal.",
    )

    @api.multi
    @api.constrains('invoice_sequence_id')
    def _check_company(self):
        for journal in self:
            sequence_company = journal.invoice_sequence_id.company_id
            if sequence_company and sequence_company != journal.company_id:
                raise exceptions.Warning(
                    _("Journal company and invoice sequence company do not "
                      "match."))

    @api.multi
    @api.constrains('refund_inv_sequence_id')
    def _check_company_refund(self):
        for journal in self:
            sequence_company = journal.refund_inv_sequence_id.company_id
            if sequence_company and sequence_company != journal.company_id:
                raise exceptions.Warning(
                    _("Journal company and refund sequence company do not "
                      "match."))

    @api.model
    def create(self, vals):
        """Use the existing sequence for new Spanish journals."""
        if not vals.get('company_id') or vals.get('sequence_id'):
            return super(AccountJournal, self).create(vals)
        company = self.env['res.company'].browse(vals['company_id'])
        if company.chart_template_id.is_spanish_chart():
            journal = self.search([('company_id', '=', company.id)], limit=1)
            if journal:
                vals['sequence_id'] = journal.sequence_id.id
                vals['refund_sequence'] = False
        return super(AccountJournal, self).create(vals)

    def _get_invoice_types(self):
        return [
            'sale',
            'purchase',
        ]

    @api.multi
    @api.depends('sequence_id.use_date_range', 'sequence_id.number_next_actual')
    def _compute_seq_number_next(self):
        for journal in self:
            if journal.sequence_id:
                sequence = journal.sequence_id._get_current_sequence()
                journal.sequence_number_next = sequence.number_next_actual
            else:
                if journal.company_id and journal.company_id.chart_template_id.is_spanish_chart():
                    other_journal = self.search([('company_id', '=', journal.company_id.id)], limit=1)
                    if other_journal:
                        journal.sequence_number_next = other_journal.sequence_number_next
                else:
                    journal.sequence_number_next = 1
