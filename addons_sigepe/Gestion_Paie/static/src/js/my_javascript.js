odoo.define('custom_module.my_javascript', function(require) {"use strict";
	/*var Model = require('web.Model')

	var custom_model = new Model('custom.model')
	custom_model.call('list_employes')*/
        //alert('ok')
        var loaded = self.fetch('wiz_hr_paramelemnetsalaire_line',['hr_elementsalaire_id','name','hr_type_elt_salaire','hr_signe'],[['wiz_hr_paramelemnetsalaire_id','=', 10], ['active', '=','true']])
   .then(function(elements){
       // ici le reste du code sera exécuté lorsque les données auront été récupérées
    });

})
