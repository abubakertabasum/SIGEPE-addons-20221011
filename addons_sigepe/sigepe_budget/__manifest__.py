{
	'name' : 'Gestion Budgetaire',
	'author' : 'Telia Informatique',
	'version' : "1.0",
	'depends' : ['base','Referentiel_Global'],
	'description' : 'Gestion Budgetaire des EPE',
    'summary' : "Gestion Budgetaire des EPE et EPL du Burkina Faso",
	'data' : ['views/budget.xml', 'views/report_budget.xml', 'security/ir.model.access.csv','security/budget_security.xml','data/budg_data.xml'],
	'installable' : True,
	'auto_install' : False,
}
