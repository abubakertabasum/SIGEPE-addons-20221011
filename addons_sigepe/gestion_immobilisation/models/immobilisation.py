from odoo import fields,api,models
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo.exceptions import AccessError, UserError, ValidationError

class AccountAssetCategory(models.Model):
	_inherit = "account.asset.category"

	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
#	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env.['ref_exercice'].search([('etat','=',1)]))


class AccountAssetAsset(models.Model):

	_inherit = "account.asset.asset"
	_rec_name= "immo_id"

	immo_id= fields.Many2one("gi_immobilisation", string= "Code", required=True)
	name= fields.Char(string= "Immobilisation", readonly= True)
	date_mise_service= fields.Date(string= "Date de mise en service", store=True)
	date_aquisition= fields.Date(string= "Date d'acquisition", store=True)
	duree_annee= fields.Integer(string= "Durée de vie en année")
	state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmer', 'Confirmer'),
        ], 'Status', default='draft', index=True, required=True, readonly=True, copy=False, track_visibility='always')
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))


	@api.multi
	def calcul(self):
		self.write({'state': 'confirmer'})



# Date d'acquisition se trouvant dans la classe (gi_immobilisation)

	@api.onchange("immo_id")
	def acq(self):
		self.date_aquisition=self.immo_id.dateacquisition
		self.name=self.immo_id.designation_id.lib_long
		self.date_mise_service=self.immo_id.date_mise_service
		self.amort_id=self.immo_id.amort_id
		self.montant_base=self.immo_id.acquisition
		self.duree_annee=self.immo_id.an_amorti



class GI_ordre_entree (models.Model):
	_name = "gi_ordre_entree"
	_rec_name= "magasin_id"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	n_mvt= fields.Char(string= "N° d'ordre", readonly= True)
	facture= fields.Char(string= "Ref Facture", required= True)
	src_fin_id= fields.Many2one("gi_source_fin", string= "Source de financement", required= True)
	mode_acqu_id= fields.Many2one("gi_mode_acquisition", string= "Mode d'acquisition", required= True)
	observation= fields.Text(string= "Observation")
	concat= fields.Char(default= "OEM")
	date_entree= fields.Date(string= "Date acquisition", required= True)
	fournisseur_id= fields.Many2one("ref_beneficiaire", string= "Fournisseurs", required= True)
	magasin_id= fields.Many2one("gi_magasin", string= "Magasin", required= True)
	state= fields.Selection([("brouillon","Brouillon"),("save","Enregistrer le stock")], string= "state", default="brouillon")
	ordo_mat_id= fields.Many2one("gi_agent_mat", string= "Ordonnateur Matières", required= True)
	compta_mat_id= fields.Many2one("gi_agent_mat", string= "Comptable Matières", required= True)
	fichiste_id= fields.Many2one("gi_agent_mat", string= "Fichistes / Détenteur", required= True)
	line_ids= fields.One2many("gi_ordre_entree_line", "ordre_entree_id", string= "Liste des biens")
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



	@api.multi
	def ordreentree(self):
		val_ex = int(self.x_exercice_id.id)
		val_struct = int(self.company_id.id)


		self.env.cr.execute("""SELECT n_compt FROM gi_compt_entree WHERE x_exercice_id = %d and company_id = %d """ %(val_ex,val_struct) )
		res= self.env.cr.fetchone()
		n_mvt = res and res[0] or 0
		c1 = int(n_mvt) + 1
		ordre= str(n_mvt)
		if ordre == "0":
			okk= str(c1).zfill(4)
			ok= self.concat + okk
			self.n_mvt = ok
			vals= c1
			self.env.cr.execute("""INSERT INTO gi_compt_entree(x_exercice_id,company_id,n_compt)  VALUES(%d, %d, %d)""" %(val_ex,val_struct,vals))

		else:
			c1 = int(n_mvt) + 1
			ordre= str(n_mvt)
			okk= str(c1).zfill(4)
			ok= self.concat + okk
			self.n_mvt = ok
			vals= c1
			self.env.cr.execute("UPDATE gi_compt_entree SET n_compt = %d  WHERE x_exercice_id = %d and company_id = %d" %(vals,val_ex,val_struct))

# Mise à jour du stock

		for record in self.line_ids:
			val_id = int(record.designation_id)
			val_qte = int(record.quant)

			if record.quant <= 0:
				raise ValidationError(('Veuillez saisir une quantitée supérieure ou égale à 1'))
			else:
				record.env.cr.execute("""UPDATE gi_designation set quant_stoc = quant_stoc + %d WHERE id = %d """ %(val_qte,val_id))

		self.write({'state': 'save'})



class Gi_Compt_entree (models.Model):
	
	_name = "gi_compt_entree"
	
	x_exercice_id = fields.Many2one("ref_exercice", default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]), string="Exercice")
	company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
	n_compt = fields.Integer()
	categorie_id = fields.Char()



class GI_ordre_entreeLine (models.Model):
	_name = "gi_ordre_entree_line"
	_rec_name= "designation_id"

	ordre_entree_id= fields.Many2one("gi_ordre_entree")
	type_immo_id= fields.Many2one("gi_typeimmobilisation", string= "Type immobilisation")
	sous_code= fields.Char(string= "Code budgetaire", compute= "concaten_imp", store = True)
	imp_budg_id = fields.Many2one("ref_compte", string= "Imputation Budgetaire", required= True)
	categorie_id= fields.Many2one("gi_categorie", string= "Categorie")
	designation_id= fields.Many2one("gi_designation", string= "Désignation")
	quant= fields.Integer(string= "Quantité", required= True)
	quant_stock = fields.Integer(string = "Quantité en stock")
	val_unit= fields.Integer(string= "Prix unitaire", required= True)
	montant= fields.Integer(string= "Total")


	@api.depends('imp_budg_id', "categorie_id")
	def concaten_imp(self):
		for rec in self:
			rec.sous_code = str(rec.imp_budg_id.cpte) + "." +str(rec.categorie_id.code)



#Calcul du montant total

	@api.onchange('quant','val_unit')
	def montant_val(self):
		self.montant= self.quant * self.val_unit



	@api.onchange('designation_id')
	def vale(self):
		self.quant_stock= self.designation_id.quant_stoc



class Gi_invent_entree (models.Model):
	_name = "gi_invent_entree"
	_rec_name= "type_invent"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	code= fields.Integer(srting= "N° Inventaire")
	ministere_id = fields.Many2one("ref_ministere", string= "Ministère", required= True)
	magasin_id = fields.Many2one("gi_magasin", string= "Magasin")
	date_debut= fields.Date(string= "Date debut", required= True)
	date_fin = fields.Date(string= "Date fin", default= fields.Date.context_today, required= True)
	type_invent= fields.Selection([("trimestre", "Trimestriel"), ("semestre", "Semestriel"), ("tournant", "Inventaire tournant"), 
		("annuel", "Annuel")], string= "Type Inventaire", default= "tournant", store= True, required= True)
	emplacement = fields.Selection([('1', 'Tous les magasins'),('2', 'Par magasin')], string= "Emplacements", default='1', required=True)
	ordo_mat_id= fields.Many2one("gi_agent_mat", string= "Ordonnateur Matières", required= True)
	compta_mat_id= fields.Many2one("gi_agent_mat", string= "Comptable Matières", required= True)
	magasinier_id= fields.Many2one("gi_agent_mat", string= "Magasinier/ Fichiste", required= True)
	entree_line_ids= fields.One2many("gi_invent_entree_line", "entree_id", string= " ")
	state= fields.Selection([("brouillon", "Brouillon"), ("fait", "Fait")], string= "Etat", default= "brouillon", store= True)
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))


#fonction de remplissage du tableau des biens en service

	def invent_entree(self):
		if self.date_debut and self.date_fin:
			ddbut = str(self.date_debut.strftime("%Y-%m-%d"))
			ddfin = str(self.date_fin.strftime("%Y-%m-%d"))
			val_mag = int(self.magasin_id)
			val_struct = int(self.company_id)
			val_ex = int(self.x_exercice_id)

			if self.emplacement== "1":

				for vals in self:
					vals.env.cr.execute("""SELECT (L.sous_code) AS code, (B.lib_long) AS type, (Q.lib_long) AS designation, (Q.quant_stoc) AS quant , (L.val_unit) valeur FROM gi_ordre_entree_line L, gi_typeimmobilisation B, gi_designation Q, gi_ordre_entree C where L.designation_id = Q.id and C.id = L.ordre_entree_id and L.type_immo_id= B.id and C.company_id =%s and C.x_exercice_id = %s and  C.date_entree BETWEEN %s and %s """,(val_struct,val_ex,ddbut,ddfin))
					res = vals.env.cr.dictfetchall()
					result = []
	                
				# delete old ordre entree lines
				vals.entree_line_ids.unlink()
				for line in res:
					result.append((0, 0, {'sous_code': line['code'], 'type_immo':line['type'], 'designation':line['designation'], 'quant':line['quant'], 'val_unit':line['valeur']}))
				self.entree_line_ids = result

			if self.emplacement== "2":

				for vals in self:
					vals.env.cr.execute("""SELECT (L.sous_code) AS code, (B.lib_long) AS type, (Q.lib_long) AS designation, (Q.quant_stoc) AS quant , (L.val_unit) valeur FROM gi_ordre_entree_line L, gi_typeimmobilisation B, gi_designation Q, gi_ordre_entree C where L.designation_id = Q.id and C.id = L.ordre_entree_id and L.type_immo_id= B.id and C.magasin_id = %s and C.company_id = %s and C.x_exercice_id = %s and  C.date_entree BETWEEN %s and %s """,(val_mag,val_struct,val_ex,ddbut,ddfin))
					res = vals.env.cr.dictfetchall()
					result = []
	                
				# delete old ordre entree lines
				vals.entree_line_ids.unlink()
				for line in res:
					result.append((0, 0, {'sous_code': line['code'], 'type_immo':line['type'], 'designation':line['designation'], 'quant':line['quant'], 'val_unit':line['valeur']}))
				self.entree_line_ids = result

			self.write({'state': 'fait'})


# Mettre à jour la quantité théorique par celle physique
	def maj(self):

		for record in self.entree_line_ids:

			val_id = str(record.designation)
			val_qte_phy = int(record.quant_phys)

			record.env.cr.execute("""UPDATE gi_designation SET quant_stoc = %s WHERE lib_long = %s """ ,(val_qte_phy,val_id))



class GI_invent_entreeLine (models.Model):
	_name = "gi_invent_entree_line"

	entree_id= fields.Many2one("gi_invent_entree")
	sous_code= fields.Char(string= "Code budgetaire")
	type_immo= fields.Char(string= "Type immobilisation")
	designation= fields.Char(string= "Désignation")
	quant = fields.Integer(string= "Quantité Théorique")
	quant_phys = fields.Integer(string = "Quantité physique")
	ecart= fields.Integer(string= "Ecart")
	val_unit= fields.Integer(string= "Prix unitaire")
	montant= fields.Integer(string= "Total")
	etat= fields.Many2one("gi_etat", string= "Etat")
	observation= fields.Text(string= "Observation")


	@api.onchange("quant_phys","val_unit")
	def ecarrrt(self):
		if self.quant and self.quant_phys:
			self.ecart= (self.quant-self.quant_phys)
			self.montant= self.quant * self.val_unit



class Gi_inv_declas (models.Model):
	_name = "gi_inv_declas"
	_rec_name= "ministere_id"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	ministere_id = fields.Many2one("ref_ministere", string= "Ministère", required= True)
	date_debut= fields.Date(string= "Date debut", required= True)
	date_fin = fields.Date(string= "Date fin", default= fields.Date.context_today, required= True)
	emplacement = fields.Selection([('1', 'Au magasin'),('2', 'Directions/Services')], string= "Emplacements", default='1', required=True)
	ordo_mat_id= fields.Many2one("gi_agent_mat", string= "Ordonnateur Matières", required= True)
	magasin_id= fields.Many2one("gi_magasin", string= "Magasin")
	compta_mat_id= fields.Many2one("gi_agent_mat", string= "Comptable Matières", required= True)
	magasinier_id= fields.Many2one("gi_agent_mat", string= "Magasinier/ Fichiste", required= True)
	declas_line_ids= fields.One2many("gi_inv_declas_line", "declas_id", string= " ")
	state= fields.Selection([("brouillon", "Brouillon"), ("fait", "Fait")], string= "Etat", default= "brouillon", store= True)
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



#Inventaire des biens en service qui sont déclasser

	def declasse(self):
		if self.date_debut and self.date_fin:
			ddbut = str(self.date_debut.strftime("%Y-%m-%d"))
			ddfin = str(self.date_fin.strftime("%Y-%m-%d"))
			val_struct = int(self.company_id)
			val_ex = int(self.x_exercice_id)

			for vals in self:
				vals.env.cr.execute("""SELECT DISTINCT (B.code_immo) AS code, (D.lib_long) AS categorie, (Q.lib_long) AS designation, (H.name) As direction, (F.lib_long) As etat, (G.val_unit) As valeur
				FROM gi_immobilisation B, gi_declassement_line L, gi_declassement C, gi_designation Q, gi_ordre_entree_line G, gi_categorie D, gi_etat F, ref_direction H
				WHERE C.id= L.declasse_id and L.code_immo= B.id and B.direction_id= H.id and B.id = G.id and G.categorie_id= D.id and G.designation_id= Q.id and L.etat_id= F.id and C.company_id = %s and C.x_exercice_id = %s and C.date_mvt BETWEEN %s and %s """,(val_struct,val_ex,ddbut,ddfin))
				res = vals.env.cr.dictfetchall()
				result = []
                
			vals.declas_line_ids.unlink()
			for line in res:
				result.append((0, 0, {'code_immo': line['code'], 'categorie':line['categorie'],'designation':line['designation'], 'direction':line['direction'], 'etat':line['etat'],'montant':line['valeur']}))
			self.declas_line_ids = result


#Biens en service à déclasser

class Gi_inv_declasLine (models.Model):
	_name = "gi_inv_declas_line"

	declas_id= fields.Many2one("gi_inv_declas")
	code_immo= fields.Char(string= "Code immobilisation")
	categorie= fields.Char(string= "Categorie")
	designation= fields.Char(string= "Désignation")
	direction= fields.Char(string= "Direction")
	montant= fields.Integer(string= "Total")
	etat= fields.Char(string= "Etat")
	observation= fields.Text(string= "Observation")



class GI_Immobilisation(models.Model):
	_name = "gi_immobilisation"
	_rec_name="code_immo"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	n_ordre= fields.Char(string= "N° d'ordre")
	code = fields.Char(string="Code Budgetaire", store= True)
	quant= fields.Integer(default= 1)
	code_immo= fields.Char(string= "Code Immobilisation", compute= "concatenate_compte", store= True)
	marque_id= fields.Many2one("gi_marque", string= "Marque")
	designation_id= fields.Many2one("gi_designation", string= "Désignation", required= True, size= 65)
	dateacquisition = fields.Date(string= "Date d'acquisition", readonly = True)
	categorie_id = fields.Char(string = "Categorie")
	souscate_id = fields.Many2one("gi_souscategorie", string = "Sous categorie")
	compte= fields.Char(store= True)
	annee_acqui_id= fields.Many2one("ref_exercice", string= "Année acquisition", default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))
	mode_acqu = fields.Char(string= "Mode d'acquisition", readonly= True)
	typefinancement= fields.Char(string= "Source de financement", readonly= True)
	description = fields.Text(string ="Description", size= 100)
	modele_id = fields.Many2one("gi_modele", string= "Modèle")
	n_serie = fields.Char(string = "N° Serie", size = 25)
	fabricant = fields.Char(string = "Fabricant", size =25)
	date_mise_service= fields.Date(string = "Date mise en service")
	amort_id= fields.Many2one("gi_typeamortissement", string='Type Amortissement', required= True)
	utilisateur_id= fields.Many2one("hr.employee", string= "Utilisateur")
	magasin= fields.Char(string= "Magasin", readonly= True)
	duree_annee= fields.Integer(string= "Durée de vie (%)", default= 1)
	an_amorti= fields.Integer(string= "Durée de vie en année", readonly= True)
	state= fields.Selection([("1","Brouillon"),("2","Codifier"),("3","Affecter")], string= "state", default="1")
	acquisition= fields.Integer(string = "Valeur brute", readonly= True)
	taux_degressif= fields.Float(compute= "degressif", string= "Taux dégressif", digits= [3,4], store= True)
	ministere_id= fields.Many2one("ref_ministere", string= "Ministère", required=True)
	epe_id= fields.Many2one("res.company", string= "EPE", required=True)
	direction_id= fields.Many2one("ref_direction", string= "Direction / Service", required=True)
	region_id= fields.Many2one("ref_region", string= "Region", required=True)
	province_id= fields.Many2one("ref_province", string= "Province", required=True)
	departement_id= fields.Many2one("ref_departement",string= "Departement", required=True)
	type_immo= fields.Char(string= "Type Immobilisation", readonly= True)
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))


	@api.onchange("duree_annee")
	def duree(self):
		self.an_amorti= 100/self.duree_annee


#Fonction de remplissage des champs

	@api.onchange('designation_id')
	def remplir(self):
		design = int(self.designation_id)
		res1 = self.env.cr.execute("""SELECT sous_code from gi_ordre_entree_line L where designation_id = %d """ %(design))
		result1 = self.env.cr.fetchone() 
		vals1 = result1 and result1[0] or 0

		sous_codes = str(vals1)

		row = self.env.cr.execute("""SELECT DISTINCT (C.id) As id from ref_compte C, gi_ordre_entree_line L, gi_designation F where L.imp_budg_id= C.id and L.designation_id = F.id and L.sous_code = '%s' """ %(sous_codes))
		rows = self.env.cr.fetchone() 
		val = rows and rows[0] or 0
		cpte = int(val)
		
		

		res = self.env.cr.execute("""SELECT (C.lib_court) As mode,(D.lib_long) As source, (L.val_unit) As montant, (DE.lib_long) As categorie, (DI.lib_long) As types, E.date_entree, (F.lib_long) As mag
		FROM gi_ordre_entree_line L, gi_mode_acquisition C, gi_source_fin D, gi_ordre_entree E, gi_magasin F, gi_categorie DE, gi_typeimmobilisation DI, ref_compte I
		WHERE E.src_fin_id= D.id and L.designation_id = %d and L.sous_code = '%s' """%(design,sous_codes))
		result = self.env.cr.dictfetchall() 

		lib = result and result[0]['mode']
		src = result and result[0]['source']
		ok = result and result[0]['date_entree']
		mags = result and result[0]['mag']
		cat = result and result[0]['categorie']
		mnt = result and result[0]['montant']
		typ_immo = result and result[0]['types']


		self.code= sous_codes
		self.mode_acqu= lib
		self.typefinancement= src
		self.dateacquisition= ok
		self.magasin= mags
		self.categorie_id= cat
		self.acquisition = mnt
		self.type_immo= typ_immo
		self.compte= cpte
		print('le numéro est', self.compte)
		
		


# Fonction de concatenation pour la codification des biens		
 
	@api.depends("code", "annee_acqui_id","ministere_id", "epe_id", "direction_id", "region_id", "province_id", "departement_id", "n_ordre")
	def concatenate_compte(self):
		for rec in self:
			rec.code_immo = str(rec.code)+ "/" + str(rec.ministere_id.code_ministere) + "/" + str(rec.epe_id.code_struct) + "." + str(rec.direction_id.code) + "/" + str(rec.region_id.code_region) + "/" + str (rec.province_id.code_province) + "/" + str (rec.departement_id.code_dep) + "/" + str(rec.annee_acqui_id.no_ex) + "/" + str(rec.n_ordre)




# Les coefficients appliquées ont été prises dans le documents du code penal du Burkina

	@api.depends("an_amorti", "amort_id")
	def degressif (self):
		if self.amort_id.lib_long == "Amortissement dégressif":
			if self.an_amorti <= 4:
				self.taux_degressif= (1/self.an_amorti) * 1.5
			elif self.an_amorti <= 6:
				self.taux_degressif= (1/self.an_amorti) * 2
			elif self.an_amorti >6:
				self.taux_degressif= (1/self.an_amorti) * 2.5



#Fonction compteur

	@api.multi
	def confirm(self):
		val_ex = int(self.x_exercice_id.id)
		val_struct = int(self.company_id.id)
		val_cat= str(self.categorie_id)


		self.env.cr.execute("""SELECT n_compt FROM gi_compt_immobilisation WHERE x_exercice_id = %d and company_id = %d and categorie_id= '%s' """ %(val_ex,val_struct, val_cat) )
		res= self.env.cr.fetchone()
		n_ordre = res and res[0] or 0
		print('Num ordre', n_ordre)
		c1 = int(n_ordre) + 1
		ordre= str(n_ordre)
		if ordre == "0":
			ok= str(c1).zfill(4)
			self.n_ordre = ok
			vals= c1
			self.env.cr.execute("""INSERT INTO gi_compt_immobilisation(x_exercice_id,company_id,n_compt,categorie_id)  VALUES(%d, %d, %d,'%s')""" %(val_ex,val_struct,vals,val_cat))

		else:
			c1 = int(n_ordre) + 1
			ordre= str(n_ordre)
			ok= str(c1).zfill(4)
			print('ordre', ok)
			self.n_ordre = ok
			vals= c1
			self.env.cr.execute("""UPDATE gi_compt_immobilisation SET n_compt = %d  WHERE x_exercice_id = %d and company_id = %d and categorie_id= '%s' """ %(vals,val_ex,val_struct,val_cat))

		self.write({'state': '2'})

# Fonction de mise à jour

	def mise_jour(self):
		design = int(self.designation_id)
		print('la designation = ',design)

		self.env.cr.execute("""UPDATE gi_designation SET quant_stoc = quant_stoc -1  WHERE id = %d """ %(design))

		self.write({'state': '3'})


class Gi_Compt_immobilisation (models.Model):
	
	_name = "gi_compt_immobilisation"
	
	x_exercice_id = fields.Many2one("ref_exercice", default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]), string="Exercice")
	company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
	n_compt = fields.Integer()
	categorie_id = fields.Char()



class Gi_designation (models.Model):
	_name = "gi_designation"
	_rec_name= "lib_long"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	categorie_id= fields.Many2one("gi_categorie", string= "Categorie", required= True)
	lib_court = fields.Char(string= "Libelle court", size= 35, required= True)
	lib_long = fields.Char(string = "Libelle long", size= 65, required= True)
	quant_stoc= fields.Integer(string = "Quantité", default= "0")
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



class GI_Categorie (models.Model):
	_name = "gi_categorie"
	_rec_name= "lib_long"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	code= fields.Char(String= "Classification", size= 2, required= True)
	lib_court = fields.Char(string= "Libelle court", size= 35)
	lib_long = fields.Char(string = "Libelle long", size= 65)
	type_immo_id = fields.Many2one("gi_typeimmobilisation", string= "Type immobilisation")
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



class GI_Souscategorie (models.Model):
	_name = "gi_souscategorie"
	_rec_name= "lib_court"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	lib_court = fields.Char(string= "Libelle court", size= 35)
	lib_long = fields.Char(string = "Libelle long", size= 65)
	categorie_id = fields.Many2one("gi_categorie")
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



class GI_Marque (models.Model):
	_name = "gi_marque"
	_rec_name= "lib_court"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	lib_court = fields.Char(string= "Libelle court", size= 35)
	lib_long = fields.Char(string= "Libelle long", size = 65)
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))




class GI_mode_acquisition (models.Model):
	_name = "gi_mode_acquisition"
	_rec_name= "lib_court"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	lib_court = fields.Char(string= "Libelle court", size= 35)
	lib_long = fields.Char(string= "Libelle long", size= 65)
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))




class GI_Typeamortissement (models.Model):
	_name = "gi_typeamortissement"
	_rec_name= "lib_court"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	lib_court = fields.Char(string= "Libelle court",size= 35)	
	lib_long = fields.Char(string = "Libelle long", size= 65)
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



class Gi_source_fin (models.Model):
	_name = "gi_source_fin"
	_rec_name= "lib_long"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	lib_court = fields.Char(string= "Libelle court",size= 35)
	lib_long = fields.Char(string = "Libelle long", size= 65)
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



class GI_Typeimmobilisation (models.Model):
	_name = "gi_typeimmobilisation"
	_rec_name= "lib_court"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	lib_court = fields.Char(string= "Libelle court", size= 35)
	lib_long = fields.Char(string= "Libelle long", size = 65)
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



class GI_Typemvtimmo (models.Model):
	_name = "gi_typemvtimmo"
	_rec_name= "lib_long"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	lib_court = fields.Char(string= "Libelle court", required= True, size= 35)
	lib_long = fields.Char(string= "Libelle long", required= True, size= 65)
	imput_id= fields.Many2one("ref_compte", string= "Imputation Budgetaire")
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



class GI_Modele (models.Model):
	_name = "gi_modele"
	_rec_name= "lib_court"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	lib_court = fields.Char(string= "Libelle court", size= 35)
	lib_long = fields.Char(string= "Libelle long", size = 65)
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



class GI_Susp_Amort (models.Model):
	_name= "gi_susp_amort"
	_rec_name="immo_id"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	immo_id= fields.Many2one("gi_immobilisation", string= "Code", required=True)
	immobilisation= fields.Char(string= "Immobilisation", readonly= True)
	date_aquisition= fields.Char(string= "Date d'acquisition", readonly= True)
	date_fin = fields.Date(string= "Date de suspension", required = True)
	direction= fields.Char(string= "Direction", readonly= True)
	amort= fields.Char(string= "Type amortissement", readonly= True)
	montant_base= fields.Char(string= "Valeur brute", readonly= True)
	statut= fields.Selection([
		('1', 'Arrêt'),
		],string='Statut', store=True, required=True, default='1')
	motif= fields.Text(string= "Motif", size= 100, required= True)
	p_justify= fields.Binary(string= "Pièce Justificative", attachement= True, required= True)
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



	@api.onchange("immo_id")
	def pamor(self):
		self.amort_id=self.immo_id.amort_id.lib_long
		self.direction=self.immo_id.direction_id.libcourt
		self.immobilisation=self.immo_id.designation_id.lib_long
		self.date_aquisition=self.immo_id.dateacquisition
		self.date_debut=self.immo_id.date_mise_service
		self.montant_base=self.immo_id.acquisition



class Gi_affectation (models.Model):
	_name="gi_affectation"
	_rec_name= "n_mvt"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	n_mvt= fields.Char(string="N° d'ordre", readonly= True)
	observation= fields.Text(string= "Observation", size= 100)
	etat= fields.Selection([("brouillon","Brouillon"),("affecter","Affecter")
		], string= "Etat", default="brouillon")
	concat= fields.Char(default= "BAM")
	affect_line_ids= fields.One2many("gi_affectation_line", "affec_id", string= " ")
	ordo_mat_id= fields.Many2one("gi_agent_mat", string= "Ordonnateur Matières", required= True)
	compta_mat_id= fields.Many2one("gi_agent_mat", string= "Comptable Matières", required= True)
	magasinier_id= fields.Many2one("gi_agent_mat", string= "Magasinier", required= True)
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



	@api.multi
	def conf_affect(self):

		val_ex = int(self.x_exercice_id.id)
		val_struct = int(self.company_id.id)


		self.env.cr.execute("""SELECT n_compt FROM gi_compt_affectation WHERE x_exercice_id = %d and company_id = %d """ %(val_ex,val_struct) )
		res= self.env.cr.fetchone()
		n_mvt = res and res[0] or 0
		c1 = int(n_mvt) + 1
		ordre= str(n_mvt)
		if ordre == "0":
			okk= str(c1).zfill(4)
			ok= self.concat + okk
			self.n_mvt = ok
			vals= c1
			self.env.cr.execute("""INSERT INTO gi_compt_affectation(x_exercice_id,company_id,n_compt)  VALUES(%d, %d, %d)""" %(val_ex,val_struct,vals))

		else:
			c1 = int(n_mvt) + 1
			ordre= str(n_mvt)
			okk= str(c1).zfill(4)
			ok= self.concat + okk
			self.n_mvt = ok
			vals= c1
			self.env.cr.execute("UPDATE gi_compt_affectation SET n_compt = %d  WHERE x_exercice_id = %d and company_id = %d" %(vals,val_ex,val_struct))

		self.write({'etat': 'affecter'})


class Gi_Compt_affectation (models.Model):
	
	_name = "gi_compt_affectation"
	
	x_exercice_id = fields.Many2one("ref_exercice", default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]), string="Exercice")
	company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
	n_compt = fields.Integer()



class Gi_affectationLine (models.Model):
	_name = "gi_affectation_line"
	_rec_name= "code_immo"

	code_immo= fields.Many2one("gi_immobilisation", string= "Code immobilisation")
	designation= fields.Char(string= "Désignation", readonly= True)
	magasin= fields.Char(string= "Magasin", readonly= True)
	val_unit = fields.Integer(string = "Montant", readonly= True)
	etat_id= fields.Many2one("gi_etat", string= "Etat", required= True)
	date_affect= fields.Date(string= "Date affectation", readonly= True)
	direction= fields.Char(string= "Direction", readonly= True)
	user= fields.Char(string= "Utilisateur", readonly= True)
	affec_id= fields.Many2one("gi_affectation")
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))


	@api.onchange("code_immo")
	def affecte(self):
		self.designation=self.code_immo.designation_id.lib_long
		self.magasin= self.code_immo.magasin
		self.quant= self.code_immo.quant
		self.val_unit= self.code_immo.acquisition
		self.date_affect= self.code_immo.date_mise_service
		self.user= self.code_immo.utilisateur_id.name
		self.direction= self.code_immo.direction_id.name

		_sql_constraints= [('code_immo_uniq', 'unique (code_immo)', "Veuillez vérifier la liste des biens à faire sortir, certains sont déjà sortis")]




class Gi_Mutation (models.Model):
	_name="gi_mutation"
	_rec_name= "date_mutation"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	serviceB_id= fields.Many2one("ref_service", string= "Service détenteur", required= True)
	date_mutation= fields.Date(string= "Date de Mutation", required= True)
	observation= fields.Text(string= "Observation", size= 100)
	mute_line_ids= fields.One2many("gi_mutation_line", "mutation_id", string= " ")
	state= fields.Selection([("1","Brouillon"),("2", "Muter")], default= "1", copy= False)
	ordo_mat_id= fields.Many2one("gi_agent_mat", string= "Ordonnateur Matières", required= True)
	compta_mat_id= fields.Many2one("gi_agent_mat", string= "Comptable Matières", required= True)
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))


	@api.onchange("affectation_id")
	def muta(self):
		self.write({'state': '2'})


class Gi_mutationLine (models.Model):
	_name = "gi_mutation_line"

	code_immo= fields.Many2one("gi_affectation_line", string= "Code immobilisation")
	new_code= fields.Char(string= "Nouveau code du bien", required= True)
	designation= fields.Char(string= "Désignation", readonly= True)
	magasin= fields.Char(string= "Magasin", readonly= True)
	val_unit = fields.Integer(string = "Montant", readonly= True)
	etat_id= fields.Many2one("gi_etat", string= "Etat", required= True)
	direction= fields.Char(string= "Direction", readonly= True)
	user= fields.Char(string= "Utilisateur", readonly= True)
	mutation_id= fields.Many2one("gi_mutation", string= " ")
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



	@api.onchange("code_immo")
	def mut(self):
		self.magasin=self.code_immo.magasin
		self.designation= self.code_immo.designation
		self.val_unit= self.code_immo.val_unit
		self.direction= self.code_immo.direction
		self.user= self.code_immo.user
		self.new_code= self.code_immo.code_immo.code_immo



class Gi_sortie (models.Model):
	_name="gi_sortie"
	_rec_name= "n_ordre"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	n_ordre= fields.Integer(string= "N° d'ordre")
	date= fields.Date(string= "Date de sortie")
	date_retour= fields.Date(string= "Date retour prévisionnelle")
	action= fields.Many2one("ir.cron", string = "Alerte")
	state= fields.Selection([("1", "Brouillon"), ("2", "Confirmer")], copy= False, string= "Etat", default= "1")
	motif_id= fields.Many2one("gi_motif_sortie", string= "Motif", required= True)
	sortiline_ids= fields.One2many("gi_sortie_line", "sortie_id", string= " ")
	destinateur= fields.Char(string= "Destinateur", size= 65)
	ordo_mat_id= fields.Many2one("gi_agent_mat", string= "Ordonnateur Matières", required= True)
	compta_mat_id= fields.Many2one("gi_agent_mat", string= "Comptable Matières", required= True)
	magasinier_id= fields.Many2one("gi_agent_mat", string= "Magasinier/ Fichiste", required= True)
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))


	@api.multi
	def sortie(self):
		val_ex = int(self.x_exercice_id.id)
		val_struct = int(self.company_id.id)


		self.env.cr.execute("select n_compt + 1 from gi_compt_sortie where x_exercice_id = %d and company_id = %d" %(val_ex,val_struct) )
		res= self.env.cr.fetchone()
		n_ordre = res and res[0]
		if n_ordre == None:
			self.n_ordre = 1
			self.env.cr.execute("""INSERT INTO gi_compt_sortie(x_exercice_id,company_id,n_compt)  VALUES(%d, %d, %d)""" %(val_ex,val_struct,self.n_ordre))

		else:
			self.n_ordre = res and res[0]
			self.env.cr.execute("UPDATE gi_compt_sortie SET n_compt = %d  WHERE x_exercice_id = %d and company_id = %d" %(self.n_ordre,val_ex,val_struct))

		self.write({'state': '2'})



class Gi_compt_sortie(models.Model):
	
	_name = "gi_compt_sortie"
	
	x_exercice_id = fields.Many2one("ref_exercice", default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]), string="Exercice")
	company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
	n_compt = fields.Integer()

class Gi_sortieLine (models.Model):
	_name = "gi_sortie_line"

	code_immo = fields.Many2one("gi_immobilisation", string= "Code Immobilisation")
	categorie = fields.Char(string= "Categorie", readonly= True)
	designation = fields.Char(string= "Désignation", readonly= True)
	val_brute = fields.Integer(string= "Valeur brute", readonly= True)
	service = fields.Char(string= "Service détenteur", readonly= True)
	detenteur = fields.Char(string= "Détenteur", readonly= True)
	etat_id= fields.Many2one("gi_etat", string= "Etat")
	observation= fields.Char(string= "Observations")
	sortie_id= fields.Many2one("gi_sortie", string= " ")



	@api.onchange("code_immo")
	def sortie(self):
		self.categorie = self.code_immo.categorie_id
		self.designation = self.code_immo.designation_id.lib_long
		self.val_brute = self.code_immo.acquisition
		self.service = self.code_immo.direction_id.libcourt
		self.detenteur = self.code_immo.utilisateur_id.name




class Gi_entree (models.Model):
	_name="gi_entree"
	_rec_name= "date_retour"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	gi_sortie_id= fields.Many2one("gi_sortie", string= "N° Entrée", required= True)
	service_id= fields.Many2one("ref_service", string= "Service détenteur")
	detenteur_id= fields.Many2one("hr.employee", string= "Détenteur")
	date_retour= fields.Date(string= "Date de retour", required= True)
	entreline_ids= fields.One2many("gi_sortie_line", "sortie_id", string= " ")
	observation= fields.Text(string= "Observation")
	ordo_mat_id= fields.Many2one("gi_agent_mat", string= "Ordonnateur Matières", required= True)
	compta_mat_id= fields.Many2one("gi_agent_mat", string= "Comptable Matières", required= True)
	magasinier_id= fields.Many2one("gi_agent_mat", string= "Magasinier/ Fichiste", required= True)
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



	@api.onchange("gi_sortie_id")
	def sortie(self):
		self.entreline_ids = self.gi_sortie_id.sortiline_ids



class Gi_transfert (models.Model):
	_name="gi_transfert"
	_rec_name= "typ_mvt"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	directionB_id= fields.Many2one("ref_direction", string= "Direction", required= True)
	ministereB_id= fields.Many2one("ref_ministere", string= "Ministère", required= True)
	date_transfert= fields.Date(string= "Date de transfert", required= True)
	observation= fields.Text(string= "Observation", size= 100)
	transfert_ids= fields.One2many("gi_transfert_line", "transfert_id", string= " ")
	typ_mvt= fields.Many2one("gi_typemvtimmo", string= "Type mouvement", required= True)
	etat= fields.Selection([("brouillon","Brouillon"), ("transfert","Transfert")], default= "brouillon", string= "Etat",)
	ordo_mat_id= fields.Many2one("gi_agent_mat", string= "Ordonnateur Matières", required= True)
	compta_mat_id= fields.Many2one("gi_agent_mat", string= "Comptable Matières", required= True)
	magasinier_id= fields.Many2one("gi_agent_mat", string= "Magasinier", required= True)
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))


	@api.multi
	def transf(self):
		for record in self.transfert_ids:
			val_id = int(record.code)

			row= self.env.cr.execute("""SELECT quant FROM gi_ordre_sortie_line WHERE id =%d """ %(val_id))
			rows = self.env.cr.fetchone()
			val = rows and rows[0]
			if val <= 0:
				raise ValidationError(('Le bien nest plus disponible dans le stock. Veuillez verifier le stock'))
			else:
				record.env.cr.execute("""UPDATE gi_ordre_sortie_line set quant = quant - 1 WHERE id = %d """ %(val_id))



class Gi_transfertLine (models.Model):
	_name = "gi_transfert_line"

	code= fields.Many2one("gi_ordre_sortie_line", string= "Code immobilisation")
	date_entree= fields.Char(string= "Date mise en service", readonly= True)
	type_immo= fields.Char(string= "Type immobilisation", readonly= True)
	categorie= fields.Char(string= "Categorie", readonly= True)
	designation= fields.Char(string= "Désignation", readonly= True)
	direction= fields.Char(string= "Direction", readonly= True)
	user= fields.Char(string= "Utilisateur", readonly= True)
	quant = fields.Integer(string = "Quantité", readonly= True)
	val_unit = fields.Integer(string = "Prix unitaire", readonly= True)
	montant = fields.Integer(string = "Total", readonly= True)
	ordre_sortie_line_id= fields.Many2one("gi_ordre_sortie")
	transfert_id= fields.Many2one("gi_transfert", string= "")
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



	@api.onchange("code")
	def transfertline(self):
		self.type_immo= self.code.type_immo
		self.designation= self.code.designation
		self.date_entree= self.code.date_entree
		self.categorie= self.code.categorie
		self.quant= self.code.quant
		self.val_unit= self.code.val_unit
		self.montant= self.code.montant
		self.direction= self.code.direction




class Gi_cession_vente (models.Model):
	_name="gi_cession_vente"
	_rec_name= "n_mvt"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	n_mvt= fields.Char(string= "N° Opération", readonly= True)
	no_ecr = fields.Integer("N° Ecriture", readonly=True)
	ministereA_id= fields.Many2one("ref_ministere", string= "Ministère")
	date_mvt= fields.Date(string= "Date de la vente", required= True)
	state= fields.Selection([("1","Brouillon"), ("2","Confirmer"),("3","Vendu"), ("P","Ecriture Produit")], string= "Etat", default= "1")
	typ_mvt= fields.Many2one("gi_typemvtimmo", string= "Type Mouvement", required= True)
	fg_sens = fields.Char(default= "D")
	type_journal = fields.Many2one("compta_type_journal", string= "Type journal", required= True)
	type_operation= fields.Many2one("compta_data", string= "Type Opération")
	cess_vente_line_ids= fields.One2many("gi_cess_vente_line", "cess_vente_id", string= " ")
	concat= fields.Char(default= "CEV")
	id_imput= fields.Char()
	var_cpte= fields.Char()
	mnt_total= fields.Integer(string= "Montant total")
	acquereur= fields.Many2one("ref_contribuable", string= "Bénéficiaire/Acquereur", required= True)
	ref_pay= fields.Char(string= "Référence quittance")
	commentaire= fields.Text(string= "Commentaire")
	ordo_mat_id= fields.Many2one("gi_agent_mat", string= "Ordonnateur Matières")
	compta_mat_id= fields.Many2one("gi_agent_mat", string= "Comptable Matières")
	vente_comiss_ids= fields.One2many("gi_mem_commis_line", "vente_comiss_id", string= " ")
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))


	@api.onchange("acquereur")
	def impu(self):
		self.id_imput = self.acquereur.cpte_fournisseur.concate_cpte
		self.var_cpte=self.acquereur.cpte_fournisseur.id



	@api.multi
	def valid(self):
		val_ex = int(self.x_exercice_id.id)
		val_struct = int(self.company_id.id)
		id_vente= self.id


		self.env.cr.execute("""SELECT n_compt + 1 FROM gi_compt_cess_vente WHERE x_exercice_id = %d and company_id = %d """ %(val_ex,val_struct) )
		res= self.env.cr.fetchone()
		result = res and res[0] or 0

		if result == None:
			self.n_mvt = int(1)
			self.env.cr.execute("""INSERT INTO gi_compt_cess_vente(x_exercice_id,company_id,n_compt) VALUES(%d, %d, %d)""" %(val_ex,val_struct,self.n_mvt))

		else:
			self.n_mvt = res and res[0]
			self.env.cr.execute("UPDATE gi_compt_cess_vente SET n_compt = %d  WHERE x_exercice_id = %d and company_id = %d" %(self.n_mvt,val_ex,val_struct))

#Fonction de calcul du montant total des biens réevaluer pour vente

		self.env.cr.execute("""SELECT sum(valeur)
		FROM gi_cess_vente_line WHERE x_exercice_id = %d AND company_id = %d AND cess_vente_id = %d """ %(val_ex, val_struct, id_vente))
		res = self.env.cr.fetchone()
		self.mnt_total = res and res[0]


		self.write({'state': '2'})



	@api.multi
	def vend(self):

		for record in self.cess_vente_line_ids:
			val_id = int(record.code_immo)

			row= self.env.cr.execute("""SELECT quant FROM gi_ordre_sortie_line WHERE id =%d """ %(val_id))
			rows = self.env.cr.fetchone()
			val = rows and rows[0]
			if val <= 0:
				raise ValidationError(('Le bien nest plus disponible dans le stock. Veuillez verifier le stock'))
			else:
				record.env.cr.execute("""UPDATE gi_ordre_sortie_line set quant = quant - 1 WHERE id = %d """ %(val_id))
			
		self.write({'state': '3'})


	@api.multi
	def generer_ecriture(self):
		self.write({'state': 'P'})


class Gi_Compt_cess_vente(models.Model):
	
	_name = "gi_compt_cess_vente"
	
	x_exercice_id = fields.Many2one("ref_exercice", default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]), string="Exercice")
	company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
	n_compt = fields.Integer()



class Gi_cess_venteLine (models.Model):
	_name = "gi_cess_vente_line"

	code_immo= fields.Many2one("gi_ordre_sortie_line", string= "Code Immobilisation")
	no_ecr = fields.Integer()
	compte= fields.Integer(store= True)
	no_lecr = fields.Integer("N° Lignes", readonly=True)
	objet = fields.Char(string= "Objet")
	categorie= fields.Char(string= "Categorie", readonly= True)
	designation = fields.Char(string= "Désignation", readonly= True)
	direction= fields.Char(string= "Direction", readonly= True)
	etat_id= fields.Many2one("gi_etat", string= "Etat")
	typ_pj = fields.Many2one("compta_piece", string='Pièce Just.')
	valeur_reev= fields.Integer(string= "Valeur Réévaluer",readonly= True)
	valeur= fields.Integer(string= "Montant reelle")
	fg_sens = fields.Char(default= "C")
	observation= fields.Text(string= "Observation", size= 50)
	cess_vente_id= fields.Many2one("gi_cession_vente")
	annee= fields.Integer(string= "Année")
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



	@api.onchange("code_immo")
	def venteline(self):
		self.categorie=self.code_immo.categorie
		self.designation= self.code_immo.designation
		self.direction= self.code_immo.direction


class Gi_mem_commis_line (models.Model):
	_name = "gi_mem_commis_line"

	nom_pre_id= fields.Many2one("hr.employee", string= "Nom & Prénom(s)", required= True)
	service_id= fields.Many2one("ref_service", string= "Structure administrative", required = True)
	membre_id= fields.Many2one("gi_type_membre", string= "Qualité", required= True)
	sign= fields.Boolean(string= "Signature")
	vente_comiss_id= fields.Many2one("gi_cession_vente")
	don_comiss_id= fields.Many2one("gi_cession_vente")
	ref_comiss_id= fields.Many2one("gi_cession_vente")




class Gi_cession_don (models.Model):
	_name="gi_cession_don"
	_rec_name= "n_mvt"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	n_mvt= fields.Char(string= "N° Opération", readonly= True)
	no_ecr = fields.Integer("N° Ecriture", readonly=True)
	ministereA_id= fields.Many2one("ref_ministere", string= "Ministère")
	date_mvt= fields.Date(string= "Date de la vente", required= True)
	state= fields.Selection([("1","Brouillon"), ("2","Confirmer"),("P","Ecriture Produit")], string= "Etat", default= "1")
	typ_mvt= fields.Many2one("gi_typemvtimmo", string= "Type Mouvement", required= True)
	imput_id= fields.Char(string= "Imputation")
	fg_sens = fields.Char(default= "C")
	acquereur= fields.Many2one("ref_contribuable", string= "Bénéficiaire/Acquereur", required= True)
	type_journal = fields.Many2one("compta_type_journal", string= "Type journal", required= True)
	type_operation= fields.Many2one("compta_data", string= "Type Opération")
	cess_don_line_ids= fields.One2many("gi_cession_don_line", "cess_don_id", string= " ")
	concat= fields.Char(default= "CEV")
	id_imput= fields.Char()
	var_cpte= fields.Char()
	mnt_total= fields.Integer(string= "Montant total")
	commentaire= fields.Text(string= "Commentaire")
	ordo_mat_id= fields.Many2one("gi_agent_mat", string= "Ordonnateur Matières")
	compta_mat_id= fields.Many2one("gi_agent_mat", string= "Comptable Matières")
	don_comiss_ids= fields.One2many("gi_mem_commis_line", "don_comiss_id", string= " ")
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



	@api.onchange("typ_mvt")
	def imput(self):
		self.imput_id=self.typ_mvt.imput_id.id



	@api.multi
	def test(self):
		val_ex = int(self.x_exercice_id.id)
		val_struct = int(self.company_id.id)

		self.env.cr.execute("""SELECT n_compt FROM gi_compt_cess_don WHERE x_exercice_id = %d and company_id = %d """ %(val_ex,val_struct) )
		res= self.env.cr.fetchone()
		n_mvt = res and res[0] or 0
		c1 = int(n_mvt) + 1
		ordre= str(n_mvt)
		if ordre == "0":
			okk= str(c1).zfill(4)
			ok= self.concat + okk
			self.n_mvt = ok
			vals= c1
			self.env.cr.execute("""INSERT INTO gi_compt_cess_don(x_exercice_id,company_id,n_compt)  VALUES(%d, %d, %d)""" %(val_ex,val_struct,vals))

		else:
			c1 = int(n_mvt) + 1
			ordre= str(n_mvt)
			okk= str(c1).zfill(4)
			ok= self.concat + okk
			self.n_mvt = ok
			vals= c1
			self.env.cr.execute("UPDATE gi_compt_cess_don SET n_compt = %d  WHERE x_exercice_id = %d and company_id = %d" %(vals,val_ex,val_struct))
		
		for record in self.cess_don_line_ids:
			val_id = int(record.code_immo)

			row= self.env.cr.execute("""SELECT quant FROM gi_ordre_sortie_line WHERE id =%d """ %(val_id))
			rows = self.env.cr.fetchone()
			val = rows and rows[0]
			if val <= 0:
				raise ValidationError((' Un ou plusieurs bien choisis ne figurent plus dans le stock. Veuillez verifier le stock'))
			else:
				record.env.cr.execute("""UPDATE gi_ordre_sortie_line set quant = quant - 1 WHERE id = %d """ %(val_id))
			
		self.write({'state': '2'})


	@api.multi
	def generer_ecriture(self):
		self.write({'state': 'P'})



class Gi_Compt_cess_don(models.Model):
	
	_name = "gi_compt_cess_don"
	
	x_exercice_id = fields.Many2one("ref_exercice", default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]), string="Exercice")
	company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
	n_compt = fields.Integer()



class Gi_cession_donLine (models.Model):
	_name = "gi_cession_don_line"

	code_immo= fields.Many2one("gi_ordre_sortie_line", string= "Code Immobilisation")
	no_ecr = fields.Integer()
	compte= fields.Integer(store= True)
	no_lecr = fields.Integer("N° Lignes", readonly=True)
	objet = fields.Char(string= "Objet")
	categorie= fields.Char(string= "Categorie", readonly= True)
	designation = fields.Char(string= "Désignation", readonly= True)
	direction= fields.Char(string= "Direction", readonly= True)
	etat_id= fields.Many2one("gi_etat", string= "Etat")
	valeur= fields.Integer(string= "Montant reelle")
	fg_sens = fields.Char(default= "D")
	observation= fields.Text(string= "Observation", size= 50)
	cess_don_id= fields.Many2one("gi_cession_don")
	annee= fields.Integer(string= "Année")
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



	@api.onchange("code_immo")
	def donline(self):
		self.categorie=self.code_immo.categorie
		self.designation= self.code_immo.designation
		self.direction= self.code_immo.direction



class Gi_reforme (models.Model):
	_name="gi_reforme"
	_rec_name= "n_ordre"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	n_ordre= fields.Integer(string= "N° Mouvement", readonly= True)
	ministereA_id= fields.Many2one("ref_ministere", string= "Ministère")
	nom_mvt= fields.Char(string= "Libelle long", readonly= True)
	date_mvt= fields.Date(string= "Date reforme")
	typ_mvt= fields.Many2one("gi_typemvtimmo", string= "Type Mouvement", required= True)
	state= fields.Selection([("brouillon","Brouillon"), ("reforme","Reformé")], string= "Etat", default= "brouillon")
	reforme_line_ids= fields.One2many("gi_reforme_line", "reforme_id", string= " ")
	ref_comiss_ids = fields.One2many("gi_mem_commis_line", "ref_comiss_id", string= " ")
	ordo_mat_id= fields.Many2one("gi_agent_mat", string= "Ordonnateur Matières")
	compta_mat_id= fields.Many2one("gi_agent_mat", string= "Comptable Matières")
	ref_piece_id= fields.Many2one("gi_pjustificative", string= "Ref Pièce", size=15)
	lib_long= fields.Char(string="Libelle long", readonly= True)
	date= fields.Char(string= "Date du", readonly= True)
	commentaire= fields.Text(string= "Commentaire")
	pj= fields.Binary(string= "Joindre PV", attachement= True)
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



	@api.onchange("ref_piece_id")
	def piece(self):
		self.lib_long=self.ref_piece_id.lib_long
		self.date=self.ref_piece_id.date



	@api.multi
	def test(self):
		val_ex = int(self.x_exercice_id.id)
		val_struct = int(self.company_id.id)


		self.env.cr.execute("select n_compt + 1 from gi_compt_reforme where x_exercice_id = %d and company_id = %d" %(val_ex,val_struct) )
		res= self.env.cr.fetchone()
		n_ordre = res and res[0]
		if n_ordre == None:
			self.n_ordre = 1
			self.env.cr.execute("""INSERT INTO gi_compt_reforme(x_exercice_id,company_id,n_compt)  VALUES(%d, %d, %d)""" %(val_ex,val_struct,self.n_ordre))

		else:
			self.n_ordre = res and res[0]
			self.env.cr.execute("UPDATE gi_compt_reforme SET n_compt = %d  WHERE x_exercice_id = %d and company_id = %d" %(self.n_ordre,val_ex,val_struct))

		for record in self.reforme_line_ids:
			val_id = int(record.code_immo)

			row= self.env.cr.execute("""SELECT quant FROM gi_ordre_sortie_line WHERE id =%d """ %(val_id))
			rows = self.env.cr.fetchone()
			val = rows and rows[0]
			if val <= 0:
				raise ValidationError((' Un ou plusieurs bien choisis ne figurent plus dans le stock. Veuillez verifier le stock'))
			else:
				record.env.cr.execute("""UPDATE gi_ordre_sortie_line set quant = quant - 1 WHERE id = %d """ %(val_id))
			

		self.write({'state': 'reforme'})



class Gi_Compt_reforme(models.Model):
	
	_name = "gi_compt_reforme"
	
	x_exercice_id = fields.Many2one("ref_exercice", default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]), string="Exercice")
	company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
	n_compt = fields.Integer()



class Gi_reformeLine (models.Model):
	_name = "gi_reforme_line"

	code_immo= fields.Many2one("gi_ordre_sortie_line", string= "Code Immobilisation")
	categorie= fields.Char(string= "Categorie", readonly= True)
	designation = fields.Char(string= "Désignation", readonly= True)
	direction= fields.Char(string= "Direction", readonly= True)
	etat_id= fields.Many2one("gi_etat", string= "Etat")
	valeur= fields.Integer(string= "Valeur")
	nature= fields.Char(string= "Nouvelle nature", size= 50)
	reforme_id= fields.Many2one("gi_reforme", string= " ")


	@api.onchange("code_immo")
	def reforline(self):
		self.categorie=self.code_immo.categorie
		self.designation= self.code_immo.designation
		self.direction= self.code_immo.direction



class Gi_declassement (models.Model):
	_name="gi_declassement"
	_rec_name= "mvt_id"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	n_ordre= fields.Integer(string= "N° Mouvement", readonly= True)
	ministereA_id= fields.Many2one("ref_ministere", string= "Ministère", required= True)
	mvt_id= fields.Many2one("gi_typemvtimmo", string= "Type mouvement", required= True)
	date_mvt= fields.Date(string= "Date declassement", required= True)
	state= fields.Selection([("1","Brouillon"), ("2","Confirmer"),("4","Declasser")], string= "Etat", default= "1")
	declassement_line_ids= fields.One2many("gi_declassement_line", "declasse_id", string= " ")
	ordo_mat_id= fields.Many2one("gi_agent_mat", string= "Ordonnateur Matières", required= True)
	compta_mat_id= fields.Many2one("gi_agent_mat", string= "Comptable Matières", required= True)
	commentaire= fields.Text(string= "Commentaire")
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))


	@api.multi
	def test(self):
		val_ex = int(self.x_exercice_id.id)
		val_struct = int(self.company_id.id)


		self.env.cr.execute("select n_compt + 1 from gi_compt_declassement where x_exercice_id = %d and company_id = %d" %(val_ex,val_struct) )
		res= self.env.cr.fetchone()
		n_ordre = res and res[0]
		if n_ordre == None:
			self.n_ordre = 1
			self.env.cr.execute("""INSERT INTO gi_compt_declassement(x_exercice_id,company_id,n_compt)  VALUES(%d, %d, %d)""" %(val_ex,val_struct,self.n_ordre))

		else:
			self.n_ordre = res and res[0]
			self.env.cr.execute("UPDATE gi_compt_declassement SET n_compt = %d  WHERE x_exercice_id = %d and company_id = %d" %(self.n_ordre,val_ex,val_struct))

		self.write({'state': '2'})


# Biens en service

	@api.multi
	def servce(self):
		for record in self.declassement_line_ids:
			val_id = int(record.code_immo)

			row= self.env.cr.execute("""SELECT quant FROM gi_ordre_sortie_line WHERE id =%d """ %(val_id))
			rows = self.env.cr.fetchone()
			val = rows and rows[0]
			if val <= 0:
				raise ValidationError(('Parmis la liste des biens saisient, certains ont déjà été déclassés, vendus ou cédés. Veuillez vérifier dans le stock'))
			else:
				record.env.cr.execute("""UPDATE gi_ordre_sortie_line set quant = quant - 1 WHERE id = %d """ %(val_id))
			
		self.write({'state': '4'})



class Gi_compt_declassement(models.Model):
	
	_name = "gi_compt_declassement"
	
	x_exercice_id = fields.Many2one("ref_exercice", default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]), string="Exercice")
	company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
	n_compt = fields.Integer()



class Gi_declassementLine (models.Model):
	_name = "gi_declassement_line"

	code_immo= fields.Many2one("gi_ordre_sortie_line", string= "Code Immobilisation")
	categorie= fields.Char(string= "Categorie", readonly= True)
	designation = fields.Char(string= "Désignation", readonly= True)
	direction= fields.Char(string= "Direction", readonly= True)
	etat_id= fields.Many2one("gi_etat", string= "Etat")
	valeur= fields.Integer(string= "Valeur")
	nature= fields.Char(string= "Nouvelle nature", size= 50)
	declasse_id= fields.Many2one("gi_declassement", string= " ")


	@api.onchange("code_immo")
	def reforline(self):
		self.categorie=self.code_immo.categorie
		self.designation= self.code_immo.designation
		self.direction= self.code_immo.direction



	@api.onchange('designation')
	def declas(self):
		design = int(self.designation)

		res = self.env.cr.execute("""SELECT (DI.lib_long) As types, (L.sous_code) As code,(L.val_unit) As montant
		FROM gi_ordre_entree_line L, ref_compte C, gi_ordre_entree E, gi_typeimmobilisation DI, gi_designation B
		WHERE L.designation_id = B.id and L.type_immo_id= DI.id and L.imp_budg_id= C.id and B.id= %d """%(design))
		result = self.env.cr.dictfetchall()

		code = result and result[0]['code']
		types = result and result[0]['types']
		mnt = result and result[0]['montant']

		self.sous_code= code
		self.type_immo= types
		self.val_unit= mnt


	@api.onchange("quant")
	def quantdeclasser(self):
		self.montant= self.quant * self.val_unit



class Gi_Pjustificative (models.Model):
	_name="gi_pjustificative"
	_rec_name= "ref_piece"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	ref_piece= fields.Char(string= " Reference pièce", required= True)
	lib_court= fields.Char(string= "Libelle court", required=True, size=35)
	lib_long= fields.Char(string="Libelle Long", required= True, size=65)
	date= fields.Date(string= "Date du")
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))


class Gi_reevaluation (models.Model):
	_name="gi_reevaluation"
	_rec_name= "immo_id"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	immo_id= fields.Many2one("gi_immobilisation", string= "Code Immobilisation", required=True)
	categorie= fields.Char(string= "Categorie", readonly= True)
	design= fields.Char(string= "Désignation", readonly= True)
	date_aquisition= fields.Date(string= "Date acquisition", readonly= True)
	date_mise_service= fields.Date(string= "Date mise en service", readonly= True)
	date_rev= fields.Date(string="Date reevaluation")
	Val_brute= fields.Integer(string="Valeur brute", readonly= True)
	val_acc= fields.Float(string= "Amortissement cumulé")
	val_reev= fields.Integer(string= "Montant réévalué")
	val_rec= fields.Date()
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



	@api.onchange("immo_id")
	def reevalue(self):
		self.design=self.immo_id.designation_id.lib_long
		self.Val_brute=self.immo_id.acquisition
		self.date_aquisition=self.immo_id.dateacquisition
		self.date_mise_service=self.immo_id.date_mise_service
		self.categorie=self.immo_id.categorie_id




	@api.onchange("date_rev")
	def reevaluer(self):
		if self.date_rev:
			ddbut = str(self.date_rev.strftime("%Y-%m-%d"))
			val_immo = int(self.immo_id)
			val_struct = int(self.company_id)
			val_ex = int(self.x_exercice_id)


			self.env.cr.execute("""SELECT DISTINCT(L.depreciated_value) As cumule, (L.remaining_value) as residuel,(L.depreciation_date) as dates FROM account_asset_depreciation_line L, account_asset_asset F WHERE L.asset_id = F.id and F.immo_id = %s and L.depreciation_date= %s and F.x_exercice_id= %s and F.company_id= %s """,(val_immo,ddbut,val_ex,val_struct))

			result = self.env.cr.dictfetchall() or 0
			self.val_acc = result and result[0]['cumule']
			self.val_reev= result and result[0]['residuel']
			self.val_rec= result and result[0]['dates']

	


class Gi_Cession (models.Model):
	_name="gi_cession"
	_rec_name= "acquereur"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	acquereur= fields.Char(string="Acquereur")
	ref_pay= fields.Char(string= "Référence quittance", required=True)
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



class Gi_magasin (models.Model):
	_name="gi_magasin"
	_rec_name= "lib_court"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	lib_court= fields.Char(string= "Libelle court", required=True, size=35)
	lib_long= fields.Char(string="Libelle Long", required= True, size=65)
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))


class Gi_etat (models.Model):
	_name="gi_etat"
	_rec_name= "lib_court"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	lib_court= fields.Char(string= "Libelle court", required=True, size=35)
	lib_long= fields.Char(string="Libelle Long", required= True, size=65)
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))


class Gi_ord_matiere (models.Model):
	_name = "gi_ord_matiere"
	_rec_name= "lib_long"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	lib_court = fields.Char(string= "Libelle court", size= 35)
	lib_long = fields.Char(string = "Libelle long", size= 65)
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



class Gi_type_membre (models.Model):
	_name = "gi_type_membre"
	_rec_name= "lib_long"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	lib_court = fields.Char(string= "Libelle court", size= 35, required= True)
	lib_long = fields.Char(string = "Libelle long", size= 65, required= True)
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



class Gi_compt_matiere (models.Model):
	_name = "gi_compt_matiere"
	_rec_name= "lib_court"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	lib_court = fields.Char(string= "Libelle court", size= 35)
	lib_long = fields.Char(string = "Libelle long", size= 65)
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))


class Gi_fichiste (models.Model):
	_name = "gi_fichiste"
	_rec_name= "lib_court"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	lib_court = fields.Char(string= "Libelle court", size= 35)
	lib_long = fields.Char(string = "Libelle long", size= 65)
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))


class Gi_type_agent (models.Model):
	_name = "gi_type_agent"
	_rec_name= "lib_long"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	lib_court = fields.Char(string= "Libelle court", required= True, size= 35)
	lib_long = fields.Char(string = "Libelle long", required= True, size= 65)
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))

class Gi_agent_mat (models.Model):
	_name = "gi_agent_mat"
	_rec_name= "employe_id"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	employe_id = fields.Many2one("hr.employee", required= True, string= " Nom & Prénom (s)")
	typeagent_id= fields.Many2one("gi_type_agent", string= "Type agent")
	direction_id= fields.Many2one("ref_direction", string= "Direction")
	service_id= fields.Many2one("ref_service", string= "Service")
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))	


class Gi_compta_libre (models.Model):

	_inherit= "compta_ecriture"

	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))	

	

class Gi_compta_amort (models.Model):
	_name = "gi_compta_amort"
	_rec_name= "n_ordre"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	n_ordre = fields.Char(string= "N° Ordre" )
	typ_op= fields.Selection([("e", "Encaissement"), ("d", "Decaissement")], string= "Type d'operation", required= True)
	date= fields.Date(string= "Date")
	mode_reglement = fields.Many2one("compta_jr_modreg", string= 'Mode de règlement', required = True)
	type_journal = fields.Char("Journal", required= True)
	cmpt_amor_line_ids = fields.One2many("gi_compta_amort_line", "cmpt_amor_id", string= " ")
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))	



class Gi_compta_amort_line (models.Model):
	_name = "gi_compta_amort_line"

	lign_ecrit = fields.Integer(string= "N° Ligne ecriture")
	pj = fields.Char(string= "Pièce Justificative")
	typ_pj= fields.Many2one("gi_cession", string= "Pièce Just")
	montant = fields.Integer(string= "Montant")
	fg_sens = fields.Char('Sens')
	libelle = fields.Char(string= "Libellé")
	intervenant = fields.Char(string= "Intervenant")
	annee= fields.Many2one("ref_service", string= "Année")
	cmpt_amor_id= fields.Many2one("gi_compta_amort", string= " ")




class Gi_compta_reeva (models.Model):
	_name = "gi_compta_reeva"
	_rec_name= "n_ordre"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	n_ordre = fields.Char(string= "N° Ordre" )
	typ_op= fields.Selection([("e", "Encaissement"), ("d", "Decaissement")], string= "Type d'operation", required= True)
	date= fields.Date(string= "Date")
	mode_reglement = fields.Many2one("compta_jr_modreg", string= 'Mode de règlement', required = True)
	type_journal = fields.Char("Journal")
	cmpt_reev_line_ids = fields.One2many("gi_compta_reeva_line", "cmpt_rev_id", string= " ")
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))	



class Gi_compta_reeva_line (models.Model):
	_name = "gi_compta_reeva_line"

	lign_ecrit = fields.Integer(string= "N° Ligne ecriture")
	pj = fields.Char(string= "Pièce Justificative")
	typ_pj= fields.Many2one("gi_cession", string= "Pièce Just")
	montant = fields.Integer(string= "Montant")
	fg_sens = fields.Char('Sens')
	libelle = fields.Char(string= "Libellé")
	intervenant = fields.Char(string= "Intervenant")
	annee= fields.Many2one("ref_service", string= "Année")
	cmpt_rev_id= fields.Many2one("gi_compta_reeva", string= " ")



class Gi_compta_mvt (models.Model):
	_name = "gi_compta_mvt"
	_rec_name= "n_ordre"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	n_ordre = fields.Char(string= "N° Ordre" )
	typ_op= fields.Selection([("e", "Encaissement"), ("d", "Decaissement")], string= "Type d'operation", required= True)
	date= fields.Date(string= "Date")
	mode_reglement = fields.Many2one("compta_jr_modreg", string= 'Mode de règlement', required = True)
	type_journal = fields.Char("Journal")
	cmpt_mvt_line_ids = fields.One2many("gi_compta_mvt_line", "cmpt_mvt_id", string= " ")
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))	




class Gi_compta_mvt_line (models.Model):
	_name = "gi_compta_mvt_line"

	lign_ecrit = fields.Integer(string= "N° Ligne ecriture")
	pj = fields.Char(string= "Pièce Justificative")
	typ_pj= fields.Many2one("gi_cession", string= "Pièce Just")
	montant = fields.Integer(string= "Montant")
	fg_sens = fields.Char('Sens')
	libelle = fields.Char(string= "Libellé")
	intervenant = fields.Char(string= "Intervenant")
	annee= fields.Many2one("ref_service", string= "Année")
	cmpt_mvt_id= fields.Many2one("gi_compta_mvt", string= " ")



class Gi_motif_sortie (models.Model):
	_name = "gi_motif_sortie"
	_rec_name= "lib_long"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	lib_court = fields.Char(string= "Libelle court", size= 35)
	lib_long = fields.Char(string = "Libelle long", size= 65)
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))


class Gi_invent_bien (models.Model):
	_name = "gi_invent_bien"
	_rec_name= "type_invent"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	code= fields.Integer(srting= "N° Inventaire")
	ministere_id = fields.Many2one("ref_ministere", string= "Ministère", required= True)
	direction_id = fields.Many2one("ref_direction", string= "Direction")
	date_debut= fields.Date(string= "Date debut", default= fields.Date.context_today, required= True)
	date_fin = fields.Date(string= "Date fin", required= True)
	type_invent= fields.Selection([("trimestre", "Trimestriel"), ("semestre", "Semestriel"), ("tournant", "Inventaire tournant"), 
		("annuel", "Annuel")], string= "Type Inventaire", default= "tournant", store= True, required= True)
	emplacement = fields.Selection([('1', 'Tous les magasins'),('2', 'Par direction')], string= "Emplacements", default='1', required=True)
	ordo_mat_id= fields.Many2one("gi_agent_mat", string= "Ordonnateur Matières", required= True)
	compta_mat_id= fields.Many2one("gi_agent_mat", string= "Comptable Matières", required= True)
	magasinier_id= fields.Many2one("gi_agent_mat", string= "Magasinier/ Fichiste", required= True)
	inventbien_line_ids= fields.One2many("gi_invent_bien_line", "invent_bien_id", string= " ")
	state= fields.Selection([("brouillon", "Brouillon"), ("fait", "Fait")], string= "Etat", default= "brouillon", store= True)
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



#Inventaire des biens en service

	def invent(self):
		if self.date_debut and self.date_fin:
			ddbut = str(self.date_debut.strftime("%Y-%m-%d"))
			ddfin = str(self.date_fin.strftime("%Y-%m-%d"))
			val_struct = int(self.company_id)
			val_ex = int(self.x_exercice_id)
			val_dire = int(self.direction_id)
			print('la valeur est', val_dire)

			if self.emplacement == "1":

				for vals in self:
					vals.env.cr.execute("""SELECT DISTINCT (L.code_immo) AS code, (L.type_immo) AS type, (Q.lib_long) AS designation, (L.acquisition) AS valeur FROM gi_immobilisation L, gi_designation Q, gi_typeimmobilisation A, gi_ordre_entree_line LI where L.designation_id = LI.designation_id  and LI.designation_id = Q.id and LI.type_immo_id= A.id and L.code_immo != '' and L.company_id =%s and L.x_exercice_id = %s and L.date_mise_service BETWEEN %s and %s """,(val_struct,val_ex,ddbut,ddfin))
					res = vals.env.cr.dictfetchall()
					print('les données',res)
					result = []
	                
				# delete old inventaire line
				vals.inventbien_line_ids.unlink()
				for line in res:
					result.append((0, 0, {'code_immo': line['code'], 'type_immo':line['type'], 'designation':line['designation'], 'valeur':line['valeur'],'quantite':1}))
				self.inventbien_line_ids = result

			elif self.emplacement == "2":
				for vals in self:
					vals.env.cr.execute("""SELECT DISTINCT (L.code_immo) AS code, (L.type_immo) AS type, (Q.lib_long) AS designation, (L.acquisition) AS valeur FROM gi_immobilisation L, gi_designation Q, gi_typeimmobilisation A, gi_ordre_entree_line LI where L.designation_id = LI.designation_id and LI.designation_id = Q.id and LI.type_immo_id = A.id and L.code_immo != '' and L.direction_id = %s and L.company_id =%s and L.x_exercice_id = %s and  L.date_mise_service BETWEEN %s and %s """,(val_dire,val_struct,val_ex,ddbut,ddfin))
					res = vals.env.cr.dictfetchall()
					print('les données',res)
					result = []
	                
				# delete old inventaire line
				vals.inventbien_line_ids.unlink()
				for line in res:
					result.append((0, 0, {'code_immo': line['code'], 'type_immo':line['type'], 'designation':line['designation'], 'valeur':line['valeur'],'quantite':1}))
				self.inventbien_line_ids = result


			self.write({'state': 'fait'})

	

class Gi_invent_bienLine (models.Model):
	_name = "gi_invent_bien_line"

	code_immo = fields.Char(string= "Code Immobilisation", readonly= True)
	type_immo= fields.Char(string= "Type Immobilisation", readonly= True)
	designation = fields.Char(string= "Désignation", readonly= True)
	quantite = fields.Integer(string= "Quantité théorique", readonly= True)
	quant_phys= fields.Integer(string= "Quantité Physique")
	valeur= fields.Integer(string= "Valeur", readonly= True)
	observation= fields.Text(string= "Observation", size= 100)
	invent_bien_id= fields.Many2one("gi_invent_bien")



class Gi_fiche_stock (models.Model):
	_name = "gi_fiche_stock"
	_rec_name= "type_invent"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	code= fields.Integer(string= "N° Inventaire")
	ministere_id = fields.Many2one("ref_ministere", string= "Ministère", required= True)
	magasin = fields.Many2one("gi_magasin", string= "Magasin")
	date_debut= fields.Date(string= "Date debut", required= True)
	date_fin = fields.Date(string= "Date fin", default= fields.Date.context_today, required= True)
	type_invent= fields.Selection([("1", "Trimestriel"), ("2", "Semestriel"), ("3", "Inventaire tournant"), 
		("4", "Annuel")], string= "Type Inventaire", default= "1", store= True, required= True)
	emplacement = fields.Selection([('1', 'Tous les magasins'),('2', 'Par magasin')], string= "Emplacements", default='1', required=True)
	ordo_mat_id= fields.Many2one("gi_agent_mat", string= "Ordonnateur Matières", required= True)
	compta_mat_id= fields.Many2one("gi_agent_mat", string= "Comptable Matières", required= True)
	magasinier_id= fields.Many2one("gi_agent_mat", string= "Magasinier/ Fichiste", required= True)
	fich_stock_line_ids= fields.One2many("gi_fiche_stock_line", "fich_stock_id", string= " ")
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



#Generations des biens en stock en fonction d'une periode

	def fche_stock(self):
		if self.date_debut and self.date_fin:
			ddbut = str(self.date_debut.strftime("%Y-%m-%d"))
			ddfin = str(self.date_fin.strftime("%Y-%m-%d"))
			val_struct = int(self.company_id)
			val_ex = int(self.x_exercice_id)
			val_mag = str(self.magasin.id)

			if self.emplacement == '1':

				for vals in self:
					vals.env.cr.execute("""SELECT DISTINCT (B.concate_souscpte) AS imputation, (L.sous_code) AS code, (F.lib_long) AS type, (C.lib_long) AS categorie, (D.lib_long) AS designation 
					FROM gi_ordre_entree_line L, ref_souscompte B, gi_typeimmobilisation F, gi_categorie C, gi_designation D, gi_ordre_entree E 
					WHERE L.ordre_entree_id = E.id and L.designation_id = D.id and L.imp_budg_id= B.id and L.type_immo_id= F.id and L.categorie_id= C.id and E.company_id =%s and E.x_exercice_id = %s and E.date_entree BETWEEN %s and %s """,(val_struct,val_ex,ddbut,ddfin))
					res = vals.env.cr.dictfetchall()
					print('les données',res)
					result = []
	                
				# delete old inventaire line
				vals.fich_stock_line_ids.unlink()
				for line in res:
					result.append((0, 0, {'sous_code': line['code'], 'type_immo_id':line['type'], 'categorie':line['categorie'], 'designation':line['designation']}))
				self.fich_stock_line_ids = result

			elif self.emplacement == '2':
				for vals in self:
					vals.env.cr.execute("""SELECT DISTINCT (B.concate_souscpte) AS imputation, (L.sous_code) AS code, (F.lib_long) AS type, (C.lib_long) AS categorie, (D.lib_long) AS designation FROM gi_ordre_entree_line L, ref_souscompte B, gi_typeimmobilisation F, gi_categorie C, gi_designation D, gi_ordre_entree E where L.ordre_entree_id = E.id and L.designation_id = D.id and L.imp_budg_id= B.id and L.type_immo_id= F.id and L.categorie_id= C.id and E.company_id =1 and E.x_exercice_id = 1 and E.magasin_id = %s and E.company_id = %s and E.x_exercice_id = %s and  E.date_entree BETWEEN %s and %s """,(val_mag,val_struct,val_ex,ddbut,ddfin))
					res = vals.env.cr.dictfetchall()
					print('les données',res)
					result = []
	                
				# delete old inventaire line
				vals.fich_stock_line_ids.unlink()
				for line in res:
					result.append((0, 0, {'sous_code': line['code'], 'type_immo':line['type'], 'categorie':line['categorie'], 'designation':line['designation']}))
				self.fich_stock_line_ids = result



class Gi_fiche_stockLine (models.Model):
	_name = "gi_fiche_stock_line"


	fich_stock_id= fields.Many2one("gi_fiche_stock")
	type_immo= fields.Char(string= "Type immobilisation")
	sous_code= fields.Char(string= "Code budgetaire")
	categorie= fields.Char(string= "Categorie")
	designation= fields.Char(string= "Désignation")
	quant_phy = fields.Char(string = "Quantité Physique")


class Gi_fiche_invent_init (models.Model):
	_name = "gi_fiche_invent_init"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	n_ordre= fields.Char(string= "Fiche N°")
	direction_id= fields.Many2one("ref_direction", string= "Direction", required= True)
	detenteur = fields.Many2one("hr.employee", string= "Detenteur", required= True)
	state = fields.Selection([('1', 'Brouillon'),('2', 'Exporter')], string= "Etat", default='1')
	fich_inven_ids= fields.One2many("gi_fiche_invent_init_line", "fich_inven_id", string= " " )
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))


	@api.multi
	def insert(self):
		for rec in self.fich_inven_ids:

			val_code= str(rec.code_immo)
			val_design= int(rec.designation)
			val_marque= int(rec.marque)
			val_amor= int(rec.typ_amort)
			val_date_ac= str(rec.date_acquisition)
			val_date_m= str(rec.date_mise_service)
			val_minis= int(rec.ministere)
			val_epe= int(rec.epe)
			val_direct= int(rec.direction_id)
			val_reg= int(rec.region)
			val_prov= int(rec.province)
			val_depa= int(rec.departement)
			val_user= int(rec.user)
			val_valeur= int(rec.val_acqu)
			val_ex= int(rec.x_exercice_id)
			val_struct= int(rec.company_id)

			self.env.cr.execute("""INSERT INTO gi_immobilisation (code_immo, designation_id, marque_id,amort_id,dateacquisition, date_mise_service, ministere_id,epe_id, direction_id, region_id, province_id, departement_id, utilisateur_id, acquisition, x_exercice_id, company_id) 
			VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""" ,(val_code,val_design, val_marque, val_amor, val_date_ac, val_date_m, val_minis, val_epe, val_direct, val_reg, val_prov, val_depa, val_user, val_valeur,val_ex, val_struct))

			self.write({'state': '2'})




class Gi_fiche_invent_initLine (models.Model):
	_name = "gi_fiche_invent_init_line"

	code_immo= fields.Char(string= "Code immobilisation")
	designation = fields.Many2one("gi_designation", string= "Désignation")
	marque = fields.Many2one("gi_marque", string= "Marque")
	typ_amort= fields.Many2one("gi_typeamortissement", string= "Type amortissement")
	date_acquisition= fields.Date(string= "Date d'acquisition")
	date_mise_service= fields.Date(string= "Date mise en service", required= True)
	ministere= fields.Many2one("ref_ministere", string= "Ministère", required= True)
	epe= fields.Many2one("res.company", string= "Structure", required= True)
	direction_id= fields.Many2one("ref_direction", string= "Direction", required= True)
	region= fields.Many2one("ref_region", string= "Region", required= True)
	province= fields.Many2one("ref_province", string= "Province",required= True)
	departement= fields.Many2one("ref_departement", string= "Departement",required= True)
	user= fields.Many2one("hr.employee", string= "Employee")
	val_acqu= fields.Integer(string= "Valeur acquisition")
	fich_inven_id= fields.Many2one("gi_fiche_invent_init")
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))




class Gi_fiche_service (models.Model):
	_name = "gi_fiche_service"
	_rec_name= "type_invent"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	code= fields.Integer(srting= "N° Inventaire")
	ministere_id = fields.Many2one("ref_ministere", string= "Ministère", required= True)
	direction_id = fields.Many2one("ref_direction", string= "Direction")
	date_debut= fields.Date(string= "Date debut",  required= True)
	date_fin = fields.Date(string= "Date fin", default= fields.Date.context_today, required= True)
	type_invent= fields.Selection([("trimestre", "Trimestriel"), ("semestre", "Semestriel"), ("tournant", "Inventaire tournant"), 
		("annuel", "Annuel")], string= "Type Inventaire", default= "tournant", store= True, required= True)
	emplacement = fields.Selection([('1', 'Toutes les directions'),('2', 'Par direction')], string= "Emplacements", default='1', required=True)
	ordo_mat_id= fields.Many2one("gi_agent_mat", string= "Ordonnateur Matières", required= True)
	compta_mat_id= fields.Many2one("gi_agent_mat", string= "Comptable Matières", required= True)
	magasinier_id= fields.Many2one("gi_agent_mat", string= "Magasinier/ Fichiste", required= True)
	stock_line_ids= fields.One2many("gi_fiche_service_line", "stock_id", string= " ")
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))


	def fchservice(self):
		if self.date_debut and self.date_fin:

			ddbut = str(self.date_debut.strftime("%Y-%m-%d"))
			ddfin = str(self.date_fin.strftime("%Y-%m-%d"))
			val_struct = int(self.company_id)
			val_ex = int(self.x_exercice_id)
			val_dire = int(self.direction_id)

			if self.emplacement == "1":

				for vals in self:
					vals.env.cr.execute("""SELECT DISTINCT (L.code_immo) AS code, (L.type_immo) AS type, (Q.lib_long) AS designation FROM gi_immobilisation L, gi_designation Q, gi_typeimmobilisation A, gi_ordre_entree_line LI where L.designation_id = LI.designation_id and LI.designation_id = Q.id and LI.type_immo_id = A.id and L.code_immo != '' and L.company_id =%s and L.x_exercice_id = %s and  L.date_mise_service BETWEEN %s and %s """,(val_struct,val_ex,ddbut,ddfin))
					res = vals.env.cr.dictfetchall()
					print('les données',res)
					result = []
	                
				# delete old inventaire line
				vals.stock_line_ids.unlink()
				for line in res:
					result.append((0, 0, {'code': line['code'], 'type_immo':line['type'], 'designation':line['designation']}))
				self.stock_line_ids = result

			elif self.emplacement == "2":

				for vals in self:
					vals.env.cr.execute("""SELECT DISTINCT (L.code_immo) AS code, (L.type_immo) AS type, (Q.lib_long) AS designation FROM gi_immobilisation L, gi_designation Q, gi_typeimmobilisation A, gi_ordre_entree_line LI where L.designation_id = LI.designation_id and LI.designation_id = Q.id and LI.type_immo_id = A.id and L.code_immo != '' and L.direction_id = %s and L.company_id =%s and L.x_exercice_id = %s and  L.date_mise_service BETWEEN %s and %s """,(val_dire,val_struct,val_ex,ddbut,ddfin))
					res = vals.env.cr.dictfetchall()
					print('les données',res)
					result = []
	                
				# delete old inventaire line
				vals.stock_line_ids.unlink()
				for line in res:
					result.append((0, 0, {'code': line['code'], 'type_immo':line['type'], 'designation':line['designation']}))
				self.stock_line_ids = result


class Gi_fiche_serviceLine (models.Model):
	_name = "gi_fiche_service_line"

	stock_id= fields.Many2one("gi_fiche_service")
	type_immo= fields.Char(string= "Type immobilisation")
	code= fields.Char(string= "code")
	designation= fields.Char(string= "Désignation")
	quant_phy = fields.Char(string = "Quantité Physique")



class Gi_journal_entree (models.Model):
	_name = "gi_journal_entree"
	_rec_name= "date_fin"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	direction_id= fields.Many2one("ref_direction", string= "Direction")
	date_debut = fields.Date(string= "Date debut", required= True)
	date_fin = fields.Date(string = "Date fin", required= True)
	state= fields.Selection([("1", "Brouillon"), ("2", "Confirmer")], default= "1", copy= False)
	mnt_total= fields.Integer(string= "Montant total")
	jr_entree_line_ids= fields.One2many("gi_journal_entree_line", "jr_entree_id", string= "")
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))


#Fonction de génération du journal des entrées des immobilisations

	def j_entree(self):
		if self.date_debut and self.date_fin:

			ddbut = str(self.date_debut.strftime("%Y-%m-%d"))
			ddfin = str(self.date_fin.strftime("%Y-%m-%d"))
			val_struct = int(self.company_id)
			val_ex = int(self.x_exercice_id)
			id_entree= self.id

			for vals in self:
				vals.env.cr.execute("""SELECT DISTINCT (E.sous_code) As code, (F.n_mvt) As ordre, (F.date_entree) AS dates, (B.lib_long) AS typeimmo, (C.lib_long) AS categorie, (D.lib_long) AS designation, (E.quant) AS quantite, (E.val_unit) AS prix, (E.montant) AS montant 
				FROM gi_typeimmobilisation B, gi_categorie C, gi_designation D, ca_recommandation_line H, gi_ordre_entree_line E, gi_ordre_entree F
				WHERE E.ordre_entree_id= F.id and E.type_immo_id= B.id and E.categorie_id= C.id and E.designation_id= D.id and F.date_entree BETWEEN %s and %s and F.company_id =%s and F.x_exercice_id = %s""",(ddbut,ddfin,val_struct,val_ex))
				res = vals.env.cr.dictfetchall()

			result = []
	                
			vals.jr_entree_line_ids.unlink()
			for line in res:
				result.append((0, 0, {'sous_code': line['code'], 'n_ordre': line['ordre'], 'date_entree': line['dates'], 'type_immo': line['typeimmo'], 'categorie':line['categorie'], 'designation':line['designation'], 'quant':line['quantite'], 'val_unit':line['prix'], 'montant':line['montant']}))
			self.jr_entree_line_ids = result

		self.env.cr.execute("""SELECT sum(montant)
		FROM gi_journal_entree_line 
		WHERE x_exercice_id = %d AND company_id = %d AND jr_entree_id = %d """ %(val_ex, val_struct, id_entree))
		res = self.env.cr.fetchone() or 0

		self.mnt_total = res and res[0]

		self.write({'state': '2'})



class Gi_journal_entreeLine (models.Model):
	_name = "gi_journal_entree_line"

	jr_entree_id= fields.Many2one("gi_journal_entree")
	sous_code= fields.Char(string= "Sous code")
	n_ordre= fields.Char(string= "N° d'ordre")
	date_entree= fields.Char(string= "Date")
	type_immo= fields.Char(string= "Type immobilisation")
	categorie= fields.Char(string= "Categorie")
	designation= fields.Char(string= "Désignation")
	quant = fields.Integer(string = "Quantité")
	val_unit = fields.Integer(string = "Prix unitaire")
	montant = fields.Integer(string = "Total")
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



class Gi_journal_sortie (models.Model):
	_name = "gi_journal_sortie"
	_rec_name= "date_fin"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	date_debut = fields.Date(string= "Date debut", required= True)
	date_fin = fields.Date(string = "Date fin", required= True)
	direction_id = fields.Many2one("ref_direction", string = "Direction", required= True)
	state= fields.Selection([("1", "Brouillon"), ("2", "Confirmer")], default= "1", copy= False)
	mnt_total= fields.Integer(string= "Montant total")
	jr_sortie_line_ids= fields.One2many("gi_journal_sortie_line", "jr_sortie_id", string= "")
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))


	def j_sortie(self):
		if self.date_debut and self.date_fin:

			ddbut = str(self.date_debut.strftime("%Y-%m-%d"))
			ddfin = str(self.date_fin.strftime("%Y-%m-%d"))
			val_struct = int(self.company_id)
			val_ex = int(self.x_exercice_id)
			id_sortie= self.id

			for vals in self:
				vals.env.cr.execute("""SELECT DISTINCT (L.code_immo) AS code,(L.type_immo) AS typ,(L.categorie_id) AS categorie,(C.lib_long) AS designation, (L.acquisition) AS acquis, (E.date_sortie) AS dates 
				FROM gi_immobilisation L, gi_designation C, gi_ordre_sortie_line B, gi_ordre_sortie E
				WHERE B.ordre_sortie_line_id = E.id and B.code= L.id and L.designation_id= C.id and E.date_sortie BETWEEN %s and %s and E.company_id =%s and E.x_exercice_id = %s""",(ddbut,ddfin,val_struct,val_ex))
				res = vals.env.cr.dictfetchall()

			result = []
	                
			vals.jr_sortie_line_ids.unlink()
			for line in res:
				result.append((0, 0, {'date_mise_service': line['dates'], 'code_immo': line['code'], 'type_immo': line['typ'], 'categorie': line['categorie'], 'categorie':line['categorie'], 'designation':line['designation'], 'montant':line['acquis']}))
			self.jr_sortie_line_ids = result

		self.env.cr.execute("""SELECT sum(montant)
		FROM gi_journal_sortie_line WHERE x_exercice_id = %d AND company_id = %d AND jr_sortie_id = %d """ %(val_ex, val_struct, id_sortie))
		res = self.env.cr.fetchone() or 0

		self.mnt_total = res and res[0]

		self.write({'state': '2'})



class Gi_journal_sortieLine (models.Model):
	_name = "gi_journal_sortie_line"

	jr_sortie_id= fields.Many2one("gi_journal_entree")
	code_immo = fields.Char(string = "Code immobilisation")
	date_mise_service = fields.Date(string = "Date mise en service")
	type_immo= fields.Char(string= "Type immobilisation")
	categorie= fields.Char(string= "Categorie")
	designation= fields.Char(string= "Désignation")
	montant = fields.Integer(string = "Montant")
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



class Gi_ordre_sortie (models.Model):
	_name = "gi_ordre_sortie"
	_rec_name= "date_sortie"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	direction_id = fields.Many2one("ref_direction", string= "Direction")
	date_sortie = fields.Date(string = "Date de l'opération", required= True)
	ordre_sortie_line_ids= fields.One2many("gi_ordre_sortie_line", "ordre_sortie_line_id", string= "")
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



class Gi_ordre_sortieLine (models.Model):
	_name = "gi_ordre_sortie_line"
	_rec_name= "code"

	code= fields.Many2one("gi_immobilisation", string= "Code immobilisation")
	code_ref= fields.Char()
	date_entree= fields.Char(string= "Date mise en service", readonly= True)
	type_immo= fields.Char(string= "Type immobilisation", readonly= True)
	categorie= fields.Char(string= "Categorie", readonly= True)
	designation= fields.Char(string= "Désignation", readonly= True)
	direction= fields.Char(string= "Direction", readonly= True)
	user= fields.Char(string= "Utilisateur", readonly= True)
	quant = fields.Integer(string = "Quantité", readonly= True)
	val_unit = fields.Integer(string = "Prix unitaire", readonly= True)
	montant = fields.Integer(string = "Total", readonly= True)
	ordre_sortie_line_id= fields.Many2one("gi_ordre_sortie")
	sort_id= fields.Many2one("gi_transfert")
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))




	@api.onchange("code")
	def sort(self):

		self.n_ordre= self.code.n_ordre
		self.type_immo= self.code.type_immo
		self.designation= self.code.designation_id.lib_long
		self.date_entree= self.code.date_mise_service
		self.categorie= self.code.categorie_id
		self.quant= self.code.quant
		self.val_unit= self.code.acquisition
		self.montant= self.code.acquisition
		self.direction= self.code.direction_id.libcourt
		self.user= self.code.utilisateur_id.name

	_sql_constraints= [('code_uniq', 'unique (code)', "Veuillez vérifier la liste des biens à faire sortir, certains sont déjà sortis")]

	


class Gi_livre_journal (models.Model):
	_name = "gi_livre_journal"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	direction_id= fields.Many2one("ref_direction", string= "Direction")
	mnt_total_1= fields.Integer(string= "Total1")
	mnt_total_2= fields.Integer(string= "Total2")
	mnt_total= fields.Integer(string= "Montant total")
	state= fields.Selection([("1", "Brouillon"), ("2", "Confirmer")], default= "1", copy= False)
	lv_jr_entree_ids= fields.One2many("gi_livre_jour_en_line", "lv_jr_entree_id", string= " ")
	lv_jr_sortie_ids= fields.One2many("gi_livre_jour_so_line", "lv_jr_sortie_id", string= " ")
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))


	@api.multi
	def livre_journal(self):

		val_struct = int(self.company_id)
		val_ex = int(self.x_exercice_id)
		id_entree= self.id
		id_sortie= self.id

		for vals in self:
			vals.env.cr.execute("""SELECT DISTINCT (E.sous_code) As code, (F.n_mvt) As ordre, (F.date_entree) AS dates, (B.lib_long) AS typeimmo, (C.lib_long) AS categorie, (D.lib_long) AS designation, (E.quant) AS quantite, (E.val_unit) AS prix, (E.montant) AS montant 
			FROM gi_typeimmobilisation B, gi_categorie C, gi_designation D, ca_recommandation_line H, gi_ordre_entree_line E, gi_ordre_entree F
			WHERE E.ordre_entree_id= F.id and E.type_immo_id= B.id and E.categorie_id= C.id and E.designation_id= D.id and F.company_id =%s and F.x_exercice_id = %s""",(val_struct,val_ex))
			res = vals.env.cr.dictfetchall()

		result = []
                
		vals.lv_jr_entree_ids.unlink()
		for line in res:
			result.append((0, 0, {'sous_code': line['code'], 'n_ordre': line['ordre'], 'date_entree': line['dates'], 'type_immo': line['typeimmo'], 'categorie':line['categorie'], 'designation':line['designation'], 'quant':line['quantite'], 'val_unit':line['prix'], 'montant':line['montant']}))
		self.lv_jr_entree_ids = result

		self.env.cr.execute("""SELECT sum(montant)
		FROM gi_livre_jour_en_line WHERE x_exercice_id = %d AND company_id = %d AND lv_jr_entree_id = %d """ %(val_ex, val_struct, id_entree))
		res = self.env.cr.fetchone() or 0

		self.mnt_total_1 = res and res[0]

		for vals in self:
			vals.env.cr.execute("""SELECT DISTINCT (L.code_immo) AS code,(L.type_immo) AS typ,(L.categorie_id) AS categorie,(C.lib_long) AS designation, (L.acquisition) AS acquis, (E.date_sortie) AS dates 
			FROM gi_immobilisation L, gi_designation C, gi_ordre_sortie_line B, gi_ordre_sortie E
			WHERE B.ordre_sortie_line_id = E.id and B.code= L.id and L.designation_id= C.id and E.company_id =%s and E.x_exercice_id = %s""",(val_struct,val_ex))
			res = vals.env.cr.dictfetchall()

		result = []
                
		vals.lv_jr_sortie_ids.unlink()
		for line in res:
			result.append((0, 0, {'date_mise_service': line['dates'], 'code_immo': line['code'], 'type_immo': line['typ'], 'categorie': line['categorie'], 'categorie':line['categorie'], 'designation':line['designation'], 'montant':line['acquis']}))
		self.lv_jr_sortie_ids = result

		self.env.cr.execute("""SELECT sum(montant)
		FROM gi_livre_jour_so_line WHERE x_exercice_id = %d AND company_id = %d AND lv_jr_sortie_id = %d """ %(val_ex, val_struct, id_sortie))
		res = self.env.cr.fetchone() or 0

		self.mnt_total_2 = res and res[0]

		self.mnt_total = self.mnt_total_1 + self.mnt_total_2

		self.write({'state': '2'})



class Gi_livre_jour_enLine (models.Model):
	_name = "gi_livre_jour_en_line"

	lv_jr_entree_id= fields.Many2one("gi_livre_journal")
	sous_code= fields.Char(string= "Sous code")
	n_ordre= fields.Char(string= "N° d'ordre")
	date_entree= fields.Char(string= "Date")
	type_immo= fields.Char(string= "Type immobilisation")
	categorie= fields.Char(string= "Categorie")
	designation= fields.Char(string= "Désignation")
	quant = fields.Integer(string = "Quantité")
	val_unit = fields.Integer(string = "Prix unitaire")
	montant = fields.Integer(string = "Total")
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))



class Gi_livre_jour_soLine (models.Model):
	_name = "gi_livre_jour_so_line"

	lv_jr_sortie_id= fields.Many2one("gi_livre_journal")
	code_immo = fields.Char(string = "Code immobilisation")
	date_mise_service = fields.Date(string = "Date mise en service")
	type_immo= fields.Char(string= "Type immobilisation")
	categorie= fields.Char(string= "Categorie")
	designation= fields.Char(string= "Désignation")
	montant = fields.Integer(string = "Montant")
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=',1)]))

