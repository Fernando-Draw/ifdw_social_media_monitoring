# -*- coding: utf-8 -*-
#############################################################################
#
#    Infinity Draw.
#
#    Copyright (C) 2024-HOY Infinity Draw (<https://infinitydraw.es>)
#    Autor: Fernan Nerd (<https://infinitydraw.es>)
#
#    Puedes modificarlo bajo los términos de GNU LESSER.
#    LICENCIA PÚBLICA GENERAL (LGPL v3), Versión 3.
#
#    Este programa se distribuye con la esperanza de que sea útil,
#    pero SIN NINGUNA GARANTÍA; sin siquiera la garantía implícita de
#    COMERCIABILIDAD o IDONEIDAD PARA UN PROPÓSITO PARTICULAR.  Ver el
#    LICENCIA PÚBLICA GENERAL MENOR GNU (LGPL v3) para más detalles.
#
#    Debería haber recibido una copia de la LICENCIA PÚBLICA GENERAL MENOR DE GNU
#    (LGPL v3) junto con este programa.
#    En caso contrario, consulte <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    "name": "Monitor de Redes Sociales para proyectos",
    'version': '17.0.1.0.0',
    'odoo_version': '17.0',
    'manifest_version': '17.0',
    'category': 'Social,Project',
    'summary': 'Con "Seguimiento de RR.SS.", podrás hacer el seguimiento de tus redes sociales en las tareas de un proyecto.',
    'description': '''Seguimiento de tus redes sociales con sus tres valores principales 
                   para poder sacar estadísticas de forma fácil y ver qué funciona en el tiempo. 
                   Al anotar los registros manualmente desde las plataformas oficiales 
                   podrás llevar un control más exacto de tus publicaciones sin tener que depender 
                   de plataformas externas para ver gráficas y estadísticas de las publicaciones.''',
    'author': 'Infinity Draw',
    'company': 'Infinity Draw',
    'maintainer': 'Infinity Draw',
    'website': "https://infinitydraw.es",
    "depends": ["project", "mail"],
    "data": ["security/ir.model.access.csv", "views/smmonitor_views.xml"],
    'assets': {
        'web.assets_backend': [
            'static/src/xml/smmonitor_styles.xml',
            'static/src/js/timezone_detector.js',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}

