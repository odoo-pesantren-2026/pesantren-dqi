# -*- coding: utf-8 -*-

{
    'name': "Modul Guru SISFO Pesantren",

    'summary': """
        Aplikasi SISFO Pesantren
        - Modul Guru untuk SISFO Pesantren""",

    'description': """
        Aplikasi SISFO Pesantren memiliki fitur-fitur sebagai berikut :
        ===============================================================
        * Modul Base / Dasar
        * Modul Akademik
        * Modul Keuangan
        * Modul Guru
        * Modul Orang Tua
        * Modul Kesantrian

        Developed by : 
        - Imam Masyhuri
        - Supriono

        Maret 2022

        Informasi Lebih lanjut, hubungi :
            PT. Cendana Teknika Utama 
            - Ruko Permata Griyashanta NR 24-25 
              Jl Soekarno Hatta - Malang
    """,

    'author': "PT. Cendana Teknika Utama",
    'website': "https://www.cendana2000.co.id",
    'category': 'Education',
    'version': '18.0.1.0',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'pesantren_base', 'report_xlsx'],

    # always loaded
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',

        # wizard
        'wizard/absensi_filter_wizard.xml',

        # views
        'views/menu.xml',
        'views/absensi_siswa.xml',
        'views/absensi_ekskul.xml',
        'views/master_rpp.xml',
        'views/penilaian.xml',
        'views/penugasan.xml',
        'views/penilaian_akhir.xml',
        'views/penilaian_akhir_guru.xml',
        'views/predikat.xml',
        'views/pembagian_ekstra.xml',
        'views/absensi_ekskul_base.xml',
        'views/absensi_siswa_base.xml',
        # reports
        'reports/report_penilaian_akhir.xml'
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
    'assets': {
        'web.assets_backend': [
            'pesantren_guru/static/src/scss/style.scss',
        ],
    },
}
