# -*- coding: utf-8 -*-

{
    'name': 'Password Toggle Widget',
    'version': '18.0.1.0.0',
    'category': 'Web',
    'summary': 'Global Password Toggle Widget for all Odoo modules',
    'description': """
        This module provides a reusable password toggle widget
        that can be used across all Odoo modules.
        
        Usage in any view:
        <field name="password_field" widget="password_toggle"/>
    """,
    'depends': ['web', 'hr'],
    'assets': {
        'web.assets_backend': [
            'web_password_toggle/static/src/js/password_toggle.js',
            'web_password_toggle/static/src/xml/password_toggle.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
