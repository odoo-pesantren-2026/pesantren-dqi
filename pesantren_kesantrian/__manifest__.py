# -*- coding: utf-8 -*-
{
    'name': "Pesantren Kesantrian",

    'summary': """
        Aplikasi SISFO Pesantren
        - Modul Kesantrian""",

    'description': """  Aplikasi SISFO Pesantren
        - Modul Kesantrian
    """,

    'author': "PT. Cendana Teknika Utama",
    'website': "https://www.cendana2000.co.id",
    'category': 'Education',
    'version': '18.0.1.0',
    'license': 'LGPL-3',

    'depends': ['base', 'pesantren_base'],

    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',

        # data
        'views/menu.xml',
        'views/menu_satpam.xml',
        'data/ir_sequence_data.xml',
        'data/hr_job_data.xml',
        'data/cdn_surah_data.xml',
        'data/cdn_ayat_data.xml',

        # views
        'views/quran.xml',
        'views/guru.xml',
        'views/guru_quran.xml',
        'views/sesi_halaqoh.xml',
        'views/sesi_tahfidz.xml',
        'views/sesi_tahsin.xml',
        'views/tindakan_hukuman.xml',
        'views/data_pelanggaran.xml',
        'views/jns_pelanggaran.xml',
        'views/halaqoh.xml',
        'views/kesehatan.xml',
        'views/mutabaah.xml',
        'views/buku_tahsin.xml',
        'views/daftar_hadits.xml',
        'views/aset_pesantren.xml',
        'views/penilaian_halaqoh.xml',
        'views/nilai_tahfidz.xml',
        'views/nilai_tahsin.xml',
        'views/kamar_santri.xml',
        'views/pelanggaran.xml',
        'views/orangtua.xml',
        'views/santri.xml',
        'views/jns_prestasi.xml',
        'views/prestasi_siswa.xml',
        'views/mutabaah_harian.xml',
        'views/absen_halaqoh.xml',
        'views/absen_malam.xml',
        'views/musyrif.xml',
        'views/perijinan.xml',
        'views/absen_tahfidz_quran.xml',
        'views/tahfidz_hadits.xml',
        'views/absen_tahsin_quran.xml',
        'views/tahsin_quran.xml',
        'views/tahfidz_quran.xml',
        'views/cdn_ayat.xml',
        'views/mutabaah_kategori.xml',
        'views/mutabaah_sesi.xml',
        'views/satpam_perijinan.xml',
        'views/keterangan.xml',
        'wizards/wizard_checkout.xml',
        'wizards/wizard_santridata.xml',
        'wizards/wizard_checkin.xml',
        'wizards/Register/register.xml',
        'wizards/Akun/pencairan_saldo.xml',
        'wizards/Akun/penonaktifan.xml',
        'wizards/Akun/blokir.xml',
        'wizards/Akun/open_account.xml',
        'wizards/Akun/open_block.xml',
        'wizards/wizard_rekap_absensi.xml',
        'wizards/wizard_rekap_penilaian.xml',
        'wizards/Akun/kelola_pin.xml',
        'wizards/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pesantren_kesantrian/static/src/scss/style.scss',
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
