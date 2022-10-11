{
	"name": "Gestion du Conseil d'Administration",
	"version": "1.0",
	"author": "TELIA INFORMATIQUE",
	"depends": ["base", "portal", "mail", "Gestion_RH"],
	"category": "EPE",
	"Summary": "Conseil d'administration des EPE",
	"installable": True,
	"auto_install": False,
	"data":["security/ir.model.access.csv",
	"views/vue_conseil.xml",
	"data/data.xml",
	"report/personnel_report.xml",
	"report/ordre_jour_report.xml",
	"security/ca_security.xml",
	'wizard/mail_schedule_date_views.xml'],

}
