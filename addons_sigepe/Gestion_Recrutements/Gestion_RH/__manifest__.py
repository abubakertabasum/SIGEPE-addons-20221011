{
    "name": "Gestion des Ressources Humaines",
    "version": "1.0",
    "author": "TELIA INFORMATIQUE",
    "depends":["base","hr","hr_contract","hr_payroll","Referentiel_Global"],
    "data":[
        "views/vue_employe.xml",
        "data/paramEmployee.xml",
        "views/vue_contrat.xml",
        "Report/vue_report_liste_empl.xml",
        "Report/report_evaluation.xml",
        "Report/report_evaluations.xml",
        "Report/report_cessation_service.xml",
        "Report/report_certificat.xml",
        "Report/report_precompte.xml",
        "Report/report_fiche_attente.xml",
        "security/security.xml",
        "security/ir.model.access.csv"],
    "category": "EPE",
    "Summary": "Gestion des ressources humaines des EPE",
    "installable": True,
    "auto_install": False,

}
