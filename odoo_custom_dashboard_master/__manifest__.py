# -*- coding: utf-8 -*-
{
    'name' : 'Dashboard',
    'version' : '1.0',
    'summary': 'OWL',
    'sequence': -1,
    'description': """OWL Custom Dashboard""",
    'category': 'OWL',
    'depends' : ['base', 'web', 'sale', 'board', 'pesantren_orangtua', 'pesantren_kesantrian', 'pesantren_guruquran', 'pesantren_karyawan', "pesantren_guru"],
    'data': [
        'views/dashboard_keuangan.xml',
        'views/dashboard_kesantrian.xml',
        'views/dashboard_musyrif.xml',
        'views/dashboard_orangtua.xml',
        # 'views/dashboard_guruquran.xml',
        'views/dashboard_pos.xml',
        'views/dashboard_sekolah.xml',
        'views/dashboard_karyawan.xml', 
        'views/dashboard_perekrutan.xml',
        'views/dashboard_guru.xml',
        'views/dashboard_penagihan.xml',
        'views/dashboard_pembelian.xml',
        'views/dashboard_pendaftaran.xml',
        'views/dashboard_absensi.xml',
        'views/dashboard_keamanan.xml',
        'views/dashboard_cuti.xml',
        # 'views/dashboard_crm.xml',
        'views/dashboard_penjualan.xml',
        'views/sales_dashboard.xml',
        'views/dashboard_wallet.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'assets': {
        'web.assets_backend': [
            # Kesantrian
            'odoo_custom_dashboard_master/static/src/kesantrian/**/*.js', 
            'odoo_custom_dashboard_master/static/src/kesantrian/**/*.xml', 
            'odoo_custom_dashboard_master/static/src/kesantrian/**/*.scss', 
    
            # Keuangan
            'odoo_custom_dashboard_master/static/src/keuangan/**/*.js', 
            'odoo_custom_dashboard_master/static/src/keuangan/**/*.xml', 
            'odoo_custom_dashboard_master/static/src/keuangan/**/*.scss', 
            
            # Musyrif
            'odoo_custom_dashboard_master/static/src/musyrif/**/*.js', 
            'odoo_custom_dashboard_master/static/src/musyrif/**/*.xml', 
            'odoo_custom_dashboard_master/static/src/musyrif/**/*.scss',
             
            # Orangtua
            'odoo_custom_dashboard_master/static/src/orangtua/**/*.js', 
            'odoo_custom_dashboard_master/static/src/orangtua/**/*.xml', 
            'odoo_custom_dashboard_master/static/src/orangtua/**/*.scss', 
            
            # Guru Quran
            'odoo_custom_dashboard_master/static/src/guruquran/**/*.js', 
            'odoo_custom_dashboard_master/static/src/guruquran/**/*.xml', 
            'odoo_custom_dashboard_master/static/src/guruquran/**/*.scss', 
            
            # POS
            'odoo_custom_dashboard_master/static/src/pos/**/*.js', 
            'odoo_custom_dashboard_master/static/src/pos/**/*.xml', 
            'odoo_custom_dashboard_master/static/src/pos/**/*.scss', 

            # Sekolah
            'odoo_custom_dashboard_master/static/src/sekolah/**/*.js', 
            'odoo_custom_dashboard_master/static/src/sekolah/**/*.xml', 
            'odoo_custom_dashboard_master/static/src/sekolah/**/*.css', 
            
            #Keamanan
            'odoo_custom_dashboard_master/static/src/keamanan/**/*.js', 
            'odoo_custom_dashboard_master/static/src/keamanan/**/*.xml', 
            'odoo_custom_dashboard_master/static/src/keamanan/**/*.css', 


            #Karyawan
            'odoo_custom_dashboard_master/static/src/karyawan/**/*.js', 
            'odoo_custom_dashboard_master/static/src/karyawan/**/*.xml', 
            'odoo_custom_dashboard_master/static/src/karyawan/**/*.css', 

            #Perekrutan
            'odoo_custom_dashboard_master/static/src/perekrutan/**/*.js', 
            'odoo_custom_dashboard_master/static/src/perekrutan/**/*.xml', 
            'odoo_custom_dashboard_master/static/src/perekrutan/**/*.css', 

            #Guru
            'odoo_custom_dashboard_master/static/src/guru/**/*.js', 
            'odoo_custom_dashboard_master/static/src/guru/**/*.xml', 
            'odoo_custom_dashboard_master/static/src/guru/**/*.css', 
            #Penagihan
            'odoo_custom_dashboard_master/static/src/penagihan/**/*.js', 
            'odoo_custom_dashboard_master/static/src/penagihan/**/*.xml', 
            'odoo_custom_dashboard_master/static/src/penagihan/**/*.css', 

            #Pembelian
            'odoo_custom_dashboard_master/static/src/pembelian/**/*.js', 
            'odoo_custom_dashboard_master/static/src/pembelian/**/*.xml', 
            'odoo_custom_dashboard_master/static/src/pembelian/**/*.css', 

            #Pendafaran
            'odoo_custom_dashboard_master/static/src/pendaftaran/**/*.js', 
            'odoo_custom_dashboard_master/static/src/pendaftaran/**/*.xml', 
            'odoo_custom_dashboard_master/static/src/pendaftaran/**/*.css', 
            
            #Absensi
            'odoo_custom_dashboard_master/static/src/absensi/**/*.js', 
            'odoo_custom_dashboard_master/static/src/absensi/**/*.xml', 
            'odoo_custom_dashboard_master/static/src/absensi/**/*.css', 

            #Cuti
            'odoo_custom_dashboard_master/static/src/cuti/**/*.js', 
            'odoo_custom_dashboard_master/static/src/cuti/**/*.xml', 
            'odoo_custom_dashboard_master/static/src/cuti/**/*.css', 

            #Crm
            'odoo_custom_dashboard_master/static/src/crm/**/*.js', 
            'odoo_custom_dashboard_master/static/src/crm/**/*.xml', 
            'odoo_custom_dashboard_master/static/src/crm/**/*.css', 


            #Penjualan
            'odoo_custom_dashboard_master/static/src/penjualan/**/*.js', 
            'odoo_custom_dashboard_master/static/src/penjualan/**/*.xml', 
            'odoo_custom_dashboard_master/static/src/penjualan/**/*.css', 

 
            # #Inventory
            'odoo_custom_dashboard_master/static/src/inventory/**/*.js',
            'odoo_custom_dashboard_master/static/src/inventory/**/*.xml',
            'odoo_custom_dashboard_master/static/src/inventory/**/*.css', 

            
            # Wallet
            'odoo_custom_dashboard_master/static/src/wallet/**/*.js',
            'odoo_custom_dashboard_master/static/src/wallet/**/*.xml',
            'odoo_custom_dashboard_master/static/src/wallet/**/*.css', 
            


            'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css',
            
        ], 
        'web.assets_frontend': [ 
            'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css', 
            
        ],

    },
}
