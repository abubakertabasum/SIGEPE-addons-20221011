{
    "name": "Gestion Congés",
    "version": "1.0",
    "author": "TELIA INFORMATIQUE",
    "depends":["base","Gestion_RH"],
    "data":[
        "views/vue_conge.xml",
        "data/data.xml",
        "Report/report_conge.xml",
        "Report/report_abs.xml",
        "Report/report_decret.xml",
        "Report/report_planning.xml",
        "Report/report_demande_conge.xml",
        "Report/report_demande_autorisation_absence.xml",
        "security/security.xml",
        "security/ir.model.access.csv"],
    "category": "EPE",
    "Summary": "Gestion des Congés des EPE",
    "installable": True,
    "auto_install": False,

}
