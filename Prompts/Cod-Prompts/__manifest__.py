Nombre de archivo:
__manifest__.py
{
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