# -*- coding: utf-8 -*-

{
    'name': "Modul Dasar/Base SISFO Pesantren",

    'summary': """
        Aplikasi SISFO Pesantren
        - Modul Dasar / Base untuk SISFO Pesantren""",

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
    'version': '18.0.1.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'l10n_id', 'l10n_id_efaktur', 'mail', 'hr', 'sale', 'account', 'muk_web_theme', 'hr_attendance', 'hr_holidays', 'web_password_toggle', 'web_progress', 'queue_job'],

    'data': [
        'security/groups.xml',
        'security/hr_employee_security.xml',
        'security/ir.model.access.csv',
        'data/company_data.xml',
        'data/base_data.xml',
        'data/ir_sequence_data.xml',
        'data/cdn_tingkat_data.xml',
        'data/jenis_pegawai_data.xml',
        'data/l10n_id_fix.xml',

        # report
        'report/cetak_sertifikat_santri.xml',
        'report/cetak_kartu_santri.xml',

        # views (load before menu so actions are available)
        'views/jenis_pegawai_views.xml',
        'views/siswa.xml',
        'views/cutigroup.xml',
        'views/orangtua.xml',
        'views/ref_pekerjaan.xml',
        'views/ref_pendidikan.xml',
        'views/ref_propinsi.xml',
        'views/ref_kota.xml',
        'views/ref_kecamatan.xml',
        'views/ref_tahunajaran.xml',
        'views/biaya_tahunajaran.xml',
        'views/komponen_biaya.xml',
        'views/master_kelas.xml',
        'views/ruang_kelas.xml',
        'views/jurusan.xml',
        'views/guru.xml',
        'views/guru_karyawan.xml',
        'views/menu.xml',
        'views/sekolah.xml',
        'views/harga_khusus.xml',
        'views/invoice_view.xml',
        'views/aspek_penilaian.xml',
        'views/ref_jam_pelajaran.xml',
        'views/mata_pelajaran.xml',
        'views/jadwal_pelajaran.xml',
        'views/hr_views_inherit.xml',
        'views/account_menuitem_inherit.xml',
        'views/organisasi.xml',
        'views/ekstrakulikuler.xml',
        'views/mobile_fasilitas.xml',
        'views/res_config_setting_inherit.xml',
        'views/activation_result_wizard_views.xml',
        'views/kongfigurasi_jenjang.xml',

        # wizard
        'wizard/wizard_invoice.xml',
        'wizard/wizard_siswa.xml',
        'wizard/wizard_kartu.xml',
        'wizard/kenaikan_kelas.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pesantren_base/static/src/js/nontifikasi.js',
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": True,
}
