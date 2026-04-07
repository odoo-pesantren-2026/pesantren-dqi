# -*- coding: utf-8 -*-

{
    'name': 'Pesantren Smart Billing',
    'version': '18.0.1.0',
    'summary': 'Integrasi Smart Billing Multi-Provider (BSI, TKI, dll) untuk Pesantren',
    'description': '''
        Modul Smart Billing yang mendukung multiple payment provider:
        - BSI (Bank Syariah Indonesia)
        - TKI (Teknologi Kartu Indonesia)
        - Provider lainnya (pluggable)
        
        Fitur:
        - Virtual Account untuk tagihan santri
        - Permanent VA untuk top-up saldo bebas nominal
        - Payment Link untuk dikirim ke orang tua
        - Webhook handler untuk notifikasi pembayaran
        - Auto-reconcile invoice
        - Auto-topup uang saku
    ''',
    'author': 'PT. Cendana Teknika Utama',
    'website': 'https://www.cendana2000.co.id',
    'category': 'Accounting/Payment',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'account',
        'mail',
        'pesantren_base',
        'pesantren_keuangan',
        'pesantren_kesantrian',
        'pesantren_orangtua',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/res_config_settings_views.xml',
        'views/smart_billing_transaction_views.xml',
        'views/account_move_views.xml',
        'views/siswa_views.xml',
        'views/orangtua_views.xml',
        'views/orangtua_portal_va_views.xml',
        'views/menu.xml',
        'wizard/topup_saldo_wizard_views.xml',
        'wizard/pilih_anak_wizard_views.xml',
        'wizard/test_api_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pesantren_smart_billing/static/src/js/smart_billing_realtime.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
