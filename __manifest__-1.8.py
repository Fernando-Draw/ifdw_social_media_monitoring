# -*- coding: utf-8 -*-
##########################################################################################################################################################
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
##########################################################################################################################################################
#
#       Los principales archivos del módulo son __manifest__-1.8.py, timezone_detector-1.3.js (con cookie) y
#       timezone_detector-1.4.js (con metodo de odoo) incluyen el para detectar la hora del usuario local.
#       El metodo de la cookie NO funcione correctamente en el navegador, pero si como módulo como tal.
#       El metodo de odoo funciona funciona correctamente tanto en el navegador como el módulo como tal.
#       El archivo smmonitor_views.3.0.xml (con cookie) para las vistas y el archivo smmonitor_views.3.1.xml (con metodo Odoo)
#       para las vistas, donde en este caso anulamos el campo 'user_timezone_offset' ya que deja de ser necesario.
#       El archivo de python smmonitor_model-3.0.py (con cookie) y el mismo terminado en 3.1.py (con metodo odoo) son los
#       que incluyen toda la lógica del módulo para hacer que todo se cree correctamente, siempre teniendo en cuenta lo que
#       hemos comentado y es que el metodo de la cookie no termina de funcionar ocasionando un error en el navegador web aunque
#       si funciona el módulo como tal, y el metodo que odoo recomienda implementar funciona correctamente en todos los sentidos,
#       teniendo en cuenta que en este metodo se quita el campo 'user_timezone_offset' ya que deja de ser necesario.
#
##########################################################################################################################################################


{
    'name': 'Monitor de Redes Sociales para proyectos',
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
    'depends': [
        'web',
        'base',
        'project',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/smmonitor_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/ifdw_social_media_monitoring/static/src/js/timezone_detector.js',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}

