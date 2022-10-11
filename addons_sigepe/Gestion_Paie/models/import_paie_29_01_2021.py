import babel
from odoo import fields,api,models,tools,_
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from num2words import num2words
from odoo.exceptions import UserError,ValidationError


#heritage de la classe de bulletin de l'employé  
class HrPrepIndividuel(models.Model):
    
    _inherit = "hr.payslip"
    current_user = fields.Many2one('res.users','Current User', default=lambda self: self.env.user)
    annee_bull = fields.Integer( string = 'Année')
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)
    x_structure_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)
    #commentaire = fields.Text(string = 'Commentaire')



#heritage de la classe permettant de tirer les lots debulletins des emploiyés   
class HrLotBulletin(models.Model):
    
    _inherit = "hr.payslip.run"
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)
    x_structure_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)
    
 
    
#heritage de la classe des structures des salaires
class HrStructureSalaire(models.Model):
    
    _inherit = "hr.payroll.structure"
    
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)
    x_structure_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)
      

#heritage de la classe des categories des salaires
class HrCategorieSalaire(models.Model):
    
    _inherit = "hr.salary.rule.category"
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)
    x_structure_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)
    

#heritage de la classe des elements de salaires
class HrElementSalaire(models.Model):
    
    _inherit = "hr.salary.rule"
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)
    x_structure_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)
   

class HrReportMode(models.TransientModel):
    
    _name = "hr_reportmode"
    financiers_id = fields.Many2one('res.users', string = "Financier", required = True)
    drhs_id = fields.Many2one('res.users', string = "DRH", required = True)
    description = fields.Text(string = 'Description')
    _rec_name = 'x_mode_paiements'
    x_type_employe_id = fields.Many2one("hr.payroll.structure",string ="Type employé", required = True)
    x_mode_paiements = fields.Selection([
        ('billetage','Billetage'),
        ('virement','Virement'),   
        ], string = "Mode de Paiement",default = 'billetage', required = True)
    x_date_debut = fields.Date(string = 'Date début',default=lambda self: fields.Date.to_string(date.today().replace(day=1)), required = True)
    x_date_fin = fields.Date(string = 'Date fin',default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()), required = True)
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)
    x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))
    x_line_ids = fields.One2many('hr_reportmode_line','x_report_id', string = "Liste des concernés")
    x_mnts = fields.Float(string = 'Montant Total')
    x_mnt_en_lettre = fields.Char(string = 'Montant en lettres')
    x_moi = fields.Selection([
        ('janvier','Janvier'),
        ('fevrier','Février'),
        ('mars','Mars'),
        ('avril','Avril'),
        ('mai','Mai'),
        ('juin','Juin'),
        ('juillet','Juillet'),
        ('aout','Août'),
        ('septembre','Septembre'),
        ('octobre','Octobre'),
        ('novembre','Novembre'),
        ('decembre','Décembre'),  
        ], string = "Choisir Mois",default = 'janvier', required = True)
    date_op = fields.Datetime(string = 'Date impression',default=datetime.today(), readonly = True)
    
    
    
    #fonction de remplissage du tableau
    def remplissage(self):
        if self.x_date_debut and self.x_date_fin:
            ddbut = str(self.x_date_debut.strftime("%Y-%m-%d"))          
            ddfin = str(self.x_date_fin.strftime("%Y-%m-%d"))
            x_struct_id = int(self.company_id)
            x_type_id = int(self.x_type_employe_id)
            nom_type = str(self.x_type_employe_id.name)
            x_mode = str(self.x_mode_paiements)
            for vals in self:
                if nom_type == 'Tout Type' and x_mode == 'billetage':
                    vals.env.cr.execute("""SELECT (P.id) AS id, (P.name) AS nom, (E.x_net_payer_ctrct) AS net,(E.matricule_genere) as mat, (EM.name) as emploi,(FC.name) as fonction, (E.name) AS employe,(S.name) as struct FROM hr_employee E ,hr_fonctionss FC, hr_emploi EM,hr_payslip P,hr_payroll_structure S WHERE E.id = P.employee_id AND EM.id = E.x_emploi_id AND FC.id = E.x_fonction_id and E.x_mode_paiement = P.x_mode_paiement and P.date_from >= %s and P.date_to <= %s and E.company_id = %s and S.id = E.x_type_employe_id and E.x_mode_paiement = 'billetage' and P.state = 'done' ORDER BY employe ASC""",(ddbut ,ddfin,x_struct_id))
                    rows = vals.env.cr.dictfetchall()
                    result = []
                    
                    # delete old payslip lines
                    vals.x_line_ids.unlink()
                    self.x_mnts = 0.0
                    text= ''
                    for line in rows:
                        result.append((0, 0, {'x_matricule': line['mat'],'name': line['employe'],'x_emploi': line['emploi'],'x_fonction': line['fonction'], 'x_sal_net':line['net'],'x_type_struct':line['struct']}))
                        self.x_mnts += line['net']
                    self.x_line_ids = result
                    text+=num2words(vals.x_mnts, lang='fr')
                    self.x_mnt_en_lettre = text
                elif nom_type == 'Tout Type' and x_mode == 'virement':
                    for vals in self:
                        vals.env.cr.execute("""SELECT (P.id) AS id, (P.name) AS nom, (E.x_net_payer_ctrct) AS net,(E.matricule_genere) as mat,(E.num_banque) as numb, (EM.name) as emploi,(FC.name) as fonction, (E.name) AS employe,(S.name) as struct  FROM hr_employee E ,hr_fonctionss FC, hr_emploi EM, res_bank R, hr_payslip P,hr_payroll_structure S WHERE E.id = P.employee_id and FC.id = E.x_fonction_id and E.x_emploi_id = EM.id  and E.x_banque_id = R.id and E.x_mode_paiement = P.x_mode_paiement and P.date_from >= %s  and P.date_to <= %s  and E.company_id = %s and S.id = E.x_type_employe_id and E.x_mode_paiement = 'virement' and P.state = 'done' ORDER BY employe ASC""",(ddbut ,ddfin,x_struct_id))
                        rows = vals.env.cr.dictfetchall()
                        result = []
                        
                        # delete old payslip lines
                        vals.x_line_ids.unlink()
                        self.x_mnts = 0.0
                        text = ''
                        for line in rows:
                            result.append((0, 0, {'x_matricule': line['mat'],'name': line['employe'],'numb': line['numb'],'x_emploi': line['emploi'],'x_fonction': line['fonction'], 'x_sal_net':line['net'],'x_type_struct':line['struct']}))
                            self.x_mnts += line['net']
                        self.x_line_ids = result
                        text+=num2words(vals.x_mnts, lang='fr')
                        self.x_mnt_en_lettre = text
                
                else:
                    if x_mode == 'billetage':
                        vals.env.cr.execute("""SELECT (P.id) AS id, (P.name) AS nom, (E.x_net_payer_ctrct) AS net,(E.matricule_genere) as mat, (EM.name) as emploi,(FC.name) as fonction, (E.name) AS employe,(S.name) as struct FROM hr_employee E ,hr_fonctionss FC, hr_emploi EM,hr_payslip P,hr_payroll_structure S WHERE E.id = P.employee_id AND EM.id = E.x_emploi_id AND FC.id = E.x_fonction_id and E.x_mode_paiement = P.x_mode_paiement and P.date_from >= %s and P.date_to <= %s and E.company_id = %s and S.id = E.x_type_employe_id and E.x_type_employe_id = %s and E.x_mode_paiement = 'billetage' and P.state = 'done' ORDER BY employe ASC""",(ddbut ,ddfin,x_struct_id,x_type_id))
                        rows = vals.env.cr.dictfetchall()
                        result = []
                        
                        # delete old payslip lines
                        vals.x_line_ids.unlink()
                        self.x_mnts = 0.0
                        text= ''
                        for line in rows:
                            result.append((0, 0, {'x_matricule': line['mat'],'name': line['employe'],'x_emploi': line['emploi'],'x_fonction': line['fonction'], 'x_sal_net':line['net'],'x_type_struct':line['struct']}))
                            self.x_mnts += line['net']
                        self.x_line_ids = result
                        text+=num2words(vals.x_mnts, lang='fr')
                        self.x_mnt_en_lettre = text
                    else:
                        for vals in self:
                            vals.env.cr.execute("""SELECT (P.id) AS id, (P.name) AS nom, (E.x_net_payer_ctrct) AS net,(E.matricule_genere) as mat,(E.num_banque) as numb, (EM.name) as emploi,(FC.name) as fonction, (E.name) AS employe,(S.name) as struct  FROM hr_employee E ,hr_fonctionss FC, hr_emploi EM, res_bank R, hr_payslip P,hr_payroll_structure S WHERE E.id = P.employee_id and FC.id = E.x_fonction_id and E.x_emploi_id = EM.id  and E.x_banque_id = R.id and E.x_mode_paiement = P.x_mode_paiement and P.date_from >= %s  and P.date_to <= %s  and E.company_id = %s and S.id = E.x_type_employe_id and E.x_type_employe_id = %s and E.x_mode_paiement = 'virement' and P.state = 'done' ORDER BY employe ASC""",(ddbut ,ddfin,x_struct_id,x_type_id))
                            rows = vals.env.cr.dictfetchall()
                            result = []
                            
                            # delete old payslip lines
                            vals.x_line_ids.unlink()
                            self.x_mnts = 0.0
                            text = ''
                            for line in rows:
                                result.append((0, 0, {'x_matricule': line['mat'],'name': line['employe'],'numb': line['numb'],'x_emploi': line['emploi'],'x_fonction': line['fonction'], 'x_sal_net':line['net'],'x_type_struct':line['struct']}))
                                self.x_mnts += line['net']
                            self.x_line_ids = result
                            text+=num2words(vals.x_mnts, lang='fr')
                            self.x_mnt_en_lettre = text
                
                    
                
        
#class permettant de recueillir les lignes de la requête   
class HrReportModeLine(models.TransientModel):
    _name = "hr_reportmode_line"
    x_report_id = fields.Many2one('hr_reportmode')
    x_matricule = fields.Char(string = 'Matricule')
    name = fields.Char(string = 'Employé')
    numb = fields.Char(string = 'N° Compte')
    x_emploi = fields.Char(string = 'Emploi')
    x_fonction = fields.Char(string = 'Fonction')
    x_sal_net = fields.Float(string = 'Salaire net')
    x_mnt = fields.Float(string = 'Montant')
    x_type_struct = fields.Char(string = 'Type employé')
    
    



class HrReportBanque(models.TransientModel):
    
    _name = "hr_reportbanque"
    _rec_name = 'x_banq_id'
    financiers_id = fields.Many2one('res.users', string = "Financier", required = True)
    drhs_id = fields.Many2one('res.users', string = "DRH", required = True)
    description = fields.Text(string = 'Description')
    x_banq_id = fields.Many2one('res.bank', string = 'Nom banque',  required = True)
    x_date_debut = fields.Date(string = 'Date début',default=lambda self: fields.Date.to_string(date.today().replace(day=1)), required = True)
    x_date_fin = fields.Date(string = 'Date fin',default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()), required = True)
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)
    x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))
    x_line_ids = fields.One2many('hr_reportbanque_line','x_report_id', string = "Liste des concernés")
    x_mnts = fields.Float(string = 'Montant Total')
    x_mnt_en_lettre = fields.Char(string = 'Montant en lettres')
    x_moi = fields.Selection([
        ('janvier','Janvier'),
        ('fevrier','Février'),
        ('mars','Mars'),
        ('avril','Avril'),
        ('mai','Mai'),
        ('juin','Juin'),
        ('juillet','Juillet'),
        ('aout','Août'),
        ('septembre','Septembre'),
        ('octobre','Octobre'),
        ('novembre','Novembre'),
        ('decembre','Décembre'),  
        ], string = "Choisir Mois",default = 'janvier', required = True)
    date_op = fields.Datetime(string = 'Date impression',default=datetime.today(), readonly = True)
    
    
    
    #fonction de remplissage du tableau
    def remplissage(self):
        if self.x_date_debut and self.x_date_fin:
            ddbut = str(self.x_date_debut.strftime("%Y-%m-%d"))          
            ddfin = str(self.x_date_fin.strftime("%Y-%m-%d"))
            banq_id = int(self.x_banq_id)
            x_struct_id = int(self.company_id)
            for vals in self:
                vals.env.cr.execute("""SELECT (P.id) AS id, (P.name) AS nom, (E.x_net_payer_ctrct) AS net,(E.matricule_genere) as mat,(E.num_banque) as numb, (EM.name) as emploi,(FC.name) as fonction, (E.name) AS employe FROM hr_employee E ,hr_fonctionss FC, hr_emploi EM, res_bank R, hr_payslip P WHERE E.id = P.employee_id and FC.id = E.x_fonction_id and E.x_emploi_id = EM.id and E.x_banque_id = R.id and P.date_from >= %s  and P.date_to <= %s  and R.id = %s and E.company_id = %s and P.state = 'done' ORDER BY employe ASC""",(ddbut ,ddfin,banq_id,x_struct_id))
                rows = vals.env.cr.dictfetchall()
                result = []
                
                # delete old payslip lines
                vals.x_line_ids.unlink()
                self.x_mnts = 0.0
                text = ''
                for line in rows:
                    result.append((0, 0, {'x_matricule': line['mat'],'name': line['employe'],'numb': line['numb'],'x_emploi': line['emploi'],'x_fonction': line['fonction'], 'x_sal_net':line['net']}))
                    self.x_mnts += line['net']
                self.x_line_ids = result
                text+=num2words(vals.x_mnts, lang='fr')
                self.x_mnt_en_lettre = text
                
                    
                
        
#class permettant de recueillir les lignes de la requête   
class HrReportBanqueLine(models.TransientModel):
    _name = "hr_reportbanque_line"
    x_report_id = fields.Many2one('hr_reportbanque')
    x_matricule = fields.Char(string = 'Matricule')
    name = fields.Char(string = 'Employé')
    numb = fields.Char(string = 'N° Compte')
    x_emploi = fields.Char(string = 'Emploi')
    x_fonction = fields.Char(string = 'Fonction')
    x_sal_net = fields.Float(string = 'Salaire net')
    x_mnt = fields.Float(string = 'Montant')
    
    
class HrEtatNominatifs(models.Model):
    
    _inherit = "hr.contribution.register"
    x_strucutre_id = fields.Many2one('res.company', string = 'Structure', default=lambda self: self.env.user.company_id.id)

#classe mère des etats des avoirs
class HrReportAvoirs(models.TransientModel):
    
    _name = "hr_reportavoir"
    name = fields.Char(string = 'Nom')
    _rec_name = 'lib_long'
    financiers_id = fields.Many2one('res.users', string = "Financier", required = True)
    drhs_id = fields.Many2one('res.users', string = "DRH", required = True)
   
    x_type_employe_id = fields.Many2one("hr.payroll.structure",string ="Type employé", required = True)
    x_elt_sal_id = fields.Many2one('hr.salary.rule',string = 'Element de salaire', required = True)
    lib_long = fields.Char(string = 'Intitulé Etat', required = True)
    x_date_debut = fields.Date(string = 'Date début',default=lambda self: fields.Date.to_string(date.today().replace(day=1)), required = True)
    x_date_fin = fields.Date(string = 'Date fin',default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()), required = True)
    x_mnts = fields.Float(string = 'Montant Total')
    x_mnt_en_lettre = fields.Char(string = 'Montant en lettres')
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)
    x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))
    x_line_ids = fields.One2many('hr_reportavoir_line','x_reportavoir_id', string = "Liste des élements")
    x_moi = fields.Selection([
        ('janvier','Janvier'),
        ('fevrier','Février'),
        ('mars','Mars'),
        ('avril','Avril'),
        ('mai','Mai'),
        ('juin','Juin'),
        ('juillet','Juillet'),
        ('aout','Août'),
        ('septembre','Septembre'),
        ('octobre','Octobre'),
        ('novembre','Novembre'),
        ('decembre','Décembre'),  
        ], string = "Choisir Mois",default = 'janvier', required = True)
    date_op = fields.Date(string = 'Date Opération',default=date.today(), readonly = True)
    
    
    
    #fonction de remplissage du tableau des avoirs
    def avoir(self):
        if self.x_type_employe_id and self.x_elt_sal_id and self.x_date_debut and self.x_date_fin:
            ddbut = str(self.x_date_debut.strftime("%Y-%m-%d"))          
            ddfin = str(self.x_date_fin.strftime("%Y-%m-%d"))
            elt_sal = int(self.x_elt_sal_id)
            emp_type = int(self.x_type_employe_id)
            x_struct_id = int(self.company_id)
            for vals in self:
                vals.env.cr.execute("""SELECT (L.total) AS Total,(E.name) AS employe,(E.matricule) as mat,(E.matricule_genere) as mat_c FROM hr_payslip_line L,hr_payslip LP, hr_employee E where L.slip_id = LP.id and E.id = L.employee_id and LP.struct_id =%s and L.salary_rule_id = %s and LP.date_from >= %s  and LP.date_to <= %s and LP.company_id = %s and LP.state = 'done' AND E.active = 'True'""",(emp_type ,elt_sal,ddbut,ddfin,x_struct_id))
                rows = vals.env.cr.dictfetchall()
                result = []
                
                # delete old payslip lines
                vals.x_line_ids.unlink()
                self.x_mnts = 0.0
                text = ''
                for line in rows:
                    result.append((0, 0, {'name': line['employe'],'x_matricule': line['mat'],'x_matricule_c': line['mat_c'], 'x_mnt':line['total']}))
                    self.x_mnts += line['total'] 
                self.x_line_ids = result
                text+=num2words(vals.x_mnts, lang='fr')
                self.x_mnt_en_lettre = text
                
                
        
    
class HrReportAvoirsLine(models.TransientModel):
    _name = "hr_reportavoir_line"
    name = fields.Char(string = 'Employé')
    x_matricule = fields.Char(string = 'Mle Fonctionnaire')
    x_matricule_c = fields.Char(string = 'Mle Contractuel')
    x_reportavoir_id = fields.Many2one('hr_reportavoir')
    x_mnt = fields.Float(string = 'Montant')
    
    
    
#classe mère des etats des parts agents et patronales
class HrReportPartAgent(models.TransientModel):
    
    _name = "hr_reportpart"
    name = fields.Char(string = 'Nom')
    _rec_name = 'lib_long'
    financiers_id = fields.Many2one('res.users', string = "Financier", required = True)
    drhs_id = fields.Many2one('res.users', string = "DRH", required = True)

    lib_long = fields.Char(string = 'Intitulé Etat',required = True)
    lib_court = fields.Char(string = 'element salaire')
    x_type_employe_id = fields.Many2one("hr.payroll.structure",string ="Type employé", required = True)
    x_date_debut = fields.Date(string = 'Date début',default=lambda self: fields.Date.to_string(date.today().replace(day=1)), required = True)
    x_date_fin = fields.Date(string = 'Date fin',default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()), required = True)
    x_mnt_agent = fields.Float(string = 'Part Totale Agent')
    x_mnt_en_lettre = fields.Char(string = 'Montant en lettres')
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)
    x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))
    x_line_ids = fields.One2many('hr_reportpart_line','x_reportpart_id', string = "Liste des élements")
    x_moi = fields.Selection([
        ('janvier','Janvier'),
        ('fevrier','Février'),
        ('mars','Mars'),
        ('avril','Avril'),
        ('mai','Mai'),
        ('juin','Juin'),
        ('juillet','Juillet'),
        ('aout','Août'),
        ('septembre','Septembre'),
        ('octobre','Octobre'),
        ('novembre','Novembre'),
        ('decembre','Décembre'),  
        ], string = "Choisir Mois",default = 'janvier', required = True)
    date_op = fields.Date(string = 'Date Opération',default=date.today(), readonly = True)
    
    
    #fonction pour remplir le libellé court
    @api.onchange('x_type_employe_id')
    def remplir_libcourt(self):
        if self.x_type_employe_id.name == 'Fonctionnaire Detaché' or self.x_type_employe_id.name == 'fonctionnaire detaché' or self.x_type_employe_id.name == 'FONCTIONNAIRE DETACHE' or self.x_type_employe_id.name == 'Fonctionnaire Mis à Disposition' or self.x_type_employe_id.name == 'FONCTIONNAIRE MIS A DISPOSITION':
            self.lib_court = 'Cotisaton CARFO'
        elif self.x_type_employe_id.name == 'Contractuel'or self.x_type_employe_id.name == 'contractuel' or self.x_type_employe_id.name == 'CONTRACTUEL':
            self.lib_court = 'Cotisaton CNSS'
        else:
            self.lib_court = ''
    
    #fonction de remplissage du tableau des parts
    def part(self):
        if self.x_date_debut and self.x_date_fin:
            ddbut = str(self.x_date_debut.strftime("%Y-%m-%d"))          
            ddfin = str(self.x_date_fin.strftime("%Y-%m-%d"))
            x_struct_id = int(self.company_id)
            x_type_id = int(self.x_type_employe_id)
            libcourt = str(self.lib_court)
            for vals in self:
                #vals.env.cr.execute("""select DISTINCT(L.name) AS element_salaire, (L.total) AS Total, (E.name) AS employe from hr_payslip_line L, hr_employee E, hr_payslip LP where L.slip_id = LP.id and E.id = L.employee_id and LP.date_from >= %s  and LP.date_to <= %s and LP.company_id = %s and L.name = 'Cotisation Carfo' or L.name = 'Cotisation CARFO' or L.name = 'Cotisation Cnss' or L.name = 'Cotisation CNSS' or L.name = 'cotisation cnss'""",(ddbut,ddfin,x_struct_id))
                if self.x_type_employe_id.name == 'Fonctionnaire Detaché' or self.x_type_employe_id.name == 'fonctionnaire detaché' or self.x_type_employe_id.name == 'FONCTIONNAIRE DETACHE' or self.x_type_employe_id.name == 'Fonctionnaire Mis à Disposition' or self.x_type_employe_id.name == 'FONCTIONNAIRE MIS A DISPOSITION': 
                    
                    vals.env.cr.execute("""select DISTINCT(L.name) AS element_salaire, (L.total) AS Total, (E.name) AS employe,(E.matricule) as mat,(E.matricule_genere) as mat_c from hr_payslip_line L, hr_employee E, hr_payslip LP where L.slip_id = LP.id and E.id = L.employee_id and LP.date_from >= %s  and LP.date_to <= %s and LP.company_id = %s and LP.struct_id = %s and LP.state = 'done' and L.name = 'Cotisation CARFO' AND E.active = 'True' ORDER BY employe ASC """,(ddbut,ddfin,x_struct_id,x_type_id))
                    rows = vals.env.cr.dictfetchall()
                    result = []
                    
                    # delete old payslip lines
                    vals.x_line_ids.unlink()
                    self.x_mnt_agent = 0.0
                    text = ''
                    for line in rows:
                        result.append((0, 0, {'name': line['employe'],'x_matricule': line['mat'],'x_matricule_c': line['mat_c'], 'x_mnt_agent':line['total']}))
                        self.x_mnt_agent += line['total']  
                    self.x_line_ids = result
                    text+=num2words(vals.x_mnt_agent, lang='fr')
                    self.x_mnt_en_lettre = text 
                else:
                    
                    vals.env.cr.execute("""select DISTINCT(L.name) AS element_salaire, (L.total) AS Total, (E.name) AS employe,(E.matricule) as mat,(E.matricule_genere) as mat_c,(E.num_declaration) as numc from hr_payslip_line L, hr_employee E, hr_payslip LP where L.slip_id = LP.id and E.id = L.employee_id and LP.date_from >= %s  and LP.date_to <= %s and LP.company_id = %s and LP.struct_id = %s and LP.state = 'done' and L.name = 'Cotisation CNSS' AND E.active = 'True' ORDER BY employe ASC """,(ddbut,ddfin,x_struct_id,x_type_id))
                    rows = vals.env.cr.dictfetchall()
                    result = []
                    
                    # delete old payslip lines
                    vals.x_line_ids.unlink()
                    self.x_mnt_agent = 0.0
                    text = ''
                    for line in rows:
                        result.append((0, 0, {'name': line['employe'],'x_matricule': line['mat'],'x_matricule_c': line['mat_c'],'x_num_cnss': line['numc'], 'x_mnt_agent':line['total']}))
                        self.x_mnt_agent += line['total']  
                    self.x_line_ids = result
                    text+=num2words(vals.x_mnt_agent, lang='fr')
                    self.x_mnt_en_lettre = text 
                        

class HrReportPartAgentLine(models.TransientModel):
    _name = "hr_reportpart_line"
    name = fields.Char(string = 'Employé')
    x_matricule = fields.Char(string = 'Mle Fonctionnaire')
    x_matricule_c = fields.Char(string = 'Mle Contractuel')
    x_num_cnss = fields.Char(string = 'N°CNSS')
    x_reportpart_id = fields.Many2one('hr_reportpart')
    x_mnt_agent = fields.Float(string = 'Part agent')
    


#classe mère des etats des parts employeurs
class HrReportPartEmployeur(models.TransientModel):
    
    _name = "hr_reportpartemp"
    name = fields.Char(string = 'Nom')
    _rec_name = 'lib_long'
    financiers_id = fields.Many2one('res.users', string = "Financier", required = True)
    drhs_id = fields.Many2one('res.users', string = "DRH", required = True)
 
    lib_long = fields.Char(string = 'Libéllé long', required = True)
    lib_court = fields.Char(string = 'element salaire')
    x_type_employe_id = fields.Many2one("hr.payroll.structure",string ="Type employé",  required = True)
    x_date_debut = fields.Date(string = 'Date début',default=lambda self: fields.Date.to_string(date.today().replace(day=1)), required = True)
    x_date_fin = fields.Date(string = 'Date fin',default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()), required = True)
    x_mnt_empl = fields.Float(string = 'Part Totale Employeur')
    x_mnt_en_lettre = fields.Char(string = 'Montant en lettres')
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)
    x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))
    x_line_ids = fields.One2many('hr_reportpartemp_line','x_reportpartemp_id', string = "Liste des élements")
    x_moi = fields.Selection([
        ('janvier','Janvier'),
        ('fevrier','Février'),
        ('mars','Mars'),
        ('avril','Avril'),
        ('mai','Mai'),
        ('juin','Juin'),
        ('juillet','Juillet'),
        ('aout','Août'),
        ('septembre','Septembre'),
        ('octobre','Octobre'),
        ('novembre','Novembre'),
        ('decembre','Décembre'),  
        ], string = "Choisir Mois",default = 'janvier', required = True)
    date_op = fields.Date(string = 'Date Opération',default=date.today(), readonly = True)
    
    
    #fonction pour remplir le libellé court
    @api.onchange('x_type_employe_id')
    def remplir_libcourt(self):
        if self.x_type_employe_id.name == 'Fonctionnaire Detaché' or self.x_type_employe_id.name == 'fonctionnaire detaché' or self.x_type_employe_id.name == 'FONCTIONNAIRE DETACHE' or self.x_type_employe_id.name == 'Fonctionnaire Mis à Disposition' or self.x_type_employe_id.name == 'FONCTIONNAIRE MIS A DISPOSITION':
            self.lib_court = 'Part Patronale CARFO'
        elif self.x_type_employe_id.name == 'Contractuel'or self.x_type_employe_id.name == 'contractuel' or self.x_type_employe_id.name == 'CONTRACTUEL':
            self.lib_court = 'Part Patronale CNSS'
        else:
            self.lib_court = ''
    
    
    #fonction de remplissage du tableau des parts
    def partemp(self):
        if self.x_date_debut and self.x_date_fin:
            ddbut = str(self.x_date_debut.strftime("%Y-%m-%d"))          
            ddfin = str(self.x_date_fin.strftime("%Y-%m-%d"))
            x_struct_id = int(self.company_id)
            x_type_id = int(self.x_type_employe_id)
            for vals in self:
                if self.x_type_employe_id.name == 'Fonctionnaire Detaché' or self.x_type_employe_id.name == 'fonctionnaire detaché' or self.x_type_employe_id.name == 'FONCTIONNAIRE DETACHE' or self.x_type_employe_id.name == 'Fonctionnaire Mis à Disposition' or self.x_type_employe_id.name == 'FONCTIONNAIRE MIS A DISPOSITION': 

                    vals.env.cr.execute("""select DISTINCT(L.name) AS element_salaire, (L.total) AS Total, (E.name) AS employe,(E.matricule) as mat,(E.matricule_genere) as mat_c from hr_payslip_line L, hr_employee E, hr_payslip LP where L.slip_id = LP.id and E.id = L.employee_id and LP.date_from >= %s  and LP.date_to <= %s and LP.company_id = %s and LP.struct_id = %s and LP.state = 'done' and L.name = 'Part Patronale CARFO' AND E.active = 'True' ORDER BY employe ASC""",(ddbut,ddfin,x_struct_id,x_type_id))
                    rows = vals.env.cr.dictfetchall()
                    result = []
                    
                    # delete old payslip lines
                    vals.x_line_ids.unlink()
                    self.x_mnt_empl = 0.0
                    text = ''
                    for line in rows:
                        result.append((0, 0, {'name': line['employe'],'x_matricule': line['mat'],'x_matricule_c': line['mat_c'],'x_mnt_employeur':line['total']}))
                        self.x_mnt_empl += line['total']  
                    self.x_line_ids = result
                    text+=num2words(vals.x_mnt_empl, lang='fr')
                    self.x_mnt_en_lettre = text 
                else:
                    
                    vals.env.cr.execute("""select DISTINCT(L.name) AS element_salaire, (L.total) AS Total, (E.name) AS employe,(E.matricule) as mat,(E.matricule_genere) as mat_c,(E.num_declaration) as numc from hr_payslip_line L, hr_employee E, hr_payslip LP where L.slip_id = LP.id and E.id = L.employee_id and LP.date_from >= %s  and LP.date_to <= %s and LP.company_id = %s and LP.struct_id = %s and LP.state = 'done' and L.name = 'Part Patronale CNSS' AND E.active = 'True' ORDER BY employe ASC""",(ddbut,ddfin,x_struct_id,x_type_id))
                    rows = vals.env.cr.dictfetchall()
                    result = []
                    
                    # delete old payslip lines
                    vals.x_line_ids.unlink()
                    self.x_mnt_empl = 0.0
                    text = ''
                    for line in rows:
                        result.append((0, 0, {'name': line['employe'],'x_matricule': line['mat'],'x_matricule_c': line['mat_c'],'x_num_cnss': line['numc'], 'x_mnt_employeur':line['total']}))
                        self.x_mnt_empl += line['total'] 
                    self.x_line_ids = result
                    text+=num2words(vals.x_mnt_empl, lang='fr')
                    self.x_mnt_en_lettre = text 
                
                
                
        
    
class HrReportPartEmpLine(models.TransientModel):
    _name = "hr_reportpartemp_line"
    name = fields.Char(string = 'Employé')
    x_matricule = fields.Char(string = 'Mle Fonctionnaire')
    x_matricule_c = fields.Char(string = 'Mle Contractuel')
    x_num_cnss = fields.Char(string = 'N°CNSS')
    x_reportpartemp_id = fields.Many2one('hr_reportpartemp')
    x_mnt_employeur = fields.Float(string = 'Part employeur')
    
    
    
#classe mère des etats recap des parts sociales
class HrReportPartRecap(models.TransientModel):
    
    _name = "hr_reportpartrecap"
    name = fields.Char(string = 'Nom')
    financiers_id = fields.Many2one('res.users', string = "Financier", required = True)
    drhs_id = fields.Many2one('res.users', string = "DRH", required = True)
 
    
    _rec_name = 'lib_long'
    lib_long = fields.Char(string = 'Intitulé Etat',required = True)
    lib_court = fields.Char(string = 'element salaire')
    x_type_employe_id = fields.Many2one("hr.payroll.structure",string ="Type employé", required = True)
    x_date_debut = fields.Date(string = 'Date début',default=lambda self: fields.Date.to_string(date.today().replace(day=1)), required = True)
    x_date_fin = fields.Date(string = 'Date fin',default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()), required = True)
    x_mnt_empl = fields.Float(string = 'Part Totale Employeur')
    x_mnt_employe = fields.Float(string = 'Part Totale Employé')
    x_mnt_total = fields.Float(compute = 'total_part', string = 'Total Part')
    
    x_mnt_en_lettre = fields.Char(compute = 'total_part', string = 'Montant en lettres')

    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)
    x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))
    x_line_ids = fields.One2many('hr_reportpartrecap_line','x_reportpartrecap_id', string = "Liste des élements")
    x_moi = fields.Selection([
        ('janvier','Janvier'),
        ('fevrier','Février'),
        ('mars','Mars'),
        ('avril','Avril'),
        ('mai','Mai'),
        ('juin','Juin'),
        ('juillet','Juillet'),
        ('aout','Août'),
        ('septembre','Septembre'),
        ('octobre','Octobre'),
        ('novembre','Novembre'),
        ('decembre','Décembre'),  
        ], string = "Choisir Mois",default = 'janvier', required = True)
    date_op = fields.Date(string = 'Date Opération',default=date.today(), readonly = True)
    
    
    @api.depends()
    def total_part(self):
        for vals in self:
            text = ''
            vals.x_mnt_total = vals.x_mnt_employe + vals.x_mnt_empl
            text+=num2words(vals.x_mnt_total, lang='fr')
            self.x_mnt_en_lettre = text

    
    #fonction de remplissage du tableau des parts
    def partgroupe(self):
        if self.x_date_debut and self.x_date_fin:
            ddbut = str(self.x_date_debut.strftime("%Y-%m-%d"))
            ddfin = str(self.x_date_fin.strftime("%Y-%m-%d"))
            x_struct_id = int(self.company_id)
            x_type_id = int(self.x_type_employe_id)
            for vals in self:
                if self.x_type_employe_id.name == 'Fonctionnaire Detaché' or self.x_type_employe_id.name == 'fonctionnaire detaché' or self.x_type_employe_id.name == 'FONCTIONNAIRE DETACHE' or self.x_type_employe_id.name == 'Fonctionnaire Mis à Disposition' or self.x_type_employe_id.name == 'FONCTIONNAIRE MIS A DISPOSITION': 

                    vals.env.cr.execute("""select (E.name) AS employe,SUM(CASE WHEN L.name LIKE %s THEN L.total END) AS element_salaire_employe , SUM(CASE WHEN L.name LIKE %s THEN L.total END) AS element_salaire_employeur,(E.matricule) as mat from hr_payslip_line L, hr_employee E, hr_payslip LP where L.slip_id = LP.id and E.id = L.employee_id and LP.date_from >= %s and LP.date_to <= %s and LP.company_id = %s and LP.struct_id = %s and L.name LIKE %s and LP.state = 'done' AND E.active = 'True' group by employe,mat""",('%Cotisation CARFO','%Part Patronale CARFO',ddbut,ddfin,x_struct_id,x_type_id,'%CARFO'))
                    rows = vals.env.cr.dictfetchall()
                    result = []
                    
                    # delete old payslip lines
                    vals.x_line_ids.unlink()
                    self.x_mnt_empl = 0.0
                    self.x_mnt_employe = 0.0
                    for line in rows:
                        result.append((0, 0, {'name': line['employe'],'x_matricule': line['mat'],'x_mnt_agent': line['element_salaire_employe'],'x_mnt_employeur': line['element_salaire_employeur']}))
                        self.x_mnt_empl += line['element_salaire_employeur']
                        self.x_mnt_employe += line['element_salaire_employe']  
                    self.x_line_ids = result
                else:
                    vals.env.cr.execute("""select (E.name) AS employe,SUM(CASE WHEN L.name LIKE %s THEN L.total END) AS element_salaire_employe , SUM(CASE WHEN L.name LIKE %s THEN L.total END) AS element_salaire_employeur,(E.matricule) as mat,(E.matricule_genere) as mat_c,(E.num_declaration) as numc from hr_payslip_line L, hr_employee E, hr_payslip LP where L.slip_id = LP.id and E.id = L.employee_id and LP.date_from >= %s and LP.date_to <= %s and LP.company_id = %s and LP.struct_id = %s and L.name LIKE %s and LP.state = 'done' AND E.active = 'True' group by employe,mat,mat_c,numc """,('%Cotisation CNSS','%Part Patronale CNSS',ddbut,ddfin,x_struct_id,x_type_id,'%CNSS'))
                    rows = vals.env.cr.dictfetchall()
                    result = []
                    
                    # delete old payslip lines
                    vals.x_line_ids.unlink()
                    self.x_mnt_empl = 0.0
                    self.x_mnt_employe = 0.0
                    for line in rows:
                        result.append((0, 0, {'name': line['employe'],'x_matricule': line['mat'],'x_matricule_c': line['mat_c'],'x_num_cnss': line['numc'],'x_mnt_agent': line['element_salaire_employe'],'x_mnt_employeur': line['element_salaire_employeur']}))
                        self.x_mnt_empl += line['element_salaire_employeur']
                        self.x_mnt_employe += line['element_salaire_employe']  
                    self.x_line_ids = result
 
 
class HrReportPartRecapLine(models.TransientModel):
    _name = "hr_reportpartrecap_line"
    x_reportpartrecap_id = fields.Many2one('hr_reportpartrecap')
    
    name = fields.Char(string = 'Employé')
    x_matricule = fields.Char(string = 'Mle Fonctionnaire')
    x_matricule_c = fields.Char(string = 'Mle Contractuel')
    x_num_cnss = fields.Char(string = 'N°CNSS')
    x_mnt_agent = fields.Float(string = 'Part agent')
    x_mnt_employeur = fields.Float(string = 'Part employeur')
           


#classe mère du livre de paie
class HrLivrePaie(models.TransientModel):
    _name = "hr_livrepaie"
    name = fields.Many2one("hr.payroll.structure",string ="Type employé", required = True)
    x_date_debut = fields.Date(string = 'Date début', required = True)
    x_date_fin = fields.Date(string = 'Date fin', required = True)
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)
    x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))
    x_line_ids = fields.One2many('hr_livrepaie_line','x_livre_id', string = "Liste des élements de salaire", readonly = True)
    current_user = fields.Many2one('res.users','Utilisateur', default=lambda self: self.env.user)
    active = fields.Boolean(string = "Etat", default=True)
    date_op = fields.Datetime('Date/heure opération', default=datetime.today(), readonly = True)

    
    def action_rech(self):
        if self.name:
            x_struct_id = int(self.company_id)
            x_type_id = int(self.name)
            x_ty = str(self.name.name)
            ddbut = str(self.x_date_debut.strftime("%Y-%m-%d"))          
            ddfin = str(self.x_date_fin.strftime("%Y-%m-%d"))
            for vals in self:
                if x_ty == 'Fonctionnaire Detaché' or x_ty == 'Fonctionnaire Mis à Disposition' or x_ty == 'FONCTIONNAIRE DETACHE' or x_ty == 'FONCTIONNAIRE MIS A DISPOSITION':
                    vals.env.cr.execute("""SELECT (P.id) AS id,(C.name) AS categorie, (EC.name) as echelle, (ECH.name) as echelon, (E.name) as employe, (E.matricule) as matricule,(EM.name) as emploi, (E.x_solde_indiciaire_net) as salaire_base, (E.x_indem_resp) as resp, (E.x_indem_astr) as astr, (E.x_indem_techn) as techn, (E.x_indem_specif) as spec,(E.x_indem_spec_inspect_trav) as spec_it,(E.x_indem_spec_inspect_ifc) as spec_ifc, (E.x_indem_loge) as loge, (E.x_indem_transp) as transp, (E.x_indem_inform) as inf, (E.x_indem_exploit) as reseau, (E.x_indem_finance) as finance, (E.x_allocation_familial) as allocation, (E.x_remuneration_total ) as remu_total, (E.x_mnt_carfo) as carfo, (E.x_mnt_cnss) as cnss, (E.x_base_imposable_ctrct) as base_impo, (E.x_iuts_net) as iuts,(E.x_mnt_patronal_cnss) as p_cnss,(E.x_mnt_patronal_carfo) as p_carfo, (E.mnt_foner) as foner, (E.x_indem_garde) as garde, (E.x_indem_risque) as risque,(E.x_indem_suj) as suje,(E.x_indem_form) as formation,(E.x_indem_caisse) as caisse,(E.x_indem_veste) as veste,(E.x_net_payer_ctrct) as net FROM  hr_payslip P, hr_employee E, hr_categorie C, hr_echelle EC, hr_echellon ECH, hr_emploi EM WHERE E.id = P.employee_id AND E.x_categorie_c_id = C.id AND E.x_echelle_c_id = EC.id AND E.x_echellon_c_id = ECH.id AND E.x_emploi_id = EM.id AND P.date_from >= %s AND P.date_to <= %s AND E.x_type_employe_id = %s AND E.company_id = %s AND P.state = 'done' AND E.active = 'True' ORDER BY employe ASC""" ,(ddbut,ddfin,x_type_id,x_struct_id))
                    rows = vals.env.cr.dictfetchall()
                    result = []
                    
                    # delete old payslip lines
                    vals.x_line_ids.unlink()
                    for line in rows:
                        result.append((0, 0, {'mat': line['matricule'], 'nom':line['employe'],'categorie': line['categorie'], 'echelle':line['echelle'],'echelon': line['echelon'], 'emploi':line['emploi'],'salaire_base':line['salaire_base'],'resp': line['resp'], 'astr':line['astr'],'loge': line['loge'],'tech': line['techn'], 'spec':line['spec'],'spec_it':line['spec_it'],'spec_ifc':line['spec_ifc'], 'transp':line['transp'], 'inf':line['inf'], 'reseau':line['reseau'], 'financ':line['finance'], 'x_indem_garde':line['garde'], 'x_indem_risque':line['risque'],'x_indem_suj':line['suje'],'x_indem_form':line['formation'],'x_indem_caisse':line['caisse'],'x_indem_veste':line['veste'], 'alloc_f':line['allocation'], 'renum_t':line['remu_total'], 'mnt_agent_carfo':line['carfo'], 'mnt_patronal_carfo':line['p_carfo'], 'mnt_agent_cnss':line['cnss'], 'mnt_patronal_cnss':line['p_cnss'], 'base_imp':line['base_impo'], 'iuts':line['iuts'], 'net':line['net']}))
                    self.x_line_ids = result
                elif x_ty == 'Contractuel' or x_ty == 'contractuel' or x_ty == 'CONTRACTUEL':
                    vals.env.cr.execute("""SELECT (P.id) AS id,(C.name) AS categorie, (EC.name) as echelle, (ECH.name) as echelon, (E.name) as employe, (E.matricule) as matricule,(E.matricule_genere) as matricule_c,(E.num_declaration) as cnss,(EM.name) as emploi, (E.x_solde_indiciaire_net) as salaire_base, (E.x_indem_resp) as resp, (E.x_indem_astr) as astr, (E.x_indem_techn) as techn, (E.x_indem_specif) as spec,(E.x_indem_spec_inspect_trav) as spec_it,(E.x_indem_spec_inspect_ifc) as spec_ifc, (E.x_indem_loge) as loge, (E.x_indem_transp) as transp, (E.x_indem_inform) as inf, (E.x_indem_exploit) as reseau, (E.x_indem_finance) as finance, (E.x_allocation_familial) as allocation, (E.x_remuneration_total) as remu_total, (E.x_mnt_carfo) as carfo, (E.x_mnt_cnss) as cnss, (E.x_base_imposable_ctrct) as base_impo, (E.x_iuts_net) as iuts,(E.x_mnt_patronal_cnss) as p_cnss,(E.x_mnt_patronal_carfo) as p_carfo, (E.mnt_foner) as foner, (E.x_indem_garde) as garde, (E.x_indem_risque) as risque,(E.x_indem_suj) as suje,(E.x_indem_form) as formation,(E.x_indem_caisse) as caisse,(E.x_indem_veste) as veste,(E.x_emolument_ctrct_net) as emolument,(E.x_net_payer_ctrct) as net FROM  hr_payslip P, hr_employee E, hr_categorie C, hr_echelle EC, hr_echellon ECH, hr_emploi EM WHERE E.id = P.employee_id AND E.x_categorie_c_id = C.id AND E.x_echelle_c_id = EC.id AND E.x_echellon_c_id = ECH.id AND E.x_emploi_id = EM.id AND P.date_from >= %s AND P.date_to <= %s AND E.x_type_employe_id = %s AND E.company_id = %s AND P.state = 'done' AND E.active = 'True' ORDER BY employe ASC""" ,(ddbut,ddfin,x_type_id,x_struct_id))
                    rows = vals.env.cr.dictfetchall()
                    result = []
                    
                    # delete old payslip lines
                    vals.x_line_ids.unlink()
                    for line in rows:
                        result.append((0, 0, {'mat_c': line['matricule_c'], 'num_cnss':line['cnss'],'nom':line['employe'],'categorie': line['categorie'], 'echelle':line['echelle'],'echelon': line['echelon'], 'emploi':line['emploi'],'salaire_base':line['salaire_base'],'resp': line['resp'], 'astr':line['astr'],'loge': line['loge'],'tech': line['techn'], 'spec':line['spec'],'spec_it':line['spec_it'],'spec_ifc':line['spec_ifc'], 'transp':line['transp'], 'inf':line['inf'], 'reseau':line['reseau'], 'financ':line['finance'], 'x_indem_garde':line['garde'], 'x_indem_risque':line['risque'],'x_indem_suj':line['suje'],'x_indem_form':line['formation'],'x_indem_caisse':line['caisse'],'x_indem_veste':line['veste'],'x_emolument_ctrct_net':line['emolument'], 'alloc_f':line['allocation'], 'renum_t':line['remu_total'], 'mnt_agent_carfo':line['carfo'], 'mnt_patronal_carfo':line['p_carfo'], 'mnt_agent_cnss':line['cnss'], 'mnt_patronal_cnss':line['p_cnss'], 'base_imp':line['base_impo'], 'iuts':line['iuts'], 'net':line['net']}))
                    self.x_line_ids = result
                elif x_ty == 'Hospitalo-Universitaire' or x_ty == 'HOSPITALO-UNIVERSITAIRE':
                    vals.env.cr.execute("""SELECT (P.id) AS id,(C.name) AS categorie, (EC.name) as echelle, (ECH.name) as echelon, (E.name) as employe, (E.matricule) as matricule,(E.matricule_genere) as matricule_c,(E.num_declaration) as cnss,(EM.name) as emploi, (E.x_solde_indiciaire_net) as salaire_base, (E.x_indem_resp) as resp, (E.x_indem_astr) as astr, (E.x_indem_techn) as techn, (E.x_indem_specif) as spec,(E.x_indem_spec_inspect_trav) as spec_it,(E.x_indem_spec_inspect_ifc) as spec_ifc, (E.x_indem_loge) as loge, (E.x_indem_transp) as transp, (E.x_indem_inform) as inf, (E.x_indem_exploit) as reseau, (E.x_indem_finance) as finance, (E.x_allocation_familial) as allocation, (E.x_remuneration_total) as remu_total, (E.x_mnt_carfo) as carfo, (E.x_mnt_cnss) as cnss, (E.x_base_imposable_ctrct) as base_impo, (E.x_iuts_net) as iuts,(E.x_mnt_patronal_cnss) as p_cnss,(E.x_mnt_patronal_carfo) as p_carfo, (E.mnt_foner) as foner, (E.x_indem_garde) as garde, (E.x_indem_risque) as risque,(E.x_indem_suj) as suje,(E.x_indem_form) as formation,(E.x_indem_caisse) as caisse,(E.x_indem_veste) as veste,(E.x_emolument_ctrct_net) as emolument,(E.x_net_payer_ctrct) as net FROM  hr_payslip P, hr_employee E, hr_categorie C, hr_echelle EC, hr_echellon ECH, hr_emploi EM WHERE E.id = P.employee_id AND E.x_categorie_c_id = C.id AND E.x_echelle_c_id = EC.id AND E.x_echellon_c_id = ECH.id AND E.x_emploi_id = EM.id AND P.date_from >= %s AND P.date_to <= %s AND E.x_type_employe_id = %s AND E.company_id = %s AND P.state = 'done' AND E.active = 'True' ORDER BY employe ASC""" ,(ddbut,ddfin,x_type_id,x_struct_id))
                    rows = vals.env.cr.dictfetchall()
                    result = []
                    
                    # delete old payslip lines
                    vals.x_line_ids.unlink()
                    for line in rows:
                        result.append((0, 0, {'mat_c': line['matricule_c'], 'num_cnss':line['cnss'],'nom':line['employe'],'categorie': line['categorie'], 'echelle':line['echelle'],'echelon': line['echelon'], 'emploi':line['emploi'],'salaire_base':line['salaire_base'],'resp': line['resp'], 'astr':line['astr'],'loge': line['loge'],'tech': line['techn'], 'spec':line['spec'],'spec_it':line['spec_it'],'spec_ifc':line['spec_ifc'], 'transp':line['transp'], 'inf':line['inf'], 'reseau':line['reseau'], 'financ':line['finance'], 'x_indem_garde':line['garde'], 'x_indem_risque':line['risque'],'x_indem_suj':line['suje'],'x_indem_form':line['formation'],'x_indem_caisse':line['caisse'],'x_indem_veste':line['veste'],'x_emolument_ctrct_net':line['emolument'], 'alloc_f':line['allocation'], 'renum_t':line['remu_total'], 'mnt_agent_carfo':line['carfo'], 'mnt_patronal_carfo':line['p_carfo'], 'mnt_agent_cnss':line['cnss'], 'mnt_patronal_cnss':line['p_cnss'], 'base_imp':line['base_impo'], 'iuts':line['iuts'], 'net':line['net']}))
                    self.x_line_ids = result
                else:
                    vals.env.cr.execute("""SELECT (P.id) AS id,(C.nameline_ids) AS categorie, (EC.name) as echelle, (ECH.name) as echelon, (E.name) as employe, (E.matricule) as matricule,(E.matricule_genere) as matricule_c,(E.num_declaration) as cnss,(EM.name) as emploi, (E.x_solde_indiciaire_net) as salaire_base, (E.x_indem_resp) as resp, (E.x_indem_astr) as astr, (E.x_indem_techn) as techn, (E.x_indem_specif) as spec,(E.x_indem_spec_inspect_trav) as spec_it,(E.x_indem_spec_inspect_ifc) as spec_ifc, (E.x_indem_loge) as loge, (E.x_indem_transp) as transp, (E.x_indem_inform) as inf, (E.x_indem_exploit) as reseau, (E.x_indem_finance) as finance, (E.x_allocation_familial) as allocation, (E.x_remuneration_total) as remu_total, (E.x_mnt_carfo) as carfo, (E.x_mnt_cnss) as cnss, (E.x_base_imposable_ctrct) as base_impo, (E.x_iuts_net) as iuts,(E.x_mnt_patronal_cnss) as p_cnss,(E.x_mnt_patronal_carfo) as p_carfo, (E.mnt_foner) as foner, (E.x_indem_garde) as garde, (E.x_indem_risque) as risque,(E.x_indem_suj) as suje,(E.x_indem_form) as formation,(E.x_indem_caisse) as caisse,(E.x_indem_veste) as veste,(E.x_emolument_ctrct_net) as emolument,(E.x_net_payer_ctrct) as net FROM  hr_payslip P, hr_employee E, hr_categorie C, hr_echelle EC, hr_echellon ECH, hr_emploi EM WHERE E.id = P.employee_id AND E.x_categorie_c_id = C.id AND E.x_echelle_c_id = EC.id AND E.x_echellon_c_id = ECH.id AND E.x_emploi_id = EM.id AND P.date_from >= %s AND P.date_to <= %s AND E.company_id = %s AND P.state = 'done' AND E.active = 'True' ORDER BY employe ASC""" ,(ddbut,ddfin,x_struct_id))
                    rows = vals.env.cr.dictfetchall()
                    result = []
                    
                    # delete old payslip lines
                    vals.x_line_ids.unlink()
                    for line in rows:
                        result.append((0, 0, {'mat': line['matricule'],'mat_c': line['matricule_c'], 'num_cnss':line['cnss'],'nom':line['employe'],'categorie': line['categorie'], 'echelle':line['echelle'],'echelon': line['echelon'], 'emploi':line['emploi'],'salaire_base':line['salaire_base'],'resp': line['resp'], 'astr':line['astr'],'loge': line['loge'],'tech': line['techn'], 'spec':line['spec'],'spec_it':line['spec_it'],'spec_ifc':line['spec_ifc'], 'transp':line['transp'], 'inf':line['inf'], 'reseau':line['reseau'], 'financ':line['finance'], 'x_indem_garde':line['garde'], 'x_indem_risque':line['risque'],'x_indem_suj':line['suje'],'x_indem_form':line['formation'],'x_indem_caisse':line['caisse'],'x_indem_veste':line['veste'],'x_emolument_ctrct_net':line['emolument'], 'alloc_f':line['allocation'], 'renum_t':line['remu_total'], 'mnt_agent_carfo':line['carfo'], 'mnt_patronal_carfo':line['p_carfo'], 'mnt_agent_cnss':line['cnss'], 'mnt_patronal_cnss':line['p_cnss'], 'base_imp':line['base_impo'], 'iuts':line['iuts'], 'net':line['net']}))
                    self.x_line_ids = result
 
 
class HrLivrePaieLine(models.TransientModel):
    _name = "hr_livrepaie_line"
    x_livre_id = fields.Many2one('hr_livrepaie')
    
    mat = fields.Char(string = 'Mle Fct')
    mat_c = fields.Char(string = 'Mle Ctrct')
    nom = fields.Char(string = 'Nom/Prénom(s)')
    num_cnss = fields.Char('N°CNSS')
    categorie = fields.Char(string ="Catégorie")
    echelle = fields.Char(string = 'Echelle')
    echelon = fields.Char(string = 'Echelon')
    emploi = fields.Char(string = 'Emploi')
    fonction = fields.Char(string = 'Fonction')
    
    salaire_base = fields.Char(string = 'Salaire base')
    
    resp = fields.Char(string = 'Indemn. Responsabilité')
    astr = fields.Char(string = 'Indemn. Astreinte')
    loge = fields.Char(string = 'Indemn. Logement')
    tech = fields.Char(string = 'Indemn. Technicité')
    spec = fields.Char(string = 'Indemn. Spécifique RH')
    spec_it = fields.Char(string = 'Indemn. Spécifique IT')
    spec_ifc = fields.Char(string = 'Indemn. Spécifique IFC')
    transp = fields.Char(string = 'Indemn. Transport')
    inf = fields.Char(string = 'Indemn. Informatique')
    reseau = fields.Char(string = 'Indemn. Exploitation-reseau')
    financ = fields.Char(string = 'Indemn. resp.financière')
    
    x_indem_garde = fields.Float(string = "Indemn.Garde")
    x_indem_risque = fields.Float(string = "Indemn.Risque.Contagion")
    x_indem_suj = fields.Float(string = "Indemn.Sujétion Géographique")
    x_indem_form = fields.Float(string = "Indemn.Formation")
    x_indem_caisse = fields.Float(string = "Indemn.Caisse")
    x_indem_veste = fields.Float(string = "Indemn.Vestimentaire")
    
    x_emolument_ctrct = fields.Float(string = "Emolument Brut")
    x_taux_retenu_emolmt = fields.Float(string = "Taux retenue (%)")
    x_mnt_taux_retenu_emolmt = fields.Float(string = "Montant Taux")
    x_emolument_ctrct_net = fields.Float(string = "Emolument Net")

    
    
    alloc_f = fields.Char(string = 'Allocation familliale')
    renum_t = fields.Char(string = 'Rénumeration totale')
    mnt_agent_carfo = fields.Char(string = 'Cotisation agent CARFO')
    mnt_patronal_carfo = fields.Char(string = 'Cotisation patronal CARFO')
    
    mnt_agent_cnss = fields.Char(string = 'Cotisation agent CNSS')
    mnt_patronal_cnss = fields.Char(string = 'Cotisation patronal CNSS')
    
    base_imp = fields.Char(string = 'Base imposable')
    iuts = fields.Char(string = 'IUTS')
    foner = fields.Char(string = 'Retenue Foner')
    avance_sal = fields.Char(string = 'Avance salaire')
    autre_mnt = fields.Char(string = 'Autre montant')
    net = fields.Char(string = 'Salaire net')
    
    
#classe de parametrage des elements d'imputation
class HrImputationElement(models.Model):
    _name = 'hr_elementimputation'
    _order = 'sequence, id'
    sequence = fields.Integer(help="Gives the sequence when displaying a list of cessation service.", default=10) 
    _rec_name = 'x_exercice_id'
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)
    x_exercice_id = fields.Many2one('ref_exercice', string = 'Exercice',required = True,default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))
    x_line_ids = fields.One2many('hr_elementimputation_line','x_input_id', string = "IMPUTATION BUDGETAIRE D'ELEMENTS")
    current_user = fields.Many2one('res.users','Utilisateur', default=lambda self: self.env.user)
    active = fields.Boolean(string = "Etat", default=True)
    name = fields.Datetime('Date/heure opération', default=datetime.today(), readonly = True)  
    
    
#classe de parametrage des elements d'imputation
class HrImputationElementLine(models.Model):
    _name = 'hr_elementimputation_line'
    x_input_id = fields.Many2one('hr_elementimputation')
    elt_salaire_id = fields.Many2one('hr.salary.rule', string = 'Element Salaire')
    type_id = fields.Many2one('hr.payroll.structure', string = 'Type personnel')
    titre_id = fields.Many2one('ref_titre', string = 'Titre')
    section_id = fields.Many2one('ref_section', string = 'Section')
    chapitre_id = fields.Many2one('ref_chapitre', string = 'Chapitre')
    article_id = fields.Many2one('ref_article', string = 'Article')
    paragraphe_id = fields.Many2one('ref_paragraphe', string = 'Paragraphe')
    #rubrique_id = fields.Many2one('ref_rubrique', string = 'Rubrique')
    imputation_id = fields.Many2one('ref_compte', string = 'Imputation')
    
    
    
#Class de cessation de paiement
class HrCessationPaiement(models.Model):
    _name = 'hr_cessation_paiement'
    _order = 'sequence, id'
    sequence = fields.Integer(help="Gives the sequence when displaying a list of cessation paiement.", default=10) 
   
    name = fields.Many2one('hr.employee', string = 'Nom', required = True)
    x_date_cess = fields.Date(string = 'Date Cessation', default=date.today(), required = True)
    date_debut_affect = fields.Date(string = 'Date Prise', readonly = True)
    x_motif_cess = fields.Many2one('hr_motif', string = 'Motif Cessation', required = True)
    
    x_titre = fields.Char(string = 'Titre', default='CESSATION DE PAIEMENT')
    p1 = fields.Char(string = 'Phrase 1',default = 'Je soussigné, ')
    p2 = fields.Char(string = 'Phrase 2',default = 'atteste que M./Mme/Mlle')
    p3 = fields.Char(string = 'Phrase 3', default = 'au  ')
    p4 = fields.Char(string = 'Phrase 4', default = 'qui a pris fonction du ')
    p5 = fields.Char(string = 'Phrase 5',default = 'Au')
    p6 = fields.Char(string = 'Phrase 6',default = 'au sein de ')
    p7 = fields.Char(string = 'Phrase 7',default = 'ne sera plus pris en compte dans le paiement de son salaire pour cause de  ')
    p8 = fields.Char(string = 'Phrase 8',default='En foi de quoi, la présente attestation lui est délivrée pour servir et valoir ce que de droit')
    responsale = fields.Many2one('hr.employee', string = 'Responsable')
    x_emploi = fields.Char(string = 'Emploi',readonly = True)
    x_fonction = fields.Many2one('hr_fonctionss', string = 'Fonction')
    x_direction = fields.Char(string = 'Direction',readonly = True)
    x_service = fields.Char(string = 'Service',readonly = True)
    date_attest = fields.Date(string = "Date", default=date.today())
    current_user = fields.Many2one('res.users','Utilisateur', default=lambda self: self.env.user)
    active = fields.Boolean(string = "Etat", default=True)
    observation = fields.Text(string = 'Observations')
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)
    x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]),string = 'Année', readonly=True)
   
    @api.onchange('name')
    def remplir_employe(self):
        if self.name:
            self.x_emploi = self.name.x_emploi_id.name
            self.x_direction = self.name.department_id.name
            self.x_service = self.name.hr_service.name
            self.date_debut_affect = self.name.date_debut
            
            
            
            
            
#Class de message du premier responsable
class HrMessagePremierResponsable(models.Model):
    _name = 'hr_message'
    _order = 'sequence, id'
    sequence = fields.Integer(help="Gives the sequence when displaying a list of cessation paiement.", default=10) 
    
    current_user = fields.Many2one('res.users','Utilisateur', default=lambda self: self.env.user)
    name = fields.Text(string = 'Contenu Message', required = True)
    x_date_op = fields.Date(string = 'Date', default=date.today(), required = True)
    active = fields.Boolean(string = "Etat", default=True)
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)
    x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]),string = 'Année', readonly=True)
    etat = fields.Selection([
        (1,'Y'),
        (2,'N'),
         
        ], string = "Etat", default=1)
    
    
    
class HrReportMode(models.Model):
    
    _name = "hr_prime"
    financiers_id = fields.Many2one('res.users', string = "Financier", required = True)
    drhs_id = fields.Many2one('res.users', string = "DRH", required = True)
    description = fields.Text(string = 'Description')
    _rec_name = 'x_moi'
    #x_type_employe_id = fields.Many2one("hr.payroll.structure",string ="Type employé", required = True)
    company_id = fields.Many2one('res.company',string = "Structure", default=lambda self: self.env.user.company_id.id)
    x_exercice_id = fields.Many2one('ref_exercice',string = 'Année',readonly =True, default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))
    x_line_ids = fields.One2many('hr_prime_line','x_prime_id', string = "Liste des concernés")
    """x_mnts = fields.Float(string = 'Montant Total', readonly =True)
    x_mnt_en_lettre = fields.Char(string = 'Montant en lettres', readonly =True)"""
    x_moi = fields.Selection([
        ('Janvier','Janvier'),
        ('Février','Février'),
        ('Mars','Mars'),
        ('Avril','Avril'),
        ('Mai','Mai'),
        ('Juin','Juin'),
        ('Juillet','Juillet'),
        ('Août','Août'),
        ('Septembre','Septembre'),
        ('Octobre','Octobre'),
        ('Novembre','Novembre'),
        ('Décembre','Décembre'),  
        ], string = "Mois",default = 'Janvier', required = True)
    date_op = fields.Datetime(string = 'Date opération',default=datetime.today(), readonly = True)
    x_intitule = fields.Char('Intitulé prime',default = 'Prime de rendement', required = True)
    x_prime_total = fields.Float('Total Prime', readonly = True)
    x_mnt_en_lettre = fields.Char(string = 'Montant en lettres')
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('Employés affichés', 'Employés affichés'),
        ('Confirmé', 'Confirmé'),
        ('Annulé', 'Annulé'),
        ], 'Etat', default='draft', index=True, required=True, readonly=True, copy=False, track_visibility='always')

    
    #Les fonctions permettant de changer d'etat 
    @api.multi
    def action_eng_draft(self):
        self.write({'state': 'draft'})
        
        
    @api.multi
    def action_confirmer(self):
        for vals in self:
            mois = str(vals.x_moi)
            print('mois',mois)
            annee = int(vals.x_exercice_id)
            print('annee',annee)
            x_struct_id = int(self.company_id)
            print('structure',x_struct_id)
            
            self.x_prime_total = 0.0
            text= ''
            
            vals.env.cr.execute("""select sum(L.x_mnt_percu) as total from hr_prime_line L, hr_prime P WHERE P.id = L.x_prime_id AND P.x_moi = '%s' AND P.x_exercice_id = %s AND P.company_id = %s"""%(mois,annee,x_struct_id))
            lo = self.env.cr.fetchone()
            self.x_prime_total = lo and lo[0] or 0
            print('total',self.x_prime_total)
            text+=num2words(self.x_prime_total, lang='fr')
            self.x_mnt_en_lettre = text
            if self.x_prime_total == 0:
                raise ValidationError(_("Attention le montant total des primes est nulle....l'opération ne peut être qu'annuléé....Merci"))
            else:
                self.write({'state': 'Confirmé'})
        
        
    @api.multi
    def action_annuler(self):
        self.write({'state': 'Annulé'})
    
    
    #fonction de remplissage du tableau
    def remplissage(self):
        if self.x_moi:
            x_struct_id = int(self.company_id)
            for vals in self:
                vals.env.cr.execute("""select (E.x_classification_ctrct) as classif,(E.matricule_genere) as mat,(E.name) as emp,(EM.name) as emploi from hr_employee E,hr_emploi EM WHERE E.x_emploi_id = EM.id AND E.company_id = %d"""%(x_struct_id))
                rows = vals.env.cr.dictfetchall()
                result = []
                
                # delete old payslip lines
                vals.x_line_ids.unlink()
                for line in rows:
                    result.append((0, 0, {'x_matricule': line['mat'],'name': line['emp'],'x_emploi': line['emploi'],'x_classification': line['classif'], 'x_mnt_percu':0,'signature':''}))
                self.x_line_ids = result
            self.write({'state': 'Employés affichés'})
                
                
                    
                
        
#class permettant de recueillir les lignes de la requête   
class HrPrimeRendementLine(models.Model):
    _name = "hr_prime_line"
    x_prime_id = fields.Many2one('hr_prime')
    x_matricule = fields.Char(string = 'Matricule', readonly = True)
    name = fields.Char(string = 'Employé', readonly = True)
    x_emploi = fields.Char(string = 'Emploi', readonly = True)
    x_classification = fields.Char(string = 'Classification', readonly = True)
    x_mnt_percu = fields.Float(string = 'Montant perçu')
    signature = fields.Text('Signature')
    
    
            
            
 
