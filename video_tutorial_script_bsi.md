# Skrip Tutorial: BSI Smart Billing & Manajemen Saldo Santri

## **Metode: Live Screen Recording (OBS)**

Skrip ini dirancang untuk Anda yang akan merekam layar secara langsung. Bagian **Tindakan** adalah panduan apa yang harus Anda lakukan di layar, dan **Narasi** adalah apa yang harus Anda ucapkan.

---

## 🎬 Bagian 1: Pembukaan & Overview

**Tindakan:** Tampilkan halaman Dashboard utama Odoo. Gerakkan kursor perlahan.
**Narasi:**
"Halo semuanya, Assalamu’alaikum Warahmatullahi Wabarakatuh. Pada kesempatan kali ini, saya akan mendemonstrasikan bagaimana sistem manajemen keuangan Pesantren kita terintegrasi dengan **BSI Smart Billing**.

Sistem ini dirancang untuk memudahkan orang tua melakukan pembayaran secara otomatis dan membantu pihak Pesantren mengelola uang saku santri secara digital tanpa perlu uang tunai (cashless)."

---

## 🆔 Bagian 2: Pengaturan Virtual Account (VA) Santri

**Tindakan:** Buka menu **Pesantren** > **Siswa** > Pilih salah satu siswa (misal: Ahmad).
**Narasi:**
"Langkah pertama adalah memastikan setiap santri memiliki nomor Virtual Account. Di halaman data siswa ini, Anda bisa melihat field **VA Saku**.

Jika santri belum memiliki VA, cukup klik tombol **Buat VA Permanen** di bagian atas. Sistem akan menghubungi server BSI dan men-generate nomor unik berdasarkan NIS santri tersebut secara instan. VA ini bersifat permanen, artinya orang tua bisa menyimpan nomor ini untuk top-up kapan saja."

**Tindakan:** Klik tombol **Kirim WA** (atau arahkan kursor ke sana).
**Narasi:**
"Agar orang tua tahu nomor VA anaknya, Anda bisa langsung klik tombol **Kirim WA**. Sistem akan membuka WhatsApp dengan pesan otomatis yang berisi: Nomor VA, Nama Bank (BSI), dan instruksi cara transfernya. Sangat praktis, tidak perlu copy-paste manual."

---

## 🛒 Bagian 3: Transaksi di Kantin/Toko (POS) & Limit Harian

**Tindakan:** Pindah ke menu **Point of Sale** > Buka Session Baru > Pilih Produk > Klik Customer.
**Narasi:**
"Sekarang, mari kita lihat bagaimana santri berbelanja. Di kasir kantin atau toko, kasir tinggal memilih produk yang dibeli. Kemudian, pada bagian pelanggan, kasir memilih nama santri atau men-scan kartu santrinya.

Saat masuk ke layar pembayaran, perhatikan ada metode **Wallet** atau **Saldo Saku**. Jika kita pilih ini, sistem akan mengecek apakah saldo santri cukup. Selain itu, sistem juga akan memvalidasi **Limit Harian** yang telah diatur oleh orang tua atau pihak sekolah. Jika santri sudah belanja melebihi batas hariannya, transaksi akan ditolak secara otomatis oleh sistem. Ini sangat penting untuk mendidik santri dalam mengelola pengeluaran mereka secara bijak."

---

## 📊 Bagian 4: Monitoring Saldo & Riwayat Transaksi

**Tindakan:** Kembali ke Form Siswa > Cari Smart Button 'Transaksi Smart Billing' atau 'Wallet'.
**Narasi:**
"Semua riwayat transaksi santri, baik itu top-up dari orang tua maupun belanjaan di kantin, tercatat dengan sangat rapi. Kita bisa melihat mutasi saldonya secara real-time. Jika orang tua bertanya, 'Dipakai apa saja uang sakunya?', Anda bisa memberikan laporan detil item apa saja yang dibeli di kantin lengkap dengan tanggal dan jamnya. Transparansi seperti ini sangat meningkatkan kepercayaan orang tua kepada Pesantren."

---

## 📑 Bagian 5: Manajemen Tagihan & Pembayaran Otomatis

**Tindakan:** Buka menu **Invoicing** > Pilih salah satu tagihan (Status 'Posted').
**Narasi:**
"Lalu bagaimana dengan tagihan bulanan seperti SPP? Di menu Invoicing ini, bagian keuangan tinggal memilih invoice yang dimaksud, lalu klik **Kirim Billing BSI**.

Setelah diklik, invoice ini akan memiliki nomor Virtual Account sendiri. Orang tua tinggal transfer sesuai nominal tagihan tersebut. Begitu pembayaran diterima oleh bank, BSI akan mengirimkan notifikasi ke Odoo kita, dan invoice ini akan otomatis berubah statusnya menjadi **Paid** atau **Lunas** tanpa perlu dicek satu-satu di mutasi bank."

---

## 💡 Bagian 6: Fitur Unggulan - Auto-Payment

**Tindakan:** Tampilkan kembali halaman Siswa yang memiliki saldo dan tagihan.
**Narasi:**
"Salah satu fitur tercanggih kita adalah **Auto-Payment**. Misalkan santri memiliki tunggakan SPP. Saat orang tua melakukan top-up ke VA Saku untuk uang jajan, sistem secara otomatis akan mendeteksi tunggakan tersebut.

Jika saldo top-up mencukupi, sistem akan langsung mengalokasikannya untuk melunasi tagihan yang paling lama. Jadi, administrasi pesantren tetap terjaga, dan piutang bisa tertangani secara sistematis."

---

## ✨ Bagian 7: Penutup & Tips

**Tindakan:** Kembali ke Dashboard utama atau tunjukkan menu Laporan Keuangan.
**Narasi:**
"Dengan integrasi BSI Smart Billing ini, pelaporan keuangan menjadi sangat transparan. Kita bisa melihat laporan saldo santri secara keseluruhan atau per kelas kapan saja.

Demikian tutorial singkat ini. Semoga dengan sistem ini, pelayanan keuangan di Pesantren kita menjadi lebih profesional dan barokah. Terima kasih, Wassalamu’alaikum Warahmatullahi Wabarakatuh."

---

### Tips OBS Recording

1. **Resolusi**: Pastikan resolusi layar 1920x1080 agar teks di Odoo terbaca jelas.
2. **Kursor**: Gunakan 'Mouse Highlighter' (lingkaran kuning di kursor) lewat aplikasi pihak ketiga agar penonton tahu Anda sedang menunjuk ke mana.
3. **Persiapan Data**: Siapkan data siswa contoh yang sudah memiliki saldo dan tagihan agar Anda tidak perlu input-input lagi saat merekam.
4. **Pause Recording**: Jika Odoo loading agak lama, gunakan fitur **Pause** di OBS agar video tetap terasa cepat dan padat.
