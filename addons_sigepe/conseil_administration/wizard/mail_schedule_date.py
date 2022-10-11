# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Mail_Schedule_Date(models.TransientModel):
    _name = 'mail_schedule_date'
    _description = 'Mail Scheduling'

    schedule_date = fields.Datetime(string= "Date d'envoie")
    mail_id = fields.Many2one('ca_nature_session')

    @api.constrains('schedule_date')
    def _check_schedule_date(self):
        for scheduler in self:
            if scheduler.schedule_date < fields.Datetime.now():
                raise ValidationError(_("Veuillez choisir une date superieure à la date d'aujourdui."))

            elif scheduler.schedule_date == fields.Datetime.now():
                ir_model_data = self.env['ir.model.data']
                try:
                    template_id = ir_model_data.get_object_reference('conseil_administration', 'email_template_edi_nature_conseil')[1]
                except ValueError:
                    template_id = False
                try:
                    compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
                except ValueError:
                    compose_form_id = False
                ctx={
                    'default_model': 'ca_nature_session',
                    'default_res_id': self.ids[0],
                    'default_use_template': bool(template_id),
                    'default_use_template': bool(template_id),
                    'default_template_id': template_id,
                    'default_composition_mode': 'comment',
                    'mark_so_as_envoyer': True,
                    'nature_session': self.env.context.get('nature_session', False),
                    'force_email': True,
                }
                return {
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'mail.compose.message',
                    'views': [(compose_form_id, 'form')],
                    'view_id': compose_form_id,
                    'target': 'new',
                    'context': ctx,
                }

    def set_schedule_date(self):
        self.mail_id.write({'schedule_date': self.schedule_date, 'state': 'in_queue'})

