# -*- coding: utf-8 -*-

# ██╗   ██╗██████╗ ██╗ ██████╗     ██████╗ ███████╗███████╗ █████╗ ███╗   ██╗████████╗██████╗ ███████╗███╗   ██╗                                              
# ██║   ██║██╔══██╗██║██╔════╝     ██╔══██╗██╔════╝██╔════╝██╔══██╗████╗  ██║╚══██╔══╝██╔══██╗██╔════╝████╗  ██║                                            
# ██║   ██║██████╔╝██║██║  ███╗    ██████╔╝█████╗  ███████╗███████║██╔██╗ ██║   ██║   ██████╔╝█████╗  ██╔██╗ ██║                                             
# ██║   ██║██╔══██╗██║██║   ██║    ██╔═══╝ ██╔══╝  ╚════██║██╔══██║██║╚██╗██║   ██║   ██╔══██╗██╔══╝  ██║╚██╗██║                                             
# ╚██████╔╝██████╔╝██║╚██████╔╝    ██║     ███████╗███████║██║  ██║██║ ╚████║   ██║   ██║  ██║███████╗██║ ╚████║                                             
#  ╚═════╝ ╚═════╝ ╚═╝ ╚═════╝     ╚═╝     ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝                                             

{
    'name': "Modul Pendaftaran Karyawan SISFO Pesantren",

    'summary': """
        Aplikasi SISFO Pesantren
        - Modul Pendaftaran untuk SISFO Pesantren""",

    'description': """
        Aplikasi SISFO Pesantren memiliki fitur-fitur sebagai berikut :
        ===============================================================
        * Modul Base / Dasar
        * Modul Akademik
        * Modul Musyrif
        * Modul Guru
        * Modul Orang Tua
        * Modul Kesantrian
        * Modul Pendaftaran
        * Modul Karywan

        Developed by : 
        - Aldo
        - Aliga
        - Akim

        Desember 2024

        Informasi Lebih lanjut, hubungi :

            PT. Universal Big Data 
            - Ruko Modern Kav A16-A17
              Jl Loncat Indah, Tasikmadu, Kota Malang
    """,

    'author': "PT. Universal Big Data",
    'website': "https://ubig.co.id",
    'category': 'Education',
    'version': '18.0.1.0',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'pesantren_base', 'hr_recruitment', 'hr'],

    # always loaded
    'data': [
        # Security
        # 'security/groups.xml',
        # 'security/ir.model.access.csv',

        # View
        'views/hr_applicant.xml',
        'views/hr_recruitment.xml',
        'views/hr_employee.xml',
        'views/calendar.xml',
        # 'views/pendaftaran_karyawan.xml',
        'views/pendaftaran_karyawan_form_template.xml',
        'views/pendaftaran_karyawan_success_template.xml',

        # Menu
        # 'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

