        val_objet = int(self.objet)
        val_struct = int(self.company_id)
        val_ex = int(self.x_exercice_id)

        self.env.cr.execute("""SELECT DISTINCT (B.commentaire) AS comment, (B.avis) AS avis
        FROM ca_consult_pro_line B, ca_consult_pro LI, ca_consult_domicile C
        WHERE B.conseline_id = LI.id and LI.objet= C.id and C.active= True and LI.objet = %s and LI.company_id = %s and LI.x_exercice_id = %s""",(val_objet,val_struct,val_ex))
        res = self.env.cr.dictfetchall()
        result = []
            
        vals.centre_line_ids.unlink()
        for line in res:
            result.append((0, 0, {'commentaire':line['comment'], 'avis':line['avis']}))
        self.centre_line_ids = result