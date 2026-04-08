# Aplikasi Manajemen Pesantren (DQI Edition)

Aplikasi **Manajemen Pesantren** dirancang untuk memenuhi kebutuhan administrasi pesantren modern secara menyeluruh. Dengan fokus pada efisiensi, transparansi, dan integrasi antar unit (Akademik, Kesantrian, Keuangan, dan Orang Tua).

## 🚀 Fitur Utama

### 1. **Smart Billing & Payment Integration (BSI SNAP BI)**

Integrasi sistem keuangan dengan perbankan menggunakan standar **SNAP BI v3.2**.

- **Virtual Account (VA)**: Generate VA otomatis untuk tagihan santri.
- **Permanent VA**: Mendukung top-up saldo uang saku bebas nominal.
- **BSI Smart Billing Compliance**: Mendukung flow `AUTH`, `INQUIRY`, `PAYMENT`, `ADVICE`, dan `WSR`.
- **Auto-Reconcile**: Otomatis menandai invoice lunas saat pembayaran diterima dari bank.
- **Real-time Notifications**: Notifikasi instan ke Dashboard Odoo dan Portal Orang Tua.

### 2. **Modul Kesantrian & Musyrif**

- Pencatatan data santri, asrama, dan perizinan.
- Monitoring perkembangan hafalan Al-Qur'an (Tahfidz) secara mendetail.
- Laporan mingguan aktivitas santri oleh Musyrif.

### 3. **Modul Akademik & Guru**

- Manajemen kurikulum, jadwal pelajaran, dan absensi guru/siswa.
- Pengelolaan rekap nilai dan raport digital.

### 4. **Portal Orang Tua**

- Akses informasi tagihan, rincian VA, dan riwayat transaksi.
- Monitoring perkembangan pendidikan dan kedisiplinan anak secara real-time.

---

## 🛠️ Smart Billing Developer Tools

Untuk pengembangan dan testing integrasi perbankan, disediakan alat pendukung:

### **BPI Mockup API Server**

Berlokasi di folder `bpi_mockup`, server ini mensimulasikan core banking BSI untuk mendukung flow SNAP BI.

- **Standalone Mode**: Berjalan dengan Node.js dan LowDB.
- **Simulation Mode**: Mendukung flag `simulation: true` untuk testing Inquiry/Payment berulang tanpa mengubah state database.

**Cara Menjalankan Mockup:**

```bash
cd bpi_mockup
npm install
node server.js
```

*Akses Dashboard Simulator di `http://localhost:8001/dashboard`*

### **API Compliance Verification**

Gunakan script verifikasi untuk memastikan endpoint Odoo dan Mockup sudah sesuai dengan standar SNAP BI v3.2.

```bash
node bpi_mockup/verify_compliance.js
```

---

## 💻 Teknologi yang Digunakan

- **Core ERP:** [Odoo 18 (Community/Enterprise)](https://www.odoo.com)
- **Programming:** Python 3.13, JavaScript (OWL & ES6+)
- **Standards:** SNAP BI (Bank Syariah Indonesia v3.2)
- **Database:** PostgreSQL
- **Mockup Backend:** Express.js & LowDB (Node.js)

---

## ⚙️ Panduan Instalasi & Konfigurasi

### 1. Persiapan Addons

Pastikan semua filter path addons diarahkan ke repo ini:

```bash
git clone git@github.com:rasyaakbar-dev/pesantren-dqi.git
```

### 2. Konfigurasi Smart Billing

Buka **Settings > Accounting > Smart Billing** di Odoo:

- **Provider**: Pilih `BSI (Bank Syariah Indonesia)`.
- **Mockup URL**: `http://localhost:8001` (Jika menggunakan simulator local).
- **Credentials**: Masukkan Client ID, Secret, dan Partner ID yang sesuai dengan `bpi_mockup/config.json`.

### 3. Test Connection

Gunakan **Test API Wizard** di menu **Settings > Smart Billing > Test API** untuk memverifikasi koneksi Anda terhadap Mockup, Sandbox, atau Production.

---

## 📄 Lisensi & Kontribusi

Modul ini dikembangkan khusus untuk ekosistem Pesantren DQI. Lisensi mengikuti standar LGPL-3.
