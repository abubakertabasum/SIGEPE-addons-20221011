from odoo import fields,api,models

#heritage de la classe Véhicule
class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"
    x_service_id = fields.Many2one("ref_service",string = "Service")
    x_categorie_id = fields.Many2one('fleet.vehicle.tag', string = 'Catégorie')
    num_chasis = fields.Char(string = "N° Chassis", required = True)
    date_mise_circulation = fields.Date(string = 'Première date de mise en service')
    x_conducteur_id = fields.Many2one('res.partner', 'Conducteur')
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)

#heritage de la classe suivi niveau carburant
class FleetVehicleLogFuel(models.Model):
    _inherit = "fleet.vehicle.log.fuel"
    x_conducteur_id = fields.Many2one('res.partner', 'Conducteur')
    x_montant_total = fields.Float(string = 'Prix Total')
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)


#heritage de la classe relevé kilométriques
class FleetVehicleReleveKiloMetrique(models.Model):
    _inherit = "fleet.vehicle.odometer"
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)



#heritage de la classe cout
class FleetVehicleCout(models.Model):
    _inherit = "fleet.vehicle.cost"
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)



#heritage de la classe contrat des vehicules
class FleetVehicleContrat(models.Model):
    _inherit = "fleet.vehicle.log.contract"
    mnt_ctrct = fields.Integer(string = 'Montant Contrat')
    fichier_joint = fields.Binary(string = 'Joindre Contrat (pdf,word,xls)', attachment = True)
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)


#heritage de la classe models des vehicules
class FleetVehicleInterventionvehicule(models.Model):
    _inherit = "fleet.vehicle.log.services"
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)


#heritage de la classe models des vehicules
class FleetVehicleInterventionvehicule(models.Model):
    _inherit = "fleet.vehicle.model"
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)



#Données de base

#heritage de la classe model de la marque des vehicules
class FleetVehicleMarque(models.Model):
    _inherit = "fleet.vehicle.model.brand"
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)


class FleetServiceType(models.Model):
    _name = 'fleet.service.type'
    _description = 'Fleet Service Type'

    name = fields.Char(required=True, translate=True)
    category = fields.Selection([
        ('contract', 'Contract'),
        ('service', 'Service')
        ], 'Category', required=True, help='Choose whether the service refer to contracts, vehicle services or both')
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)

 
#heritage de la classe type d'intervention des vehicules
"""class FleetVehicleTypeIntervention(models.Model):
    _inherit = "fleet.service.type"
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)
  """
#heritage de la classe type de contrat des vehicules
"""class FleetVehicleTypeContrat(models.Model):
    _inherit = "fleet.service.type"
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)"""
 
#heritage de la classe statut des vehicules
class FleetVehicleStatut(models.Model):
    _inherit = "fleet.vehicle.state"
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)

#heritage de la classe statut des vehicules
class FleetVehicleEtiquette(models.Model):
    _inherit = "fleet.vehicle.tag"
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)

#heritage de la classe type d'activités des vehicules
class FleetVehicleTypeActivites(models.Model):
    _inherit = "mail.activity.type"
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)
          
