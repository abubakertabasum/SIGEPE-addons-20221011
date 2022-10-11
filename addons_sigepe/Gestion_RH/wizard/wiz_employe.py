from odoo import models, fields, api
from odoo.exceptions import UserError

class WizEMploye(models.TransientModel): 
    _name="wiz_employe"
       
    wiz_employe_ids = fields.One2many("wiz_employe_line", "wiz_participant_id")    
    session_id = fields.Many2one("session")    
    
    @api.multi 
    def add_attendee(self):
        for wiz in self:
            if not wiz.session_id:
                raise UserError("Session field is necessary")
            for wizpart in wiz.wiz_participant_ids:
                # import pdb; pdb.set_trace()
                wiz.session_id.write({
                    "participant_ids":[(0, 0, {
                        "name": wizpart.name,
                        "partner_id": wizpart.partner_id.id,
                        "session_id": wiz.session_id.id,
                        })]})    
            
  
class WizEmployeLine(models.TransientModel):
    _name="wiz_employe_line"
    
    wiz_employe_id = fields.Many2one("wiz_employe")
    name = fields.Many2one("categorie")
    partner_id = fields.Many2one("res.partner")