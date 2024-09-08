{
    'name': 'Monitor de Redes Sociales para proyectos',
    'version': '17.0.1.0.0',
    'odoo_version': '17.0',
    'manifest_version': '17.0',
    'category': 'Social,Project',
    'summary': 'Con "Seguimiento de RR.SS.", podrás hacer el seguimiento de tus redes sociales en las tareas de un proyecto. Por Infinity Draw',
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
        'views/smmonitor_views_project_task.xml',
        'views/smmonitor_views_project_project.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/ifdw_social_media_monitoring/static/src/js/timezone_detector.js',
            '/ifdw_social_media_monitoring/static/src/js/smmonitor_copy_hashtags.js',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
