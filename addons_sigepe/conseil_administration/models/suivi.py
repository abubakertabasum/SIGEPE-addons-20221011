from odoo import fields,api,models
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError



class Ca_convocation(models.Model):
	_name ="ca_convocation"
	_inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
	_description = "Convocation"
	_rec_name= "session_id"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	name = fields.Char(string = "Objet", size=100)
	cat_id=fields.Many2one("ca_type_session", string ="Session", required=True)
	session_id=fields.Many2one("ca_nature_session", string ="Nature de la session", required=True)
	heure_debut = fields.Char(string = "Date debut", readonly= True)
	heure_fin = fields.Char(string = "Date fin", readonly= True)
	state = fields.Selection([
        ('brouillon', 'Brouillon'),
        ('envoyer', 'Envoyer'),
    ],  string='Status', readonly=True, copy=False, store=True, default='brouillon', track_visibility='onchange')
	lieu = fields.Char(string="Lieu", readonly = True)
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)

#Fonction d'envoi de mail (Les références ont été crées dans le repertoire data du module)

	@api.multi
	def action_envoyer_mail(self):
		self.ensure_one()
		ir_model_data = self.env['ir.model.data']
		try:
			template_id = ir_model_data.get_object_reference('conseil_administration', 'email_template_edi_convocation')[1]
		except ValueError:
			template_id = False
		try:
			compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
		except ValueError:
			compose_form_id = False
		ctx={
			'default_model': 'ca_convocation',
			'default_res_id': self.ids[0],
			'default_use_template': bool(template_id),
			'default_use_template': bool(template_id),
			'default_template_id': template_id,
			'default_composition_mode': 'comment',
			'mark_so_as_envoyer': True,
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


	@api.multi
	@api.returns('mail.message', lambda value: value.id)
	def message_post(self, **kwargs):
		if self.env.context.get('mark_so_as_envoyer'):
			self.filtered(lambda o: o.state == 'brouillon').with_context(tracking_disable=True).write({'state': 'envoyer'})
		return super(Ca_convocation, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)



	@api.onchange("session_id")
	def pres(self):
		self.heure_debut=self.session_id.date_prevue
		self.heure_fin=self.session_id.date_fin
		self.lieu=self.session_id.lieu


class Ca_conseil(models.Model):
	_name ="ca_conseil"
	_rec_name="intitule"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	n_ordre= fields.Char(string = "N° d'ordre")
	intitule = fields.Many2one("ca_nature_session", "Intitulé du conseil", required=True, domain=[('state','=','2')])
	cat_id = fields.Many2one("ca_type_session", string="Type de Session", readonly= True)
	session_id = fields.Many2one("ca_nature_de_session", string ="Nature de la session", readonly= True)
	heure_debut = fields.Date(string = " Date de debut prévue", readonly= True)
	heure_fin = fields.Date(string= "Date de fin Prévue", readonly= True)
	lieu = fields.Char(string="Lieu", readonly= True)
	date_reelle_debut = fields.Datetime(string = " Date de debut réelle", required= True)
	date_reelle = fields.Datetime(string = "Date de fin réelle",required=True)
	observation = fields.Text(string= "Observation", size=100)
	conseiladmin_ids = fields.One2many("ca_conseil_line_jj", "conseil_id", string="Ajout participants")
	ordre_id = fields.Many2one("ca_ordre_jour", string="Ajout ordre du jour")	
	ordre_ids = fields.One2many("ca_ordre_jour_acte_jj", "conseil_id", readonly=True)
	state= fields.Selection([('brouillon','Brouillon'),("cours", "En cours"),("fait", "Fait"),
		],string='Etat', store=True, required= True, default='brouillon', track_visibility='onchange')
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)


	@api.onchange("intitule")
	def heur(self):
		self.heure_debut=self.intitule.date_prevue
		self.heure_fin= self.intitule.date_fin
		self.lieu= self.intitule.lieu
		self.session_id = self.intitule.lib_long
		self.cat_id = self.intitule.cat_id
	
	@api.multi
	def confirm(self):

		self.MajPrepa()			
		self.write({'state': 'cours'})
		
	
	def MajPrepa(self):
		v_id = int(self.intitule)
		v_struct = int(self.company_id)
		
		self.env.cr.execute("UPDATE ca_nature_session SET state = 'fait' WHERE id = %d and company_id = %d" %(v_id, v_struct))
	
	
	def Insertion(self):
		v_id = int(self.intitule)
		v_struct = int(self.company_id)
		
		for vals in self:
			vals.env.cr.execute("""select l.membre_id as nom, l.fonction_id as fonc, l.structure_id as struct
			from ca_conseil_line l, ca_nature_session n WHERE n.id = l.sessionline_id and n.id = %d and company_id = %d""" %(v_id, v_struct))
			
			rows = vals.env.cr.dictfetchall()
			result = []
			
			vals.conseiladmin_ids.unlink()
			for line in rows:
				result.append((0,0, {'membre_id' : line['nom'],'fonction_id' : line['fonc'],'structure_id' : line['struct']}))
			self.conseiladmin_ids = result
		
		for vals in self:
			vals.env.cr.execute("""select l.ordre_jour as ordre, l.acte as act, l.ref as refe
			from ca_ordre_jour_acte l, ca_nature_session n WHERE n.id = l.nature_id and n.id = %d and company_id = %d""" %(v_id, v_struct))
			
			rows = vals.env.cr.dictfetchall()
			result = []
			
			vals.ordre_ids.unlink()
			for line in rows:
				result.append((0,0, {'ordre_jour' : line['ordre'],'ref' : line['refe'],'acte' : line['act']}))
			self.ordre_ids = result


class CaOrdreJourActeJj(models.Model):
	_name = "ca_ordre_jour_acte_jj"
	
	conseil_id = fields.Many2one("ca_conseil", ondelete="cascade")
	ordre_jour = fields.Many2one("ca_ordre_jour", "Ordre du jour", readonly=True)
	ref = fields.Char("Réf. acte", readonly=True)
	acte = fields.Binary(string= "Joindre l'acte de délibération", attachment=False)


class Ca_conseilLineJj(models.Model):
	_name ="ca_conseil_line_jj"
	conseil_id = fields.Many2one("ca_conseil", string="Conseil")
	membre_id = fields.Many2one("ca_membre", string= "Nom & Prénom", readonly=True)
	fonction_id= fields.Many2one("ca_type_membre", string= "Fonction", readonly=True)
	structure_id= fields.Many2one("ca_cat_representant", string="Structure Représentée", readonly=True)
	etat = fields.Selection([("present", "Présent"), ("absent", "Absent"),("procuration","Procuration"),], 
		string= "Statut", default= "present", required= True)
	signature = fields.Char(string= "Signature")
	observation= fields.Text(string= "Observation") 
	procuration= fields.Binary(string= "Procuration", attachment= True)

	

class Ca_compt_conseil (models.Model):
	
	_name = "ca_compt_conseil"
	
	x_exercice_id = fields.Many2one("ref_exercice", default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]), string="Exercice")
	company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
	n_compt = fields.Integer()


class Ca_conseilLine(models.Model):
	_name ="ca_conseil_line"
	conseil_id = fields.Many2one("ca_conseil", string="Conseil")
	sessionline_id = fields.Many2one("ca_nature_session", ondelete='cascade')
	membre_id = fields.Many2one("ca_membre", string= "Nom & Prénom", required=True)
	fonction_id= fields.Many2one("ca_type_membre", string= "Fonction", readonly=True)
	structure_id= fields.Many2one("ca_cat_representant", string="Structure Représentée", readonly=True)
	etat = fields.Selection([("present", "Présent"), ("absent", "Absent"),("procuration","Procuration"),], 
		string= "Statut", default= "present", required= False)
	signature = fields.Char(string= "Signature")
	observation= fields.Text(string= "Observation") 
	procuration= fields.Binary(string= "Procuration", attachment= True)
	
	

	@api.onchange("membre_id")
	def fonc(self):
		self.fonction_id=self.membre_id.typemembre_id
		self.structure_id=self.membre_id.structure_id


class Ca_postconseil(models.Model):
	_name ="ca_postconseil"
	_rec_name= "session_id"
	_inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
	_description = "Postconseil"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	intitule = fields.Many2one("ca_conseil", "Intitulé", required=True, domain=[('state','=','cours')])
	cat_id = fields.Many2one ("ca_type_session", string= "Type de session", readonly=True)
	session_id = fields.Many2one("ca_nature_de_session", string= "Nature de session", readonly=True)
	date= fields.Date(string= "Date d'envoi", default=date.today(), readonly=True)
	doc_ids= fields.One2many("ca_document_postconseil", "session_delibe_id", string="Documents session")
	state_postconseil = fields.Selection([
        ('draft', 'Brouillon'),
        ('sent', 'Envoyer'),
    ], string='Status', readonly=True, copy=False, store=True, default='draft', track_visibility='onchange')
	delib_ids = fields.One2many("ca_acte_deliberation", "session_delibe_id", string= "Acte de déliberation")
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)



# Fonction d'envoie de Mail (Les références ont été crées dans le repertoire data du module)

	@api.multi
	def action_send_mail(self):
		self.ensure_one()
		ir_model_data = self.env['ir.model.data']
		try:
			template_id = ir_model_data.get_object_reference('conseil_administration', 'email_template_edi_postconseil')[1]
		except ValueError:
			template_id = False
		try:
			compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
		except ValueError:
			compose_form_id = False
		ctx={
			'default_model': 'ca_postconseil',
			'default_res_id': self.ids[0],
			'default_use_template': bool(template_id),
			'default_use_template': bool(template_id),
			'default_template_id': template_id,
			'default_composition_mode': 'comment',
			'mark_so_as_envoyer': True,
			'convocation': self.env.context.get('convocation', False),
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

#Fonction de changement d"etat après avoir cliquer sur envoyer mail

	@api.multi
	@api.returns('mail.message', lambda value: value.id)
	def message_post(self, **kwargs):
		if self.env.context.get('mark_so_as_envoyer'):
			self.filtered(lambda o: o.state_postconseil == 'draft').with_context(tracking_disable=True).write({'state_postconseil': 'sent'})
		return super(Ca_postconseil, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)
		self.MajConseil()

	
	def MajConseil(self):
		v_id = int(self.intitule)
		v_struct = int(self.company_id)
		
		self.env.cr.execute("UPDATE ca_conseil SET state = 'fait where id = %d and comapny_id = %d " %(v_id, v_struct))
	
	@api.onchange("intitule")
	def Sess(self):
		
		self.cat_id = self.intitule.cat_id
		self.session_id = self.intitule.session_id
	

class Ca_acte_deliberation (models.Model):
    _name= "ca_acte_deliberation"
    
    session_delibe_id = fields.Many2one("ca_postconseil", ondelete='cascade')
    lib_long= fields.Char(string= "Intitulé de l'acte", required = True, size=100)
    refe= fields.Char(string= "Référence de l'acte", required = True, size=100)
    join_doc = fields.Binary(string= "Acte de déliberation", required = True, attachment=False)
    company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)

class CaDocPost(models.Model):
    _name= "ca_document_postconseil"
    
    session_delibe_id = fields.Many2one("ca_postconseil", ondelete='cascade')
    lib_long= fields.Char(string= "Intitulé du document", required = True, size=100)
    join_doc = fields.Binary(string= "Document", required = True, attachment=False)
    company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)



class Ca_Sejour_Pca (models.Model):
    _name= "ca_sejour_pca"
    _rec_name= "date_debut"
    _order = 'sequence, id'

    sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
    date_debut= fields.Date(string= "Date debut", required= True, state= {2: [('readonly',True)]})
    date_fin= fields.Date(string= "Date fin", required= True)
    nom_pca= fields.Many2one("ca_administrateur", string= "Nom du PCA", required= True)
    observation= fields.Text(string= "Observation")
    piece_jointe= fields.Binary(string= "Rapport", attachment= True)
    state = fields.Selection([
        ('1', 'Brouillon'),
        ('2', 'S1 Valider'),
        ('3', 'S2 Valider')
    ],  string='Status', readonly=True, copy=False, store=True, default='1', track_visibility='onchange')
    date_deb= fields.Date(string= "Date debut")
    date_fi= fields.Date(string= "Date fin")
    pca= fields.Many2one("ca_administrateur", string= "Nom du PCA")
    piece_join= fields.Binary(string= "Rapport", attachment= True)
    company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)


    @api.onchange("date_fin")
    def ctrl(self):
    	for scheduler in self:
    		if scheduler.date_fin < scheduler.date_debut:
    			raise ValidationError(("La date de fin prévue doit être superieure à la date de debut."))



    @api.onchange("date_fi")
    def ctrl(self):
    	for scheduler in self:
    		if scheduler.date_fi < scheduler.date_deb:
    			raise ValidationError(("La date de fin prévue doit être superieure à la date de debut."))


    @api.multi
    def action(self):
    	for scheduler in self:
    		if scheduler.date_fin < scheduler.date_debut:
    			raise ValidationError(("La date de fin prévue doit être superieure à la date de debut."))
    	self.write({'state': '2'})


    @api.multi
    def action_conf(self):
    	for scheduler in self:
    		if scheduler.date_fi < scheduler.date_deb:
    			raise ValidationError(("La date de fin prévue doit être superieure à la date de debut."))

    	self.write({'state': '3'})


class Ca_Sejour_permanent (models.Model):
    _name= "ca_sejour_permanent"
    _rec_name= "date_debut"
    _order = 'sequence, id'

    sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
    date_debut= fields.Date(string= "Date debut", required= True)
    date_fin= fields.Date(string= "Date fin", required= True)
    nom_pca= fields.Many2one("ca_administrateur", string= "Nom du PCA", required= True)
    observation= fields.Text(string= "Observation")
    piece_jointe= fields.Binary(string= "Rapport", attachment= True)
    company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)


    @api.onchange("date_fin")
    def action_ctrl(self):
    	for scheduler in self:
    		if scheduler.date_fin < scheduler.date_debut:
    			raise ValidationError(("La date de fin doit être superieure à la date de debut."))



class Ca_type_session (models.Model):
    _name= "ca_type_session"
    _rec_name= "lib_court"
    _order = 'sequence, id'

    sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
    lib_court= fields.Char(string= "Libelle court", required = True, size=35)
    lib_long= fields.Char(string= "Libelle long", required = True, size=65)
    company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)



class Ca_consult_domicile (models.Model):
    _name= "ca_consult_domicile"
    _rec_name= "lib_long"
    _order = 'sequence, id'

    sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
    lib_court= fields.Char(string= "Libelle court", required = False, size=35)
    lib_long= fields.Text(string= "Objet", required = True, size=65)
    date_entree= fields.Date(string= "Date de début", required= True)
    date_fin = fields.Date(string= "Date de fin", required= True)
    cat_id = fields.Many2one("ca_type_session","Type de session", required=True)
    session_id = fields.Many2one("ca_nature_de_session","Nature de session", required=True)
    active= fields.Boolean('Actif', default= True)
    company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
    doc_ids = fields.One2many("ca_document_dom","domicile_id")

    @api.onchange("date_fin")
    def ctrl(self):
    	for scheduler in self:
    		if scheduler.date_fin < scheduler.date_entree:
    			raise ValidationError(("La date de fin prévue doit être superieure à la date de debut."))
    

class CaDocumentDom(models.Model):
	_name = "ca_document_dom"
	
	domicile_id = fields.Many2one("ca_consult_domicile", ondelete='cascade')
	libelle = fields.Char(string="Libellé du document", required=True)
	docu_id = fields.Binary(string= "Joindre le document", attachment= False)
	


class Ca_rec_objet (models.Model):
    _name= "ca_rec_objet"
    _rec_name= "lib_long"
    _order = 'sequence, id'

    sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
    lib_court= fields.Char(string= "Libelle court", required = True, size=35)
    lib_long= fields.Char(string= "Libelle long", required = True, size=65)
    active= fields.Boolean('Actif', default= True)
    company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)



class Ca_nature_session (models.Model):
	_name= "ca_nature_session"
	_rec_name= "intitule"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	n_ordre = fields.Char(string= "N° d'ordre", readonly= True)
	intitule = fields.Char(string= "Intitulé", required = True)
	lib_long = fields.Many2one("ca_nature_de_session",string= "Nature de la session", required = True)
	cat_id = fields.Many2one("ca_type_session", string= "Type de session", required = True)
	date_prevue = fields.Date(string = "Date de début prevue", required = True)
	date_fin = fields.Date(string = "Date de fin prevue", required = True)
	action= fields.Many2one("ir.cron", string= "Alerte")
	state= fields.Selection([("1", "brouillon"),("2", "Confirmer"), ("fait","Fait")], string="Etat",required=True, default="1") 
	ordres_ids = fields.One2many("ca_ordre_jour_acte", "nature_id")
	doc_ids = fields.One2many("ca_document", "nature_id")
	lieu = fields.Char(string= "Lieu", required = True)
	line_ids= fields.One2many("ca_conseil_line", "sessionline_id")
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)

    
	def confirm(self):
	
		for x in self:
			if x.date_fin < x.date_prevue:
				raise ValidationError(("La date de fin prévue doit être superieure à la date prévue."))
		self.write({'state': '2'})
    
	def afficher_piece(self):
		
		val_struct = int(self.company_id)
		v_id = int(self.lib_long)
	
		for vals in self:
			vals.env.cr.execute("select l.doc_id as doc from ca_parametre_line l, ca_parametre_nature n where n.id = l.parametre_id and n.nature_id = %d and n.company_id = %d" %(v_id, val_struct))
	
			rows = vals.env.cr.dictfetchall()
			result = []
	
			vals.doc_ids.unlink()
			for line in rows:
				result.append((0,0, {'doc_id' : line['doc']}))
			self.doc_ids = result
	

class CaOrdreJourActe(models.Model):
	_name = "ca_ordre_jour_acte"
	
	nature_id = fields.Many2one("ca_nature_session", ondelete="cascade")
	ordre_jour = fields.Many2one("ca_ordre_jour", "Ordre du jour", required=True)
	ref = fields.Char("Réf. acte", required=True)
	acte = fields.Binary(string= "Joindre l'acte de délibération", attachment=False)


class CaDocument(models.Model):
	_name = "ca_document"
	
	nature_id = fields.Many2one("ca_nature_session", ondelete="cascade")
	doc_id = fields.Many2one("ca_type_doc", "Intitulé du document", readonly=True)
	doc = fields.Binary(string= "Joindre document", attachment=False)
	


class Ca_compt_nature (models.Model):
	
	_name = "ca_compt_nature"
	
	x_exercice_id = fields.Many2one("ref_exercice", default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]), string="Exercice")
	company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
	n_compt = fields.Integer()
	categorie_id = fields.Char()



class Ca_type_membre (models.Model):
    _name= "ca_type_membre"
    _rec_name= "lib_court"
    _order = 'sequence, id'

    sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
    lib_court= fields.Char(string= "Libelle court", required = True, size=35)
    lib_long= fields.Char(string= "Libelle long", required = True, size=65)
    company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)



class Ca_type_doc (models.Model):
    _name= "ca_type_doc"
    _rec_name="lib_long"
    _order = 'sequence, id'

    sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
    session_id = fields.Many2one("ca_nature_session", string= "Nature de session", required=False)
    lib_court= fields.Char(string= "Libelle court", required = False, size=35)
    lib_long= fields.Char(string= "Libelle long", required = True, size=100)
    nat_doc_ids = fields.Many2many("ca_nature_session", "ca_doc_nat_id", "nat_doc_ids", "doc_ids", string=" ")
    flag_actif= fields.Boolean(string= "Obligatoire")
    company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)



class Ca_recommandation (models.Model):
	_name= "ca_recommandation"
	_rec_name="objet"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	objet= fields.Many2one("ca_nature_session", string= "Objet", domain=[('state','=','2')])
	session_id = fields.Many2one("ca_nature_de_session", string= "Nature de session", readonly=True)
	cat_id = fields.Many2one("ca_type_session", string = "Type de session", readonly=True)
	date= fields.Date(string= "Date",default=date.today(), readonly= True)
	membre_id= fields.Many2one('res.users', string= 'Administrateurs', default=lambda self: self.env.user, readonly= True)
	observation= fields.Text(string= "Observations")
	join_doc = fields.Binary(string= "Joindre fichier", attachment=False)
	line_ids= fields.One2many("ca_recommandation_line", "line_id", string= " " )
	state= fields.Selection([("B", "Brouillon"),("V", "Valider")],string= "Etat", default= "B", copy= False)
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)

	@api.onchange("objet")
	def obejt(self):
		
		self.cat_id = self.objet.cat_id
		self.session_id = self.objet.lib_long
	
	def afficher(self):
		
		v_struct = int(self.company_id)
		v_id = int(self.objet)
		
		for vals in self:
			vals.env.cr.execute("""select l.ordre_jour as ordre
			from ca_ordre_jour_acte l, ca_nature_session n WHERE n.id = l.nature_id and n.id = %d and company_id = %d""" %(v_id, v_struct))
			
			rows = vals.env.cr.dictfetchall()
			result = []
			
			vals.line_ids.unlink()
			for line in rows:
				result.append((0,0, {'ordre_id' : line['ordre']}))
			self.line_ids = result


	@api.multi
	def formule(self):
		self.write({'state': 'V'})
	


class Ca_recommandationLine (models.Model):
    _name= "ca_recommandation_line"
    
    ordre_id = fields.Many2one("ca_ordre_jour","Ordre du jour", readonly=True)
    commentaire= fields.Text(String= "Commentaires")
    line_id= fields.Many2one("ca_recommandation", ondelete='cascade')


class Ca_centre_rec (models.Model):
    _name= "ca_centre_rec"
    _rec_name="objet"
    _order = 'sequence, id'

    sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
    state= fields.Selection([("B", "Brouillon"),("C", "Centralisation")],
    string= "Etat", default= "B", copy= False)
    objet= fields.Many2one("ca_nature_session", string= "Objet", required= True, domain=[('state','=','2')])
    rec_line_ids= fields.One2many("ca_centre_rec_line", "rec_line_id", string= " ")
    line_ids= fields.One2many("ca_action_line", "action_id", string= " ")
    company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)

# Centralisations des récommandations

    @api.multi
    def central(self):
    	
        v_id = int(self.objet)
        v_struct = int(self.company_id)

        for vals in self:
        	vals.env.cr.execute("""select l.ordre_id as ordre, l.commentaire as obs, n.membre_id as admin
			from ca_recommandation_line l, ca_recommandation n WHERE n.id = l.line_id and n.objet = %d and company_id = %d""" %(v_id, v_struct))
        	res = vals.env.cr.dictfetchall()
        	result = []

        	vals.rec_line_ids.unlink()
        	for line in res:
        		result.append((0, 0, { 'ordre_id':line['ordre'],'commentaire':line['obs'],'membre':line['admin']}))
        	self.rec_line_ids = result

        self.write({'state': 'C'})




class Ca_centre_recLine (models.Model):
	_name= "ca_centre_rec_line"
    
	ordre_id = fields.Many2one("ca_ordre_jour","Ordre du jour", readonly=True)
	membre= fields.Many2one('res.users', "Administrateurs")
	commentaire= fields.Text(String= "Commentaires")
	reformulation= fields.Text(string= "Reformulation")
	retenue= fields.Boolean(string= "Retenue")
	rec_line_id= fields.Many2one("ca_centre_rec", ondelete='cascade')
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)


class Ca_actionLine (models.Model):
    _name= "ca_action_line"
    _rec_name="objet"
    _order = 'sequence, id'

    sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
    objet= fields.Char(string = "Objet")
    date_debut= fields.Date(string= "Date debut")
    date_fin= fields.Date(string= "Date fin")
    observation= fields.Text(string= "Observation")
    state= fields.Boolean(string= "Etat")
    action_id= fields.Many2one("ca_centre_rec")
    company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)




class Ca_com_compte (models.Model):
	_name= "ca_com_compte"
	_rec_name="objet"
	_order = 'sequence, id'
	
	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	objet= fields.Many2one("ca_nature_session", "Objet", required= True)
	cat_id= fields.Many2one("ca_type_session", string = "Session", readonly= True)
	session_id= fields.Many2one("ca_nature_de_session", string="Nature de session", readonly= True)
	membre_id= fields.Many2one('res.users', string= 'Administrateurs', default=lambda self: self.env.user, readonly= True)
	date= fields.Date(default=date.today(), readonly= True)
	piece_jointe= fields.Binary(string= "Pièce Jointe")
	observation= fields.Text(string= "Observations")
	state= fields.Selection([("B", "Brouillon"),("V", "Validé")], string= "Etat", default= "B", copy= False)
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)

	@api.onchange("objet")
	def Objet(self):
		
		self.cat_id = self.objet.cat_id
		self.session_id = self.objet.lib_long

	
	@api.multi
	def valider(self):
			self.write({'state': 'V'})


class Ca_ordre_jour (models.Model):
    _name= "ca_ordre_jour"
    _rec_name="lib_long"
    _order = 'sequence, id'

    sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
    lib_court= fields.Char(string= "Libelle court", required = True, size=35)
    lib_long= fields.Char(string= "Libelle long", required = True, size=65)
    session_id= fields.Many2one("ca_nature_session", string="Nature de la session")
    nature_ids= fields.Many2many("ca_nature_session", "ca_ordres_nat_id", "nature_ids", "ordres_ids")
    sess_jour_ids= fields.Many2many("ca_nature_session", "ca_sess_jour", "sess_jour_ids", "ordres_ids")
    commentaire= fields.Text(String= "Commentaire", size=100)
    flag_actif= fields.Boolean(string= "Obligatoire")
    company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)



class Ca_consult_pro (models.Model):
	_name= "ca_consult_pro"
	_rec_name= "objet"
	_order = 'sequence, id'

	sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
	objet= fields.Many2one("ca_consult_domicile", string= "Objet")
	membre_id= fields.Many2one('res.users', string= 'Administrateurs', default=lambda self: self.env.user, readonly= True)
	date_debut= fields.Date("Date de début", readonly= True)
	date_fin= fields.Date(string= "Date de fin", readonly= True)
	cat_id = fields.Many2one("ca_type_session", "Type de session", readonly= True)
	session_id = fields.Many2one("ca_nature_de_session", "Nature de session", readonly= True)
	doc= fields.Binary(attachment= False, string= "Documents")
	consult_line_ids= fields.One2many("ca_consult_pro_line", "conseline_id")
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
   

	@api.onchange("objet")
	def consul(self):
		self.date_debut= self.objet.date_entree
		self.date_fin= self.objet.date_fin
		self.cat_id= self.objet.cat_id
		self.session_id= self.objet.session_id



	def afficher(self):
	
		val_objet = int(self.objet)
		val_struct = int(self.company_id)
		
		for vals in self:
			vals.env.cr.execute("""select l.libelle as libelle, l.docu_id as doc from ca_consult_domicile c, ca_document_dom l 
			where c.id = l.domicile_id and c.id = %d and company_id = %d"""%(val_objet,val_struct))
			res = vals.env.cr.dictfetchall()
			result = []
			
			vals.consult_line_ids.unlink()
			for line in res:
				result.append((0, 0, {'libelle':line['libelle'],'doc':line['doc']}))
			self.consult_line_ids = result



class Ca_consult_proLine (models.Model):
    _name= "ca_consult_pro_line"

    commentaire= fields.Text(String= "Commentaires")
    doc= fields.Binary(attachment= False, string= "Documents")
    libelle= fields.Char("Libellé du document", readonly= True)
    conseline_id= fields.Many2one("ca_consult_pro", ondelete='cascade')


class Ca_avis_admin (models.Model):
    _name= "ca_avis_admin"
    _rec_name="lib_long"
    _order = 'sequence, id'

    sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
    lib_court= fields.Char(string= "lib_court")
    lib_long= fields.Char(string= "lib_long", required= True)


class Ca_consult_centrale (models.Model):
    _name= "ca_consult_centrale"
    _rec_name="objet"
    _order = 'sequence, id'

    sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
    objet= fields.Many2one("ca_consult_domicile", string= "Objet")
    date= fields.Date(string= "Date", default=date.today(), readonly=True)
    acte_del= fields.Binary(string= "Acte de délibiration")
    action= fields.Many2one("ir.cron", string= "Alerte", required= False)
    state= fields.Selection([("1", "brouillon"), ("2", "Centraliser")], default= "1", string= "Etat", copy= False)
    centre_line_ids= fields.One2many("ca_consult_centrale_line", "consuline_id", readonly=True)
    company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)


#Centralisation des consultations à domicile
    @api.multi
    def cent(self):
    	
        val_objet = int(self.objet)
        print("objet",val_objet)
        val_struct = int(self.company_id)

        for vals in self:
        	vals.env.cr.execute("""select l.commentaire as com, l.libelle as lib, c.membre_id as membre from ca_consult_pro c, ca_consult_pro_line l
			where c.id = l.conseline_id and c.objet = %d and c.company_id = %d""" %(val_objet,val_struct))
        	res = vals.env.cr.dictfetchall()
        	result = []

        	vals.centre_line_ids.unlink()
        	for line in res:
        		result.append((0, 0, {'commentaire':line['com'], 'libelle':line['lib'], 'membre':line['membre']}))
        	self.centre_line_ids = result

        self.write({'state': '2'})




class Ca_consult_centraleLine (models.Model):
    _name= "ca_consult_centrale_line"

    membre = fields.Many2one('res.users',string= "Administrateurs")
    commentaire = fields.Text(String= "Commentaire/Avis")
    libelle = fields.Char(string= "Libellé du document")
    consuline_id = fields.Many2one("ca_consult_centrale", ondelete='cascade')



class Ca_motif_mandat (models.Model):
    _name= "ca_motif_mandat"
    _rec_name="lib_court"
    _order = 'sequence, id'

    sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
    lib_court= fields.Char(string= "Libelle court", required = True, size=35)
    lib_long= fields.Char(string= "Libelle long", required= True, size=65)
    description= fields.Text(string= "Description", size= 100)
    company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
    x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))



class Ca_cat_representant (models.Model):
    _name= "ca_cat_representant"
    _rec_name= "lib_court"
    _order = 'sequence, id'

    sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
    lib_court= fields.Char(string= "Libelle court", required = True, size=35)
    lib_long= fields.Char(string= "Libelle long", required = True, size=65)    
    company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
    x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))


	
class Ca_membre(models.Model):
    _name = "ca_membre"
    _rec_name= "nom"
    _order = 'sequence, id'

    sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
    image= fields.Binary(string= "Photo", filters='*.png*.jpeg', store= True)
    acte= fields.Binary(string= "Acte de nomination", attachment=True)
    decret_nom= fields.Char(string= "Référence du décret", required= True, size= 20)
    date_nom= fields.Date(string= "Date de nomination")
    cv= fields.Binary(string= "Curriculum Vitae", attachment= False)
    nom = fields.Char(string= "Nom & Prénom(s)", required= True)
    date_entree= fields.Date(string="Date d'entrée", required= True)
    typemembre_id = fields.Many2one("ca_type_membre", string= "Type de Membre", required= True)
    n_matricule= fields.Char(string= "N° matricule", size= 20)
    date_renou_fin= fields.Date(string= "Date fin mandat", readonly= True)
    structure_id= fields.Many2one("ca_cat_representant", string="Structure d'origine")
    action= fields.Many2one("ir.cron", string= "Alerte", required= False)
    courriel = fields.Char("E-Mail")
    company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
    x_fonction_id = fields.Many2one("hr_fonctionss",string = 'Fonction', required= True)
    autre = fields.Char("Autres fonction")
    active= fields.Boolean('Actif', default= True)

	

    @api.onchange("date_entree")
    def mandat_global(self):
    	if self.date_entree:
    		date1=self.date_entree.strftime("%Y-%m-%d")
    		date2=self.date_entree.year + 6
    		self.date_renou_fin= datetime(date2,self.date_entree.month, (self.date_entree.day - 1),0,0,0,0).date()



class Ca_membreLine (models.Model):
    _name= "ca_membre_line"
    _rec_name= "membre_id"

    membre_id= fields.Many2one("ca_membre", string= "Administrateurs")
    typemembre_id = fields.Char(string= "Type Membre", readonly= True)
    date_entree = fields.Date(string= "date d'entrée", readonly= True)
    date_fin= fields.Date(string= "Date fin", readonly= True)
    observation= fields.Text(String= "Observation")
    admin_line_id= fields.Many2one("ca_administrateur")


    @api.onchange("date_entree")
    def mandat1(self):
    	if self.date_entree:
    		date1=self.date_entree.strftime("%Y-%m-%d")
    		date2=self.date_entree.year + 3
    		self.date_fin= datetime(date2,self.date_entree.month, (self.date_entree.day),0,0,0,0).date()


    @api.onchange("membre_id")
    def remp(self):
    	self.typemembre_id= self.membre_id.typemembre_id.lib_long
    	self.date_entree= self.membre_id.date_entree




#fonction de calcul du mandat qui est de trois ans

    @api.depends("date_fin_rel")
    def date_fin_renouv(self):
    	if self.date_fin_rel:
    		date1=self.date_fin_rel.strftime("%Y-%m-%d")
    		date2=self.date_fin_rel.year + 3
    		self.date_renou_fin= datetime(date2,self.date_fin_rel.month, (self.date_fin_rel.day-1),0,0,0,0).date()




class Ca_membresLine (models.Model):
    _name= "ca_membres_line"

    membre_id= fields.Many2one("ca_membre_line", string= "Administrateurs")
    typemembre_id = fields.Char(string= "Type Membre", readonly= True)
    date_entree = fields.Date(string= "date_entree", readonly= True)
    date_fin_rel= fields.Date(string= "Date rénouvellement prévue", readonly= True)
    date_renou_reelle= fields.Date(string= "Date renouvellement reelle", required= True)
    date_renou_fin= fields.Date(string= "Date fin mandat", readonly= True)
    date_fin_reelle= fields.Date(string= "Date fin reelle", required= True)
    decret_renou= fields.Char(string="Decret de renouvellement", size= 65)
    acte_renou= fields.Binary(string= "Acte renouvellement", attachment= False)
    admin_lines_id= fields.Many2one("ca_administrateur")


    @api.onchange("membre_id")
    def remp(self):
    	self.typemembre_id= self.membre_id.typemembre_id
    	self.date_entree= self.membre_id.date_entree
    	self.date_fin_rel= self.membre_id.date_entree



    @api.onchange("date_entree")
    def mandat2(self):
    	if self.date_entree:
    		date1=self.date_entree.strftime("%Y-%m-%d")
    		date2=self.date_entree.year + 6
    		self.date_renou_fin= datetime(date2,self.date_entree.month, (self.date_entree.day-1),0,0,0,0).date()



class Ca_administrateur(models.Model):
    _name= "ca_administrateur"
    _rec_name= "nom_id"
    _order = 'sequence, id'

    sequence = fields.Integer(help="Gives the sequence when displaying a list of cat.Struct.", default=10)
    nom_id= fields.Many2one("ca_membre", string= "Nom & Prénom(s)", required= True)
    motif_id= fields.Many2one("ca_motif_mandat", string= "Motif de depart")
    date_entree= fields.Date(string="Date d'entrée", readonly= True)
    date_fin= fields.Date(compute="_compute_date_fin", string= "Date fin", store=True)
    date_fin_rel= fields.Date(string= "Date rénouvellement prévue", compute= "date_fin_ren")
    mandat_renou= fields.Selection([("2", "2"),], string="Mandat renouvellé", default="2", copy=False)
    nom_renou_id= fields.Many2one("ca_membre", string= "Nom & Prénom(s)")
    typemem_renou_id = fields.Many2one("ca_type_membre", string= "Type Membre")
    motif_renou_id= fields.Many2one("ca_motif_mandat", string= "Motif de depart")
    date_renou_fin= fields.Date(compute= "date_fin_renouv", string= "Date fin mandat", store= True)
    state = fields.Selection([
        ('brouillon', 'Brouillon'),
        ('en cours', 'En cours'),
        ('renouveller', 'Renouvellé'),
    ],  string='Mandat', readonly=True, copy=False, store=True, default='brouillon', track_visibility='onchange')
    acte_renou= fields.Binary(string= "Acte renouvellement", attachment= True)
    date_depart= fields.Date(string= "Date depart")
    nom_entrant_id= fields.Many2one("ca_membre", string= "Nom (remplaçant)")
    admin_lines_ids= fields.One2many("ca_membres_line", "admin_lines_id", string= "")
    admin_line_ids= fields.One2many("ca_membre_line", "admin_line_id", string= " ")
    date_renou_reelle= fields.Date(string= "Date renouvellement réelle")
    date_fin_reelle= fields.Date(string= "Date fin reelle")
    decret_renou= fields.Char(string="Référence Decret", size= 65)
    company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)
    x_exercice_id = fields.Many2one('ref_exercice', default=lambda self: self.env['ref_exercice'].search([('etat','=', 1)]))
    etat = fields.Selection([
        (1, 'Y'),
        (2, 'N'),
    ], string='Etat',default=1, required = True)
	


    @api.onchange("nom_id")
    def champ_date(self):
    	self.date_entree= self.nom_id.date_entree


#fonction de calcul de la durée du mandat qui est de trois ans

    @api.depends("date_entree")
    def _compute_date_fin(self):
    	if self.date_entree:
    		date1=self.date_entree.strftime("%Y-%m-%d")
    		date2=self.date_entree.year + 3
    		self.date_fin= datetime(date2,self.date_entree.month, (self.date_entree.day),0,0,0,0).date()



    @api.depends("date_fin")
    def date_fin_ren(self):
    	date_fin_re= self.date_fin
    	self.date_fin_rel= date_fin_re



#fonction de calcul du mandat qui est de trois ans

    @api.depends("date_fin_rel")
    def date_fin_renouv(self):
    	if self.date_fin_rel:
    		date1=self.date_fin_rel.strftime("%Y-%m-%d")
    		date2=self.date_fin_rel.year + 3
    		self.date_renou_fin= datetime(date2,self.date_fin_rel.month, (self.date_fin_rel.day-1),0,0,0,0).date()



    @api.multi
    def mandat(self):
    	self.write({'state': 'en cours'})


    @api.multi
    def renouveller(self):
    	self.write({'state': 'renouveller'})


class CaNatureDeSession(models.Model):
	_name = "ca_nature_de_session"
	_rec_name = "lblong"
	
	lbcourt = fields.Char("Libellé court")
	lblong = fields.Char("Libellé long",required=True)
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)


class CaParametreNatureDocument(models.Model):
	_name = "ca_parametre_nature"
	_rec_name = "nature_id"
	
	nature_id = fields.Many2one("ca_nature_de_session", "Nature de la session", required=True)
	doc_ids = fields.One2many("ca_parametre_line", "parametre_id")
	company_id = fields.Many2one('res.company', string='Structure', index=True, default=lambda self: self.env.user.company_id.id)

class CaParametreLine(models.Model):
	_name = "ca_parametre_line"
	
	parametre_id = fields.Many2one("ca_parametre_nature", ondelete='cascade')
	doc_id = fields.Many2one("ca_type_doc", "Libellé document", required=True)
