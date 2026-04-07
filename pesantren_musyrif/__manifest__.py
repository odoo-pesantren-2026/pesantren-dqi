# -*- coding: utf-8 -*-
#    ________  __      ________  _______   ______          _______    _______   ________     __      _____  ___  ___________  _______    _______  _____  ___   
#   /"       )|" \    /"       )/"     "| /    " \        |   __ "\  /"     "| /"       )   /""\    (\"   \|"  \("     _   ")/"      \  /"     "|(\"   \|"  \  
#  (:   \___/ ||  |  (:   \___/(: ______)// ____  \       (. |__) :)(: ______)(:   \___/   /    \   |.\\   \    |)__/  \\__/|:        |(: ______)|.\\   \    | 
#   \___  \   |:  |   \___  \   \/    | /  /    ) :)      |:  ____/  \/    |   \___  \    /' /\  \  |: \.   \\  |   \\_ /   |_____/   ) \/    |  |: \.   \\  | 
#    __/  \\  |.  |    __/  \\  // ___)(: (____/ //       (|  /      // ___)_   __/  \\  //  __'  \ |.  \    \. |   |.  |    //      /  // ___)_ |.  \    \. | 
#   /" \   :) /\  |\  /" \   :)(:  (    \        /       /|__/ \    (:      "| /" \   :)/   /  \\  \|    \    \ |   \:  |   |:  __   \ (:      "||    \    \ | 
#  (_______/ (__\_|_)(_______/  \__/     \"_____/       (_______)    \_______)(_______/(___/    \___)\___|\____\)    \__|   |__|  \___) \_______) \___|\____\) 
#
#

                                                                                                                                                            

{
    'name': "Modul Musyrif SISFO Pesantren",

    'summary': """
        Aplikasi SISFO Pesantren
        - Modul Musyrif untuk SISFO Pesantren""",

    'description': """
        Aplikasi SISFO Pesantren memiliki fitur-fitur sebagai berikut :
        ===============================================================
        * Modul Base / Dasar
        * Modul Akademik
        * Modul Musyrif
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
    'depends': ['base','pesantren_base','pesantren_keuangan', 'pesantren_kesantrian'],

    # always loaded
    'data': [
        'security/groups.xml',
        'security/musyrif_security.xml',
        'security/ir.model.access.csv',

        # data
        'views/menu.xml',
        # 'data/ks_musyrif_data.xml',
        
        # wizard
        'wizard/res_partner_change_pin.xml',
        'wizard/saldo.xml',
        
        # views
        'views/cek_santri.xml',
        'views/perijinan.xml',
        'views/mutabaah_harian.xml',
        'views/absen_malam.xml',
        'views/pelanggaran.xml',
        'views/kesehatan.xml',
        'views/prestasi_siswa.xml',
        'views/uang_saku.xml',
        'views/pos_wallet_transaction.xml',
        # 'views/keterangan.xml',

    ],
    'assets': {
        'web.assets_backend': [
            # "pesantren_musyrif/static/src/js/change_pin_popup.js",
            "pesantren_musyrif/static/src/js/change_pin_popup.js",
            "pesantren_musyrif/static/src/js/saldo_santri.js",
            # "pesantren_musyrif/static/src/xml/change_pin_popup.xml",
            # "pesantren_musyrif/static/src/js/change_pin_popup.css",
        ],
    },
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    "installable": True,
	"auto_install": False,
	"application": True,  
}
