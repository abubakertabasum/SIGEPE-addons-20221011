from odoo import fields,api,models,_
from odoo.exceptions import UserError,ValidationError
from _datetime import date, datetime


#Definition des Classes pour gerer l'evaluation de la fiche A des employés de la fonction publique
class HrBusiness(models.Model):
    
    _name = "bus_intro"
    _order = 'sequence, id'
    sequence = fields.Integer(help="Gives the sequence when displaying a list of Evalauation.", default=10)
    
    name = fields.Char(string = "Libellé court", readonly = False)
    lib_court = fields.Char(string = "Libellé long", readonly = False)
    description = fields.Char(string = "Description", readonly = False)
    

# Definition des classes de synthèses GFC

#Part des charges personnel dans les recettes propres et subventions de l'etat
class GfcChargePersonnel(models.Model):
    _name = 'gfc_charge_personnel'
    _order = 'sequence, id'
    sequence = fields.Integer(help="Gives the sequence when displaying a list of Evalauation.", default=10)
    
    x_exercice_id = fields.Many2one("ref_exercice", default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]), string="Exercice")
    charges_personnel_line = fields.One2many('gfc_charges_personnel_line', 'charge_personnel_id')
    
    @api.multi
    def remplir_balance(self):
        print('rien  afficher pour le moment')
    
class GfcChargePersonnelLine(models.Model):
    _name = 'gfc_charges_personnel_line'
    
    charge_personnel_id = fields.Many2one('gfc_charges_personnel', ondelete='cascade')
    secteur_activite = fields.Char("Secteur d'activité")
    charge_personnel = fields.Integer("Charges personnel")
    montant_rp = fields.Integer("Montant RP")
    taux_rp = fields.Float("CP/RP")
    montant_se = fields.Integer("Montant SE")
    taux_se = fields.Float("CP/Sub. Etat")


#Evolution des recetts et des dépenses des EPE sur les trois dernières années   
class GfcEvolutionRecDep(models.Model):
    _name = 'gfc_evolution_rec_dep'
    _order = 'sequence, id'
    sequence = fields.Integer(help="Gives the sequence when displaying a list of Evalauation.", default=10)
    
    categorie = fields.Selection([
        ('1','EPS Hospitaliers'),
        ('2','EPS non Hospitaliers'),
        ('3','Hydraulique, Développement rural et Foresterie'),
        ('4','Education, Enseignement et Formation Professionnelle'),
        ('5','Ecole Nationale des Enseignants du Primaire'),
        ('6','Système Universitaire'),
        ('7','Prestations de Services et Autres'),
        ('8', 'Communication et Culture'),
        ], 'Catégorie')
    x_exercice_id = fields.Many2one("ref_exercice", default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]), string="Exercice")
    evolution_rec_dep_line = fields.One2many("gfc_evolution_rec_dep_line", "evolution_rec_dep_id")
    
    @api.multi
    def remplir_balance(self):
        print('rien  afficher pour le moment')
    
    
class GfcEvolutionRecDepLine(models.Model):
    _name = 'gfc_evolution_rec_dep_line'

    evolution_rec_dep_id = fields.Many2one("gfc_evolution_rec_dep", ondelete='cascade')
    epe = fields.Char("Structure (EPE)")
    annee2r = fields.Integer("Rec. Année N-2")
    annee1r = fields.Integer("Rec. Année N-1")
    anneer = fields.Integer("Rec. Année N")
    variationr = fields.Integer("Variation Recette")
    annee2d = fields.Integer("Dep. Année N-2")
    annee1d = fields.Integer("Dep. Année N-1")
    anneed = fields.Integer("Dep. Année N")
    variationd = fields.Integer("Variation Dépense")
    
    
    
#CLASS mère de la balance des depenses et recettes    
class Budg_Balance(models.Model):
    @api.depends('type','dt_debut', 'dt_fin')
    def _concate(self):
        for test in self:
            test.concate = "BALANCE DES" + " " + " " + str(test.type)+ " " + "DU" + " " +str(test.dt_debut)+ " " + "AU" + " " +str(test.dt_fin)
        
    _name = 'budg_balance'
    _rec_name = 'concate'
    
    concate = fields.Char(compute = '_concate')
    type = fields.Selection([
        ('DEPENSES', 'Dépense'),
        ('RECETTES', 'Recette')], string = "Balance",required = True)
    dt_debut = fields.Date("Date début",required = True)
    dt_fin = fields.Date("Date fin", required = True)
    x_exercice_id = fields.Many2one("ref_exercice", default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]), string="Exercice")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
    balance_lines = fields.One2many("budg_balance_line", "balance_id")
    total_budget = fields.Integer()
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency", readonly=True)
    total_engagement = fields.Integer()
    total_mandat = fields.Integer()


    @api.onchange('dt_fin')
    def change_dt_fin(self):
        
        if self.dt_fin < self.dt_debut:
            raise ValidationError(_('La date de début ne peut être supérieure à la date de fin'))
    

    
    def remplir_balance(self):
        
        val_ex = int(self.x_exercice_id)
        val_struct = int(self.company_id)
        val_deb = str(self.dt_debut)
        val_fin = str(self.dt_fin)
        balance_id = self.id
        
        if self.type == 'DEPENSES':
            for vals in self:
                vals.env.cr.execute("""SELECT DISTINCT p.paragraphe as code, rp.lb_long as libelle, e.mnt_budgetise as montant, e.mnt_engage as engagement
                FROM budg_ligne_exe_dep e, budg_paragraphe p, ref_paragraphe rp, budg_engagement en
                WHERE e.cd_paragraphe_id = p.id AND rp.id = p.paragraphe AND e.x_exercice_id = %s and e.company_id = %s and en.dt_etat BETWEEN %s and %s """ ,(val_ex, val_struct, val_deb, val_fin))
                rows = vals.env.cr.dictfetchall()
                result = []
                
                vals.balance_lines.unlink()
                for line in rows:
                    result.append((0,0, {'numero_compte' : line['code'], 'libelle': line['libelle'], 'montant_budgetise': line['montant'], 'montant_engagement': line['engagement']}))
                self.balance_lines = result
        else:
            for vals in self:
                vals.env.cr.execute("""SELECT DISTINCT p.paragraphe as code, rp.lb_long as libelle, r.mnt_budgetise as montant, r.mnt_emis as emis
                FROM budg_ligne_exe_rec r,ref_paragraphe rp, budg_paragraphe p, budg_titrerecette re 
                WHERE r.cd_paragraphe_id = p.id AND rp.id = p.paragraphe AND r.x_exercice_id = %s and r.company_id = %s and re.dt_rec BETWEEN %s and %s """ ,(val_ex, val_struct, val_deb, val_fin))
                rows = vals.env.cr.dictfetchall()
                result = []
                
                vals.balance_lines.unlink()
                for line in rows:
                    result.append((0,0, {'numero_compte' : line['code'], 'libelle': line['libelle'], 'montant_budgetise': line['montant'], 'montant_recette': line['emis']}))
                self.balance_lines = result
        
        self.env.cr.execute("""SELECT sum(montant_budgetise)
        FROM budg_balance_line WHERE x_exercice_id = %d AND company_id = %d AND balance_id = %d """ %(val_ex, val_struct, balance_id))
        res = self.env.cr.fetchone()
        self.total_budget = res and res[0]
        val_mnt = self.total_budget
        
        self.env.cr.execute("""SELECT sum(montant_engagement)
        FROM budg_balance_line WHERE x_exercice_id = %d AND company_id = %d AND balance_id = %d """ %(val_ex, val_struct, balance_id))
        res = self.env.cr.fetchone()
        self.total_engagement = res and res[0]
        val_mnt1 = self.total_engagement
        
        self.env.cr.execute("""SELECT sum(montant_mandatement)
        FROM budg_balance_line WHERE x_exercice_id = %d AND company_id = %d AND balance_id = %d """ %(val_ex, val_struct, balance_id))
        res = self.env.cr.fetchone()
        self.total_mandat = res and res[0]
        val_mnt2 = self.total_mandat    
    
    
class Budg_balance_line(models.Model):
    _name = 'budg_balance_line'
    
    balance_id = fields.Many2one("budg_balance")
    numero_compte = fields.Char("Numéro compte")
    libelle = fields.Char("Libellé")
    montant_budgetise = fields.Integer("Budget")
    montant_engagement = fields.Integer("Engagements")
    montant_mandatement = fields.Integer("Mandats")
    montant_recette = fields.Integer("Recettes")
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency", readonly=True)    
    x_exercice_id = fields.Many2one("ref_exercice", default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]), string="Exercice")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)


    
#class de bordereau d'annulation
class BusinessBordereauAnnuleMandat(models.Model): 
    _name = 'bus_bord_annul_mandat'
    x_date_debut = fields.Date('Date debut', required = True)
    x_date_fin = fields.Date('Date fin', required = True)
    x_line_ids = fields.One2many('bus_bord_annul_mandat_line','x_bord_id', string = 'Liste Des Elements')
    x_exercice_id = fields.Many2one("ref_exercice",string = 'Exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))
    company_id = fields.Many2one('res.company',string = 'Structure', default=lambda self: self.env.user.company_id.id)
    total_mandat_annule = fields.Integer('Montant Total annulé')
 
#class de bordereau d'annulation line
class BusinessBordereauAnnuleMandatLine(models.Model): 
    _name = 'bus_bord_annul_mandat_line'
    
    x_bord_id = fields.Many2one('bus_bord_annul_mandat')
    num_mandat = fields.Char("N° mandat")
    nature_depense = fields.Char("Nature de la dépense")
    nom_creancier = fields.Char("Nom Créancier")
    adress_creancier = fields.Char("Adresse Créancier")
    compte = fields.Char("Compte")
    somme_a_annuler = fields.Integer("Somme à annuler")
    x_exercice_id = fields.Many2one("ref_exercice",string = 'Exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))
    company_id = fields.Many2one('res.company',string = 'Structure', default=lambda self: self.env.user.company_id.id)
     
    

#class de synthese generale
class BusinessSyntheseGenerale(models.Model): 
    _name = 'bus_synthese_generale'
    x_line_ids = fields.One2many('bus_synthese_generale_line','x_synth_id', string = 'Liste Des Elements')
    x_exercice_id = fields.Many2one("ref_exercice",string = 'Exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))
    company_id = fields.Many2one('res.company',string = 'Structure', default=lambda self: self.env.user.company_id.id)
    total_recette = fields.Integer('RECETTES TOTALES', readonly = True)
    total_depense = fields.Integer('DEPENSES TOTALES', readonly = True)
    excedent = fields.Integer('EXCEDENT', readonly = True)
    deficit = fields.Integer('DEFICIT', readonly = True)
    date_op = fields.Datetime(string = 'Date opération',default=datetime.today(), readonly = True)
    
    
    
    @api.multi
    def remplir_balance(self):
        print('rien  afficher pour le moment')
 
#class de synthese generale line
class BusinessSyntheseGeneraleLine(models.Model): 
    _name = 'bus_synthese_generale_line'
    
    x_synth_id = fields.Many2one('bus_synthese_generale')
    budget = fields.Integer("Budget")
    pris_en_charge = fields.Integer("Pris en charge")
    recouvrement = fields.Integer("Recouvrement/Paiement")
    x_taux = fields.Char("Taux")
    reste_a_recouvrer = fields.Integer("Reste à Recouvrer/Reste à payer")
    
    x_exercice_id = fields.Many2one("ref_exercice",string = 'Exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))
    company_id = fields.Many2one('res.company',string = 'Structure', default=lambda self: self.env.user.company_id.id)
     
    
    

    

#class des responsables de l'epe
class BusinessPrincipauxResponsables(models.Model): 
    _name = 'bus_principaux_resp'
    _rec_name = 'company_id'
    x_line_ids = fields.One2many('bus_principaux_resp_line','x_princ_id', string = 'Liste Des Principaux Responsables')
    x_exercice_id = fields.Many2one("ref_exercice",string = 'Exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))
    company_id = fields.Many2one('res.company',string = 'Structure', default=lambda self: self.env.user.company_id.id)
    date_op = fields.Datetime(string = 'Date opération',default=datetime.today(), readonly = True)
    
    
    #fonction de recherche des principaux responsables
    def action_rech(self):
        if self.x_exercice_id and self.company_id:
            x_struct_id = int(self.company_id)
            val_exo = int(self.x_exercice_id)
            annee_cours = date(date.today().year,12,31)
            for vals in self:
                    vals.env.cr.execute("""SELECT C.*, R.name,M.decret_nom, M.date_nom,M.date_entree,(F.name) as fct  FROM ca_administrateur C,ca_membre M,hr_fonction F,res_users U,res_partner R WHERE M.id = C.nom_id AND M.nom = U.id and U.partner_id = R.id AND F.id = M.x_fonction_id AND C.etat = 1 AND C.x_exercice_id = %d AND C.company_id = %d """ %(val_exo,x_struct_id))
                    rows = vals.env.cr.dictfetchall()
                    result = []
                    
                    # delete old payslip lines
                    vals.x_line_ids.unlink()
                    for line in rows:
                        nbre = (annee_cours - line['date_entree']).days
                        print('duree', nbre)
                        annee = round(nbre/365)
                        print('annee', annee)
                        result.append((0, 0, {'nom_prenom': line['name'],'fction_id': line['fct'], 'ref':line['decret_nom'],'date_acte': line['date_nom'], 'date_prise_serv':line['date_entree'],'nbre_annee':annee}))
                    self.x_line_ids = result
                    
                    
                    vals.env.cr.execute("""SELECT (E.name) as nom,(E.date_embauche) as date_embauche, (F.name) as fction, (D.date_nomination) as date_nom, (D.ref_acte) as ref FROM hr_employee E, hr_decret_nomination D, hr_fonction F WHERE E.id = D.x_employees_id AND E.x_fonction_id = F.id AND D.etat_nomination = 1 AND E.company_id = %d""" %(x_struct_id))
                    rows = vals.env.cr.dictfetchall()
                    result = []
                    
                    
                    for line in rows:
                        nbre = (annee_cours - line['date_embauche']).days
                        print('durees', nbre)
                        annee = round(nbre/365)
                        print('annees', annee)
                        result.append((0, 0, {'nom_prenom': line['nom'],'fction_id': line['fction'], 'ref':line['ref'],'date_acte': line['date_nom'], 'date_prise_serv':line['date_embauche'],'nbre_annee': annee}))
                    self.x_line_ids = result
 
#class des responsables de l'epe line
class BusinessPrincipauxResponsablesLine(models.Model): 
    _name = 'bus_principaux_resp_line'
    
    x_princ_id = fields.Many2one('bus_principaux_resp')
    nom_prenom = fields.Char("Nom et Prénoms")
    fction_id = fields.Char("Fonction")
    ref = fields.Char("Référence")
    date_acte = fields.Date("Date acte Nomination")
    date_prise_serv = fields.Date("Date prise service")
    nbre_annee = fields.Integer("Nombre d'année de service revolu au poste")
    
    x_exercice_id = fields.Many2one("ref_exercice",string = 'Exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))
    company_id = fields.Many2one('res.company',string = 'Structure', default=lambda self: self.env.user.company_id.id)




#class de resolutions d'ordre generale
class BusinessResolutionsGenerales(models.Model): 
    _name = 'bus_resolution_gle'
    _rec_name = 'x_exercice_id'
    x_line_ids = fields.One2many('bus_resolution_gle_line','x_resol_gle_id', string = 'Liste Des Resolutions Generales')
    x_line_c_ids = fields.One2many('bus_struct_resolution_gle_line','x_struct_resol_gle_id', string = 'Liste Des Resolutions Generales Par Structures')
    x_exercice_id = fields.Many2one("ref_exercice",string = 'Exercice',readonly = True,  default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))
    cat_struct = fields.Many2one('ref_categorie_structure', string = 'Catégorie Structure')
    company_id = fields.Many2one('res.company',string = 'Structure', default=lambda self: self.env.user.company_id.id, readonly = True)
    date_op = fields.Datetime(string = 'Date opération',default=datetime.today(), readonly = True)
    struct_id = fields.Many2one('res.company',string = 'Structure')

    
     #fonction de recherche des structures
    def action_rech(self):
        if self.cat_struct and self.company_id:
            x_struct_id = str(self.struct_id.name)
            print('struct', x_struct_id)
            x_cat_id = str(self.cat_struct.name)
            print('cat', x_cat_id)
            for vals in self:
                if x_struct_id == 'TOUTES LES STRUCTURES' and x_cat_id == 'TOUTES LES CATEGORIES':
                    vals.env.cr.execute("""SELECT (C.id) as cat, (R.id) as structure FROM res_company R, ref_categorie_structure C WHERE C.id = R.ref_cat_struct_id """)
                    rows = vals.env.cr.dictfetchall()
                    result = []
                    
                    # delete old payslip lines
                    vals.x_line_c_ids.unlink()
                    for line in rows:
                        result.append((0, 0, {'cat_struct': line['cat'], 'company_id':line['structure']}))
                    self.x_line_c_ids = result
                else:
                    # delete old payslip lines
                    vals.x_line_c_ids.unlink()
                    raise ValidationError(_('Veuillez selectionnez TOUTES LES CATEGORIES et TOUTES LES STRUCTURES avant de cliquer sur ce bouton svp!'))
                    
                    
    
#class de resolutions d'ordre generale line
class BusinessResolutionsGeneralesLine(models.Model): 
    _name = 'bus_resolution_gle_line'
    
    x_resol_gle_id = fields.Many2one('bus_resolution_gle')
    nature_resolution = fields.Text("NATURE DE LA RESOLUTION")
    etat_mise_en_oeuvre = fields.Text("ETAT DE MISE EN OEUVRE")
    observation_damof = fields.Text("OBSERVATIONS DAMOF")
    
    x_exercice_id = fields.Many2one("ref_exercice",string = 'Exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))
    company_id = fields.Many2one('res.company',string = 'Structure', default=lambda self: self.env.user.company_id.id)


#class de resolutions d'ordre generale structures concernes line
class BusinessStructuresResolutionsGeneralesLine(models.Model): 
    _name = 'bus_struct_resolution_gle_line'
    
    x_struct_resol_gle_id = fields.Many2one('bus_resolution_gle')
    cat_struct = fields.Many2one('ref_categorie_structure', string = 'Catégorie Structure')
    company_id = fields.Many2one('res.company',string = 'Structure')
          
  
  
#class de resolutions d'ordre spec
class BusinessResolutionsSpecifiques(models.Model): 
    _name = 'bus_resolution_spec'
    _rec_name = 'x_exercice_id'
    x_line_ids = fields.One2many('bus_resolution_spec_line','x_resol_spec_id', string = 'Liste Des Resolutions Spécifiques')
    x_line_c_ids = fields.One2many('bus_struct_resolution_spec_line','x_struct_resol_spec_id', string = 'Liste Des Structures concernées')
    x_exercice_id = fields.Many2one("ref_exercice",string = 'Exercice',readonly = True,  default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))
    cat_struct = fields.Many2one('ref_categorie_structure', string = 'Catégorie Structure')
    company_id = fields.Many2one('res.company',string = 'Structure', default=lambda self: self.env.user.company_id.id, readonly = True)
    date_op = fields.Datetime(string = 'Date opération',default=datetime.today(), readonly = True)
    struct_id = fields.Many2one('res.company',string = 'Structure')
    
    
    #fonction de recherche des structures
    def action_rech(self):
        if self.cat_struct:
            
            x_cat_id = str(self.cat_struct.name)
            x_cats_id = int(self.cat_struct)
            print('cat', x_cats_id)
            for vals in self:
                vals.env.cr.execute("""SELECT (C.id) as cat, (R.id) as structure FROM res_company R, ref_categorie_structure C WHERE C.id = R.ref_cat_struct_id AND C.id = %d""" %(x_cats_id))
                rows = vals.env.cr.dictfetchall()
                result = []
                
                # delete old payslip lines
                vals.x_line_c_ids.unlink()
                for line in rows:
                    result.append((0, 0, {'cat_struct': line['cat'], 'company_id':line['structure']}))
                self.x_line_c_ids = result
                
    
    
#class de resolutions d'ordre spec line
class BusinessResolutionsSpecifiquesLine(models.Model): 
    _name = 'bus_resolution_spec_line'
    
    x_resol_spec_id = fields.Many2one('bus_resolution_gle')
    nature_resolution = fields.Text("NATURE DE LA RESOLUTION")
    etat_mise_en_oeuvre = fields.Text("ETAT DE MISE EN OEUVRE")
    observation_damof = fields.Text("OBSERVATIONS DAMOF")
    
    x_exercice_id = fields.Many2one("ref_exercice",string = 'Exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))
    company_id = fields.Many2one('res.company',string = 'Structure', default=lambda self: self.env.user.company_id.id)
     
     
#class de resolutions d'ordre spec structures concernes line
class BusinessStructuresResolutionsSpecifiquesLine(models.Model): 
    _name = 'bus_struct_resolution_spec_line'
    
    x_struct_resol_spec_id = fields.Many2one('bus_resolution_spec')
    cat_struct = fields.Many2one('ref_categorie_structure', string = 'Catégorie Structure')
    company_id = fields.Many2one('res.company',string = 'Structure')


#class de recommandations d'ordre generale
class BusinessRecommandationsGenerales(models.Model): 
    _name = 'bus_recommandation_gle'
    _rec_name = 'x_exercice_id'
    x_line_ids = fields.One2many('bus_recommandation_gle_line','x_recomm_gle_id', string = 'Liste Des Recommandations Generales')
    x_exercice_id = fields.Many2one("ref_exercice",string = 'Exercice',readonly = True,  default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))
    company_id = fields.Many2one('res.company',string = 'Structure', default=lambda self: self.env.user.company_id.id, readonly = True)
    date_op = fields.Datetime(string = 'Date opération',default=datetime.today(), readonly = True)
    
    
#class de recommandations d'ordre generale line
class BusinessRecommandationsGeneralesLine(models.Model): 
    _name = 'bus_recommandation_gle_line'
    
    x_recomm_gle_id = fields.Many2one('bus_recommandation_gle')
    nature_recommandation = fields.Text("NATURE DE LA RECOMMANDATION")
    etat_mise_en_oeuvre = fields.Text("ETAT DE MISE EN OEUVRE")
    observation_damof = fields.Text("OBSERVATIONS DAMOF")
    
    x_exercice_id = fields.Many2one("ref_exercice",string = 'Exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))
    company_id = fields.Many2one('res.company',string = 'Structure', default=lambda self: self.env.user.company_id.id)
     
 

#class de recommandations d'ordre spec
class BusinessRecommandationsSpecifiques(models.Model): 
    _name = 'bus_recommandation_spec'
    _rec_name = 'x_exercice_id'
    x_line_ids = fields.One2many('bus_recommandation_spec_line','x_recommandation_spec_id', string = 'Liste Des Recommandations Spécifiques')
    x_exercice_id = fields.Many2one("ref_exercice",string = 'Exercice',readonly = True,  default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))
    company_id = fields.Many2one('res.company',string = 'Structure',default=lambda self: self.env.user.company_id.id)
    date_op = fields.Datetime(string = 'Date opération',default=datetime.today(), readonly = True)
    
    
#class de recommandations d'ordre spec line
class BusinessRecommandationsSpecifiquesLine(models.Model): 
    _name = 'bus_recommandation_spec_line'
    
    x_recommandation_spec_id = fields.Many2one('bus_recommandation_spec')
    nature_recommandation = fields.Text("NATURE DE LA RECOMMANDATION")
    etat_mise_en_oeuvre = fields.Text("ETAT DE MISE EN OEUVRE")
    observation_damof = fields.Text("OBSERVATIONS DAMOF")
    
    x_exercice_id = fields.Many2one("ref_exercice",string = 'Exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))
    company_id = fields.Many2one('res.company',string = 'Structure', default=lambda self: self.env.user.company_id.id)
      





     
     
    
