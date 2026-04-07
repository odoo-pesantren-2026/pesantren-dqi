{
    'name': 'Hide Module Menu',
    'version': '18.0.1.0.0',
    'category': 'Hidden',
    'summary': 'Hide specific menus from sidebar',
    'depends': ['base', 'pesantren_keuangan', 'account', 'point_of_sale', 'purchase', 'stock', 'hr_holidays'],
    'data': [
        'views/hide_module_menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}