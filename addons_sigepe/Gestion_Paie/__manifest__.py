{
    "name": "Gestion de la paie",
    "version": "1.0",
    "author": "TELIA INFORMATIQUE",
    "depends":["base","hr_payroll","Referentiel_Global","Gestion_RH"],
    "data":[
        "views/vue_paie.xml",
        "views/vue_report_bulletin.xml",
        "views/vue_report_etat.xml",
        "Report/report_mode_paiement.xml",
        "Report/report_par_banque.xml",
        "Report/report_elt_salaire.xml",
        "Report/report_part_agent.xml",
        "Report/report_part_patronal.xml",
        "Report/report_part_global.xml",
        "Report/report_cessation_paiement.xml",
        "Report/report_prime.xml",
        "data/paie.xml",
        "security/paie_security.xml",
        
        "security/ir.model.access.csv"],
    "category": "EPE",
    "Summary": "Gestion de la paie des EPE",
    "installable": True,
    "auto_install": False,

}
