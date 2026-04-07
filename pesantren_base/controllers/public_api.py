# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class Karts(http.Controller):
    @http.route('/cetak_kts', type='http', auth='public')
    def cetak_kts(self, **kwargs):
        record_ids = request.httprequest.args.getlist('id')

        if not record_ids:
            return request.not_found()

        records = request.env['cdn.siswa'].sudo().search(
            [('id', 'in', record_ids)])

        if not records:
            return request.not_found()

        html_head = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Kartu Santri</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
                
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                    font-family: 'Inter', sans-serif;
                }
                
                html, body {
                    background-color: #eaf2f7;
                    width: 100%;
                    height: 100%;
                    margin: 0;
                    padding: 0;
                }
                
                .card-number {
                    font-family: 'Inter', monospace;
                    font-size: 16px;
                    letter-spacing: 1px;
                    font-weight: 600;
                    padding: 8px 0px;
                    display: inline-block;
                    width: fit-content;
                }
                
                .limited-lines {
                    width: 270px;
                    word-wrap: break-word;
                    display: -webkit-box;
                    -webkit-line-clamp: 3;
                    -webkit-box-orient: vertical;
                    overflow: hidden;
                }
                
                .page {
                    width: 100%;
                    height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    page-break-after: always;
                }
                
                /* Remove page break for the last page */
                .page:last-child {
                    page-break-after: avoid;
                }
                
                .card-wrapper {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 10px;
                }
                
                .card {
                    width: 450px;
                    height: 260px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    position: relative;
                    overflow: hidden;
                }
                
                .front {
                    background: linear-gradient(to top right, #339966 0%, #00cc66 100%);
                    color: white;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    padding: 15px;
                }
                
                .front .title {
                    font-size: 1.5rem;
                    font-weight: 700;
                    line-height: 1.2;
                }
                
                .front .subtitle {
                    font-size: 1.2rem;
                    font-weight: 400;
                    margin-top: 3px;
                    line-height: 1.2;
                }
                
                .front .barcode-text {
                    font-size: 12px;
                    line-height: 1.4;
                    width: 300px;
                }
                
                .front .barcode img {
                    width: 15rem;
                    height: 5rem;
                    background-color: #eaf2f7;
                    border-radius: 5px;
                }
                
                .back {
                    background: linear-gradient(to top right, #339966 0%, #00cc66 100%);
                    color: white;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    padding: 15px;
                }
                
                .back .card-header {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                
                .back .card-header .text-container {
                    line-height: 1.3;
                }
                
                .back .card-header .title {
                    font-size: 18px;
                    font-weight: 700;
                }
                
                .back .card-header .subtitle {
                    font-size: 14px;
                    font-weight: 400;
                }
                
                .back .card-info {
                    margin-top: 5px;
                }
                
                .back .card-info p {
                    margin-bottom: 3px;
                    line-height: 1.4;
                }
                
                .back .info {
                    font-size: 13px;
                    font-weight: 400;
                }
                
                .back .qr-code img {
                    margin-top: 15px;
                    height: 140px;
                    width: 120px;
                    background-color: #eaf2f7;
                    border-radius: 10px;
                    z-index: 10;
                    position: relative;
                }
                
                .back .qr-code p {
                    font-weight: 600;
                    text-align: center;
                    margin-top: 5px;
                    font-size: 13px;
                }
                
                .right-s {
                    position: absolute;
                    rotate: -40deg;
                    right: 0px;
                    bottom: 5rem;
                    display: flex;
                    z-index: 4;
                }
                
                .sprite {
                    position: relative;
                    background-color: #ffb901;
                    height: 400px;
                    width: 20px;
                }
                
                .site {
                    position: relative;
                    background-color: #0000cc;
                    z-index: 3;
                    height: 400px;
                    width: 120px;
                }
                
                .icon-card {
                    position: absolute;
                    z-index: 100;
                    right: 1rem;
                    top: 10px;
                    width: 2.5rem;
                    height: 2.5rem;
                }
                
                .qr-code {
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-content: center;
                    position: static;
                    width: min-content;
                }
                
                .banner {
                    border-radius: 50%;
                    position: absolute;
                    background-image: url('https://i.ibb.co.com/wRNC9B0/img1.jpg');
                    width: 12rem;
                    height: 12rem;
                    background-position: center;
                    background-repeat: no-repeat;
                    background-size: auto;
                    right: -4.7rem;
                    top: 13.5%;
                    box-shadow: #000000ad 3px 4px 30px;
                }
                
                @media print {
                    @page {
                        size: A4;
                        margin: 0;
                    }
                    
                    html, body {
                        width: 100%;
                        height: 100%;
                        margin: 0;
                        padding: 0;
                        background-color: white;
                    }
                    
                    .page {
                        width: 100%;
                        height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        page-break-after: always;
                    }
                    
                    .page:last-child {
                        page-break-after: avoid;
                    }
                }
            </style>
        </head>
        <body>
        """

        # Generate HTML for each student card, each in its own page
        cards_html = ""
        barcode_scripts = ""

        for i, record in enumerate(records):
            # Create unique canvas ID for each barcode
            canvas_id = f"canvasbarcode_{record.id}"

            # HTML for a student's card (front and back) in a single page
            cards_html += f"""
            <div class="page">
                <div class="card-wrapper">
                    <!-- Kartu Santri Depan -->
                    <div class="card front">
                        <div class="card-header">
                            <div>
                                <h1 class="title">Kartu Santri</h1>
                                <h3 class="subtitle">Daarul Qu`ran Istiqomah</h3>
                            </div>
                        </div>
                        <div class="barcode">
                            <canvas id="{canvas_id}" style="border-radius: 5px; margin-bottom: 8px;" class="rounded-2"></canvas>
                            <p class="barcode-text">Jl. Ambawang, RT.03/RW.01, Karang Taruna, Kec. Pelaihari, Kab. Tanah Laut, Kalsel</p>
                        </div>
                        <div class="banner"></div>
                    </div>

                    <!-- Kartu Santri Belakang -->
                    <div class="card back">
                        <div class="card-header">
                            <img src="https://i.ibb.co.com/19Q6yyx/credit-card.png" class="icon-card" alt="">
                            <img src="https://i.ibb.co.com/SmWmBTW/SAVE-20220114-075750-removebg-preview-4.png" width="45px" height="45px" alt="img">
                            <div class="text-container">
                                <div class="title">Kartu Santri</div>
                                <div class="subtitle">Daarul Qu`ran Istiqomah</div>
                            </div>
                            <div class="right-s">
                                <div class="sprite"></div>
                                <div class="site"></div>
                            </div>
                        </div>
                        <div style="display: flex; align-items: end; justify-content: space-between;">
                            <div class="card-info">
                                <p class="card-number">Nama : {record.partner_id.name}</p>
                                <p class="info">NISN : {record.nisn}</p>
                                <p class="info">Tgl Lahir : {record.tgl_lahir}</p>
                                <p class="info limited-lines">Alamat : {record.street or ''}</p>
                            </div>
                            <div class="qr-code">
                                <img src="/web/image?model=cdn.siswa&id={record.id}&field=image_1920" alt="QR Code" style="object-fit: cover;">
                                <p>
                                    {record.kamar_id.kamar_id.name if record.kamar_id and record.kamar_id.kamar_id else ''}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """

            # Add barcode initialization script for this student
            barcode_scripts += f"""
            JsBarcode("#{canvas_id}", "{record.barcode}", {{
                format: "CODE128",
                width: 2,
                height: 60,
                displayValue: true
            }});
            """

        # Complete HTML document
        html_footer = f"""
            <script src="https://cdn.jsdelivr.net/npm/jsbarcode@3.11.0/dist/JsBarcode.all.min.js"></script>
            <script>
                document.addEventListener('DOMContentLoaded', function() {{
                    // Initialize all barcodes
                    {barcode_scripts}
                    
                    // Wait a moment to ensure everything is rendered before printing
                    setTimeout(function() {{
                        window.print();
                    }}, 800);
                }});
            </script>
        </body>
        </html>
        """

        # Combine all parts
        complete_html = html_head + cards_html + html_footer

        return request.make_response(complete_html)
