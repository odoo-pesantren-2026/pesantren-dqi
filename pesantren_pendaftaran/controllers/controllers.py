# -*- coding: utf-8 -*-
# from odoo import http
from odoo.exceptions import UserError
from odoo import http
from odoo.http import request
from datetime import date
import requests
import datetime
import base64
import tempfile
import os
import json
from .nobox import Nobox



class PesantrenBeranda(http.Controller):
    @http.route('/beranda_psb', type='http', auth='public')
    def index(self, **kwargs):

        # Ambil perusahaan yang aktif (current company)
        company = http.request.env.user.company_id

        # Ambil alamat perusahaan
        alamat_perusahaan = {
            'street': company.street or '',
            'street2': company.street2 or '',
            'city': company.city or '',
            'state': company.state_id.name if company.state_id else '',
            'zip': company.zip or '',
            'country': company.country_id.name if company.country_id else '',
        }

        # Gabungkan alamat menjadi satu string (opsional)
        alamat_lengkap = ', '.join(filter(None, [
            alamat_perusahaan['street'],
            alamat_perusahaan['street2'],
            alamat_perusahaan['city'],
            alamat_perusahaan['state'],
            alamat_perusahaan['zip'],
            alamat_perusahaan['country']
        ]))

         # Ambil nilai dari field konfigurasi
        config_obj = http.request.env['ir.config_parameter'].sudo() 

        tgl_mulai_pendaftaran = config_obj.get_param('pesantren_pendaftaran.tgl_mulai_pendaftaran')
        tgl_akhir_pendaftaran = config_obj.get_param('pesantren_pendaftaran.tgl_akhir_pendaftaran')
        tgl_mulai_seleksi = config_obj.get_param('pesantren_pendaftaran.tgl_mulai_seleksi')
        tgl_akhir_seleksi = config_obj.get_param('pesantren_pendaftaran.tgl_akhir_seleksi')
        tgl_pengumuman_hasil_seleksi = config_obj.get_param('pesantren_pendaftaran.tgl_pengumuman_hasil_seleksi')
        tgl_mulai_pendaftaran_gel_2 = config_obj.get_param('pesantren_pendaftaran.tgl_mulai_pendaftaran_gel_2')
        tgl_akhir_pendaftaran_gel_2 = config_obj.get_param('pesantren_pendaftaran.tgl_akhir_pendaftaran_gel_2')
        tgl_mulai_seleksi_gel_2 = config_obj.get_param('pesantren_pendaftaran.tgl_mulai_seleksi_gel_2')
        tgl_akhir_seleksi_gel_2 = config_obj.get_param('pesantren_pendaftaran.tgl_akhir_seleksi_gel_2')
        tgl_pengumuman_hasil_seleksi_gel_2 = config_obj.get_param('pesantren_pendaftaran.tgl_pengumuman_hasil_seleksi_gel_2')

        # Set nilai default dinamis jika parameter kosong
        if not tgl_mulai_pendaftaran:
            tgl_mulai_pendaftaran_dt = datetime.datetime.now() + datetime.timedelta(days=1)
            tgl_mulai_pendaftaran = tgl_mulai_pendaftaran_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_mulai_pendaftaran_dt = datetime.datetime.strptime(tgl_mulai_pendaftaran, '%Y-%m-%d %H:%M:%S')

        if not tgl_akhir_pendaftaran:
            tgl_akhir_pendaftaran_dt = tgl_mulai_pendaftaran_dt + datetime.timedelta(days=3)
            tgl_akhir_pendaftaran = tgl_akhir_pendaftaran_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_akhir_pendaftaran_dt = datetime.datetime.strptime(tgl_akhir_pendaftaran, '%Y-%m-%d %H:%M:%S')

        if not tgl_mulai_seleksi:
            tgl_mulai_seleksi_dt = tgl_akhir_pendaftaran_dt
            tgl_mulai_seleksi = tgl_mulai_seleksi_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_mulai_seleksi_dt = datetime.datetime.strptime(tgl_mulai_seleksi, '%Y-%m-%d %H:%M:%S')

        if not tgl_akhir_seleksi:
            tgl_akhir_seleksi_dt = tgl_mulai_seleksi_dt + datetime.timedelta(days=3)
            tgl_akhir_seleksi = tgl_akhir_seleksi_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_akhir_seleksi_dt = datetime.datetime.strptime(tgl_akhir_seleksi, '%Y-%m-%d %H:%M:%S')

        if not tgl_pengumuman_hasil_seleksi:
            tgl_pengumuman_hasil_seleksi_dt = tgl_akhir_seleksi_dt + datetime.timedelta(days=2)
            tgl_pengumuman_hasil_seleksi = tgl_pengumuman_hasil_seleksi_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_pengumuman_hasil_seleksi_dt = datetime.datetime.strptime(tgl_pengumuman_hasil_seleksi, '%Y-%m-%d %H:%M:%S')
        
        if not tgl_mulai_pendaftaran_gel_2:
            tgl_mulai_pendaftaran_gel_2_dt = datetime.datetime.now() + datetime.timedelta(days=1)
            tgl_mulai_pendaftaran_gel_2 = tgl_mulai_pendaftaran_gel_2_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_mulai_pendaftaran_gel_2_dt = datetime.datetime.strptime(tgl_mulai_pendaftaran_gel_2, '%Y-%m-%d %H:%M:%S')

        if not tgl_akhir_pendaftaran_gel_2:
            tgl_akhir_pendaftaran_gel_2_dt = tgl_mulai_pendaftaran_gel_2_dt + datetime.timedelta(days=3)
            tgl_akhir_pendaftaran_gel_2 = tgl_akhir_pendaftaran_gel_2_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_akhir_pendaftaran_gel_2_dt = datetime.datetime.strptime(tgl_akhir_pendaftaran_gel_2, '%Y-%m-%d %H:%M:%S')

        if not tgl_mulai_seleksi_gel_2:
            tgl_mulai_seleksi_gel_2_dt = tgl_akhir_pendaftaran_gel_2_dt
            tgl_mulai_seleksi_gel_2 = tgl_mulai_seleksi_gel_2_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_mulai_seleksi_gel_2_dt = datetime.datetime.strptime(tgl_mulai_seleksi_gel_2, '%Y-%m-%d %H:%M:%S')

        if not tgl_akhir_seleksi_gel_2:
            tgl_akhir_seleksi_gel_2_dt = tgl_mulai_seleksi_gel2_dt + datetime.timedelta(days=3)
            tgl_akhir_seleksi_gel_2 = tgl_akhir_seleksi_gel_2_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_akhir_seleksi_gel_2_dt = datetime.datetime.strptime(tgl_akhir_seleksi_gel_2, '%Y-%m-%d %H:%M:%S')

        if not tgl_pengumuman_hasil_seleksi_gel_2:
            tgl_pengumuman_hasil_seleksi_gel_2_dt = tgl_akhir_seleksi_gel_2_dt + datetime.timedelta(days=2)
            tgl_pengumuman_hasil_seleksi_gel_2 = tgl_pengumuman_hasil_seleksi_gel_2_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_pengumuman_hasil_seleksi_gel_2_dt = datetime.datetime.strptime(tgl_pengumuman_hasil_seleksi_gel_2, '%Y-%m-%d %H:%M:%S')

        # Format tanggal manual dalam bahasa Indonesia
        def format_tanggal_manual(dt):
            bulan_indonesia = [
                "Januari", "Februari", "Maret", "April", "Mei", "Juni",
                "Juli", "Agustus", "September", "Oktober", "November", "Desember"
            ]
            return f"{dt.day} {bulan_indonesia[dt.month - 1]} {dt.year}"

        # Format tanggal untuk ditampilkan di halaman
        tgl_mulai_pendaftaran_formatted = format_tanggal_manual(tgl_mulai_pendaftaran_dt)
        tgl_akhir_pendaftaran_formatted = format_tanggal_manual(tgl_akhir_pendaftaran_dt)
        tgl_mulai_seleksi_formatted = format_tanggal_manual(tgl_mulai_seleksi_dt)
        tgl_akhir_seleksi_formatted = format_tanggal_manual(tgl_akhir_seleksi_dt)
        tgl_pengumuman_hasil_seleksi_formatted = format_tanggal_manual(tgl_pengumuman_hasil_seleksi_dt)
        tgl_mulai_pendaftaran_gel_2_formatted = format_tanggal_manual(tgl_mulai_pendaftaran_gel_2_dt)
        tgl_akhir_pendaftaran_gel_2_formatted = format_tanggal_manual(tgl_akhir_pendaftaran_gel_2_dt)
        tgl_mulai_seleksi_gel_2_formatted = format_tanggal_manual(tgl_mulai_seleksi_gel_2_dt)
        tgl_akhir_seleksi_gel_2_formatted = format_tanggal_manual(tgl_akhir_seleksi_gel_2_dt)
        tgl_pengumuman_hasil_seleksi_gel_2_formatted = format_tanggal_manual(tgl_pengumuman_hasil_seleksi_gel_2_dt)

        html_content = f"""
                    <!doctype html>
                    <html lang="en">

            <head>
            <!-- Primary Meta Tags --> 
            <title>PSB Daarul Qur`an Istiqomah</title> 
            <meta name="title" content="PSB Daarul Qur`an Istiqomah" /> 
            <meta name="description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
 
            <!-- Open Graph / Facebook --> 
            <meta property="og:type" content="website" /> 
            <meta property="og:url" content="https://aplikasi.dqi.ac.id/pendaftaran" /> 
            <meta property="og:title" content="PSB Daarul Qur`an Istiqomah" /> 
            <meta property="og:description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
            <meta property="og:image" content="https://drive.usercontent.google.com/download?id=1VZRccbFtq82wTNcReEq43piA_GJQddcm" /> 
 
            <!-- Twitter --> 
            <meta property="twitter:card" content="summary_large_image" /> 
            <meta property="twitter:url" content="https://aplikasi.dqi.ac.id/pendaftaran" /> 
            <meta property="twitter:title" content="PSB Daarul Qur`an Istiqomah" /> 
            <meta property="twitter:description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
            <meta property="twitter:image" content="https://drive.usercontent.google.com/download?id=1VZRccbFtq82wTNcReEq43piA_GJQddcm" />

            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Daarul Qur'an Istiqomah</title>
            <link rel="icon" type="image/x-icon" href="/pesantren_pendaftaran/static/img/favicon.ico?v=1">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet"
                integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
            
            </head>
            <style>
            .bg-body-grenyellow {{ background: white; }}

            .rounded-90 {{ border-radius: 0 0 25% 0; }}

            .p-auto {{ padding: 6% 0; }}

            .stepper {{ justify-content: space-around; align-items: center; margin-top: 50px; }}

            .step {{ text-align: center; position: relative; padding-top: 30px; }}

            .step-circle {{ 
                width: 50px;
                height: 50px;
                background-color: #009688;
                color: white;
                font-size: 1.5rem;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto;
                position: relative;z-index: 1; }}

            .step-line {{ 
                width: 100%;
                height: 2px;
                background-color: #009688;
                position: absolute;
                top: 55px;
                left: 0;
                z-index: -10; }}

            .step:last-child .step-line {{ 
                width: 50%; }}

            .step:first-child .step-line {{ 
                width: 50%;
                left: 50%; }}

            .text-green {{ 
                color: #009688; }}
            .footer {{ 
                background-color: #4a4a4a;
             }}
            .footer h5 {{
                font-weight: bold;
            }}
            .footer p, .footer a {{
            color: #ffffff;
            font-size: 0.9rem;
            }}
            .footer a:hover {{
            text-decoration: underline;
            }}
            .footer hr {{
            border-color: #ffffff;
            opacity: 0.3;
            }}
            .card p{{
            margin: 0;
            }}
            @media(max-width:768px) {{
            h1{{
                font-size:1.5rem;
            }}
            h3{{
                font-size: 1rem;
            }}
            h5{{
                font-size: 0.9rem;
            }}
            .step{{
                padding: 5px;
                padding-top: 20px;
                margin: 30px 0;
                box-shadow: var(--bs-box-shadow) !important;
                border-radius: 10px;
            }}
            .bg-body-grenyellow.rounded-90{{
                border-radius: 0;
            }}
            .w-set-auto{{
                width: 100%;
            }}
            }}

            /* Styling umum */
            .card-item {{
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100%; /* Pastikan tinggi fleksibel */
                text-align: center; /* Pusatkan semua teks */
            }}

            .card-value {{
                font-weight: bold;
                font-size: 2rem; /* Ukuran dasar untuk angka */
                line-height: 1; /* Pastikan tidak ada spasi tambahan */
                margin: 0; /* Hapus margin */
                height: 50px;
            }}

            .card-label {{
                font-weight: 600;
                color: #6c757d; /* Warna teks sekunder */
                font-size: 1.25rem; /* Ukuran dasar untuk label */
                margin: 0; /* Hapus margin */
                line-height: 1.2; /* Sedikit lebih tinggi untuk label */
                height: 30px;
            }}

            /* Responsif untuk layar medium */
            @media (max-width: 768px) {{
                .card-value {{
                    font-size: 1.75rem; /* Lebih kecil untuk tablet */
                }}
                .card-label {{
                    font-size: 1rem; /* Lebih kecil untuk label tablet */
                }}
            }}

            /* Responsif untuk layar kecil */
            @media (max-width: 576px) {{
                .card-value {{
                    font-size: 1.5rem; /* Lebih kecil untuk layar kecil */
                    height: 30px;
                }}
                .card-label {{
                    font-size: 0.875rem; /* Ukuran kecil untuk label */
                }}
            }}

            /* Responsif untuk layar sangat kecil */
            @media (max-width: 400px) {{
                .card-value {{
                    font-size: 1.25rem; /* Ukuran paling kecil */
                }}
                .card-label {{
                    font-size: 0.75rem; /* Ukuran kecil untuk label */
                }}
            }}

            </style>

            <body style="background-color: white; height:100vh;">
            <!-- Navbar -->
            <nav class="navbar navbar-expand-lg bg-body-grenyellow shadow sticky-top">
            <div class="container d-flex">
                <a class="navbar-brand d-flex  fw-bold" href="#">
                <img src="https://i.ibb.co.com/1MFsvMq/1731466812700.png" alt="Icon Daarul Qur’an Istiqomah" class="me-2 d-md-block d-none" width="40" height="40">
                <span class="d-md-block d-none h3">
                    PSB Daarul Qur’an Istiqomah
                </span> 
                <span class="d-md-none d-block h3">
                    PSBDQI
                </span> 
                </a>
                <div class="d-flex justify-content-end" id="navbarSupportedContent">
                <div>
                    <!-- Buttons for Pendaftaran and Login -->
                    <a href="/psb" class="btn btn-light ms-2" type="submit">Pendaftaran</a>
                    <a href="/login" class="btn btn-warning ms-2" type="submit">Login</a>
                </div>
                </div>
            </div>
            </nav>
            <!-- Navbar end -->


            <!-- banner -->
            <div class="bg-body-grenyellow rounded-90">
                <div class="container py-3 d-md-flex d-block text-light justify-content-center align-items-center">
                <div class="me-5 w-set-auto d-flex justify-content-center">
                    <img src="https://i.ibb.co.com/1MFsvMq/1731466812700.png" alt="" width="65%">
                </div>
                <div class="ms-md-3 m-0 text-center text-md-start">
                    <h1 class="fw-bold">Pendaftaran Santri Baru</h1>
                    <h3 class="fw-bold pb-3">Pondok Pesantren Daarul Qur’an Istiqomah</h3>
                    <h5 class="fw-bold">Daarul Qur’an Istiqomah Boarding School for Education and Science</h5>
                    <h5 class="fw-bold">Tahun Ajaran 2026 - 2027</h5>
                    <a href="/psb" class="btn btn-light rounded-5 text-primary mt-2">Daftar Sekarang</a>
                </div>
                </div>
            </div>
            <!-- banner end -->

            <!-- Step Pendaftaran -->
            <!-- <div class="container">
                <div class="row shadow rounded mt-5 mb-5 p-5" style="background-color: #EAF1FB;">
                    <div class="col-3 col-sm-3 col-md-3 col-lg-3">
                        <div class="card-item">
                            <span class="card-value" id="count-kuota">0</span>
                            <span class="card-label">Jumlah Kuota</span>
                        </div>
                    </div>
                    <div class="col-3 col-sm-3 col-md-3 col-lg-3">
                        <div class="card-item">
                            <span class="card-value" id="count-pendaftar">0</span>
                            <span class="card-label">Jumlah Pendaftar</span>
                        </div>
                    </div>
                    <div class="col-3 col-sm-3 col-md-3 col-lg-3">
                        <div class="card-item">
                            <span class="card-value" id="count-diterima">0</span>
                            <span class="card-label">Jumlah Diterima</span>
                        </div>
                    </div>
                    <div class="col-3 col-sm-3 col-md-3 col-lg-3">
                        <div class="card-item">
                            <span class="card-value" id="count-sisa">0</span>
                            <span class="card-label">Sisa Kuota</span>
                        </div>
                    </div>
                </div>
            </div> -->
            
            <div class="container text-center my-3">
                <h1 class="fw-bold"><span class="text-green">Alur</span> Pendaftaran Online</h1>
                <div class="container">
                <div class="stepper d-md-flex d-block">
                    <div class="step">
                    <div class="step-circle">1</div>
                    <div class="step-line d-md-block d-none"></div>
                    <p class="mt-3 fw-bold">Pembuatan Akun</p>
                    <p class="text-muted">Mengisi identitas calon peserta didik sekaligus pembuatan akun untuk mendapatkan Nomor
                        Registrasi.</p>
                    </div>
                    <div class="step">
                    <div class="step-circle">2</div>
                    <div class="step-line d-md-block d-none"></div>
                    <p class="mt-3 fw-bold">Login & Melengkapi Data</p>
                    <p class="text-muted">Melengkapi data peserta didik, data orang tua / wali atau mahram khususnya santri putri.
                    </p>
                    </div>
                    <div class="step">
                    <div class="step-circle">3</div>
                    <div class="step-line d-md-block d-none"></div>
                    <p class="mt-3 fw-bold">Mengunggah Berkas</p>
                    <p class="text-muted">Mengunggah berkas persyaratan dan berkas pendukung lainnya yang berupa gambar / foto.
                    </p>
                    </div>
                    <div class="step">
                    <div class="step-circle">4</div>
                    <div class="step-line d-md-block d-none"></div>
                    <p class="mt-3 fw-bold">Pembayaran</p>
                    <p class="text-muted">Melakukan pembayaran biaya pendaftaran sesuai pendidikan yang telah dipilih.</p>
                    </div>
                    <div class="step">
                    <div class="step-circle">5</div>
                    <div class="step-line d-md-block d-none"></div>
                    <p class="mt-3 fw-bold">Cetak Pendaftaran</p>
                    <p class="text-muted">Cetak atau simpan Nomor Registrasi sebagai bukti pendaftaran untuk ditunjukkan ke
                        petugas PSB.</p>
                    </div>
                </div>
                </div>
            </div>
            <!-- End step pendaftaran -->


            <!-- Syarat Pendaftaran -->
            <div class="container my-5">
                <div class="row align-items-center">
                <!-- Text Section -->
                <div class="col-md-6">
                    <h2 class="fw-bold"><span class="text-green ">Syarat</span> Pendaftaran</h2>
                    <p>Untuk memenuhi persyaratan pendaftaran santri baru, perlu beberapa berkas yang harus disiapkan:</p>
                    <ul class="list-unstyled d-grid gap-2">
                    <li class="d-flex"><i class="bi bi-check-circle-fill me-2 text-warning"></i>
                        <div class="d-flex flex-column"><strong>Fotocopy Akta Kelahiran 2lembar</strong> </div>
                    </li>
                    <li class="d-flex"><i class="bi bi-check-circle-fill me-2 text-warning"></i>
                        <div class="d-flex flex-column"><strong>Fotocopy KK 1lembar</strong></div>
                    </li>
                    <li class="d-flex"><i class="bi bi-check-circle-fill me-2 text-warning"></i>
                        <div class="d-flex flex-column"><strong>Fotocopy KTP Orangtua (Masing-masing 1lembar)</strong></div>
                    </li>
                    <li class="d-flex"><i class="bi bi-check-circle-fill me-2 text-warning"></i>
                        <div class="d-flex flex-column"><strong>Fotocopy Raport Semester akhir (menyusul)</strong>
                        </div>
                    </li>
                    <li class="d-flex"><i class="bi bi-check-circle-fill me-2 text-warning"></i>
                        <div class="d-flex flex-column"><strong>Pas Foto berwarna ukuran 3x4 4lembar</strong> </div>
                    </li>
                    <li class="d-flex"><i class="bi bi-check-circle-fill me-2 text-warning"></i>
                        <div class="d-flex flex-column"><strong>Pas Foto Orangtua masing-masing 1lembar (Khusus Pendaftar KB dan TK)</strong> </div>
                    </li>
                    <li class="d-flex"><i class="bi bi-check-circle-fill me-2 text-warning"></i>
                        <div class="d-flex flex-column"><strong>Berkas dimasukkan dalam Map warna hijau dan diberi nama serta lembaga pendidikan</strong> </div>
                    </li>
                    </ul>
                </div>
                <!-- Image Section -->
                <div class="col-md-6">
                    <img src="pesantren_pendaftaran/static/src/img/PAGE2.44b0e259.png" class="img-fluid rounded-4"
                    alt="Syarat Pendaftaran">
                </div>
                </div>
            </div>
            <!-- Syarat Pendaftaran End -->

            <!-- Alur Penyerahan Santri -->
            <div class="container mt-5">
                <h1 class="fw-bold">Alur <span class="text-green">Penyerahan Santri</span></h1>
                <div class="row justify-content-center">
                <!-- Card 1 -->
        
                <!-- Card 2 -->
                <div class="col-md-4 text-center my-2">
                    <div class="card p-4 shadow border-0 h-100">
                    <div class="circle-icon mb-3">
                        <i class="bi bi-file-earmark-text-fill h1 text-green"></i>
                    </div>
                    <h2 class="step-number">2</h2>
                    <h5 class="font-weight-bold mt-3">Konfirmasi Nomor Registrasi</h5>
                    <p>Menyerahkan Nomor Registrasi dan bukti pendaftaran online kepada petugas PSB.</p>
                    <div class="bottom-icon mt-4">
                        <i class="bi bi-handshake text-success"></i>
                    </div>
                    </div>
                </div>
                <!-- Card 3 -->
                <div class="col-md-4 text-center my-2">
                    <div class="card p-4 shadow border-0 h-100">
                    <div class="circle-icon mb-3">
                        <i class="bi bi-person-check-fill h1 text-green"></i>
                    </div>
                    <h2 class="step-number">3</h2>
                    <h5 class="font-weight-bold mt-3">Ikrar Santri</h5>
                    <p>Melakukan Ikrar Santri dan kesediaan mengikuti aturan yang ditetapkan Pondok.
                    </p>
                    </div>
                </div>
                <!-- Card 4 -->
                <div class="col-md-4 text-center my-2">
                    <div class="card p-4 shadow border-0 h-100">
                    <div class="circle-icon mb-3">
                        <i class="bi bi-box-seam-fill h1 text-green"></i>
                    </div>
                    <h2 class="step-number">4</h2>
                    <h5 class="font-weight-bold mt-3">Pengambilan Seragam</h5>
                    <p>Pengambilan seragam sesuai dengan ukuran yang telah dipilih oleh pendaftar. </p>
                    <div class="bottom-icon mt-4">
                        <i class="bi bi-shirt text-info"></i>
                    </div>
                    </div>
                </div>
                <!-- Card 5 -->
                <div class="col-md-4 text-center my-2">
                    <div class="card p-4 shadow border-0 h-100">
                    <div class="circle-icon mb-3">
                        <i class="bi bi-people h1 text-green"></i>
                    </div>
                    <h2 class="step-number">5</h2>
                    <h5 class="font-weight-bold mt-3">Sowan Pengasuh</h5>
                    <p>Penyerahan calon peserta didik oleh orangtua / wali kepada pengasuh </p>
                    <div class="bottom-icon mt-4">
                        <i class="bi bi-handshake text-success"></i>
                    </div>
                    </div>
                </div>
                <!-- Card 6 -->
                <div class="col-md-4 text-center my-2">
                    <div class="card p-4 shadow border-0 h-100">
                    <div class="circle-icon mb-3">
                        <i class="bi bi-buildings h1 text-green"></i>
                    </div>
                    <h2 class="step-number">6</h2>
                    <h5 class="font-weight-bold mt-3">Asrama Santri</h5>
                    <p>Santri baru menempati asrama yang telah ditetepkan oleh pengurus. </p>
                    </div>
                </div>
                </div>
            </div>
            <!-- Alur Penyerahan Santri end-->

            <!-- Informasi Pelayanan Pendaftaran -->
            <div class="container my-5">
                <div class="row align-items-center">
                <div class="col-md-6">
                    <img src="pesantren_pendaftaran/static/src/img/PAGE3.e3b6d704.png" alt="Image" class="rounded-custom img-fluid" />
                </div>
                <div class="col-md-6 col-sm-12">
                    <h3 class="fw-bold"><span class="text-primary ">Informasi</span> Pelayanan Pendaftaran</h3>
                    <div class="accordion" id="accordionExample">
                    <div class="accordion-item mb-3">
                        <h2 class="accordion-header" id="headingOne">
                        <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapseOne"
                            aria-expanded="true" aria-controls="collapseOne">
                            Pembukaan Pendaftaran & Kantor Layanan:
                        </button>
                        </h2>
                        <div id="collapseOne" class="accordion-collapse collapse show" aria-labelledby="headingOne"
                        data-bs-parent="#accordionExample">
                        <div class="accordion-body">
                            <p class="m-0">Tanggal:</p>
                            <p class="fw-bold">1 Desamber 2025 s.d. 31 Januari 2026</p>
                            <p class="m-0">Tempat Layanan:</p>
                            <p class="fw-bold">Kantor Yayasan Daarul Qur'an Istiqomah</p>
                        
                        </div>
                        </div>
                    </div>
                    <div class="accordion-item mb-3">
                        <h2 class="accordion-header" id="headingTwo">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse"
                            data-bs-target="#collapseTwo" aria-expanded="false" aria-controls="collapseTwo">
                            Verifikasi Berkas:
                        </button>
                        </h2>
                        <div id="collapseTwo" class="accordion-collapse collapse" aria-labelledby="headingTwo"
                        data-bs-parent="#accordionExample">
                        <div class="accordion-body">
                            <!-- Konten untuk Verifikasi Berkas -->
                            <p class="m-0">Tanggal:</p>
                            <p class="fw-bold">Gelombang 1{tgl_mulai_pendaftaran_formatted} s.d {tgl_akhir_pendaftaran_formatted}</p>
                            <p class="fw-bold">Gelombang 2{tgl_mulai_pendaftaran_gel_2_formatted} s.d {tgl_akhir_pendaftaran_gel_2_formatted}</p>
                            <p class="m-0">Tempat Penerimaan:</p>
                            <p class="fw-bold">Pondok Pesantren Daarul Qur'an Istiqomah</p>
                            <p>Kantor Yayasan Daarul Qur'an Istiqomah<br>
                            Jl. H. Boedjasin Simpang 3 Al Manar</p>

                        </div>
                        </div>
                    </div>
                    <div class="accordion-item">
                        <h2 class="accordion-header" id="headingThree">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse"
                            data-bs-target="#collapseThree" aria-expanded="false" aria-controls="collapseThree">
                            Waktu Pelayanan:
                        </button>
                        </h2>
                        <div id="collapseThree" class="accordion-collapse collapse" aria-labelledby="headingThree"
                        data-bs-parent="#accordionExample">
                        <div class="accordion-body">
                            <!-- Konten untuk Waktu Pelayanan -->
                            <p class="m-0">Pagi:</p>
                            <p class="fw-bold">08.15 ~ 12.30 WIB</p>
                            <p class="m-0">Siang:</p>
                            <p class="fw-bold">13.30 ~ 15.50 WIB</p>
                        </div>
                        </div>
                    </div>
                    </div>
                </div>
                </div>
            </div>
            <!-- Informasi Pelayanan Pendaftaran end-->

            # <!-- Footer -->
            # <footer class="footer py-4">
            #     <div class="container">
            #     <div class="row ">
            #         <div class="col-md-4">
            #         <h5>Pondok Pesantren Daarul Qur’an Istiqomah</h5>
            #         <p>
            #             {alamat_lengkap} <br>
            #             Telp. (0888-307-7077)
            #         </p>
            #         </div>
            #         <div class="col-md-4">
            #         <h5>Social</h5>
            #         <ul class="list-unstyled">
            #             <li><a href="https://www.facebook.com/daquistiqomah?mibextid=ZbWKwL" class=""><i class="bi bi-facebook"></i> Facebook</a></li>
            #             <li><a href="https://www.instagram.com/dqimedia?igsh=NTVwdWlwd3o5MTF1" class=""><i class="bi bi-instagram"></i> Instagram</a></li>
            #             <li><a href="https://youtube.com/@dqimedia?si=6_A8Vr3nysaegI7B" class=""><i class="bi bi-youtube"></i> Youtube</a></li>
            #         </ul>
            #         </div>
            #         <div class="col-md-4">
            #         <h5><i class="bi bi-telephone"></i> Pusat Layanan Informasi</h5>
            #         <p>
            #             0822 5207 9785
            #         </p>
            #         </div>
            #     </div>
            #     <div class="text-center  mt-4">
            #         <hr class="border-white">
            #         <p>©Copyright 2025 - Daarul Qur’an Istiqomah</p>
            #     </div>
            #     </div>
            # </footer>
            
            <!-- Footer end -->
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"
                integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz"
                crossorigin="anonymous"></>

                <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
                <script>

                // Fungsi easing: Memulai lambat, kemudian cepat (Ease In Out Cubic)
                // function easeInOutCubic(t) {{
                //    return t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1;
                // }}

                // Fungsi untuk animasi menghitung dengan ancang-ancang yang lebih lama
                // function animateCount(elementId) {{
                //    const element = document.getElementById(elementId);
                //    const targetValue = parseInt(element.getAttribute('data-value'), 10);
                //    let currentValue = 0;

                    // Durasi animasi (ms)
                    // const duration = 2500; // Menambah durasi sedikit untuk memberi efek ancang-ancang yang lebih lama
                    // let startTime = null;

                    // Fungsi untuk update angka setiap frame
                    // function updateNumber(currentTime) {{
                    // if (!startTime) startTime = currentTime; // Inisialisasi waktu mulai animasi
                    // let elapsedTime = currentTime - startTime; // Waktu yang telah berlalu
                    // let progress = elapsedTime / duration; // Normalisasi progress waktu antara 0 dan 1

                    // if (progress > 1) progress = 1; // Membatasi progress agar tidak melebihi 1

                    // Membuat animasi "ancang-ancang" yang lebih lama
                    // let easingProgress = easeInOutCubic(progress);
                    // Memberikan sedikit "slow start" di awal untuk memperpanjang transisi awal
                    // let dynamicProgress = progress < 0.4 ? easingProgress * 0.6 : easingProgress; // 40% pertama lebih lambat

                    // Hitung nilai yang akan ditampilkan berdasarkan progress
                    // let increment = Math.floor(targetValue * dynamicProgress);

                    // Update nilai elemen
                    // element.textContent = increment;

                    // Jika progress sudah mencapai 100%, hentikan animasi
                    // if (progress < 1) {{
                    //    requestAnimationFrame(updateNumber);
                    //}}
                    //}}

                    // Mulai animasi dengan requestAnimationFrame
                    //requestAnimationFrame(updateNumber);
                //}}

                // Panggil fungsi untuk setiap elemen setelah halaman dimuat
                // document.addEventListener("DOMContentLoaded", () => {{
                    // animateCount("count-kuota");
                    // animateCount("count-pendaftar");
                    // animateCount("count-diterima");
                    // animateCount("count-sisa");
                //}});

                function easeInOutCubic(t) {{
    return t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1;
}}

function animateCount(elementId, targetValue) {{
    const element = document.getElementById(elementId);
    let currentValue = parseInt(element.textContent, 10) || 0;

    const duration = 2500; // Durasi animasi (ms)
    let startTime = null;

    function updateNumber(currentTime) {{
        if (!startTime) startTime = currentTime;
        const elapsedTime = currentTime - startTime;
        const progress = Math.min(elapsedTime / duration, 1);
        const dynamicValue = currentValue + (targetValue - currentValue) * easeInOutCubic(progress);

        element.textContent = Math.round(dynamicValue);

        if (progress < 1) {{
            requestAnimationFrame(updateNumber);
        }}
    }}

    requestAnimationFrame(updateNumber);
}}




                </script>
            </body>

            </html>
        """
        return request.make_response(html_content, headers=[('Content-Type', 'text/html')])


class PesantrenPendaftaran(http.Controller):
    @http.route('/psb', auth='public')
    def index(self, **kw):

    

        # Ambil nilai dari field konfigurasi
        config_obj = http.request.env['ir.config_parameter'].sudo()

        tgl_mulai_pendaftaran = config_obj.get_param('pesantren_pendaftaran.tgl_mulai_pendaftaran')
        tgl_akhir_pendaftaran = config_obj.get_param('pesantren_pendaftaran.tgl_akhir_pendaftaran')
        tgl_mulai_seleksi = config_obj.get_param('pesantren_pendaftaran.tgl_mulai_seleksi')
        tgl_akhir_seleksi = config_obj.get_param('pesantren_pendaftaran.tgl_akhir_seleksi')
        tgl_pengumuman_hasil_seleksi = config_obj.get_param('pesantren_pendaftaran.tgl_pengumuman_hasil_seleksi')
        tgl_mulai_pendaftaran_gel_2 = config_obj.get_param('pesantren_pendaftaran.tgl_mulai_pendaftaran_gel_2')
        tgl_akhir_pendaftaran_gel_2 = config_obj.get_param('pesantren_pendaftaran.tgl_akhir_pendaftaran_gel_2')
        tgl_mulai_seleksi_gel_2 = config_obj.get_param('pesantren_pendaftaran.tgl_mulai_seleksi_gel_2')
        tgl_akhir_seleksi_gel_2 = config_obj.get_param('pesantren_pendaftaran.tgl_akhir_seleksi_gel_2')
        tgl_pengumuman_hasil_seleksi_gel_2 = config_obj.get_param('pesantren_pendaftaran.tgl_pengumuman_hasil_seleksi_gel_2')
        is_halaman_pendaftaran = config_obj.get_param('pesantren_pendaftaran.is_halaman_pendaftaran')
        is_halaman_pengumuman = config_obj.get_param('pesantren_pendaftaran.is_halaman_pengumuman')

        # Set nilai default dinamis jika parameter kosong
        if not tgl_mulai_pendaftaran:
            tgl_mulai_pendaftaran_dt = datetime.datetime.now() + datetime.timedelta(days=1)
            tgl_mulai_pendaftaran = tgl_mulai_pendaftaran_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_mulai_pendaftaran_dt = datetime.datetime.strptime(tgl_mulai_pendaftaran, '%Y-%m-%d %H:%M:%S')

        if not tgl_akhir_pendaftaran:
            tgl_akhir_pendaftaran_dt = tgl_mulai_pendaftaran_dt + datetime.timedelta(days=3)
            tgl_akhir_pendaftaran = tgl_akhir_pendaftaran_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_akhir_pendaftaran_dt = datetime.datetime.strptime(tgl_akhir_pendaftaran, '%Y-%m-%d %H:%M:%S')

        if not tgl_mulai_seleksi:
            tgl_mulai_seleksi_dt = tgl_akhir_pendaftaran_dt
            tgl_mulai_seleksi = tgl_mulai_seleksi_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_mulai_seleksi_dt = datetime.datetime.strptime(tgl_mulai_seleksi, '%Y-%m-%d %H:%M:%S')

        if not tgl_akhir_seleksi:
            tgl_akhir_seleksi_dt = tgl_mulai_seleksi_dt + datetime.timedelta(days=3)
            tgl_akhir_seleksi = tgl_akhir_seleksi_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_akhir_seleksi_dt = datetime.datetime.strptime(tgl_akhir_seleksi, '%Y-%m-%d %H:%M:%S')

        if not tgl_pengumuman_hasil_seleksi:
            tgl_pengumuman_hasil_seleksi_dt = tgl_akhir_seleksi_dt + datetime.timedelta(days=2)
            tgl_pengumuman_hasil_seleksi = tgl_pengumuman_hasil_seleksi_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_pengumuman_hasil_seleksi_dt = datetime.datetime.strptime(tgl_pengumuman_hasil_seleksi, '%Y-%m-%d %H:%M:%S')
       
       
        # SEt Pendaftaran Gelombang 2
        if not tgl_mulai_pendaftaran_gel_2:
            tgl_mulai_pendaftaran_gel_2_dt = datetime.datetime.now() + datetime.timedelta(days=1)
            tgl_mulai_pendaftaran_gel_2 = tgl_mulai_pendaftaran_gel_2_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_mulai_pendaftaran_gel_2_dt = datetime.datetime.strptime(tgl_mulai_pendaftaran_gel_2, '%Y-%m-%d %H:%M:%S')

        if not tgl_akhir_pendaftaran_gel_2:
            tgl_akhir_pendaftaran_gel_2_dt = tgl_mulai_pendaftaran_gel_2_dt + datetime.timedelta(days=3)
            tgl_akhir_pendaftaran_gel_2 = tgl_akhir_pendaftaran_gel_2_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_akhir_pendaftaran_gel_2_dt = datetime.datetime.strptime(tgl_akhir_pendaftaran_gel_2, '%Y-%m-%d %H:%M:%S')

        if not tgl_mulai_seleksi_gel_2:
            tgl_mulai_seleksi_gel_2_dt = tgl_akhir_pendaftaran_gel_2_dt
            tgl_mulai_seleksi_gel_2 = tgl_mulai_seleksi_gel_2_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_mulai_seleksi_gel_2_dt = datetime.datetime.strptime(tgl_mulai_seleksi_gel_2, '%Y-%m-%d %H:%M:%S')

        if not tgl_akhir_seleksi_gel_2:
            tgl_akhir_seleksi_gel_2_dt = tgl_mulai_seleksi_gel_2_dt + datetime.timedelta(days=3)
            tgl_akhir_seleksi_gel_2 = tgl_akhir_seleksi_gel_2_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_akhir_seleksi_gel_2_dt = datetime.datetime.strptime(tgl_akhir_seleksi_gel_2, '%Y-%m-%d %H:%M:%S')

        if not tgl_pengumuman_hasil_seleksi_gel_2:
            tgl_pengumuman_hasil_seleksi_gel_2_dt = tgl_akhir_seleksi_gel_2_dt + datetime.timedelta(days=2)
            tgl_pengumuman_hasil_seleksi_gel_2 = tgl_pengumuman_hasil_seleksi_gel_2_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            tgl_pengumuman_hasil_seleksi_gel_2_dt = datetime.datetime.strptime(tgl_pengumuman_hasil_seleksi_gel_2, '%Y-%m-%d %H:%M:%S')

        # Format tanggal manual dalam bahasa Indonesia
        def format_tanggal_manual(dt):
            bulan_indonesia = [
                "Januari", "Februari", "Maret", "April", "Mei", "Juni",
                "Juli", "Agustus", "September", "Oktober", "November", "Desember"
            ]
            return f"{dt.day} {bulan_indonesia[dt.month - 1]} {dt.year}"

        # Format tanggal untuk ditampilkan di halaman
        tgl_mulai_pendaftaran_formatted = format_tanggal_manual(tgl_mulai_pendaftaran_dt)
        tgl_akhir_pendaftaran_formatted = format_tanggal_manual(tgl_akhir_pendaftaran_dt)
        tgl_mulai_seleksi_formatted = format_tanggal_manual(tgl_mulai_seleksi_dt)
        tgl_akhir_seleksi_formatted = format_tanggal_manual(tgl_akhir_seleksi_dt)
        tgl_pengumuman_hasil_seleksi_formatted = format_tanggal_manual(tgl_pengumuman_hasil_seleksi_dt)
       
        # Format tanggal Gelombang 2 untuk ditampilkan di halaman
        tgl_mulai_pendaftaran_gel_2_formatted = format_tanggal_manual(tgl_mulai_pendaftaran_gel_2_dt)
        tgl_akhir_pendaftaran_gel_2_formatted = format_tanggal_manual(tgl_akhir_pendaftaran_gel_2_dt)
        tgl_mulai_seleksi_gel_2_formatted = format_tanggal_manual(tgl_mulai_seleksi_gel_2_dt)
        tgl_akhir_seleksi_gel_2_formatted = format_tanggal_manual(tgl_akhir_seleksi_gel_2_dt)
        tgl_pengumuman_hasil_seleksi_gel_2_formatted = format_tanggal_manual(tgl_pengumuman_hasil_seleksi_gel_2_dt)


        html_response = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
            <!-- Primary Meta Tags --> 
            <title>PSB Daarul Qur`an Istiqomah</title> 
            <meta name="title" content="PSB Daarul Qur`an Istiqomah" /> 
            <meta name="description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
 
            <!-- Open Graph / Facebook --> 
            <meta property="og:type" content="website" /> 
            <meta property="og:url" content="https://aplikasi.dqi.ac.id/pendaftaran" /> 
            <meta property="og:title" content="PSB Daarul Qur`an Istiqomah" /> 
            <meta property="og:description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
            <meta property="og:image" content="https://drive.usercontent.google.com/download?id=1VZRccbFtq82wTNcReEq43piA_GJQddcm" /> 
 
            <!-- Twitter --> 
            <meta property="twitter:card" content="summary_large_image" /> 
            <meta property="twitter:url" content="https://aplikasi.dqi.ac.id/pendaftaran" /> 
            <meta property="twitter:title" content="PSB Daarul Qur`an Istiqomah" /> 
            <meta property="twitter:description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
            <meta property="twitter:image" content="https://drive.usercontent.google.com/download?id=1VZRccbFtq82wTNcReEq43piA_GJQddcm" />
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>PSB - Daarul Qur'an Istiqomah</title>
                <link rel="icon" type="image/x-icon" href="/pesantren_pendaftaran/static/img/favicon.ico?v=1">
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/all.min.css" integrity="sha512-Kc323vGBEqzTmouAECnVceyQqyqdsSiqLQISBL29aUW4U/M7pSPA/gEUZQqv1cwx4OnYxTxve5UMg5GT6L4JJg==" crossorigin="anonymous" referrerpolicy="no-referrer" />
                <link href=" https://cdn.jsdelivr.net/npm/sweetalert2@11.14.5/dist/sweetalert2.min.css " rel="stylesheet">
                <link rel="preconnect" href="https://fonts.googleapis.com"/>
                <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="crossorigin"/>
                <link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&amp;display=swap" rel="stylesheet"/>
                <link rel="preconnect" href="https://fonts.googleapis.com"/>
                <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="crossorigin"/>
                <link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&amp;display=swap" rel="stylesheet"/>
                <style>

                    body {{
                        background: #f5f5f4 !important;
                        min-height: 120vh;
                        display: flex;
                        flex-direction: column;
                        font-family: "poppins";
                    }}
                    
                    a.effect {{
                        transition: .1s !important;
                    }}

                    a.effect:hover {{
                        box-shadow: 0 3px 10px rgba(0,0,0,0.2) !important;
                        border-radius: 12px;
                    }}

                   .offcanvas.offcanvas-end {{
                        width: 280px;
                        background: white !important;
                   }}
                    
                     .offcanvas-header .btn-close{{ 
                        display: flex;
                        justify-content: center;
                      }}
                    
                    .offcanvas .nav-link {{
                        color: black;
                        padding: 0.75rem 1rem;
                        margin-bottom: 0.5rem;
                        border-radius: 4px;
                    }}
                    
                    .offcanvas .nav-link:hover {{
                        background-color: rgba(255,255,255,0.2);
                    }}
                    

                    .judul {{
                        height: 81px;
                        display: flex;
                        align-items: end;
                    }}

                    .teks-judul {{
                        height: 72px;
                    }}

                    .background {{
					    background: white !important;
					}}

					a.effect {{
						transition: .1s !important;
					}}

					a.effect:hover {{
						box-shadow: 0 3px 10px rgba(0,0,0,0.2) !important;
					}}

                    /* Desain Dropdown */
                    .dropdown {{
                        position: relative;
                    }}

                    .dropdown-link {{
                        cursor: pointer;
                    }}

                    .dropdown-content {{
                        display: none;
                        position: absolute;
                        top: 100%;
                        right: 0;
                        background-color: #ffffff;
                        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
                        border-radius: 5px;
                        min-width: 180px;
                        z-index: 1;
                        overflow: hidden;
                    }}

                    .dropdown-content a {{
                        color: #333;
                        padding: 10px 15px;
                        display: block;
                        text-decoration: none;
                        transition: background-color 0.2s;
                    }}

                    .dropdown-content a:hover {{
                        background-color: #f1f1f1;
                    }}

                    /* Menampilkan dropdown saat hover */
                    .dropdown:hover .dropdown-content {{
                        display: block;
                        animation: fadeIn 0.3s;
                    }}

                    #daftar {{
                        transition: .3s;
                    }}

                    #daftar:hover {{ 
                        background-color: #f5407d !important;
                    }}

                    .info-card {{
                        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
                        border: none;
                        border-radius: 20px;
                        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
                        overflow: hidden;
                        position: relative;
                        width: 280px;
                        min-height: 400px;
                    }}

                    .info-card::before {{
                        content: '';
                        position: absolute;
                        top: 0;
                        left: 0;
                        right: 0;
                        height: 4px;
                        background: linear-gradient(90deg, #e91e63, #9c27b0);
                        border-radius: 20px 20px 0 0;
                    }}

                    .info-card:hover {{
                        transform: translateY(-8px);
                        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
                    }}

                    .card-header {{
                        background: transparent;
                        border: none;
                        padding: 25px 20px 15px;
                        text-align: center;
                    }}

                    .card-category {{
                        font-size: 12px;
                        font-weight: 500;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                        color: #6c757d;
                        margin-bottom: 15px;
                    }}

                    .icon-wrapper {{
                        width: 80px;
                        height: 80px;
                        margin: 0 auto 20px;
                        background: linear-gradient(135deg, #e91e63, #f06292);
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        position: relative;
                        transition: all 0.3s ease;
                    }}

                    .info-card:hover .icon-wrapper {{
                        transform: scale(1.1);
                        box-shadow: 0 8px 25px rgba(233, 30, 99, 0.3);
                    }}

                    .icon-wrapper i {{
                        font-size: 2rem;
                        color: white;
                    }}

                    .card-title {{
                        font-size: 1.25rem;
                        font-weight: 600;
                        color: #2c3e50;
                        margin-bottom: 15px;
                        line-height: 1.3;
                        min-height: 60px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        text-align: center;
                    }}

                    .card-description {{
                        color: #6c757d;
                        font-size: 14px;
                        line-height: 1.6;
                        margin-bottom: 25px;
                        min-height: 80px;
                        display: flex;
                        align-items: center;
                        text-align: center;
                        padding: 0 15px;
                    }}

                    .detail-btn {{
                        background: linear-gradient(135deg, #059669, #34d399);
                        border: none;
                        padding: 12px 30px;
                        border-radius: 25px;
                        color: white;
                        font-weight: 500;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        transition: all 0.3s ease;
                        text-decoration: none;
                        display: inline-block;
                        position: relative;
                        overflow: hidden;
                    }}

                    .detail-btn::before {{
                        content: '';
                        position: absolute;
                        top: 0;
                        left: -100%;
                        width: 100%;
                        height: 100%;
                        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                        transition: left 0.5s;
                    }}

                    .detail-btn:hover::before {{
                        left: 100%;
                    }}

                    .detail-btn:hover {{
                        transform: translateY(-2px);
                        box-shadow: 0 8px 25px rgba(5, 150, 105, 0.3);
                        color: white;
                    }}

                    /* Modal Styling */
                    .modal-content {{
                        border: none;
                        border-radius: 20px;
                        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
                        overflow: hidden;
                    }}

                    .modal-header {{
                        background: linear-gradient(135deg, #059669, #34d399);
                        color: white;
                        border: none;
                        padding: 25px 30px;
                        position: relative;
                    }}

                    .modal-header::after {{
                        content: '';
                        position: absolute;
                        bottom: 0;
                        left: 0;
                        right: 0;
                        height: 3px;
                        background: linear-gradient(90deg, #e91e63, #9c27b0);
                    }}

                    .modal-title {{
                        font-weight: 600;
                        font-size: 1.3rem;
                    }}

                    .modal-body {{
                        padding: 30px;
                        background: #fafbfc;
                    }}

                    .section-title {{
                        font-weight: 600;
                        color: #2c3e50;
                        margin-bottom: 15px;
                        display: flex;
                        align-items: center;
                        gap: 10px;
                    }}

                    .section-title::before {{
                        content: '';
                        width: 4px;
                        height: 20px;
                        background: linear-gradient(135deg, #e91e63, #9c27b0);
                        border-radius: 2px;
                    }}

                    .info-section {{
                        background: white;
                        border-radius: 15px;
                        padding: 20px;
                        margin-bottom: 20px;
                        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
                        border-left: 4px solid #059669;
                    }}

                    .info-section img {{
                        border-radius: 10px;
                        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                        transition: transform 0.3s ease;
                    }}

                    .info-section img:hover {{
                        transform: scale(1.05);
                    }}

                    .info-list {{
                        color: #6c757d;
                        line-height: 1.8;
                    }}
                    
                    .info-numbered-list {{
                        color: #6c757d;
                        line-height: 1.8;
                    }}

                    .info-list li,
                    .info-numbered-list li {{
                        margin-bottom: 8px;
                        position: relative;
                        padding-left: 10px;
                    }}

                    .info-list li::before {{
                        content: '•';
                        color: #059669;
                        font-weight: bold;
                        position: absolute;
                        left: 0;
                    }}

                    .highlight-text {{
                        background: linear-gradient(135deg, #e91e63, #f06292);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        background-clip: text;
                        font-weight: 600;
                    }}
                    
                    .text-underlined-hover {{
                        transition: 0.3s all ease-in-out;
                        text-decoration: none;
                    }}
                    
                    .text-underlined-hover:hover {{
                        text-decoration: underline;
                    }}

                    .note-section {{
                        background: linear-gradient(135deg, #fff3cd, #ffeaa7);
                        border: 1px solid #f6d55c;
                        border-radius: 10px;
                        padding: 15px;
                        margin-top: 20px;
                    }}

                    .note-section p {{
                        margin: 0;
                        color: #856404;
                        font-style: italic;
                    }}

                    /* Animation */
                    @keyframes fadeInUp {{
                        from {{
                            opacity: 0;
                            transform: translateY(30px);
                        }}
                        to {{
                            opacity: 1;
                            transform: translateY(0);
                        }}
                    }}

                    .info-card {{
                        animation: fadeInUp 0.6s ease forwards;
                    }}

                    .info-card:nth-child(2) {{ animation-delay: 0.1s; }}
                    .info-card:nth-child(3) {{ animation-delay: 0.2s; }}
                    .info-card:nth-child(4) {{ animation-delay: 0.3s; }}

                    /* Responsive */
                    @media (max-width: 768px) {{
                        .info-card {{
                            width: 100%;
                            max-width: 350px;
                            margin: 0 auto 20px;
                        }}
                        
                        .modal-body {{
                            padding: 20px;
                        }}
                    }}

                    /* Animasi fade-in */
                    @keyframes fadeIn {{
                        from {{
                        opacity: 0;
                        transform: translateY(-10px);
                        }}
                        to {{
                        opacity: 1;
                        transform: translateY(0);
                        }}
                    }}

                    .nav-link{{
                        color:black !important;
                    }}
                </style>
            </head>
            <body style="background-color:#f5f5f4 !important; height: 100vh;">
            <nav class="navbar navbar-expand-lg" style="height: 65px;background-color:white;">
                <div class="container-fluid">
                     <a class="navbar-brand ms-5  fw-semibold" href="/psb">
                    	<img src="https://i.ibb.co.com/1MFsvMq/1731466812700.png" alt="1731466812700" width="50" alt="Logo Pesantren">       Daarul Qur'an Istiqomah
                	</a>
                    <button class="navbar-toggler ms-auto" type="button" data-bs-toggle="offcanvas" data-bs-target="#offcanvasNavbar" aria-controls="offcanvasNavbar">
                        <span class="navbar-toggler-icon"></span>
                    </button>
                    <div class="collapse navbar-collapse" id="navbarNav">
                        <ul class="navbar-nav ms-auto">
                            <li class="nav-item me-3">
                                <a class="nav-link effect" href="/psb"><i class="fa-solid fa-house me-2" style="color:black !important;"></i>Beranda</a>
                            </li>
                            {f'<li class="nav-item me-3">'  
                            f'<a class="nav-link effect" href="/pendaftaran" {"data-bs-toggle='modal' data-bs-target='#modalPendaftaranTutup'" if not is_halaman_pendaftaran else ""}>'
                            f'<i class="fa-solid fa-note-sticky me-2" style="color:black !important;"></i>Pendaftaran</a>'
                            f'</li>'}
                            <li class="nav-item dropdown">
                                <a href="#" class="dropdown-link nav-link effect"
                                    style="color: black !important;">
                                    <i class="fa-solid fa-fingerprint me-2"></i>Login</a>
                                <div class="dropdown-content">
                                    <a href="/login" style="color:black;">Login PSB</a>
                                    <a href="/web/login" style="color:black;">Login Orang Tua</a>
                                </div>
                            </li>
                            <li class="nav-item me-3">
                                <a class="nav-link effect" href="/bantuan"><i class="fa-solid fa-lock me-2" style="color:black;"></i>Bantuan</a>
                            </li>
                            {f'<li class="nav-item dropdown">'
                            f'<a href="#" class="dropdown-link nav-link effect"><i class="fa-solid fa-bullhorn me-2"></i>Pengumuman</a>'
                            f'<div class="dropdown-content">'
                            f'<a href="/pengumuman/paud">PAUD</a>'
                            f'<a href="/pengumuman/tk-ra">TK / RA</a>'
                            f'<a href="/pengumuman/sd-mi">SD / MI</a>'
                            f'<a href="/pengumuman/smp-mts">SMP / MTS</a>'
                            f'<a href="/pengumuman/sma-ma">SMA / MA</a>'
                            f'</div>'
                            f'</li>' if is_halaman_pengumuman else ''}
                        </ul>
                    </div>
                </div>
            </nav>

           <div class="offcanvas offcanvas-end" tabindex="-1" id="offcanvasNavbar" aria-labelledby="offcanvasNavbarLabel" style="background-color: white !important;">
            <div class="offcanvas-header">
                <button type="button" class="btn-close ms-auto" data-bs-dismiss="offcanvas" aria-label="Close"></button>
            </div>
            <a class="navbar-brand mt-4 text-center" href="/psb">
                <img class="w-25 h-auto" src="https://i.ibb.co.com/1MFsvMq/1731466812700.png" alt="Logo Pesantren" />
                <span class="d-block mt-2">Daarul Qur'an Istiqomah</span>
            </a>
            <div class="offcanvas-body">
                <ul class="navbar-nav">
                <li class="nav-item">
                    <a class="nav-link" href="/psb" style="color: black;">
                    <i class="fa-solid fa-house me-2"></i>Beranda
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="/pendaftaran" style="color: black;">
                    <i class="fa-solid fa-note-sticky me-2"></i>Pendaftaran
                    </a>
                </li>
                <li class="nav-item dropdown">
                    <a href="#" class="dropdown-link nav-link" style="color: black;">
                    <i class="fa-solid fa-fingerprint me-2" ></i>Login
                    </a>
                    <div class="dropdown-content">
                    <a href="/login" style="color: black;">Login PSB</a>
                    <a href="/web/login" style="color: black;">Login Orang Tua</a>
                    </div>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="/bantuan" style="color: black;">
                    <i class="fa-solid fa-lock me-2"></i>Bantuan
                    </a>
                </li>
                <t t-if="is_halaman_pengumuman">
                    <li class="nav-item dropdown">
                    <a href="#" class="dropdown-link nav-link">
                        <i class="fa-solid fa-bullhorn me-2"></i>Pengumuman
                    </a>
                    <div class="dropdown-content">
                        <a href="/pengumuman/paud">PAUD</a>
                        <a href="/pengumuman/tk-ra">TK / RA</a>
                        <a href="/pengumuman/sd-mi">SD / MI</a>
                        <a href="/pengumuman/smp-mts">SMP / MTS</a>
                        <a href="/pengumuman/sma-ma">SMA / MA</a>
                    </div>
                    </li>
                </t>
                </ul>
            </div>
            </div>

            <div style="display: flex; padding-top:3rem; justify-content: center;" class="mt-5">
                <div class="text-center">
                    <h4 class="fs-2 fw-semibold mb-2">Aplikasi Pendaftaran Santri Baru</h4>
                    <span>Daarul Qur'an Istiqomah Tanah Laut Kalimantan Selatan</span> <br><br>
                    {f'<div class="nav-item d-flex justify-content-center align-items-center">'
                            f'<a class="nav-link " style="background-color: #059669; color: white !important; text-decoration: none; padding: 8px 16px; border-radius: 5px; font-size: 14px; width: 50%;" class=" id="daftar" href="/pendaftaran" {"data-bs-toggle='modal' data-bs-target='#modalPendaftaranTutup'" if not is_halaman_pendaftaran else ""}>'
                            f'<i class="fa-solid fa-note-sticky d-none"></i>Daftar Sekarang !</a>'
                    f'</div>'}
                </div>
            </div>
            
              <div class="mt-5 mb-5" style="height:80vh; padding-top:4rem; padding-bottom:10rem;">
                <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 20px;">
                    <!-- Program Pendidikan Card -->
                    <div class="info-card">
                        <div class="card-header">
                            <div class="card-category">Program Pendidikan</div>
                            <div class="icon-wrapper">
                                <i class="fa-solid fa-graduation-cap"></i>
                            </div>
                            <div class="card-title">Jenjang Pendidikan</div>
                        </div>
                        <div class="card-description">
                            <div>
                                1. Paud baby Qu (KB dan TK)<br>
                                2. SD Tahfizh bilingual<br>
                                3. SMP Tahfizh bilingual<br>
                                4. MA Tahfizh bilingual
                            </div>
                        </div>
                        <div class="text-center pb-4">
                            <a href="#" data-bs-toggle="modal" data-bs-target="#detailProgramPendidikan" class="detail-btn">
                                Detail
                            </a>
                        </div>
                    </div>

                    <!-- Jadwal Kegiatan Card -->
                    <div class="info-card">
                        <div class="card-header">
                            <div class="card-category">Jadwal Kegiatan</div>
                            <div class="icon-wrapper">
                                <i class="fa-regular fa-calendar"></i>
                            </div>
                            <div class="card-title">Jadwal Kegiatan</div>
                        </div>
                        <div class="card-description">
                            <div>
                                Jadwal kegiatan PSB dan Kuota Test untuk tahun akademik baru
                            </div>
                        </div>
                        <div class="text-center pb-4">
                            <a href="#" data-bs-toggle="modal" data-bs-target="#detailJadwalKegiatan" class="detail-btn">
                                Detail
                            </a>
                        </div>
                    </div>

                    <!-- Persyaratan Card -->
                    <div class="info-card">
                        <div class="card-header">
                            <div class="card-category">Persyaratan</div>
                            <div class="icon-wrapper">
                                <i class="fa-solid fa-clipboard-list"></i>
                            </div>
                            <div class="card-title">Syarat Pendaftaran</div>
                        </div>
                        <div class="card-description">
                            <div>
                                Persyaratan lengkap untuk pendaftaran santri baru dapat dilihat di sini
                            </div>
                        </div>
                        <div class="text-center pb-4">
                            <a href="#" data-bs-toggle="modal" data-bs-target="#detailPersyaratan" class="detail-btn">
                                Detail
                            </a>
                        </div>
                    </div>

                    <!-- Bantuan Card -->
                    <div class="info-card">
                        <div class="card-header">
                            <div class="card-category">Bantuan</div>
                            <div class="icon-wrapper">
                                <i class="fa-solid fa-headset"></i>
                            </div>
                            <div class="card-title">Hubungi Kami</div>
                        </div>
                        <div class="card-description">
                            <div>
                                Jika memerlukan bantuan:<br>
                                <strong>Telp / WA: 0822-5207-9785</strong>
                            </div>
                        </div>
                        <div class="text-center pb-4">
                            <a href="/bantuan" class="detail-btn">
                                Detail
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            
           


            <!-- Modal Program Pendidikan -->
            <div class="modal fade" id="detailProgramPendidikan" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h1 class="modal-title fs-5" id="exampleModalLabel">
                                <i class="fa-solid fa-graduation-cap me-2"></i>
                                Pendaftaran Santri Baru
                            </h1>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body" style="max-height: 80vh; overflow-y: auto;">
                            <div class="info-section">
                                <div class="row align-items-center">
                                    <div class="col-md-8">
                                        <div class="section-title">PEMBUKAAN PROGRAM PENDIDIKAN (Putra dan Putri)</div>
                                        <ul class="info-list">                                   
                                            <li class="list-unstyled">KB (2 - 3 tahun)</li>
                                            <li class="list-unstyled">TK (4 - 5 tahun)</li>
                                            <li class="list-unstyled">SD Tahfizh Bilingual</li>
                                            <li class="list-unstyled">SMP Tahfizh bilingual</li>
                                            <li class="list-unstyled">MA Tahfizh bilingual</li>
                                        </ul>
                                    </div>
                                    <div class="col-md-4 text-center">
                                        <img src="pesantren_pendaftaran/static/src/img/IMG_20251015_160257_521.jpg" alt="Gambar Pondok" width="150" class="rounded" style="aspect-ratio: 1/1; object-fit: cover; height: auto;">
                                    </div>
                                </div>
                            </div>

                            <div class="info-section">
                                <div class="row align-items-center">
                                    <div class="col-md-8">
                                        <div class="section-title">PELAKSANAAN TEST MASUK</div>
                                        <p class="info-list">
                                            Seluruh test dilaksanakan dalam <span class="highlight-text">2 Gelombang</span><br>
                                            Test dilaksanakan secara <span class="highlight-text">OFFLINE</span>
                                        </p>
                                    </div>
                                    <div class="col-md-4 text-center">
                                        <img src="pesantren_pendaftaran/static/src/img/IMG_20251015_160257_839.jpg" alt="Gambar Pondok" width="150" class="rounded" style="aspect-ratio: 1/1; object-fit: cover; height: auto;">
                                    </div>
                                </div>
                            </div>

                            <div class="info-section">
                                <div class="row align-items-center">
                                    <div class="col-md-8">
                                        <div class="section-title">MATERI UJIAN SELEKSI</div>
                                        <ul class="info-list">
                                            <li class="list-unstyled">Membaca Al Qur'an dan Tulis Arab</li>
                                            <li class="list-unstyled">Tes wawancara anak dan wawancara orangtua</li>
                                            <li class="list-unstyled">Tes Potensi Akademik Anak</li>
                                        </ul>
                                    </div>
                                    <div class="col-md-4 text-center">
                                        <img src="pesantren_pendaftaran/static/src/img/IMG_20251015_160257_277.jpg" alt="Gambar Pondok" width="150" class="rounded" style="aspect-ratio: 1/1; object-fit: cover; height: auto;">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Modal Jadwal Kegiatan -->
            <div class="modal fade" id="detailJadwalKegiatan" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h1 class="modal-title fs-5" id="exampleModalLabel">
                                <i class="fa-regular fa-calendar me-2"></i>
                                Jadwal Pelaksanaan PSB
                            </h1>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body" style="max-height: 80vh; overflow-y: auto;">
                            <div class="info-section">
                                <div class="row align-items-center">
                                    <div class="col-md-8">
                                        <div class="section-title">1. Pendaftaran Online</div>
                                        <p class="info-list">
                                            Pendaftaran dilaksanakan pada:<br>
                                            <span class="highlight-text">Gel 1:</span> {tgl_mulai_pendaftaran_formatted} - {tgl_akhir_pendaftaran_formatted}<br>
                                            <span class="highlight-text">Gel 2:</span> {tgl_mulai_pendaftaran_gel_2_formatted} - {tgl_akhir_pendaftaran_gel_2_formatted}<br>
                                            melalui website <a href="/pendaftaran" class="text-decoration-none" style="color: #059669; font-weight: 600;">https://aplikasi.dqi.ac.id/psb</a>
                                        </p>
                                    </div>
                                    <div class="col-md-4 text-center">
                                        <img src="pesantren_pendaftaran/static/src/img/IMG_20251014_113930_248.jpg" alt="Gambar Pondok" width="150" class="rounded" style="aspect-ratio: 1/1; object-fit: cover; height: auto;">
                                    </div>
                                </div>
                            </div>

                            <div class="info-section">
                                <div class="row align-items-center">
                                    <div class="col-md-8">
                                        <div class="section-title">2. Pelaksanaan Test Masuk</div>
                                        <p class="info-list">
                                            <span class="highlight-text">Gel 1:</span> {tgl_mulai_seleksi_formatted} - {tgl_akhir_seleksi_formatted}<br>
                                            <span class="highlight-text">Gel 2:</span> {tgl_mulai_seleksi_gel_2_formatted} - {tgl_akhir_seleksi_gel_2_formatted}
                                        </p>
                                    </div>
                                    <div class="col-md-4 text-center">
                                        <img src="pesantren_pendaftaran/static/src/img/IMG_20251015_160257_476.jpg" alt="Gambar Pondok" width="150" class="rounded" style="aspect-ratio: 1/1; object-fit: cover; height: auto;">
                                    </div>
                                </div>
                            </div>

                            <div class="info-section">
                                <div class="row align-items-center">
                                    <div class="col-md-8">
                                        <div class="section-title">4. Pengumuman Hasil Seleksi</div>
                                        <p class="info-list">
                                            <span class="highlight-text">Gel 1:</span> {tgl_pengumuman_hasil_seleksi_formatted}<br>
                                            <span class="highlight-text">Gel 2:</span> {tgl_pengumuman_hasil_seleksi_gel_2_formatted}
                                        </p>
                                    </div>
                                    <div class="col-md-4 text-center">
                                        <img src="pesantren_pendaftaran/static/src/img/IMG_20251014_113930_334.jpg" alt="Gambar Pondok" width="150" class="rounded" style="aspect-ratio: 1/1; object-fit: cover; height: auto;">
                                    </div>
                                </div>
                            </div>

                            <div class="note-section">
                                <p><strong>Catatan:</strong> Seluruh kegiatan akan mengikuti protokol kesehatan sesuai ketentuan dari pemerintah.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Modal Persyaratan -->
            <div class="modal fade" id="detailPersyaratan" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h1 class="modal-title fs-5" id="exampleModalLabel">
                                <i class="fa-solid fa-clipboard-list me-2"></i>
                                Persyaratan Test Masuk
                            </h1>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body" style="max-height: 80vh; overflow-y: auto;">
                            <div class="info-section">
                                <div class="section-title">SYARAT UTAMA PENDAFTARAN</div>
                                <ol class="info-numbered-list" style="padding-left: 30px;">
                                    <li>Mengisi formulir online secara lengkap dan benar melalui laman <span class="highlight-text"><a class="hightlight-text text-underlined-hover" href="https://aplikasi.dqi.ac.id/psb" target="_blank">https://aplikasi.dqi.ac.id/psb</a></span></li>
                                    <li>Membayar biaya pendaftaran untuk program <span class="highlight-text">Paud baby Qu KB A & B (usia 2-3th)</span> sebesar <strong>Rp.300.000</strong></li>
                                    <li>Membayar biaya pendaftaran untuk program <span class="highlight-text">TK</span> sebesar <strong>Rp.300.000</strong></li>
                                    <li>Membayar biaya pendaftaran untuk program <span class="highlight-text">SD Tahfizh bilingual</span> sebesar <strong>Rp.300.000</strong></li>
                                    <li>Membayar biaya pendaftaran untuk program <span class="highlight-text">SMP Tahfizh bilingual</span> sebesar <strong>Rp.300.000</strong></li>
                                    <li>Membayar biaya pendaftaran untuk program <span class="highlight-text">MA Tahfizh bilingual</span> sebesar <strong>Rp.300.000</strong></li>
                                    <li>
                                        <strong>Syarat Pendaftaran:</strong>
                                        <ul class="info-list mt-2">
                                            <li class="list-unstyled">Fotocopy Akta Kelahiran 2 lembar</li>
                                            <li class="list-unstyled">Fotocopy KK 1 lembar</li>
                                            <li class="list-unstyled">Fotocopy KTP Orangtua (Masing-masing 1 lembar)</li>
                                            <li class="list-unstyled">Fotocopy Raport Semester akhir (menyusul)</li>
                                            <li class="list-unstyled">Pas Foto berwarna ukuran 3x4 4 lembar</li>
                                            <li class="list-unstyled">Pas Foto Orangtua masing-masing 1 lembar (Khusus Pendaftar KB dan TK)</li>
                                            <li class="list-unstyled">Berkas dimasukkan dalam Map warna hijau dan diberi nama serta lembaga pendidikan</li>
                                        </ul>
                                    </li>
                                </ol>
                            </div>

                            <div class="note-section">
                                <p><strong>Penting:</strong> Seluruh persyaratan yang harus di upload/diunggah ke website pendaftaran harus sesuai format yang ditentukan.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div style="position:absolute left-0 bottom-0;">
             <footer style="display: flex; justify-content: space-between; flex-wrap: wrap;">
            	<div class="ms-5">
            		<ul style="list-style-type: none; display: flex; text-transform: uppercase; font-size: 13px;" class="fw-semibold">
            			<li><a href="/psb" class="me-4" style="text-decoration: none; color: black;">Home</a></li>
            			<li><a href="/beranda" class="me-4" style="text-decoration: none; color: black;" target="_blank">Info Pondok</a></li>
            			<li><a href="https://drive.google.com/drive/folders/1C5U4oDSJlOe1qO7tbw0wZgYenHKEHUVM?usp=sharing" class="me-4" style="text-decoration: none; color:black;" target="_blank">Brosur</a></li>
            			<li><a href="" class="me-4" style="text-decoration: none; color: black;">Panduan</a></li>
            		</ul>
            	</div>
            	<div class="me-5">
            		<p class="text-center mt-1">© 2025 TIM IT PPIB</p>
            	</div>
            </footer>
            </div>

            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
            <script src=" https://cdn.jsdelivr.net/npm/sweetalert2@11.14.5/dist/sweetalert2.all.min.js "></script>


            </body>
            </html>
        """


        return request.make_response(html_response)
        
class UbigPendaftaranController(http.Controller):
    @http.route('/pendaftaran', type='http', auth='public')
    def pendaftaran_form(self, **kwargs):
        config_param = request.env['ir.config_parameter'].sudo()
        is_halaman_pendaftaran = config_param.get_param('pesantren_pendaftaran.is_halaman_pendaftaran')

        if not is_halaman_pendaftaran or is_halaman_pendaftaran == 'False':
            html_response = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PSB - Daarul Qur'an Istiqomah - Pendaftaran Ditutup</title>
    <meta property="og:image" content="https://drive.usercontent.google.com/download?id=1VZRccbFtq82wTNcReEq43piA_GJQddcm" /> 
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/all.min.css">
    <style>
        body {{
            background: white !important;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}

        .offcanvas.offcanvas-end {{
            width: 250px;
        }}
        
        .offcanvas .nav-link {{
            color: #ffffff;
        }}
        
        .offcanvas .btn-close {{
            position: absolute;
            top: 10px;
            right: 10px;
            filter: invert(1);
        }}

        .background {{
            background: white !important;
        }}

        .dropdown {{
            position: relative;
        }}

        .dropdown-link {{
            cursor: pointer;
        }}

        .dropdown-content {{
            display: none;
            position: absolute;
            top: 100%;
            right: 0;
            background-color: #ffffff;
            box-shadow:  0 4px 6px -1px rgba(0, 0, 0, 0.2);
            border-radius: 5px;
            min-width: 150px;
            z-index: 1;
            overflow: hidden;
        }}

        .dropdown-content a {{
            color: #333;
            padding: 10px 15px;
            display: block;
            text-decoration: none;
            transition: background-color 0.2s;
        }}

        .dropdown-content a:hover {{
            background-color: #f1f1f1;
        }}

        .dropdown:hover .dropdown-content {{
            display: block;
            animation: fadeIn 0.3s;
        }}

        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(-10px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .closed-message {{
            background: rgba(255, 255, 255, 0.9);
            border-radius: 10px;
            padding: 2rem;
            margin: 2rem auto;
            max-width: 600px;
            text-align: center;
        }}

        .back-button {{
            background-color: #e91e63;
            color: white;
            padding: 10px 30px;
            border-radius: 25px;
            text-decoration: none;
            transition: background-color 0.3s;
            display: inline-block;
            margin-top: 1rem;
        }}

        .back-button:hover {{
            background-color: #c2185b;
            color: white;
        }}

        .content-wrapper {{
            flex: 1;
        }}
    </style>
</head>
<body>
    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg" style="height: 65px;">
        <div class="container-fluid">
            <a class="navbar-brand ms-5  fw-semibold" href="/psb" style="color: black;">
                <img src="https://i.ibb.co.com/SmWmBTW/SAVE-20220114-075750-removebg-preview-4.png" width="50" alt="Logo Pesantren">
                Daarul Qur'an Istiqomah
            </a>
            <button class="navbar-toggler ms-auto" type="button" data-bs-toggle="offcanvas" data-bs-target="#offcanvasNavbar" aria-controls="offcanvasNavbar">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item me-3">
                        <a class="nav-link " href="/psb"><i class="fa-solid fa-house me-2" style="color: black;"></i>Beranda</a>
                    </li>
                    <li class="nav-item dropdown">
                        <a href="#" class="dropdown-link nav-link" style="color: black;">
                            <i class="fa-solid fa-fingerprint me-2"></i>Login</a>
                        <div class="dropdown-content">
                            <a href="/login" style="color: black;">Login PSB</a>
                            <a href="/web/login" style="color: black;">Login Orang Tua</a>
                        </div>
                    </li>
                    <li class="nav-item me-3">
                        <a class="nav-link " href="/bantuan"><i class="fa-solid fa-lock me-2" style="color: black;"></i>Bantuan</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- Offcanvas Menu -->
    <div class="offcanvas offcanvas-end background" tabindex="-1" id="offcanvasNavbar" aria-labelledby="offcanvasNavbarLabel">
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="offcanvas" aria-label="Close"></button>
        <a class="navbar-brand mt-1  fw-semibold" href="/psb" style="display: flex; flex-direction: column; align-items: center;">
            <img src="https://i.ibb.co.com/SmWmBTW/SAVE-20220114-075750-removebg-preview-4.png" width="50" alt="Logo Pesantren">
            Daarul Qur'an Istiqomah
        </a>
        <div class="offcanvas-body">
            <ul class="navbar-nav justify-content-end flex-grow-1 pe-3">
                <li class="nav-item me-3">
                    <a class="nav-link " href="/psb"><i class="fa-solid fa-house me-2" style="color: black;"></i>Beranda</a>
                </li>
                <li class="nav-item dropdown">
                    <a href="#" class="dropdown-link nav-link" style="color: black;">
                        <i class="fa-solid fa-fingerprint me-2"></i>Login</a>
                    <div class="dropdown-content" style="color: black;">
                        <a href="/login">Login PSB</a>
                        <a href="/web/login">Login Orang Tua</a>
                    </div>
                </li>
                <li class="nav-item me-3">
                    <a class="nav-link " href="/bantuan"><i class="fa-solid fa-lock me-2" style="color: black;"></i>Bantuan</a>
                </li>
            </ul>
        </div>
    </div>

    <!-- Main Content -->
    <div class="content-wrapper">
        <div class="closed-message">
            <i class="fa-solid fa-clock-rotate-left fs-1 mb-3" style="color: #e91e63;"></i>
            <h2 class="mb-4">Pendaftaran Ditutup</h2>
            <p class="mb-4">Pendaftaran saat ini sudah ditutup. Silakan kembali lagi nanti.</p>
            <a href="/psb" class="back-button">
                <i class="fa-solid fa-house me-2"></i>Kembali ke Beranda
            </a>
        </div>
    </div>

    <!-- Footer -->
    <footer class=" p-2" style="display: flex; justify-content: space-between; flex-wrap: wrap;">
        <div class="ms-5">
            <ul style="list-style-type: none; display: flex; text-transform: uppercase; font-size: 13px;" class="fw-semibold">
                <li><a href="/psb" class="me-4" style="text-decoration: none; color: white;">Home</a></li>
                <li><a href="/beranda" class="me-4" style="text-decoration: none; color: white;" target="_blank">Info Pondok</a></li>
                <li><a href="https://drive.google.com/drive/folders/1C5U4oDSJlOe1qO7tbw0wZgYenHKEHUVM?usp=sharing" class="me-4" style="text-decoration: none; color: white;" target="_blank">Brosur</a></li>
                <li><a href="" class="me-4" style="text-decoration: none; color: white;">Panduan</a></li>
            </ul>
        </div>
        <div class="me-5">
            <p class="text-center mt-1">© 2025 TIM IT PPIB</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
            return request.make_response(html_response)

        pendidikan_list = request.env['ubig.pendidikan'].sudo().search([])
        return request.render('pesantren_pendaftaran.pendaftaran_form_template', {
            'pendidikan_list': pendidikan_list,
        })

    # def pendaftaran_form(self, **kwargs):

    #     # Mengambil nilai kuota pendaftaran dari ir.config_parameter
    #     config_param = request.env['ir.config_parameter'].sudo()
    #     is_halaman_pengumuman = config_param.get_param('pesantren_pendaftaran.is_halaman_pengumuman')

    #     pendidikan_list = request.env['ubig.pendidikan'].sudo().search([])
    #     return request.render('pesantren_pendaftaran.pendaftaran_form_template', {
    #         'pendidikan_list': pendidikan_list,
    #         'is_halaman_pengumuman': is_halaman_pengumuman,
    #     })

    @http.route('/pendaftaran/submit', type='http', auth='public', methods=['POST'], csrf=True)
    def pendaftaran_submit(self, **post):
        def verify_recaptcha(response_token):
            secret_key = '6LdSjyQsAAAAAL9nRSg1dzXDAJfbpW1zf05Fru7r'

            payload = {
                'secret': secret_key,
                'response': response_token,
            }

            # Kirim permintaan ke API Google reCAPTCHA
            verify_url = 'https://www.google.com/recaptcha/api/siteverify'
            response = requests.post(verify_url, data=payload)
            result = response.json()

            # Kembalikan status verifikasi
            return result.get('success')
        
          # Ambil token reCAPTCHA dari form
        recaptcha_response_token = post.get('g-recaptcha-response')

        # if not recaptcha_response_token:
        #     raise UserError("reCAPTCHA tidak terisi. Silakan coba lagi.")

        # Verifikasi token reCAPTCHA
        # if not verify_recaptcha(recaptcha_response_token):
        #     raise UserError("Verifikasi reCAPTCHA gagal. Silakan coba lagi.")

        # Ambil data dari form
        # kode_akses             = post.get('kode_akses')
        nama                   = post.get('nama')
        nik                    = post.get('nik')
        email                  = post.get('email') if post.get('email') else ''
        password               = post.get('password')
        nomor_login            = post.get('nomor_login') if post.get('nomor_login') else ''
        jenjang_id             = post.get('jenjang_id')
        is_alumni              = request.params.get('is_alumni') if request.params.get('is_alumni') else ''
        is_pindahan_sd         = request.params.get('is_pindahan_sd') if request.params.get('is_pindahan_sd') else ''
        gender                 = request.params.get('gender')
        kota_lahir             = post.get('kota_lahir')
        tanggal_lahir_str      = request.params.get('tanggal_lahir')
        # Mengonversi format tanggal dd/mm/yyyy menjadi date
        tanggal_lahir          = datetime.datetime.strptime(tanggal_lahir_str, '%d/%m/%Y').date()
        alamat                 = post.get('alamat')
        provinsi_id            = request.params.get('provinsi_id')
        kota_id                = request.params.get('kota_id')
        kecamatan_id           = request.params.get('kecamatan_id')
        golongan_darah         = request.params.get('golongan_darah') if request.params.get('golongan_darah') else ''
        kewarganegaraan        = request.params.get('kewarganegaraan')
        nisn                   = post.get('nisn') if post.get('nisn') else ''
        anak_ke                = post.get('anak_ke') if post.get('anak_ke') else ''
        jml_saudara_kandung    = post.get('jml_saudara_kandung') if post.get('jml_saudara_kandung') else ''
        cita_cita              = post.get('cita_cita') if post.get('cita_cita') else ''

        # Data Orang Tua - Ayah
        nama_ayah              = post.get('nama_ayah')
        ktp_ayah               = post.get('ktp_ayah')
        tanggal_lahir_ayah_str = request.params.get('tanggal_lahir_ayah')
        # Mengonversi format tanggal dd/mm/yyyy menjadi date
        tanggal_lahir_ayah     = datetime.datetime.strptime(tanggal_lahir_ayah_str, '%d/%m/%Y').date()
        email_ayah             = post.get('email_ayah')
        telepon_ayah           = post.get('telepon_ayah')
        pekerjaan_ayah         = request.params.get('pekerjaan_ayah')
        penghasilan_ayah       = request.params.get('penghasilan_ayah')
        # email_ayah             = post.get('email_ayah')
        agama_ayah             = request.params.get('agama_ayah')
        kewarganegaraan_ayah   = request.params.get('kewarganegaraan_ayah')
        pendidikan_ayah        = request.params.get('pendidikan_ayah')

        # Data Orang Tua - Ibu
        nama_ibu               = post.get('nama_ibu')
        ktp_ibu                = post.get('ktp_ibu')
        tanggal_lahir_ibu_str  = request.params.get('tanggal_lahir_ibu')
        email_ibu              = post.get('email_ibu')
        # Mengonversi format tanggal dd/mm/yyyy menjadi date
        agama_ibu              = request.params.get('agama_ibu')
        tanggal_lahir_ibu      = datetime.datetime.strptime(tanggal_lahir_ibu_str, '%d/%m/%Y').date()
        telepon_ibu            = post.get('telepon_ibu')
        pekerjaan_ibu          = request.params.get('pekerjaan_ibu')
        penghasilan_ibu        = request.params.get('penghasilan_ibu')
        # email_ibu              = post.get('email_ibu')
        kewarganegaraan_ibu    = request.params.get('kewarganegaraan_ibu')
        pendidikan_ibu         = request.params.get('pendidikan_ibu')
        
        # Data Wali
        wali_nama              = post.get('wali_nama') if post.get('wali_nama') else ''

        # Mendapatkan nilai tanggal lahir dari parameter
        wali_tgl_lahir_str = request.params.get('wali_tgl_lahir')

        # Mengecek apakah parameter tidak kosong atau tidak None
        if wali_tgl_lahir_str:
            try:
                # Mengonversi format tanggal dd/mm/yyyy menjadi date
                wali_tgl_lahir = datetime.datetime.strptime(wali_tgl_lahir_str, '%d/%m/%Y').date()
            except ValueError:
                # Jika format tanggal tidak valid
                wali_tgl_lahir = None  # Atau bisa beri nilai default seperti datetime.date(1900, 1, 1) atau lainnya
        else:
            # Jika tidak ada input tanggal
            wali_tgl_lahir = None  # Atau beri nilai default jika diperlukan

        # wali_tgl_lahir_str     = request.params.get('wali_tgl_lahir')
        # Mengonversi format tanggal dd/mm/yyyy menjadi date
        # wali_tgl_lahir         = datetime.datetime.strptime(wali_tgl_lahir_str, '%d/%m/%Y').date()
        wali_telp              = post.get('wali_telp') if post.get('wali_telp') else ''
        wali_email             = post.get('wali_email') if post.get('wali_email') else ''
        # wali_password          = post.get('password') if post.get('password') else ''
        wali_hubungan          = request.params.get('wali_hubungan') if request.params.get('wali_hubungan') else ''

        # Data Pendidikan
        asal_sekolah           = post.get('asal_sekolah') if post.get('asal_sekolah') else ''
        alamat_asal_sek        = post.get('alamat_asal_sek') if post.get('alamat_asal_sek') else ''
        telp_asal_sek          = post.get('telp_asal_sek') if post.get('telp_asal_sek') else ''
        status_sekolah_asal    = request.params.get('status_sekolah_asal') if request.params.get('status_sekolah_asal') else ''
        npsn                   = post.get('npsn') if post.get('npsn') else ''

        # Ambil file dari request
        uploaded_files = request.httprequest.files

        # Data Berkas
        # akta_kelahiran         = request.params.get('akta_kelahiran')
        # kartu_keluarga         = request.params.get('kartu_keluarga')
        # ijazah                 = request.params.get('ijazah') if request.params.get('ijazah') else ''
        # surat_kesehatan        = request.params.get('surat_kesehatan') if request.params.get('surat_kesehatan') else ''
        # pas_foto               = request.params.get('pas_foto')
        # raport_terakhir        = request.params.get('raport_terakhir') if request.params.get('raport_terakhir') else ''
        # ktp_ortu               = request.params.get('ktp_ortu')
        # skhun                  = request.params.get('skhun') if request.params.get('skhun') else ''

        # Ambil setiap file, konversi ke Base64, dan proses
        akta_kelahiran = uploaded_files.get('akta_kelahiran')
        kartu_keluarga = uploaded_files.get('kartu_keluarga')
        ijazah = uploaded_files.get('ijazah')
        surat_kesehatan = uploaded_files.get('surat_kesehatan')
        pas_foto = uploaded_files.get('pas_foto')
        raport_terakhir = uploaded_files.get('raport_terakhir')
        ktp_ortu = uploaded_files.get('ktp_ortu')
        skhun = uploaded_files.get('skhun')

        # Fungsi bantu untuk memproses file
        def process_file(file):
            if file:
                # Baca file dan konversi ke Base64
                file_content = file.read()
                file_base64 = base64.b64encode(file_content)
                return file_base64
            return None

        # Konversi file yang diunggah
        akta_kelahiran_b64 = process_file(akta_kelahiran)
        kartu_keluarga_b64 = process_file(kartu_keluarga)
        ijazah_b64 = process_file(ijazah)
        surat_kesehatan_b64 = process_file(surat_kesehatan)
        pas_foto_b64 = process_file(pas_foto)
        raport_terakhir_b64 = process_file(raport_terakhir)
        ktp_ortu_b64 = process_file(ktp_ortu)
        skhun_b64 = process_file(skhun)

        nama = post.get('nama')

        wali_terdaftar = request.env['ubig.pendaftaran'].sudo().search([('wali_email', '=', wali_email)])

        # if wali_terdaftar:
        #     kode_akses = wali_terdaftar[0].kode_akses

        # Simpan data ke model ubig.pendaftaran
        pendaftaran = request.env['ubig.pendaftaran'].sudo().create({
            # 'kode_akses'             : kode_akses,
            'name'                   : nama,
            'nik'                    : nik,
            'email'                  : email,
            'password'               : password,
            'nomor_login'            : nomor_login,
            'jenjang_id'             : int(jenjang_id),
            'is_alumni'              : is_alumni,
            'is_pindahan_sd'         : is_pindahan_sd,
            'gender'                 : gender,
            'kota_lahir'             : kota_lahir,
            'tanggal_lahir'          : tanggal_lahir,
            'alamat'                 : alamat,
            'provinsi_id'            : provinsi_id,
            'kota_id'                : kota_id,
            'kecamatan_id'           : kecamatan_id,
            'golongan_darah'         : golongan_darah,
            'kewarganegaraan'        : kewarganegaraan,
            'nisn'                   : nisn,
            'anak_ke'                : anak_ke,
            'jml_saudara_kandung'    : jml_saudara_kandung,
            'cita_cita'              : cita_cita,

            # Data Orang Tua - Ayah
            'nama_ayah'              : nama_ayah,
            'ktp_ayah'               : ktp_ayah,
            'tanggal_lahir_ayah'     : tanggal_lahir_ayah,
            'telepon_ayah'           : telepon_ayah,
            'pekerjaan_ayah'         : pekerjaan_ayah,
            'email_ayah'             : email_ayah,
            'penghasilan_ayah'       : penghasilan_ayah,
            'agama_ayah'             : agama_ayah,
            # 'email_ayah'             : email_ayah,
            'kewarganegaraan_ayah'   : kewarganegaraan_ayah,
            'pendidikan_ayah'        : pendidikan_ayah, 

            # Data Orang Tua - Ibu
            'nama_ibu'               : nama_ibu,
            'ktp_ibu'                : ktp_ibu,
            'tanggal_lahir_ibu'      : tanggal_lahir_ibu,
            'telepon_ibu'            : telepon_ibu,
            'pekerjaan_ibu'          : pekerjaan_ibu,
            'email_ibu'              : email_ibu,
            'penghasilan_ibu'        : penghasilan_ibu,
            'agama_ibu'              : agama_ibu,
            # 'email_ibu'              : email_ibu,
            'kewarganegaraan_ibu'    : kewarganegaraan_ibu,
            'pendidikan_ibu'         : pendidikan_ibu,
            
            # Data Wali
            'wali_nama'              : wali_nama,
            'wali_tgl_lahir'         : wali_tgl_lahir,
            'wali_telp'              : wali_telp,
            'wali_email'             : wali_email,
            # 'wali_password'          : wali_password,
            'wali_hubungan'          : wali_hubungan,

            # Data Pendidikan
            'asal_sekolah'           : asal_sekolah,
            'alamat_asal_sek'        : alamat_asal_sek,
            'telp_asal_sek'          : telp_asal_sek,
            'status_sekolah_asal'    : status_sekolah_asal,
            'npsn'                   : npsn,

            # Data Berkas
            'akta_kelahiran'         : akta_kelahiran_b64 if akta_kelahiran_b64 else False,
            'kartu_keluarga'         : kartu_keluarga_b64 if kartu_keluarga_b64 else False,
            'ijazah'                 : ijazah_b64 if ijazah_b64 else False,
            'surat_kesehatan'        : surat_kesehatan_b64 if surat_kesehatan_b64 else False,
            'pas_foto'               : pas_foto_b64 if pas_foto_b64 else False,
            'raport_terakhir'        : raport_terakhir_b64 if raport_terakhir_b64 else False,
            'ktp_ortu'               : ktp_ortu_b64 if ktp_ortu_b64 else False,
            'skhun'                  : skhun_b64 if skhun_b64 else False,
            'state'                  : 'draft'  # set status awal menjadi 'terdaftar'
        })

        token = pendaftaran.token

        # Redirect ke halaman sukses atau halaman lain yang diinginkan
        return request.redirect(f'/pendaftaran/success?token={token}')

    @http.route('/pendaftaran/success', type='http', auth='public')   
    def pendaftaran_success(self, token=None, **kwargs):

        Pendaftaran = request.env['ubig.pendaftaran']

        # Mengambil nilai kuota pendaftaran dari ir.config_parameter
        config_param = request.env['ir.config_parameter'].sudo()
        is_halaman_pengumuman = config_param.get_param('pesantren_pendaftaran.is_halaman_pengumuman')
        no_rekening = config_param.get_param('pesantren_pendaftaran.no_rekening', default='7181863913')
        # Menangkap Token pendaftaran dari URL
        token = request.params.get('token')

        if not token:
            return request.not_found()

        # Cari pendaftaran berdasarkan token
        pendaftaran = Pendaftaran.sudo().search([('token', '=', token)], limit=1)
        if not pendaftaran:
            return request.not_found()
        
        if pendaftaran.is_notified:
            return request.render('pesantren_pendaftaran.pendaftaran_success_template', {
            'pendaftaran': pendaftaran,
        })

        # Kirim whatsapp
        if pendaftaran.nomor_login:
            # Contoh password (validasi minimal 8 karakter sudah dilakukan)
            pw = pendaftaran.password

            # Sembunyikan bagian tengah kecuali dua karakter awal dan dua karakter akhir
            masked_password = pw[:2] + '*' * (len(pw) - 4) + pw[-2:]
            biaya_formatted = f"Rp. {pendaftaran.biaya:,.0f}".replace(",", ".")
            
            pesan = f"""
_*Pesantren Tahfizh Daarul Qur'an Istiqomah*_

_*Assalamualaikum Wr. Wb*_

Bapak/Ibu {pendaftaran.wali_nama or pendaftaran.nama_ayah or pendaftaran.nama_ibu},

Pendaftaran telah berhasil! Berikut adalah informasi login Anda:

*Akun Login:*
- No Telp/Wa: {pendaftaran.nomor_login}
- Kata Sandi: {masked_password}

*Data Pendaftaran:*
- Nama: {pendaftaran.partner_id.name}
- TTL: {pendaftaran.kota_lahir}, {pendaftaran.get_formatted_tanggal_lahir()}
- Alamat: {pendaftaran.alamat}
- NIK: {pendaftaran.nik}

*Jenjang Pendidikan:* {pendaftaran.jenjang_id.name}

*Informasi Pembayaran:*
- Bank: BSI (Bank Syariah Indonesia)
- No. Rekening: {no_rekening}
- Jumlah: {biaya_formatted}

Untuk mengakses akun Anda, silakan klik link berikut: https://aplikasi.dqi.ac.id/login

Terima kasih!
            """
            
            # Mengambil informasi untuk login ke API Nobox
            username = "ponpesdqi@gmail.com"  # Ganti dengan username yang sesuai
            password = "dqimedia123"  # Ganti dengan password yang sesuai

            # Kirim pesan menggunakan Nobox API
            try:
                nobox = Nobox()
                response = nobox.generateToken(username, password)

                if response.get('IsError'):
                    return request.redirect('/error')

                token_nobox = response.get('Data')  # Token dari API Nobox


                # lakukan send wa
                nobox = Nobox(token_nobox)
                sendRes = nobox.sendMessageExt(pendaftaran.nomor_login, 1, 624718353219589, 1, pesan, attachment=None)

                if sendRes.get('IsError', False):
                    raise UserError(f"Gagal mengirim pesan WhatsApp: {sendRes.get('Error')}")
                else:
                    return request.render('pesantren_pendaftaran.pendaftaran_success_template', {
                        'pendaftaran': pendaftaran,
                        'is_halaman_pengumuman': is_halaman_pengumuman,
                        'no_rekening': no_rekening,
                    })
            except Exception as e:
                raise UserError(f"Terjadi kesalahan saat mengirim pesan WhatsApp: {str(e)}")

        # Kirim email
        if pendaftaran.email:
            thn_sekarang = datetime.datetime.now().year
            # Contoh password (validasi minimal 8 karakter sudah dilakukan)
            pw = pendaftaran.password
            

            # Sembunyikan bagian tengah kecuali dua karakter awal dan dua karakter akhir
            masked_password = pw[:2] + '*' * (len(pw) - 4) + pw[-2:]
            biaya_formatted = f"Rp. {pendaftaran.biaya:,.0f}".replace(",", ".")

            email_values = {
                'subject': "Informasi Login Sistem Pesantren Daarul Qur'an Istiqomah",
                'email_to': pendaftaran.email,
                'body_html': f'''
                    <div style="background-color: #d9eaf7; padding: 20px; font-family: Arial, sans-serif;">
                        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden;">
                            <!-- Header -->
                            <div style="background-color: #0066cc; color: #ffffff; text-align: center; padding: 20px;">
                                <h1 style="margin: 0; font-size: 24px;">Pesantren Daarul Qur'an Istiqomah</h1>
                            </div>
                            <!-- Body -->
                            <div style="padding: 20px; color: #555555;">
                                <p style="margin: 0 0 10px;">Assalamualaikum Wr. Wb,</p>
                                <p style="margin: 0 0 20px;">
                                    Bapak/Ibu <strong>{pendaftaran.wali_nama or pendaftaran.nama_ayah or pendaftaran.nama_ibu}</strong>,<br>
                                    Akun Login telah dibuat di sistem pesantren kami. Berikut adalah informasi login Anda:
                                </p>
                                <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                                    <h3>Akun Login</h3>
                                    <table style="width: 100%; border-collapse: collapse;">
                                        <tr>
                                            <td style="padding: 8px; font-weight: bold; color: #333333;">Email :</td>
                                            <td style="padding: 8px; color: #555555;">{pendaftaran.email}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px; font-weight: bold; color: #333333;">Kata Sandi :</td>
                                            <td style="padding: 8px; color: #555555;">{masked_password}</td>
                                        </tr>
                                    </table>

                                    <h3>Data Pendaftaran</h3>
                                    <table style="width: 100%; border-collapse: collapse;">
                                        <tr>
                                            <td style="padding: 8px; font-weight: bold; color: #333333;">Nama :</td>
                                            <td style="padding: 8px; color: #555555;">{pendaftaran.partner_id.name}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px; font-weight: bold; color: #333333;">TTL :</td>
                                            <td style="padding: 8px; color: #555555;">{pendaftaran.kota_lahir}, {pendaftaran.get_formatted_tanggal_lahir()}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px; font-weight: bold; color: #333333;">Alamat :</td>
                                            <td style="padding: 8px; color: #555555;">{pendaftaran.alamat}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px; font-weight: bold; color: #333333;">NIK :</td>
                                            <td style="padding: 8px; color: #555555;">{pendaftaran.nik}</td>
                                        </tr>
                                    </table>

                                    <h3>Jenjang Pendidikan Yang Dipilih</h3>
                                    <table style="width: 100%; border-collapse: collapse;">
                                        <tr>
                                            <td style="padding: 8px; font-weight: bold; color: #333333;">Jenjang :</td>
                                            <td style="padding: 8px; color: #555555;">{pendaftaran.jenjang_id.name}</td>
                                        </tr>
                                    </table>

                                    <h3>Informasi Pembayaran</h3>
                                    <table style="width: 100%; border-collapse: collapse;">
                                        <tr>
                                            <td style="padding: 8px; font-weight: bold; color: #333333;">Bank :</td>
                                            <td style="padding: 8px; color: #555555;">BSI</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px; font-weight: bold; color: #333333;">Nomor Rekening :</td>
                                            <td style="padding: 8px; color: #555555;">{no_rekening}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 8px; font-weight: bold; color: #333333;">Sejumlah :</td>
                                            <td style="padding: 8px; color: #555555;">{biaya_formatted}</td>
                                        </tr>
                                    </table>

                                </div>
                                <p style="text-align: center;">
                                    <a href="https://aplikasi.dqi.ac.id/login" style="background-color: #0066cc; color: #ffffff; padding: 10px 20px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">
                                        Masuk Ke Akun Anda
                                    </a>
                                </p>
                                <p style="margin: 20px 0;">
                                    Apabila terdapat kesulitan atau membutuhkan bantuan, silakan hubungi tim teknis kami melalui nomor:
                                </p>
                                <ul style="margin: 0; padding-left: 20px; color: #555555;">
                                    <li>0822 5207 9785</li>
                                </ul>
                                <p style="margin: 20px 0;">
                                    Kami berharap portal ini dapat membantu Bapak/Ibu memantau perkembangan putra/putri selama berada di pesantren.
                                </p>
                            </div>
                            <!-- Footer -->
                            <div style="background-color: #f1f1f1; text-align: center; padding: 10px;">
                                <p style="font-size: 12px; color: #888888; margin: 0; color: black;">
                                    &copy; {thn_sekarang} Pesantren Tahfizh Daarul Qur'an Istiqomah. All rights reserved.
                                </p>
                            </div>
                        </div>
                    </div>
                ''',
            }

            mail = request.env['mail.mail'].sudo().create(email_values)
            mail.send()
            
        pendaftaran.sudo().write({'is_notified': True})

        return request.render('pesantren_pendaftaran.pendaftaran_success_template', {
            'pendaftaran': pendaftaran,
            'is_halaman_pengumuman': is_halaman_pengumuman,
            'no_rekening': no_rekening,
        })  
        


class PesantrenCetakPembayaran(http.Controller):
    @http.route('/pendaftaran/cetak', type='http', auth='public')
    def pendaftaran_cetak(self, token=None, **kwargs):

        Pendaftaran = request.env['ubig.pendaftaran']

        # Mengambil nilai kuota pendaftaran dari ir.config_parameter
        config_param = request.env['ir.config_parameter'].sudo()
        no_rekening = config_param.get_param('pesantren_pendaftaran.no_rekening', default='7181863913')

        # Menangkap Token pendaftaran dari URL
        token = request.params.get('token')

        # Cek apakah Token ada
        if not token:
            return request.not_found()

        # Mengambil data pendaftaran berdasarkan Token
        pendaftaran = Pendaftaran.sudo().search([('token', '=', token)], limit=1)
        if not pendaftaran:
            return request.not_found()

        return request.render('pesantren_pendaftaran.pendaftaran_cetak_form_pembayaran_template', {
            'pendaftaran': pendaftaran,
            'no_rekening': no_rekening,
        })

class PesantrenPsbBantuan(http.Controller):
    @http.route('/bantuan', auth='public')
    def index(self, **kw):
        # Ambil nilai dari field konfigurasi
        config_obj = http.request.env['ir.config_parameter'].sudo()
        is_halaman_pengumuman = config_obj.get_param('pesantren_pendaftaran.is_halaman_pengumuman')
        is_halaman_pendaftaran = config_obj.get_param('pesantren_pendaftaran.is_halaman_pendaftaran')

        html_response = f"""
            <html lang="en">
            <head>
            <!-- Primary Meta Tags --> 
            <title>PSB Daarul Qur`an Istiqomah</title> 
            <meta name="title" content="PSB Daarul Qur`an Istiqomah" /> 
            <meta name="description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
            <!-- Open Graph / Facebook --> 
            <meta property="og:type" content="website" /> 
            <meta property="og:url" content="https://aplikasi.dqi.ac.id/pendaftaran" /> 
            <meta property="og:title" content="PSB Darul Qur`an Istiqomah" /> 
            <meta property="og:description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
            <meta property="og:image" content="https://drive.usercontent.google.com/download?id=1VZRccbFtq82wTNcReEq43piA_GJQddcm" /> 
            <!-- Twitter --> 
            <meta property="twitter:card" content="summary_large_image" /> 
            <meta property="twitter:url" content="https://aplikasi.dqi.ac.id/pendaftaran" /> 
            <meta property="twitter:title" content="PSB Darul Qur`an Istiqomah" /> 
            <meta property="twitter:description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
            <meta property="twitter:image" content="https://drive.usercontent.google.com/download?id=1VZRccbFtq82wTNcReEq43piA_GJQddcm" />
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Bantuan - Daarul Qur'an Istiqomah</title>
                <link rel="icon" type="image/x-icon" href="/pesantren_pendaftaran/static/img/favicon.ico?v=1">
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/all.min.css" integrity="sha512-Kc323vGBEqzTmouAECnVceyQqyqdsSiqLQISBL29aUW4U/M7pSPA/gEUZQqv1cwx4OnYxTxve5UMg5GT6L4JJg==" crossorigin="anonymous" referrerpolicy="no-referrer" />
                <link href="https://cdn.jsdelivr.net/npm/sweetalert2@11.14.5/dist/sweetalert2.min.css" rel="stylesheet">
                <link rel="preconnect" href="https://fonts.googleapis.com"/>
                <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="crossorigin"/>
                <link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&amp;display=swap" rel="stylesheet"/>

                <style>
                    body {{
                        background: #f5f5f4 !important;
                        font-family: "Poppins";
                        min-height: 100vh;
                        display: flex;
                        flex-direction: column;
                    }}

                    .offcanvas.offcanvas-end {{
                        width: 250px;
                    }}
                    
                    .offcanvas .nav-link {{
                        color: black;
                    }}

                    .nav-link {{
                        color: black !important;
                    }}
                    
                    .offcanvas .btn-close {{
                        position: absolute;
                        top: 10px;
                        right: 10px;
                        filter: invert(1);
                    }}

                    .timeline {{
                        position: relative;
                        padding: 20px 0;
                    }}

                    .timeline::before {{
                        content: '';
                        position: absolute;
                        left: 5px;
                        top: 50px;
                        bottom: 0;
                        width: 4px;
                        background: white;
                    }}

                    .timeline-item {{
                        position: relative;
                        margin-left: 50px;
                        margin-bottom: 40px;
                    }}

                    .timeline-icon {{
                        position: absolute;
                        left: -63px;
                        top: 20px;
                        width: 40px;
                        height: 40px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        border-radius: 50%;
                        color: #fff;
                        font-size: 18px;
                        box-shadow: 0 4px 6px -1px #cbd5e1;
                    }}

                    .timeline-icon::after {{
                        content: "";
                        position: absolute;
                        top: 50%;
                        left: 84%;
                        border-width: 15px;
                        border-style: solid;
                        border-color: transparent transparent transparent white;
                        transform: translateY(-50%) rotate(180deg);
                    }}

                    .timeline-content {{
                        padding: 20px;
                        background-color: #fff;
                        border-radius: 8px;
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    }}

                    .judul {{
                        height: 81px;
                        display: flex;
                        align-items: end;
                    }}

                    .teks-judul {{
                        height: 72px;
                    }}

                    .background {{
                        background: white !important;
                    }}

                    a.effect {{
                        transition: .1s !important;
                    }}

                    a.effect:hover {{
                        box-shadow: 0 3px 10px rgba(0,0,0,0.2) !important;
                        border-radius: 12px;
                    }}

                    /* Desain Dropdown */
                    .dropdown {{
                        position: relative;
                    }}

                    .dropdown-link {{
                        cursor: pointer;
                    }}

                    .dropdown-content {{
                        display: none;
                        position: absolute;
                        top: 100%;
                        right: 0;
                        background-color: #ffffff;
                        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
                        border-radius: 5px;
                        min-width: 150px;
                        z-index: 1;
                        overflow: hidden;
                    }}

                    .dropdown-content a {{
                        color: #333;
                        padding: 10px 15px;
                        display: block;
                        text-decoration: none;
                        transition: background-color 0.2s;
                    }}

                    .dropdown-content a:hover {{
                        background-color: #f1f1f1;
                    }}

                    .dropdown:hover .dropdown-content {{
                        display: block;
                        animation: fadeIn 0.3s;
                    }}

                    @keyframes fadeIn {{
                        from {{ opacity: 0; transform: translateY(-10px); }}
                        to {{ opacity: 1; transform: translateY(0); }}
                    }}

                    /* Media Queries untuk Responsivitas */
                    @media (max-width: 768px) {{
                        .offcanvas.offcanvas-end {{
                            width: 50%;
                        }}

                        .timeline::before {{
                            left: 10px;
                        }}

                        .timeline-item {{
                            margin-left: 30px;
                        }}

                        .timeline-icon {{
                            left: -43px;
                            width: 30px;
                            height: 30px;
                            font-size: 14px;
                        }}

                        .timeline-content {{
                            padding: 10px;
                            font-size: 14px;
                        }}

                        .navbar-brand img {{
                            width: 40px;
                        }}

                        .navbar-brand {{
                            font-size: 1rem;
                        }}

                        .container {{
                            padding: 10px;
                        }}

                        footer {{
                            flex-direction: column;
                            text-align: center;
                            padding: 10px;
                        }}

                        footer ul {{
                            justify-content: center;
                            margin-bottom: 10px;
                        }}

                        .navbar-nav .nav-item {{
                            margin: 5px 0;
                        }}
                    }}

                    @media (max-width: 576px) {{
                        .timeline-item {{
                            margin-left: 20px;
                        }}

                        .timeline-icon {{
                            left: -33px;
                            width: 25px;
                            height: 25px;
                            font-size: 12px;
                        }}

                        .timeline-content {{
                            padding: 8px;
                            font-size: 12px;
                        }}
                    }}
                </style>
            </head>
            <body>
            <nav class="navbar navbar-expand-lg" style="height: 65px; background-color: white;">
                <div class="container-fluid">
                    <a class="navbar-brand ms-5 fw-semibold" href="/psb">
                        <img src="https://i.ibb.co.com/1MFsvMq/1731466812700.png" alt="Logo Pesantren" width="50">
                        Daarul Qur'an Istiqomah
                    </a>
                    <button class="navbar-toggler ms-auto" type="button" data-bs-toggle="offcanvas" data-bs-target="#offcanvasNavbar" aria-controls="offcanvasNavbar">
                        <span class="navbar-toggler-icon"></span>
                    </button>
                    <div class="collapse navbar-collapse" id="navbarNav">
                        <ul class="navbar-nav ms-auto">
                            <li class="nav-item me-3">
                                <a class="nav-link effect" style="color: black !important;" href="/psb"><i class="fa-solid fa-house me-2"></i>Beranda</a>
                            </li>
                            {f'<li class="nav-item me-3">'
                            f'<a class="nav-link effect" href="/pendaftaran" {"data-bs-toggle=\'modal\' data-bs-target=\'#modalPendaftaranTutup\'" if not is_halaman_pendaftaran else ""}>'
                            f'<i class="fa-solid fa-note-sticky me-2" style="color: black;"></i>Pendaftaran</a>'
                            f'</li>'}
                            <li class="nav-item dropdown">
                                <a href="#" class="dropdown-link nav-link effect" style="color: black;">
                                    <i class="fa-solid fa-fingerprint me-2"></i>Login</a>
                                <div class="dropdown-content">
                                    <a href="/login" style="color: black;">Login PSB</a>
                                    <a href="/web/login" style="color: black;">Login Orang Tua</a>
                                </div>
                            </li>
                            <li class="nav-item me-3">
                                <a class="nav-link effect" href="/bantuan"><i class="fa-solid fa-lock me-2" style="color: black;"></i>Bantuan</a>
                            </li>
                            {f'<li class="nav-item dropdown">'
                            f'<a href="#" class="dropdown-link nav-link effect"><i class="fa-solid fa-bullhorn me-2" style="color: black;"></i>Pengumuman</a>'
                            f'<div class="dropdown-content">'
                            f'<a href="/pengumuman/paud">PAUD</a>'
                            f'<a href="/pengumuman/tk-ra">TK / RA</a>'
                            f'<a href="/pengumuman/sd-mi">SD / MI</a>'
                            f'<a href="/pengumuman/smp-mts">SMP / MTS</a>'
                            f'<a href="/pengumuman/sma-ma">SMA / MA</a>'
                            f'</div>'
                            f'</li>' if is_halaman_pengumuman else ''}
                        </ul>
                    </div>
                </div>
            </nav>

            <div class="offcanvas offcanvas-end background" tabindex="-1" id="offcanvasNavbar" aria-labelledby="offcanvasNavbarLabel">
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="offcanvas" aria-label="Close"></button>
                <a class="navbar-brand mt-1 fw-semibold" href="/psb" style="display: flex; flex-direction: column; align-items: center;">
                    <img src="https://i.ibb.co.com/1MFsvMq/1731466812700.png" alt="Logo Pesantren" width="50">
                    Daarul Qur'an Istiqomah
                </a>
                <div class="offcanvas-body">
                    <ul class="navbar-nav justify-content-end flex-grow-1 pe-3">
                        <li class="nav-item me-3">
                            <a class="nav-link effect" style="color: black !important;" href="/psb"><i class="fa-solid fa-house me-2"></i>Beranda</a>
                        </li>
                        {f'<li class="nav-item me-3">'
                        f'<a class="nav-link effect" href="/pendaftaran" {"data-bs-toggle=\'modal\' data-bs-target=\'#modalPendaftaranTutup\'" if not is_halaman_pendaftaran else ""}>'
                        f'<i class="fa-solid fa-note-sticky me-2"></i>Pendaftaran</a>'
                        f'</li>'}
                        <li class="nav-item dropdown">
                            <a href="#" class="dropdown-link nav-link effect" style="color: black !important;">
                                <i class="fa-solid fa-fingerprint me-2"></i>Login</a>
                            <div class="dropdown-content">
                                <a href="/login" style="color: black;">Login PSB</a>
                                <a href="/web/login" style="color: black;">Login Orang Tua</a>
                            </div>
                        </li>
                        <li class="nav-item me-3">
                            <a class="nav-link effect" href="/bantuan"><i class="fa-solid fa-lock me-2"></i>Bantuan</a>
                        </li>
                        {f'<li class="nav-item dropdown">'
                        f'<a href="#" class="dropdown-link nav-link effect" style="color: black;"><i class="fa-solid fa-bullhorn me-2"></i>Pengumuman</a>'
                        f'<div class="dropdown-content">'
                        f'<a href="/pengumuman/paud">PAUD</a>'
                        f'<a href="/pengumuman/tk-ra">TK / RA</a>'
                        f'<a href="/pengumuman/sd-mi">SD / MI</a>'
                        f'<a href="/pengumuman/smp-mts">SMP / MTS</a>'
                        f'<a href="/pengumuman/sma-ma">SMA / MA</a>'
                        f'</div>'
                        f'</li>' if is_halaman_pengumuman else ''}
                    </ul>
                </div>
            </div>

            <div class="container mt-5 mb-5" style="background-color: #f5f5f4;">
                <div class="row">
                    <!-- Timeline -->
                    <div class="col-12 col-lg-6 mb-5">
                        <div class="timeline">
                            <!-- Panduan Pendaftaran Online -->
                            <div class="timeline-item">
                                <div class="timeline-icon bg-danger">
                                    <i class="fa-solid fa-briefcase"></i>
                                </div>
                                <div class="timeline-content bg-white rounded p-3">
                                    <span class="badge text-bg-danger text-uppercase mb-2">Panduan Pendaftaran Online</span>
                                    <p>Panduan pendaftaran online dapat didownload dengan klik link di bawah ini :</p>
                                    <div class="ratio ratio-16x9 my-4">
                                        <iframe src="https://www.youtube.com/embed/N7eYT3LQ7tQ" title="YouTube video player" allowfullscreen></iframe>
                                    </div>
                                </div>
                            </div>

                            <!-- Alur Pendaftaran Santri Baru -->
                            <div class="timeline-item">
                                <div class="timeline-icon bg-success">
                                    <i class="fa-solid fa-puzzle-piece"></i>
                                </div>
                                <div class="timeline-content bg-white rounded p-3">
                                    <span class="badge text-bg-success text-uppercase mb-3">Alur Pendaftaran Santri Baru</span>
                                    <ul>
                                        <li>Buka website <a href="/psb" class="text-decoration-none" style="color: purple;">https://aplikasi.dqi.ac.id/psb</a></li>
                                        <li>Klik menu daftar dan isikan data yang tersedia.</li>
                                        <li>Login di <a href="/login" class="text-decoration-none" style="color: purple;">https://aplikasi.dqi.ac.id/login</a></li>
                                        <li>Upload berkas yang dipersyaratkan dan bukti pembayaran.</li>
                                        <li>Tunggu verifikasi maksimal 3 hari.</li>
                                        <li>Ikuti tes seleksi Offline.</li>
                                        <li>Lihat hasil tes di <a href="/" class="text-decoration-none" style="color: purple;">https://aplikasi.dqi.ac.id/psb</a></li>
                                        <li>Setelah pembayaran daftar ulang, tunggu pengumuman serah terima santri baru.</li>
                                    </ul>
                                </div>
                            </div>

                            <!-- Video Profil -->
                            <div class="timeline-item">
                                <div class="timeline-icon bg-info">
                                    <i class="fa-solid fa-fingerprint"></i>
                                </div>
                                <div class="timeline-content bg-white rounded p-3">
                                    <span class="badge text-bg-info text-white text-uppercase">Video Profil Ponpes Daarul Qur'an Istiqomah</span>
                                    <div class="ratio ratio-16x9 my-4">
                                        <iframe width="437" height="315" src="https://www.youtube.com/embed/OiPEDy0Sv1U" title="" frameborder="0" allowfullscreen></iframe>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Informasi Kontak -->
                    <div class="col-12 col-lg-6">
                        <div class="bg-white rounded p-3 text-center">
                            <span style="font-size: 60px; font-weight: bold;">"</span>
                            <div class="text-secondary mb-4">
                                <span>Pondok Pesantren Daarul Qur'an Istiqomah</span><br>
                                <span>Jl. Ambawang, RT.03/RW.01, Karang Taruna, Kec. Pelaihari, Kabupaten Tanah Laut, Kalimantan Selatan 70815</span><br>
                                <span>Telp/Whatsapp: <a href="https://api.whatsapp.com/send?phone=%2B6282252079785" class="text-decoration-none" style="color: purple;">0822-5207-9785</a></span><br>
                            </div>
                            <div class="text-secondary mb-4">
                                <span>Informasi PSB & Konsultasi Pendidikan:</span><br>
                                <a href="#" class="text-decoration-none" style="color: purple;">0822-5207-9785</a><br>
                            </div>
                            <h5>Media Sosial Kami</h5>
                            <!-- <span class="text-uppercase" style="color: purple;">Instagram : @dqimedia</span><br>
                            <span class="text-uppercase" style="color: purple;">Facebook  : @Daarul Quran Istiqomah</span><br>
                            <span class="text-uppercase" style="color: purple;">Youtube   : @dqimedia</span><br>
                            -->
                            
                            <span style="color: purple;">Instagram : <a href="https://www.instagram.com/dqimedia" class="text-decoration-none" style="color: purple;">@dqimedia</a></span><br>
                            <span style="color: purple;">Facebook  : <a href="https://www.facebook.com/daquistiqomah/" class="text-decoration-none" style="color: purple;">@Daarul Quran Istiqomah</span></a><br>
                            <span style="color: purple;">Youtube   : <a href="https://www.youtube.com/@dqimedia" class="text-decoration-none" style="color: purple;">@dqimedia</a></span><br>
                        </div>
                    </div>
                </div>
            </div>

            <footer class="p-2 mt-auto" style="background-color: #f5f5f4; display: flex; justify-content: space-between; flex-wrap: wrap;">
                <div class="ms-5">
                    <ul style="list-style-type: none; display: flex; text-transform: uppercase; font-size: 13px;" class="fw-semibold">
                        <li><a href="/psb" class="me-4 effect" style="text-decoration: none; color: black !important;">Home</a></li>
                        <li><a href="/beranda" class="me-4 effect" style="text-decoration: none; color: black !important;" target="_blank">Info Pondok</a></li>
                        <li><a href="https://drive.google.com/drive/folders/1C5U4oDSJlOe1qO7tbw0wZgYenHKEHUVM?usp=sharing" class="me-4 effect" style="text-decoration: none; color: black !important;" target="_blank">Brosur</a></li>
                        <li><a href="#" class="me-4 effect" style="text-decoration: none; color: black !important;">Panduan</a></li>
                    </ul>
                </div>
                <div class="me-5">
                    <p class="text-center mt-1">© 2025 TIM IT PPIB</p>
                </div>
            </footer>

            <!-- Modal -->
            <div class="modal fade" id="modalPendaftaranTutup" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h1 class="modal-title fs-5" id="exampleModalLabel">Pendaftaran ditutup!</h1>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <p>Mohon maaf, pendaftaran telah ditutup karena kuota telah terpenuhi.</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Tutup</button>
                        </div>
                    </div>
                </div>
            </div>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11.14.5/dist/sweetalert2.all.min.js"></script>
            </body>
            </html>
        """
        return request.make_response(html_response)

class PendaftaranSeleksiPaud(http.Controller):
    @http.route('/pengumuman/paud', type='http', auth='public')
    def pengumuman(self, **kwargs):

        # Mengambil nilai kuota pendaftaran dari ir.config_parameter
        config_param = request.env['ir.config_parameter'].sudo()
        is_halaman_pendaftaran = config_param.get_param('pesantren_pendaftaran.is_halaman_pendaftaran')
        is_halaman_pengumuman = config_param.get_param('pesantren_pendaftaran.is_halaman_pengumuman')

        if is_halaman_pengumuman:
            # Render form pendaftaran HTML
            calon_santri = request.env['ubig.pendaftaran'].sudo().search([('state', 'in', ['diterima', 'ditolak']), ('jenjang_id.jenjang', '=', 'paud')])

            return request.render('pesantren_pendaftaran.pendaftaran_seleksi_paud_template', {
                'santri': calon_santri,
                'is_halaman_pendaftaran': is_halaman_pendaftaran,
            })
        else:
            return request.redirect('/psb')
class PendaftaranSeleksiTk(http.Controller):
    @http.route('/pengumuman/tk-ra', type='http', auth='public')
    def pengumuman(self, **kwargs):

        # Mengambil nilai kuota pendaftaran dari ir.config_parameter
        config_param = request.env['ir.config_parameter'].sudo()
        is_halaman_pendaftaran = config_param.get_param('pesantren_pendaftaran.is_halaman_pendaftaran')
        is_halaman_pengumuman = config_param.get_param('pesantren_pendaftaran.is_halaman_pengumuman')

        if is_halaman_pengumuman:
            # Render form pendaftaran HTML
            calon_santri = request.env['ubig.pendaftaran'].sudo().search([('state', 'in', ['diterima', 'ditolak']), ('jenjang_id.jenjang', '=', 'tk')])

            return request.render('pesantren_pendaftaran.pendaftaran_seleksi_tk_template', {
                'santri': calon_santri,
                'is_halaman_pendaftaran': is_halaman_pendaftaran,
            })
        else:
            return request.redirect('/psb')
class PendaftaranSeleksiSdMi(http.Controller):
    @http.route('/pengumuman/sd-mi', type='http', auth='public')
    def pengumuman(self, **kwargs):

        # Mengambil nilai kuota pendaftaran dari ir.config_parameter
        config_param = request.env['ir.config_parameter'].sudo()
        is_halaman_pendaftaran = config_param.get_param('pesantren_pendaftaran.is_halaman_pendaftaran')
        is_halaman_pengumuman = config_param.get_param('pesantren_pendaftaran.is_halaman_pengumuman')

        if is_halaman_pengumuman:
            # Render form pendaftaran HTML
            calon_santri = request.env['ubig.pendaftaran'].sudo().search([('state', 'in', ['diterima', 'ditolak']), ('jenjang_id.jenjang', '=', 'sdmi')])
            
            return request.render('pesantren_pendaftaran.pendaftaran_seleksi_sdmi_template', {
                'santri': calon_santri,
                'is_halaman_pendaftaran': is_halaman_pendaftaran,
            })
        else:
            return request.redirect('/psb')

class PendaftaranSeleksiSmpMts(http.Controller):
    @http.route('/pengumuman/smp-mts', type='http', auth='public')
    def pengumuman(self, **kwargs):

        # Mengambil nilai kuota pendaftaran dari ir.config_parameter
        config_param = request.env['ir.config_parameter'].sudo()
        is_halaman_pendaftaran = config_param.get_param('pesantren_pendaftaran.is_halaman_pendaftaran')
        is_halaman_pengumuman = config_param.get_param('pesantren_pendaftaran.is_halaman_pengumuman')

        if is_halaman_pengumuman:
            # Render form pendaftaran HTML
            calon_santri = request.env['ubig.pendaftaran'].sudo().search([('state', 'in', ['diterima', 'ditolak']), ('jenjang_id.jenjang', '=', 'smpmts')])
            return request.render('pesantren_pendaftaran.pendaftaran_seleksi_smpmts_template', {
                'santri': calon_santri,
                'is_halaman_pendaftaran': is_halaman_pendaftaran,
            })
        else:
            return request.redirect('/psb')
    
class PendaftaranSeleksiSmaMa(http.Controller):
    @http.route('/pengumuman/sma-ma', type='http', auth='public')
    def pengumuman(self, **kwargs):

        # Mengambil nilai kuota pendaftaran dari ir.config_parameter
        config_param = request.env['ir.config_parameter'].sudo()
        is_halaman_pendaftaran = config_param.get_param('pesantren_pendaftaran.is_halaman_pendaftaran')
        is_halaman_pengumuman = config_param.get_param('pesantren_pendaftaran.is_halaman_pengumuman')

        if is_halaman_pengumuman:
            # Render form pendaftaran HTML
            calon_santri = request.env['ubig.pendaftaran'].sudo().search([('state', 'in', ['diterima', 'ditolak']), ('jenjang_id.jenjang', '=', 'smama')])
            return request.render('pesantren_pendaftaran.pendaftaran_seleksi_smama_template', {
                'santri': calon_santri,
                'is_halaman_pendaftaran': is_halaman_pendaftaran,
            })
        else:
            return request.redirect('/psb')


class RefDataController(http.Controller):
    @http.route('/get_provinsi', type='http', auth='public', methods=['POST'], csrf=False)
    def get_provinsi(self, **kwargs):
        # Ambil parameter 'query' dari permintaan
        query = request.httprequest.json.get('query', '').lower()
        
        provinces = request.env['cdn.ref_propinsi'].sudo().search([('name', 'ilike', query)])
        data = [{'id': prov.id, 'name': prov.name} for prov in provinces]
        
        if request.httprequest.headers.get('Content-Type') == 'application/json':
            # Permintaan JSON
            return json.dumps(data)
        else:
            # Permintaan HTTP biasa
            return request.make_response(
                json.dumps(data),
                headers={'Content-Type': 'application/json'}
            )

    @http.route('/get_kota/<int:provinsi_id>', type='http', auth='public', methods=['POST'], csrf=False)
    def get_kota(self, provinsi_id, **kwargs):
        kota = request.env['cdn.ref_kota'].sudo().search([('propinsi_id', '=', provinsi_id)])
        data = [{'id': city.id, 'name': city.name} for city in kota]
        
        if request.httprequest.headers.get('Content-Type') == 'application/json':
            # Permintaan JSON
            return json.dumps(data)
        else:
            # Permintaan HTTP biasa
            return request.make_response(
                json.dumps(data),
                headers={'Content-Type': 'application/json'}
            )

    @http.route('/get_kecamatan/<int:kota_id>', type='http', auth='public', methods=['POST'], csrf=False)
    def get_kecamatan(self, kota_id, **kwargs):
        kecamatan = request.env['cdn.ref_kecamatan'].sudo().search([('kota_id', '=', kota_id)])
        data = [{'id': kec.id, 'name': kec.name} for kec in kecamatan]
        
        if request.httprequest.headers.get('Content-Type') == 'application/json':
            # Permintaan JSON
            return json.dumps(data)
        else:
            # Permintaan HTTP biasa
            return request.make_response(
                json.dumps(data),
                headers={'Content-Type': 'application/json'}
            )




class PortalOrangTua(http.Controller):
    @http.route('/portal_orang_tua', type='http', auth='public', website=True)
    def portal_orang_tua(self, *kwargs):
        # Ambil data dari sesi
        user_id = request.session.get('user_id')
        
        record = request.env['ubig.pendaftaran'].sudo().search([('id', '=', user_id)])

        if not user_id or not record:
            return request.redirect('/login')

        email = record.email
        no_telp = record.nomor_login

        if email:
            records = request.env['ubig.pendaftaran'].sudo().search([('email', '=', email)])

        if no_telp:
            records = request.env['ubig.pendaftaran'].sudo().search([('nomor_login', '=', no_telp)])

        first_record = records[0]

        # Prioritaskan nama
        display_name = first_record['wali_nama'] or first_record['nama_ayah'] or first_record['nama_ibu']
        
        # Ambil nilai dari field konfigurasi
        config_obj = http.request.env['ir.config_parameter'].sudo()

        is_halaman_pengumuman = config_obj.get_param('pesantren_pendaftaran.is_halaman_pengumuman')
        is_halaman_pendaftaran = config_obj.get_param('pesantren_pendaftaran.is_halaman_pendaftaran')
        no_rekening = config_obj.get_param('pesantren_pendaftaran.no_rekening', default='7181863913')

        # Daftar status yang akan ditampilkan
        state_list = [
            ('batal', 'Batal'),
            ('draft', 'Draft'),
            ('terdaftar', 'Terdaftar'),
            ('seleksi', 'Seleksi'),
            ('diterima', 'Diterima'),
            ('ditolak', 'Ditolak'),
        ]

        state_progress = {
            'batal': 0,
            'draft': 25,
            'terdaftar': 50,
            'seleksi': 75,
            'diterima': 100,
        }

        state_tooltip_messages = {
            'batal': "Status ini menunjukkan bahwa pendaftaran dibatalkan oleh peserta atau sistem.",
            'draft': "Status ini menunjukkan bahwa pendaftaran masih dalam tahap draft, Calon Sudah terdaftar, tetapi belum membayar biaya pendaftaran.",
            'terdaftar': "Status ini menunjukkan bahwa pendaftaran sudah berhasil, dan data sudah konfirmasi oleh Ponpes.",
            'seleksi': "Status ini menunjukkan bahwa pendaftaran sedang dalam tahap seleksi, Calon Santri Melalukan Membaca Al-Qur'an & Wawancara.",
            'diterima': "Status ini menunjukkan bahwa pendaftaran telah diterima, dan peserta memenuhi syarat.",
            'ditolak': "Status ini menunjukkan bahwa pendaftaran ditolak karena tidak memenuhi kriteria atau persyaratan.",
        }

        rows_html = ''
        for rec in records:
            csrf_token = request.csrf_token()
            
            # Tentukan status pembayaran dan kelas badge
            status_text = (
                'Menunggu Validasi'
                if rec.bukti_pembayaran
                else rec.status_pembayaran.replace('belumbayar', 'Belum Bayar').replace('sudahbayar', 'Sudah Bayar')
            )

            badge_class = (
                'success'
                if rec.status_pembayaran == 'sudahbayar'
                else 'warning' if rec.bukti_pembayaran
                else 'danger'
            )

            is_disabled = 'disabled' if rec.status_pembayaran == 'sudahbayar' else ''
            
            # Buat HTML untuk status pendaftaran siswa
            state_html = ''
            for state_key, state_label in state_list:
                tooltip_message = state_tooltip_messages.get(state_key, "Tidak ada informasi status.")
                if state_key == rec.state:
                    state_html += f'<span class="badge me-1 mb-2 badge-active" title="Ini adalah status pendaftaran saat ini dari anak anda. {tooltip_message}" data-bs-toggle="tooltip" data-bs-placement="bottom">{state_label}</span>'
                else:
                    state_html += f'<span class="badge badge-inactive me-1 mb-2" title="{tooltip_message}" data-bs-toggle="tooltip" data-bs-placement="bottom">{state_label}</span>'
            
            # Progress bar untuk pendaftaran
            if rec.state == "ditolak":
                progress_html = ''
            else:
                progress_percentage = state_progress.get(rec.state, 0)
                progress_html = f"""
                <div class="progress-container mb-3">
                    <div class="progress-bar-custom">
                        <div class="progress-fill" style="width: {progress_percentage}%"></div>
                    </div>
                    <span class="progress-text">Pendaftaran: {progress_percentage}%</span>
                </div>
                """

            # Card untuk setiap siswa
            rows_html += f"""
            <div class="student-card">
                <div class="student-card-header">
                    <div class="student-info">
                        <i class="fas fa-user-graduate student-icon"></i>
                        <span class="student-name">{rec.partner_id.name}</span>
                    </div>
                    <button class="btn btn-upload {is_disabled}" data-bs-toggle="modal" data-bs-target="#uploadModal-{rec.id}" {is_disabled}>
                        <i class="fas fa-upload me-2"></i>Upload Bukti
                    </button>
                </div>
                
                <div class="student-card-body">
                    <div class="status-badges">
                        {state_html}
                    </div>
                    
                    {progress_html}
                    
                    <div class="payment-status">
                        <span class="badge payment-badge payment-{badge_class}">{status_text}</span>
                    </div>
                </div>
                
                <!-- Modal tetap sama -->
                <div class="modal fade" id="uploadModal-{rec.id}" tabindex="-1" aria-labelledby="uploadModalLabel-{{rec.id}}" aria-hidden="true">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title" id="uploadModalLabel-{rec.id}">Upload Bukti Pembayaran</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <form action="/upload_bukti_pembayaran" method="post" enctype="multipart/form-data">
                                    <input type="hidden" name="csrf_token" value="{csrf_token}">
                                    <input type="hidden" name="record_id" value="{rec.id}">
                                    <div class="mb-3">
                                        <label for="buktiPembayaran-{rec.id}" class="form-label">Pilih File</label>
                                        <input type="file" class="form-control" id="buktiPembayaran-{{rec.id}}" name="bukti_pembayaran" required>
                                    </div>
                                    <button type="submit" class="btn btn-success">Upload</button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """


            next_rows = ""
            for data in records:
                # Filter biaya_ids berdasarkan kondisi
                filtered_biaya = [
                    biaya for biaya in data.jenjang_id.rincian_ids
                    if (data.is_alumni and biaya.is_alumni) or (data.is_pindahan_sd and biaya.is_pindahan_sd) or (not data.is_alumni and not data.is_pindahan_sd and not biaya.is_alumni and not biaya.is_pindahan_sd)
                ]

                biaya_details = ""
                if data.status_pembayaran == 'sudahbayar':  # Cek apakah sudah bayar
                    for biaya in filtered_biaya:
                        # Buat URL untuk unduh file
                        download_url = f"/download/biaya/{biaya.id}"
                        
                        # Tambahkan detail biaya dengan tautan unduhan
                        biaya_details += f"""
                        <div class="d-flex justify-content-between mb-3">
                            <p class="fw-semibold">({biaya.name})</p>
                            <a href="{download_url}" class="btn btn-secondary btn-sm">Unduh Rincian</a>
                        </div>
                        """

                # Tentukan status pembayaran dan styling
                if data.status_pembayaran == 'belumbayar':
                    status_pembayaran = f"Rp {int(data.biaya):,}".replace(',', '.') + " (Belum Bayar)"
                    status_class = "status-belum-bayar"
                elif data.status_pembayaran == 'sudahbayar':
                    status_pembayaran = "Rp 0 (Sudah Bayar)"
                    status_class = "status-sudah-bayar"
                elif data.state == 'ditolak':
                    status_pembayaran = "Pendaftaran Dibatalkan"
                    status_class = "status-dibatalkan"
                else:
                    status_pembayaran = ""
                    status_class = ""

                # Buat HTML untuk setiap record dengan desain card modern
                next_rows += f"""
                <div class="biaya-card mb-3">
                    <div class="biaya-card-header">
                        <div class="student-info-biaya">
                            <i class="fas fa-user-graduate student-icon-biaya"></i>
                            <span class="student-name-biaya">{data.partner_id.name}</span>
                        </div>
                    </div>
                    <div class="biaya-card-body">
                        <div class="jenjang-info">
                            <span class="jenjang-label">Jenjang:</span>
                            <span class="jenjang-value">{data.jenjang.replace('sdmi', 'SD / MI').replace('smpmts', 'SMP / MTS').replace('smama', 'SMA / MA').replace('paud', 'PAUD').replace('tk', 'TK')}</span>
                        </div>
                        
                        {biaya_details}
                        
                        <div class="biaya-info">
                            <span class="biaya-label">Biaya Pendaftaran</span>
                            <span class="biaya-amount {status_class}">{status_pembayaran}</span>
                        </div>
                    </div>
                </div>
                """

        # Membuat HTML dinamis
        html_content = f"""
                <html lang="en">
            <head>
            <!-- Primary Meta Tags --> 
            <title>PSB Daarul Qur`an Istiqomah</title> 
            <meta name="title" content="PSB Daarul Qur`an Istiqomah" /> 
            <meta name="description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
 
            <!-- Open Graph / Facebook --> 
            <meta property="og:type" content="website" /> 
            <meta property="og:url" content="https://aplikasi.dqi.ac.id/pendaftaran" /> 
            <meta property="og:title" content="PSB Daarul Qur`an Istiqomah" /> 
            <meta property="og:description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
            <meta property="og:image" content="https://drive.usercontent.google.com/download?id=1VZRccbFtq82wTNcReEq43piA_GJQddcm" /> 
 
            <!-- Twitter --> 
            <meta property="twitter:card" content="summary_large_image" /> 
            <meta property="twitter:url" content="https://aplikasi.dqi.ac.id/pendaftaran" /> 
            <meta property="twitter:title" content="PSB Daarul Qur`an Istiqomah" /> 
            <meta property="twitter:description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
            <meta property="twitter:image" content="https://drive.usercontent.google.com/download?id=1VZRccbFtq82wTNcReEq43piA_GJQddcm" />
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Portal Orang Tua - Daarul Qur'an Istiqomah</title>
                <link rel="icon" type="image/x-icon" href="/pesantren_pendaftaran/static/img/favicon.ico?v=1">
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/all.min.css" />
                <link href="https://cdn.jsdelivr.net/npm/sweetalert2@11.14.5/dist/sweetalert2.min.css" rel="stylesheet"/>
                <style>

                    body {{
                        background: white !important;
                    }}

                    .offcanvas.offcanvas-end {{
                        
                        width: 250px; /* Lebar kustom untuk offcanvas */
                    }}
                    
                    .offcanvas .nav-link {{
                        color: black; /* teks warna putih */
                    }}
                    
                    .offcanvas .btn-close {{
                        position: absolute;
                        top: 10px;
                        right: 10px;
                        filter: invert(1);
                    }}

                    .background {{
                        background: white !important;
                    }}

                    a.effect {{
                        transition: .1s !important;
                    }}

                    a.effect:hover {{
                        box-shadow: 0 3px 10px rgba(0,0,0,0.2) !important;
                    }}

                    /* Desain Dropdown */
                    .dropdown {{
                        position: relative;
                    }}

                    .dropdown-link {{
                        cursor: pointer;
                    }}

                    .dropdown-content {{
                        display: none;
                        position: absolute;
                        top: 100%;
                        right: 0;
                        background-color: #ffffff;
                        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
                        border-radius: 5px;
                        min-width: 150px;
                        z-index: 1;
                        overflow: hidden;
                    }}

                    .dropdown-content a {{
                        color: #333;
                        padding: 10px 15px;
                        display: block;
                        text-decoration: none;
                        transition: background-color 0.2s;
                    }}

                    .dropdown-content a:hover {{
                        background-color: #f1f1f1;
                    }}

                    /* Menampilkan dropdown saat hover */
                    .dropdown:hover .dropdown-content {{
                        display: block;
                        animation: fadeIn 0.3s;
                    }}

                    /* Animasi fade-in */
                    @keyframes fadeIn {{
                        from {{
                        opacity: 0;
                        transform: translateY(-10px);
                        }}
                        to {{
                        opacity: 1;
                        transform: translateY(0);
                        }}
                    }}


                .card-header {{
                    background-color: #4CAF50;
                    color: white;
                    font-size: 1.2rem;
                    font-weight: bold;
                    }}

                .card-body {{
                    background-color: white;
                    color: #333;
                }}

                .table th, .table td {{
                    vertical-align: middle;
                }}

                .progress-bar {{
                    background-color: #28a745;
                }}

                .status-card {{
                    border-left: 5px solid #4CAF50;
                }}

                .inactive {{
                    opacity: 0.6;
                }}

                .progress-bar {{
                    transition: width 1s ease-in-out;
                }}

                @media (max-width: 767px) {{
                    .table thead {{
                        display: none;
                    }}

                    .table, .table tbody, .table tr, .table td {{
                        display: block;
                        width: 100%;
                    }}

                    .table td {{
                        text-align: right;
                        position: relative;
                        padding-left: 50%;
                    }}

                    .table td::before {{
                        content: attr(data-label);
                        position: ab        solute;
                        left: 10px;
                        font-weight: bold;
                    }}
                }}
                .student-card {{
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 15px;
                    padding: 20px;
                    margin-bottom: 20px;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                    border-left: 5px solid #4CAF50;
                }}

                .student-card-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;
                }}

                .student-info {{
                    display: flex;
                    align-items: center;
                }}

                .student-icon {{
                    color: #4CAF50;
                    font-size: 20px;
                    margin-right: 10px;
                }}

                .student-name {{
                    font-size: 18px;
                    font-weight: 600;
                    color: #333;
                    text-transform: capitalize;
                }}

                .btn-upload {{
                    background: white;
                    border: none;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-size: 14px;
                    transition: all 0.3s ease;
                }}

                .btn-upload:hover:not(.disabled) {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);
                }}

                .btn-upload.disabled {{
                    background: #6c757d;
                    cursor: not-allowed;
                }}

                .student-card-body {{
                    border-top: 1px solid #eee;
                    padding-top: 15px;
                }}

                .status-badges {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                    margin-bottom: 15px;
                }}

                .badge-active {{
                    background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                    color: white;
                    padding: 6px 12px;
                    border-radius: 15px;
                    font-size: 12px;
                    font-weight: 500;
                }}

                .badge-inactive {{
                    background: #e9ecef;
                    color: #6c757d;
                    padding: 6px 12px;
                    border-radius: 15px;
                    font-size: 12px;
                    font-weight: 500;
                }}

                .progress-container {{
                    margin-bottom: 15px;
                }}

                .progress-bar-custom {{
                    width: 100%;
                    height: 12px;
                    background-color: #e9ecef;
                    border-radius: 10px;
                    overflow: hidden;
                    position: relative;
                }}

                .progress-fill {{
                    height: 100%;
                    background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%);
                    border-radius: 10px;
                    transition: width 0.8s ease-in-out;
                }}

                .progress-text {{
                    font-size: 13px;
                    color: #666;
                    margin-top: 5px;
                    display: block;
                }}

                .payment-status {{
                    display: flex;
                    justify-content: flex-start;
                }}

                .payment-badge {{
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-size: 13px;
                    font-weight: 500;
                }}

                .payment-success {{
                    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                    color: white;
                }}

                .payment-warning {{
                    background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
                    color: #212529;
                }}

                .payment-danger {{
                    background: linear-gradient(135deg, #dc3545 0%, #e83e8c 100%);
                    color: white;
                }}
                .instructions-section {{
                    background: #f8f9fa;
                    border-radius: 12px;
                    padding: 20px;
                    margin-top: 20px;
                }}

                .instructions-title {{
                    color: #333;
                    font-weight: 600;
                    margin-bottom: 15px;
                    display: flex;
                    align-items: center;
                }}

                .instructions-title i {{
                    color: #4CAF50;
                    margin-right: 8px;
                }}

                .payment-method {{
                    background: white;
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 15px;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
                }}

                .payment-method-title {{
                    color: #4CAF50;
                    font-weight: 600;
                    margin-bottom: 10px;
                    display: flex;
                    align-items: center;
                }}

                .payment-method-title i {{
                    margin-right: 8px;
                }}

                .payment-method ul {{
                    margin: 0;
                    padding-left: 20px;
                }}

                .payment-method li {{
                    margin-bottom: 5px;
                    color: #666;
                    font-size: 14px;
                }}

                .account-info {{
                    background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 12px;
                    text-align: center;
                    margin-top: 20px;
                    box-shadow: 0 4px 15px rgba(76, 175, 80, 0.2);
                }}

                .account-info i {{
                    font-size: 2rem;
                    margin-bottom: 10px;
                    display: block;
                }}

                .account-info p {{
                    margin: 0;
                    font-size: 1.1rem;
                    font-weight: 600;
                }}

                .account-info small {{
                    opacity: 0.9;
                    display: block;
                    margin-top: 5px;
                }}

                /* Responsive Design */
                @media (max-width: 768px) {{
                    .student-card-header {{
                        flex-direction: column;
                        gap: 10px;
                        align-items: flex-start;
                    }}
                    
                    .btn-upload {{
                        align-self: flex-end;
                    }}
                    
                    .status-badges {{
                        justify-content: center;
                    }}
                }}

                /* Remove table styling untuk section progress */
                .progress-section .table {{
                    display: none;
                }}

                .biaya-card {{
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 15px;
                    padding: 20px;
                    margin-bottom: 15px;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                    border-left: 5px solid #4CAF50;
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                }}

                .biaya-card:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
                }}

                .biaya-card-header {{
                    display: flex;
                    align-items: center;
                    margin-bottom: 15px;
                    padding-bottom: 10px;
                    border-bottom: 1px solid #eee;
                }}

                .student-info-biaya {{
                    display: flex;
                    align-items: center;
                }}

                .student-icon-biaya {{
                    color: #4CAF50;
                    font-size: 18px;
                    margin-right: 10px;
                }}

                .student-name-biaya {{
                    font-size: 18px;
                    font-weight: 600;
                    color: #333;
                    text-transform: capitalize;
                }}

                .biaya-card-body {{
                    space-y: 10px;
                }}

                .jenjang-info {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;
                    padding: 10px;
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    border-radius: 8px;
                }}

                .jenjang-label {{
                    font-weight: 500;
                    color: #666;
                    font-size: 14px;
                }}

                .jenjang-value {{
                    font-weight: 600;
                    color: #333;
                    font-size: 14px;
                }}

                .biaya-info {{
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    padding: 15px;
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    border-radius: 10px;
                    margin-top: 15px;
                }}

                .biaya-label {{
                    color: #666;
                    font-size: 14px;
                    font-weight: 500;
                    margin-bottom: 5px;
                }}

                .biaya-amount {{
                    font-size: 18px;
                    font-weight: 700;
                    color: white;
                }}

                .status-belum-bayar {{
                    color: #dc2626 !important;
                }}

                .status-sudah-bayar {{
                    color: #51cf66 !important;
                }}

                .status-dibatalkan {{
                    color: #ffd43b !important;
                }}

                /* Total Bayar Card */
                .total-bayar-card {{
                    background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                    border-radius: 15px;
                    padding: 20px;
                    text-align: center;
                    color: white;
                    margin-top: 20px;
                    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
                }}

                .total-bayar-icon {{
                    font-size: 2rem;
                    margin-bottom: 10px;
                    display: block;
                }}

                .total-bayar-label {{
                    font-size: 16px;
                    font-weight: 500;
                    margin-bottom: 5px;
                    opacity: 0.9;
                }}

                .total-bayar-amount {{
                    font-size: 24px;
                    font-weight: 700;
                    margin: 0;
                }}

                /* Responsive Design */
                @media (max-width: 768px) {{
                    .jenjang-info {{
                        flex-direction: column;
                        text-align: center;
                        gap: 5px;
                    }}
                    
                    .biaya-amount {{
                        font-size: 16px;
                    }}
                    
                    .total-bayar-amount {{
                        font-size: 20px;
                    }}
                }}


                </style>
                
            </head>
            <body>

            <nav class="navbar navbar-expand-lg" style="height: 65px;">
                <div class="container-fluid">
                    <a class="navbar-brand ms-5  fw-semibold" href="/psb">
                        <img src="https://i.ibb.co.com/1MFsvMq/1731466812700.png" width="50" alt="Logo Pesantren" />
                        Daarul Qur'an Istiqomah
                    </a>
                    <button class="navbar-toggler ms-auto" type="button" data-bs-toggle="offcanvas" data-bs-target="#offcanvasNavbar" aria-controls="offcanvasNavbar">
                        <span class="navbar-toggler-icon"></span>
                    </button>
                    <div class="collapse navbar-collapse" id="navbarNav">
                        <ul class="navbar-nav ms-auto">
                            <li class="nav-item me-3">
                                <a class="nav-link " style="color: black !important;" href="/psb"><i class="fa-solid fa-house me-2"></i>Beranda</a>
                            </li>
                            {f'<li class="nav-item me-3">'
                            f'<a class="nav-link " href="/pendaftaran" {"data-bs-toggle='modal' data-bs-target='#modalPendaftaranTutup'" if not is_halaman_pendaftaran else ""}>'
                            f'<i class="fa-solid fa-note-sticky me-2"></i>Pendaftaran</a>'
                            f'</li>'}
                            <li class="nav-item dropdown">
                                <a href="#" class="dropdown-link nav-link"
                                    style="color: black !important;">
                                    <i class="fa-solid fa-fingerprint me-2"></i>Login</a>
                                <div class="dropdown-content">
                                    <a href="/login">Login PSB</a>
                                    <a href="/web/login">Login Orang Tua</a>
                                </div>
                            </li>
                            <li class="nav-item me-3">
                                <a class="nav-link " href="/bantuan"><i class="fa-solid fa-lock me-2"></i>Bantuan</a>
                            </li>
                            {f'<li class="nav-item dropdown">'
                            f'<a href="#" class="dropdown-link nav-link "><i class="fa-solid fa-bullhorn me-2"></i>Pengumuman</a>'
                            f'<div class="dropdown-content">'
                            f'<a href="/pengumuman/paud">PAUD</a>'
                            f'<a href="/pengumuman/tk-ra">TK / RA</a>'
                            f'<a href="/pengumuman/sd-mi">SD / MI</a>'
                            f'<a href="/pengumuman/smp-mts">SMP / MTS</a>'
                            f'<a href="/pengumuman/sma-ma">SMA / MA</a>'
                            f'</div>'
                            f'</li>' if is_halaman_pengumuman else ''}
                            <li class="nav-item me-3">
                                <a class="nav-link  log" href="/logout"><i class="fa-solid fa-right-from-bracket me-2"></i>Keluar</a>
                            </li>
                            </ul>
                    </div>
                </div>
            </nav>

            <div class="offcanvas offcanvas-end background" tabindex="-1" id="offcanvasNavbar" aria-labelledby="offcanvasNavbarLabel">
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="offcanvas" aria-label="Close"></button>
                <a class="navbar-brand mt-1  fw-semibold" href="/psb" style="display: flex; flex-direction: column; align-items: center;">
                    <img src="https://i.ibb.co.com/1MFsvMq/1731466812700.png" width="50" alt="Logo Pesantren" />
                    Daarul Qur'an Istiqomah
                </a>
                <div class="offcanvas-body">
                    <ul class="navbar-nav justify-content-end flex-grow-1 pe-3">
                        <li class="nav-item me-3">
                            <a class="nav-link " style="color: black !important;" href="/psb"><i class="fa-solid fa-house me-2"></i>Beranda</a>
                        </li>
                        {f'<li class="nav-item me-3">'
                        f'<a class="nav-link " href="/pendaftaran" {"data-bs-toggle='modal' data-bs-target='#modalPendaftaranTutup'" if not is_halaman_pendaftaran else ""}>'
                        f'<i class="fa-solid fa-note-sticky me-2"></i>Pendaftaran</a>'
                        f'</li>'}
                        <li class="nav-item dropdown">
                            <a href="#" class="dropdown-link nav-link"
                                style="color: black !important;">
                                <i class="fa-solid fa-fingerprint me-2"></i>Login</a>
                            <div class="dropdown-content">
                                <a href="/login">Login PSB</a>
                                <a href="/web/login">Login Orang Tua</a>
                            </div>
                        </li>
                        <li class="nav-item me-3">
                            <a class="nav-link " href="/bantuan"><i class="fa-solid fa-lock me-2"></i>Bantuan</a>
                        </li>
                        {f'<li class="nav-item dropdown">'
                        f'<a href="#" class="dropdown-link nav-link "><i class="fa-solid fa-bullhorn me-2"></i>Pengumuman</a>'
                        f'<div class="dropdown-content">'
                        f'<a href="/pengumuman/paud">PAUD</a>'
                        f'<a href="/pengumuman/tk-ra">TK / RA</a>'
                        f'<a href="/pengumuman/sd-mi">SD / MI</a>'
                        f'<a href="/pengumuman/smp-mts">SMP / MTS</a>'
                        f'<a href="/pengumuman/sma-ma">SMA / MA</a>'
                        f'</div>'
                        f'</li>' if is_halaman_pengumuman else ''}
                        <li class="nav-item me-3">
                            <a class="nav-link  log" href="/logout"><i class="fa-solid fa-right-from-bracket me-2"></i>Keluar</a>
                        </li>
                        </ul>
                    </ul>
                </div>
            </div>

            <div class="container my-5">
                <h2 class="text-center mb-4 ">Selamat Datang Bapak/Ibu,<span class="text-capitalize"> {display_name}</span></h2>

                <!-- Progres PSB Anak -->
                <div class="card mb-4 progress-section">
                    <div class="card-header">
                        <i class="fas fa-chart-line me-2"></i>Progres PSB Anak Anda
                    </div>
                    <div class="card-body">
                        {rows_html}
                    </div>
                </div>

                <!-- Info Pembayaran PSB -->
                <div class="card mb-4">
                    <div class="card-header">
                        Informasi Pembayaran PSB
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h5 class="mb-4">
                                    <i class="fas fa-money-bill-wave me-2" style="color: #4CAF50;"></i>
                                    Biaya PSB:
                                </h5>
                                <div class="biaya-container">
                                    {next_rows}
                                </div>
                                
                                <div class="total-bayar-card">
                                    <i class="fas fa-calculator total-bayar-icon"></i>
                                    <div class="total-bayar-label">Total Bayar</div>
                                    <p class="total-bayar-amount">Rp {str(f"{sum(int(data.biaya) if data.status_pembayaran == 'belumbayar' else 0 for data in records):,}").replace(',', '.')}</p>
                                </div>
                            </div>
                           <div class="col-lg-6">
                            <div class="instructions-section">
                            <h5 class="instructions-title">
                                <i class="fas fa-info-circle"></i>
                                Instruksi Pembayaran:
                            </h5>

                            <div class="payment-method">
                                <div class="payment-method-title">
                                <i class="fas fa-mobile-alt"></i>
                                Melalui Mobile Bank BSI:
                                </div>
                                <ul>
                                <li>Login ke aplikasi BSI Mobile.</li>
                                <li>Pilih menu Transfer.</li>
                                <li>Masukkan nomor rekening tujuan.</li>
                                <li>Masukkan jumlah pembayaran.</li>
                                <li>Tambahkan catatan (opsional) jika diperlukan.</li>
                                <li>
                                    Pembayaran berhasil dan Anda akan menerima bukti transaksi.
                                </li>
                                </ul>
                            </div>

                            <div class="payment-method">
                                <div class="payment-method-title">
                                <i class="fas fa-credit-card"></i>
                                Melalui ATM Bank BSI:
                                </div>
                                <ul>
                                <li>Masukkan kartu ATM dan PIN.</li>
                                <li>Pilih menu Transfer.</li>
                                <li>Pilih tujuan transfer.</li>
                                <li>Masukkan nomor rekening tujuan.</li>
                                <li>Verifikasi pembayaran dan lanjutkan.</li>
                                <li>Pembayaran berhasil dan Anda menerima bukti pembayaran.</li>
                                </ul>
                            </div>

                            <div class="account-info">
                                <i class="fas fa-university"></i>
                                <p>Rekening: BSI {no_rekening}</p>
                                <small
                                >Silakan melakukan pembayaran melalui transfer bank ke rekening
                                yang tertera</small
                                >
                            </div>
                            </div>
                        </div>
                        </div>
                    </div>
                </div>

                <!-- Riwayat Pembayaran -->
                <!-- <div class="card mb-4">
                    <div class="card-header">
                        Riwayat Pembayaran
                    </div>
                    <div class="card-body">
                        <table class="table table-bordered">
                            <thead>
                                <tr>
                                    <th>Tanggal Pembayaran</th>
                                    <th>Jumlah Pembayaran</th>
                                    <th>Status Pembayaran</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>15 Jan 2025</td>
                                    <td>IDR 1.250.000,-</td>
                                    <td><span class="badge bg-success">Lunas</span></td>
                                </tr>
                                <tr>
                                    <td>20 Jan 2025</td>
                                    <td>IDR 1.250.000,-</td>
                                    <td><span class="badge bg-warning">Menunggu Konfirmasi</span></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div> -->
            </div>

            <footer class=" p-2" style="display: flex; justify-content: space-between; flex-wrap: wrap;">
                <div class="ms-5">
                    <ul style="list-style-type: none; display: flex; text-transform: uppercase; font-size: 13px;" class="fw-semibold">
                        <li><a href="/psb" class="me-4" style="text-decoration: none; color: white;">Home</a></li>
                        <li><a href="/beranda" class="me-4" style="text-decoration: none; color: white;" target="_blank">Info Pondok</a></li>
                        <li><a href="https://drive.google.com/drive/folders/1C5U4oDSJlOe1qO7tbw0wZgYenHKEHUVM?usp=sharing" class="me-4" style="text-decoration: none; color: white;" target="_blank">Brosur</a></li>
                        <li><a href="" class="me-4" style="text-decoration: none; color: white;">Panduan</a></li>
                    </ul>
                    </ul>
                </div>
                <div class="me-5">
                    <p class="text-center mt-1">© 2025 TIM IT PPIB</p>
                </div>
            </footer>

            <!-- Modal -->
            <div class="modal fade" id="modalPendaftaranTutup" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                <div class="modal-header">
                    <h1 class="modal-title fs-5" id="exampleModalLabel">Pendaftaran ditutup!</h1>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <p>Mohon maaf, pendaftaran telah ditutup.</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Tutup</button>
                </div>
                </div>
            </div>
            </div>

            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11.14.5/dist/sweetalert2.all.min.js"></script>

            <script>

            const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
            console.log(tooltipTriggerList)
            const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

            document.addEventListener("DOMContentLoaded", function () {{
                // Ambil semua elemen dengan class "log"
                const logoutButtons = document.querySelectorAll('.log');

                // Tambahkan event listener ke setiap tombol
                logoutButtons.forEach(button => {{
                    button.addEventListener('click', function (event) {{
                        event.preventDefault(); // Mencegah tindakan default (navigasi)
                        const logoutUrl = this.getAttribute('href'); // Ambil URL logout

                        // Tampilkan SweetAlert
                        Swal.fire({{
                            title: 'Keluar',
                            text: "Apakah anda ingin keluar?",
                            icon: 'warning',
                            showCancelButton: true,
                            confirmButtonColor: '#3085d6',
                            cancelButtonColor: '#d33',
                            confirmButtonText: 'Logout'
                        }}).then((result) => {{
                            if (result.isConfirmed) {{
                                // Redirect ke URL logout jika dikonfirmasi
                                window.location.href = logoutUrl;
                            }}
                        }});
                    }});
                }});
            }});

            </script>
            </body>
            </html>
        """
        return request.make_response(html_content, headers=[('Content-Type', 'text/html')])



class PesantrenLogin(http.Controller):
    @http.route('/login', type='http', auth='public')
    def index(self, **kwargs):
        # Ambil data dari sesi
        user_id = request.session.get('user_id')
        if user_id:
            return request.redirect('/portal_orang_tua')
        
        return request.render('pesantren_pendaftaran.pendaftaran_login_template')
    
    @http.route('/login/submit', type='http', auth='public', methods=['POST'], csrf=True)
    def login(self, **post):
        phone = post.get('phone') if post.get('phone') else ''
        email = post.get('email') if post.get('email') else ''

        if phone:
            record = request.env['ubig.pendaftaran'].sudo().search([('nomor_login', '=', phone)], limit=1)

        if email:
            record = request.env['ubig.pendaftaran'].sudo().search([('email', '=', email)], limit=1)

        if record:
            password = post.get('password')
            if record.password == password:
                request.session['user_id'] = record.id
                return request.redirect('/portal_orang_tua')
            else:
                return """
                    <html>
                        <head>
                        <!-- Primary Meta Tags --> 
            <title>PSB Daarul Qur`an Istiqomah</title> 
            <meta name="title" content="PSB Daarul Qur`an Istiqomah" /> 
            <meta name="description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
 
            <!-- Open Graph / Facebook --> 
            <meta property="og:type" content="website" /> 
            <meta property="og:url" content="https://aplikasi.dqi.ac.id/pendaftaran" /> 
            <meta property="og:title" content="PSB Daarul Qur`an Istiqomah" /> 
            <meta property="og:description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
            <meta property="og:image" content="https://drive.usercontent.google.com/download?id=1VZRccbFtq82wTNcReEq43piA_GJQddcm" /> 
 
            <!-- Twitter --> 
            <meta property="twitter:card" content="summary_large_image" /> 
            <meta property="twitter:url" content="https://aplikasi.dqi.ac.id/pendaftaran" /> 
            <meta property="twitter:title" content="PSB Daarul Qur`an Istiqomah" /> 
            <meta property="twitter:description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
            <meta property="twitter:image" content="https://drive.usercontent.google.com/download?id=1VZRccbFtq82wTNcReEq43piA_GJQddcm" />
                            <link href="https://cdn.jsdelivr.net/npm/sweetalert2@11.14.5/dist/sweetalert2.min.css" rel="stylesheet"/>
                        </head>
                        <body>
                            <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11.14.5/dist/sweetalert2.all.min.js"></script>
                            <script>
                                Swal.fire({
                                    icon: 'error',
                                    title: 'Gagal',
                                    text: 'Kata sandi salah!',
                                    confirmButtonText: 'OK'
                                }).then((result) => {
                                    if (result.isConfirmed) {
                                        window.location.href = '/login';
                                    }
                                });
                            </script>
                        </body>
                    </html>
                """
        else:
            return """
                    <html>
                        <head>
                        <!-- Primary Meta Tags --> 
            <title>PSB Daarul Qur`an Istiqomah</title> 
            <meta name="title" content="PSB Daarul Qur`an Istiqomah" /> 
            <meta name="description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
 
            <!-- Open Graph / Facebook --> 
            <meta property="og:type" content="website" /> 
            <meta property="og:url" content="https://aplikasi.dqi.ac.id/pendaftaran" /> 
            <meta property="og:title" content="PSB Daarul Qur`an Istiqomah" /> 
            <meta property="og:description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
            <meta property="og:image" content="https://drive.usercontent.google.com/download?id=1VZRccbFtq82wTNcReEq43piA_GJQddcm" /> 
 
            <!-- Twitter --> 
            <meta property="twitter:card" content="summary_large_image" /> 
            <meta property="twitter:url" content="https://aplikasi.dqi.ac.id/pendaftaran" /> 
            <meta property="twitter:title" content="PSB Daarul Qur`an Istiqomah" /> 
            <meta property="twitter:description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
            <meta property="twitter:image" content="https://drive.usercontent.google.com/download?id=1VZRccbFtq82wTNcReEq43piA_GJQddcm" />
                            <link href="https://cdn.jsdelivr.net/npm/sweetalert2@11.14.5/dist/sweetalert2.min.css" rel="stylesheet"/>
                        </head>
                        <body>
                            <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11.14.5/dist/sweetalert2.all.min.js"></script>
                            <script>
                                Swal.fire({
                                    icon: 'error',
                                    title: 'Gagal',
                                    text: 'No Telp/Wa atau Email belum terdaftar!',
                                    confirmButtonText: 'OK'
                                }).then((result) => {
                                    if (result.isConfirmed) {
                                        window.location.href = '/login';
                                    }
                                });
                            </script>
                        </body>
                    </html>
                """

    @http.route('/logout', type='http', auth='public')
    def logout(self, **kwargs):
        request.session.logout()  # Menghapus semua data dalam sesi
        return request.redirect('/login')


class UploadBuktiPembayaran(http.Controller):
    @http.route('/upload_bukti_pembayaran', type='http', auth='public', methods=['POST'], csrf=True)
    def upload_bukti_pembayaran(self, **post):
        record_id = post.get('record_id')
        # Ambil file dari request
        uploaded_files = request.httprequest.files

        bukti_pembayaran = uploaded_files.get('bukti_pembayaran')

        # Fungsi bantu untuk memproses file
        def process_file(file):
            if file:
                # Baca file dan konversi ke Base64
                file_content = file.read()
                file_base64 = base64.b64encode(file_content)
                return file_base64
            return None
        
        bukti_pembayaran_b64 = process_file(bukti_pembayaran)

        if record_id and bukti_pembayaran_b64:
            # Cari record berdasarkan ID
            record = request.env['ubig.pendaftaran'].sudo().browse(int(record_id))
            if record:
                # Update field dengan file yang diunggah
                record.sudo().write({
                    'bukti_pembayaran': bukti_pembayaran_b64,
                })
                return """
                    <html>
                        <head>
                        <!-- Primary Meta Tags --> 
            <title>PSB Daarul Qur`an Istiqomah</title> 
            <meta name="title" content="PSB Daarul Qur`an Istiqomah" /> 
            <meta name="description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
 
            <!-- Open Graph / Facebook --> 
            <meta property="og:type" content="website" /> 
            <meta property="og:url" content="https://aplikasi.dqi.ac.id/pendaftaran" /> 
            <meta property="og:title" content="PSB Daarul Qur`an Istiqomah" /> 
            <meta property="og:description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
            <meta property="og:image" content="https://drive.usercontent.google.com/download?id=1VZRccbFtq82wTNcReEq43piA_GJQddcm" /> 
 
            <!-- Twitter --> 
            <meta property="twitter:card" content="summary_large_image" /> 
            <meta property="twitter:url" content="https://aplikasi.dqi.ac.id/pendaftaran" /> 
            <meta property="twitter:title" content="PSB Daarul Qur`an Istiqomah" /> 
            <meta property="twitter:description" content="Pendaftaran Santri Baru PP Daarul Qur`an Istiqomah Tahun pelajaran 2025-2026 Telah dibuka. segera daftarkan anak anda sekarang" /> 
            <meta property="twitter:image" content="https://drive.usercontent.google.com/download?id=1VZRccbFtq82wTNcReEq43piA_GJQddcm" />
                            <link href="https://cdn.jsdelivr.net/npm/sweetalert2@11.14.5/dist/sweetalert2.min.css" rel="stylesheet"/>
                        </head>
                        <body>
                            <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11.14.5/dist/sweetalert2.all.min.js"></script>
                            <script>
                                Swal.fire({
                                    icon: 'success',
                                    title: 'Berhasil',
                                    text: 'Berhasil mengunggah bukti pembayaran.',
                                    confirmButtonText: 'OK'
                                }).then((result) => {
                                    if (result.isConfirmed) {
                                        window.location.href = '/portal_orang_tua';
                                    }
                                });
                            </script>
                        </body>
                    </html>
                """

class RincianBiayaController(http.Controller):
    @http.route('/download/biaya/<int:biaya_id>', type='http', auth='public')
    def download_biaya(self, biaya_id, **kwargs):

        def convert_binary_to_pdf(binary_data, file_name="converted_file.pdf"):
            # Mengonversi data biner kembali ke format PDF
            pdf_data = base64.b64decode(binary_data)
            
            # Gunakan tempfile untuk membuat file sementara
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(pdf_data)
                return temp_file.name  # Mengembalikan path ke file sementara
        # Ambil data biaya berdasarkan ID
        biaya = request.env['ubig.rincian_biaya'].sudo().browse(biaya_id)
        
        if biaya.gambar:
            binary_data = biaya.gambar
            file_path = convert_binary_to_pdf(binary_data)
            # Pastikan file ada sebelum melanjutkan
            if os.path.exists(file_path):
                with open(file_path, 'rb') as file:
                    dt = file.read()

            nama_file_download = f"RincianBiaya{biaya.name}.pdf"

            # Kirimkan file ke pengguna sebagai download
            return request.make_response(dt, headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'attachment; filename={nama_file_download}'),
            ])
        else:
            return "No PDF found"


