#Fonction compteur et génération des numéros des ecritures et des lignes d'ecritures

	@api.multi
	def generer_ecriture(self):
		val_ex = int(self.x_exercice_id.id)
		print('lexercice', val_ex)
		val_struct = int(self.company_id.id)
		print('la structure', val_struct)
		val_ecr = self.no_ecr
		id_vente = self.id
		var_cptes = int(self.var_cpte)
		vl_mnt = self.mnt_total
		val_sens = str(self.fg_sens)

	
#Attribution des numero et lignes d'ecritures pour l'enregistrement d'une vente

		self.env.cr.execute("select no_ecr,no_lecr from compta_compteur_ecr where x_exercice_id = %d and company_id = %d" %(val_ex,val_struct))
		noecr = self.env.cr.dictfetchall()
		print('Résultats',noecr)
		no_ecrs = noecr and noecr[0]['no_ecr']
		no_ecrs1 = noecr and noecr[0]['no_lecr']
		no_ecr = no_ecrs
		print('Résultats avancés',noecr)

		if not(no_ecr):
			self.no_ecr = 1
			print('lecriture est',self.no_ecr)
			no_ecrs1 = 0

			for x in self.cess_vente_line_ids:
				no_ecrs1 = no_ecrs1 + 1
				print('Lecriture', no_ecrs1)
				x.no_lecr = no_ecrs1
				print('Lecriture est', x.no_lecr )
			self.env.cr.execute("""INSERT INTO compta_compteur_ecr(x_exercice_id,company_id,no_ecr,no_lecr) VALUES(%d, %d, %d, %d)""" %(val_struct,val_ex,self.no_ecr,x.no_lecr))
		else:
			self.no_ecr = no_ecr + 1
			no_ecrs11 = no_ecrs1 + 1
			no_ecrs1= no_ecrs11

			for x in self.cess_vente_line_ids:
				no_ecrs1 = no_ecrs1 + 1
				x.no_lecr = no_ecrs1

			self.env.cr.execute("UPDATE compta_compteur_ecr SET no_ecr = %d, no_lecr = %d WHERE x_exercice_id = %d and company_id = %d" %(self.no_ecr,x.no_lecr,val_ex,val_struct))

			self.env.cr.execute("SELECT * from gi_cession_vente where x_exercice_id = %d and company_id = %d and id = %d" %(val_ex,val_struct, id_vente))

			curs_vente = self.env.cr.dictfetchall()

			no_ecrs = curs_vente and curs_vente[0]['no_ecr']
			no_ecr = int(no_ecrs)
			print('lecriture est',no_ecr)
			typ_jr = curs_vente and curs_vente[0]['type_journal']
			print('le type de journal',typ_jr)

			self.env.cr.execute("INSERT INTO compta_ecriture(no_ecr, type_journal, type_op ,x_exercice_id, company_id) VALUES (%d, %d, 'G', %d, %d)" %(no_ecr, typ_jr, val_struct, val_ex))

			self.env.cr.execute("select * from gi_cess_vente_line where x_exercice_id = %d and company_id = %d and cess_vente_id = %d " %(val_ex,val_struct, id_vente))
			rows = self.env.cr.dictfetchall()

			self.env.cr.execute("""INSERT INTO compta_ligne_ecriture(no_lecr, no_souscpte, mt_lecr, x_exercice_id, company_id, fg_sens) 
			VALUES (%d, %d, %d, %d, %d, '%s') """ %(no_ecrs11, var_cptes, vl_mnt,val_ex, val_struct, val_sens))

			self.env.cr.execute("""INSERT INTO compta_ligne_ecriture(no_lecr, no_souscpte, mt_lecr, fg_sens, type_pj, x_exercice_id, company_id) 
			SELECT no_lecr, compte, valeur, fg_sens, typ_pj, x_exercice_id, company_id
			FROM gi_cess_vente_line WHERE x_exercice_id = %d AND company_id = %d AND cess_vente_id = %d """ %(val_ex, val_struct, id_vente))

--------------------------------------------------------------------------------------------------------------------------
#Fonction compteur et génération des numéros des ecritures et des lignes d'ecritures

	@api.multi
	def generer_ecriture(self):
		val_ex = int(self.x_exercice_id.id)
		print('lexercice', val_ex)
		val_struct = int(self.company_id.id)
		print('la structure', val_struct)
		val_ecr = self.no_ecr
		id_don = self.id
		var_cptes = int(self.var_cpte)
		vl_mnt = self.mnt_total
		val_sens = str(self.fg_sens)

	
#Attribution des numero et lignes d'ecritures pour l'enregistrement d'une vente

		self.env.cr.execute("select no_ecr,no_lecr from compta_compteur_ecr where x_exercice_id = %d and company_id = %d" %(val_ex,val_struct))
		noecr = self.env.cr.dictfetchall()
		print('Résultats',noecr)
		no_ecrs = noecr and noecr[0]['no_ecr']
		no_ecrs1 = noecr and noecr[0]['no_lecr']
		no_ecr = no_ecrs
		print('Résultats avancés',noecr)

		if not(no_ecr):
			self.no_ecr = 1
			print('lecriture est',self.no_ecr)
			no_ecrs1 = 0

			for x in self.cess_don_line_ids:
				no_ecrs1 = no_ecrs1 + 1
				print('Lecriture', no_ecrs1)
				x.no_lecr = no_ecrs1
				print('Lecriture est', x.no_lecr )
			self.env.cr.execute("""INSERT INTO compta_compteur_ecr(x_exercice_id,company_id,no_ecr,no_lecr) VALUES(%d, %d, %d, %d)""" %(val_struct,val_ex,self.no_ecr,x.no_lecr))
		else:
			self.no_ecr = no_ecr + 1
			no_ecrs11 = no_ecrs1 + 1
			no_ecrs1= no_ecrs11

			for x in self.cess_don_line_ids:
				no_ecrs1 = no_ecrs1 + 1
				x.no_lecr = no_ecrs1

			self.env.cr.execute("UPDATE compta_compteur_ecr SET no_ecr = %d, no_lecr = %d WHERE x_exercice_id = %d and company_id = %d" %(self.no_ecr,x.no_lecr,val_ex,val_struct))

			self.env.cr.execute("SELECT * from gi_cession_don where x_exercice_id = %d and company_id = %d and id = %d" %(val_ex,val_struct, id_don))

			curs_vente = self.env.cr.dictfetchall()

			no_ecrs = curs_vente and curs_vente[0]['no_ecr']
			no_ecr = int(no_ecrs)
			print('lecriture est',no_ecr)
			typ_jr = curs_vente and curs_vente[0]['type_journal']
			print('le type de journal',typ_jr)

			self.env.cr.execute("INSERT INTO compta_ecriture(no_ecr, type_journal, type_op ,x_exercice_id, company_id) VALUES (%d, %d, 'G', %d, %d)" %(no_ecr, typ_jr, val_struct, val_ex))

			self.env.cr.execute("select * from gi_cession_don_line where x_exercice_id = %d and company_id = %d and cess_don_id = %d " %(val_ex,val_struct, id_don))
			rows = self.env.cr.dictfetchall()

			self.env.cr.execute("""INSERT INTO compta_ligne_ecriture(no_lecr, no_souscpte, mt_lecr, x_exercice_id, company_id, fg_sens) 
			VALUES (%d, %d, %d, %d, %d, '%s') """ %(no_ecrs11, var_cptes, vl_mnt,val_ex, val_struct, val_sens))

			self.env.cr.execute("""INSERT INTO compta_ligne_ecriture(no_lecr, no_souscpte, mt_lecr, x_exercice_id, company_id, fg_sens) 
			SELECT no_lecr, compte, valeur, x_exercice_id, company_id, fg_sens 
			FROM gi_cession_don_line WHERE x_exercice_id = %d AND company_id = %d AND cess_don_id = %d """ %(val_ex, val_struct, id_don))

           
--------------------------------------------------------------------------------------------------
	@api.onchange('designation_id')
	def remplir(self):
		design = int(self.designation_id)
		res1 = self.env.cr.execute("""SELECT sous_code from gi_ordre_entree_line L where designation_id = %d """ %(design))
		result1 = self.env.cr.fetchone() 
		vals1 = result1 and result1[0] or 0

		sous_codes = str(vals1)

		row = self.env.cr.execute("""SELECT DISTINCT (B.souscpte) As cpmte from ref_souscompte B, ref_compte C, gi_ordre_entree_line L where B.cpte_id= C.id and C.id= B.id and L.designation_id = %d and L.sous_code = '%s' """ %(design,sous_codes))
		rows = self.env.cr.fetchone() 
		val = rows and rows[0] or 0
		cpte = str(val)
		self.compte= cpte
		

		res = self.env.cr.execute("""SELECT (C.lib_court) As mode,(D.lib_long) As source, (L.val_unit) As montant, (DE.lib_long) As categorie, (DI.lib_long) As types, E.date_entree, (F.lib_long) As mag FROM gi_ordre_entree_line L, gi_mode_acquisition C, gi_source_fin D, gi_ordre_entree E, gi_magasin F, gi_categorie DE, gi_typeimmobilisation DI WHERE L.designation_id = %d and L.sous_code = '%s' """%(design,sous_codes))
		result = self.env.cr.dictfetchall() 

		print('les resultats',result)
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
--------------------------------------------------------------------------------------------------
			self.env.cr.execute("""INSERT INTO gi_immobilisation (code_immo, designation_id, marque_id, dateacquisition,direction_id, utilisateur_id, acquisition) VALUES(%s, %s, %s,%s,%s,%s,%s)""" ,(val_code,val_design,val_marque,val_date,val_direct,val_user,val_valeur))



