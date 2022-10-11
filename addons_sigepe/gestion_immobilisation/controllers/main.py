# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape

import json


class BarcodeController(http.Controller):

    @http.route(['/gestion_immobilisation/barcode/'], type='http', auth='user')
    def a(self, debug=False, **k):
        if not request.session.uid:
            return http.local_redirect('/web/login?redirect=/gestion_immobilisation/barcode/')

        return request.render('gestion_immobilisation.barcode_index')
