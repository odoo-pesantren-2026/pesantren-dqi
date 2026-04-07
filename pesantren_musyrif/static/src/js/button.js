/** @odoo-module */

import { Component, useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class CustomSaldoSantriWizard extends Component {
  static template = "custom_saldo_santri_wizard.template";

  setup() {
    this.orm = useService("orm");
    this.notification = useService("notification");
    this.dialog = useService("dialog");

    this.state = useState({
      currentStep: 1,
      totalSteps: 3,
      isLoading: false,
      santriData: {
        nama: "",
        nis: "",
        kelas: "",
        asrama: "",
        saldoAwal: 0,
        jenisTransaksi: "",
        jumlahTransaksi: 0,
        keterangan: "",
        saldoAkhir: 0,
      },
      // Data dummy untuk demo
      dummyData: {
        nama: "Ahmad Fauzi",
        nis: "2024001",
        kelas: "3A",
        asrama: "Al-Ikhlas",
        saldoAwal: 250000,
        kelasOptions: [
          { value: "1A", label: "Kelas 1A" },
          { value: "1B", label: "Kelas 1B" },
          { value: "2A", label: "Kelas 2A" },
          { value: "2B", label: "Kelas 2B" },
          { value: "3A", label: "Kelas 3A" },
          { value: "3B", label: "Kelas 3B" },
        ],
        asramaOptions: [
          { value: "Al-Ikhlas", label: "Al-Ikhlas" },
          { value: "Al-Husna", label: "Al-Husna" },
          { value: "Ar-Rahman", label: "Ar-Rahman" },
          { value: "As-Syifa", label: "As-Syifa" },
        ],
        jenisTransaksiOptions: [
          { value: "deposit", label: "Deposit (Tambah Saldo)" },
          { value: "withdraw", label: "Penarikan (Kurangi Saldo)" },
          { value: "transfer", label: "Transfer Antar Santri" },
        ],
      },
    });

    onMounted(() => {
      this.loadDummyData();
    });
  }

  loadDummyData() {
    // Load data dummy
    this.state.santriData.nama = this.state.dummyData.nama;
    this.state.santriData.nis = this.state.dummyData.nis;
    this.state.santriData.kelas = this.state.dummyData.kelas;
    this.state.santriData.asrama = this.state.dummyData.asrama;
    this.state.santriData.saldoAwal = this.state.dummyData.saldoAwal;
  }

  nextStep() {
    if (this.validateCurrentStep()) {
      if (this.state.currentStep < this.state.totalSteps) {
        this.state.currentStep++;
        if (this.state.currentStep === 3) {
          this.updateSummary();
        }
      } else {
        this.finishWizard();
      }
    }
  }

  previousStep() {
    if (this.state.currentStep > 1) {
      this.state.currentStep--;
    }
  }

  validateCurrentStep() {
    const data = this.state.santriData;

    if (this.state.currentStep === 1) {
      if (!data.nama) {
        this.notification.add(_t("Nama santri harus diisi!"), {
          type: "warning",
        });
        return false;
      }
      if (!data.nis) {
        this.notification.add(_t("NIS harus diisi!"), { type: "warning" });
        return false;
      }
      if (!data.kelas) {
        this.notification.add(_t("Kelas harus dipilih!"), { type: "warning" });
        return false;
      }
      if (!data.asrama) {
        this.notification.add(_t("Asrama harus dipilih!"), { type: "warning" });
        return false;
      }
    } else if (this.state.currentStep === 2) {
      if (!data.jenisTransaksi) {
        this.notification.add(_t("Jenis transaksi harus dipilih!"), {
          type: "warning",
        });
        return false;
      }
      if (!data.jumlahTransaksi || data.jumlahTransaksi <= 0) {
        this.notification.add(
          _t("Jumlah transaksi harus diisi dan lebih dari 0!"),
          { type: "warning" }
        );
        return false;
      }
    }

    return true;
  }

  updateSummary() {
    const data = this.state.santriData;
    let saldoAkhir = data.saldoAwal;

    if (data.jenisTransaksi === "deposit") {
      saldoAkhir += data.jumlahTransaksi;
    } else if (data.jenisTransaksi === "withdraw") {
      saldoAkhir -= data.jumlahTransaksi;
    }

    this.state.santriData.saldoAkhir = saldoAkhir;
  }

  async finishWizard() {
    this.state.isLoading = true;

    try {
      // Simulasi save data (ganti dengan actual API call)
      await new Promise((resolve) => setTimeout(resolve, 1000));

      this.notification.add(_t("Data berhasil disimpan!"), {
        type: "success",
        title: _t("Sukses"),
      });

      this.closeWizard();
    } catch (error) {
      this.notification.add(_t("Terjadi kesalahan saat menyimpan data!"), {
        type: "danger",
        title: _t("Error"),
      });
    } finally {
      this.state.isLoading = false;
    }
  }

  closeWizard() {
    this.props.close();
  }

  formatRupiah(amount) {
    return new Intl.NumberFormat("id-ID", {
      style: "currency",
      currency: "IDR",
      minimumFractionDigits: 0,
    }).format(amount);
  }

  getJenisTransaksiLabel(value) {
    const option = this.state.dummyData.jenisTransaksiOptions.find(
      (opt) => opt.value === value
    );
    return option ? option.label : "-";
  }

  getProgressPercentage() {
    return (this.state.currentStep / this.state.totalSteps) * 100;
  }

  onInputChange(field, event) {
    const value =
      event.target.type === "number"
        ? parseFloat(event.target.value) || 0
        : event.target.value;
    this.state.santriData[field] = value;
  }
}

CustomSaldoSantriWizard.template = `
<div class="modal-dialog modal-lg" style="max-width: 600px;">
    <div class="modal-content" style="border-radius: 20px; overflow: hidden; box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);">
        <!-- Header -->
        <div class="modal-header" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 25px 30px; border: none;">
            <h4 class="modal-title" style="font-size: 24px; font-weight: 600; margin: 0;">
                🏦 Wizard Saldo Santri
            </h4>
            <button type="button" class="btn-close btn-close-white" t-on-click="closeWizard" style="filter: brightness(0) invert(1);"></button>
        </div>
        
        <!-- Progress Bar -->
        <div class="progress" style="height: 6px; background: #e2e8f0; border-radius: 0;">
            <div class="progress-bar" role="progressbar" 
                t-att-style="'width: ' + getProgressPercentage() + '%; background: linear-gradient(90deg, #28a745, #20c997); transition: width 0.5s ease;'"></div>
        </div>
        
        <!-- Step Indicators -->
        <div class="d-flex justify-content-center py-3" style="background: #f8fafc;">
            <t t-foreach="[1, 2, 3]" t-as="step" t-key="step">
                <div class="rounded-circle mx-2" 
                     t-att-class="step &lt; state.currentStep ? 'bg-success' : (step === state.currentStep ? 'bg-primary' : 'bg-light')"
                     style="width: 12px; height: 12px; transition: all 0.3s ease;"></div>
            </t>
        </div>
        
        <!-- Content -->
        <div class="modal-body" style="padding: 30px; min-height: 400px;">
            <!-- Step 1: Data Santri -->
            <div t-if="state.currentStep === 1" class="wizard-step">
                <h5 style="color: #28a745; margin-bottom: 20px;">📋 Data Santri</h5>
                <div class="mb-3">
                    <label class="form-label fw-bold">Nama Lengkap Santri</label>
                    <input type="text" class="form-control" 
                           t-att-value="state.santriData.nama"
                           t-on-input="(ev) => onInputChange('nama', ev)"
                           placeholder="Masukkan nama lengkap santri"
                           style="border-radius: 10px; padding: 12px 16px; border: 2px solid #e2e8f0; background: #f8fafc;"/>
                </div>
                
                <div class="mb-3">
                    <label class="form-label fw-bold">NIS (Nomor Induk Santri)</label>
                    <input type="text" class="form-control"
                           t-att-value="state.santriData.nis"
                           t-on-input="(ev) => onInputChange('nis', ev)"
                           placeholder="Contoh: 2024001"
                           style="border-radius: 10px; padding: 12px 16px; border: 2px solid #e2e8f0; background: #f8fafc;"/>
                </div>
                
                <div class="mb-3">
                    <label class="form-label fw-bold">Kelas</label>
                    <select class="form-select"
                            t-att-value="state.santriData.kelas"
                            t-on-change="(ev) => onInputChange('kelas', ev)"
                            style="border-radius: 10px; padding: 12px 16px; border: 2px solid #e2e8f0; background: #f8fafc;">
                        <option value="">Pilih Kelas</option>
                        <t t-foreach="state.dummyData.kelasOptions" t-as="option" t-key="option.value">
                            <option t-att-value="option.value" t-esc="option.label"></option>
                        </t>
                    </select>
                </div>
                
                <div class="mb-3">
                    <label class="form-label fw-bold">Asrama</label>
                    <select class="form-select"
                            t-att-value="state.santriData.asrama"
                            t-on-change="(ev) => onInputChange('asrama', ev)"
                            style="border-radius: 10px; padding: 12px 16px; border: 2px solid #e2e8f0; background: #f8fafc;">
                        <option value="">Pilih Asrama</option>
                        <t t-foreach="state.dummyData.asramaOptions" t-as="option" t-key="option.value">
                            <option t-att-value="option.value" t-esc="option.label"></option>
                        </t>
                    </select>
                </div>
            </div>
            
            <!-- Step 2: Saldo & Transaksi -->
            <div t-if="state.currentStep === 2" class="wizard-step">
                <h5 style="color: #28a745; margin-bottom: 20px;">💰 Informasi Saldo</h5>
                
                <div class="mb-3">
                    <label class="form-label fw-bold">Saldo Awal</label>
                    <input type="number" class="form-control"
                           t-att-value="state.santriData.saldoAwal"
                           t-on-input="(ev) => onInputChange('saldoAwal', ev)"
                           placeholder="0"
                           style="border-radius: 10px; padding: 12px 16px; border: 2px solid #e2e8f0; background: #f8fafc;"/>
                </div>
                
                <div class="mb-3">
                    <label class="form-label fw-bold">Jenis Transaksi</label>
                    <select class="form-select"
                            t-att-value="state.santriData.jenisTransaksi"
                            t-on-change="(ev) => onInputChange('jenisTransaksi', ev)"
                            style="border-radius: 10px; padding: 12px 16px; border: 2px solid #e2e8f0; background: #f8fafc;">
                        <option value="">Pilih Jenis Transaksi</option>
                        <t t-foreach="state.dummyData.jenisTransaksiOptions" t-as="option" t-key="option.value">
                            <option t-att-value="option.value" t-esc="option.label"></option>
                        </t>
                    </select>
                </div>
                
                <div class="mb-3">
                    <label class="form-label fw-bold">Jumlah Transaksi</label>
                    <input type="number" class="form-control"
                           t-att-value="state.santriData.jumlahTransaksi"
                           t-on-input="(ev) => onInputChange('jumlahTransaksi', ev)"
                           placeholder="0"
                           style="border-radius: 10px; padding: 12px 16px; border: 2px solid #e2e8f0; background: #f8fafc;"/>
                </div>
                
                <div class="mb-3">
                    <label class="form-label fw-bold">Keterangan</label>
                    <textarea class="form-control" rows="3"
                              t-att-value="state.santriData.keterangan"
                              t-on-input="(ev) => onInputChange('keterangan', ev)"
                              placeholder="Masukkan keterangan transaksi..."
                              style="border-radius: 10px; padding: 12px 16px; border: 2px solid #e2e8f0; background: #f8fafc;"></textarea>
                </div>
            </div>
            
            <!-- Step 3: Konfirmasi -->
            <div t-if="state.currentStep === 3" class="wizard-step">
                <h5 style="color: #28a745; margin-bottom: 20px;">✅ Konfirmasi Data</h5>
                
                <div class="card" style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 15px; border-left: 5px solid #28a745;">
                    <div class="card-body">
                        <h6 class="text-success mb-3">Ringkasan Data Santri</h6>
                        
                        <div class="row mb-2">
                            <div class="col-5 fw-bold">Nama Santri:</div>
                            <div class="col-7" t-esc="state.santriData.nama || '-'"></div>
                        </div>
                        
                        <div class="row mb-2">
                            <div class="col-5 fw-bold">NIS:</div>
                            <div class="col-7" t-esc="state.santriData.nis || '-'"></div>
                        </div>
                        
                        <div class="row mb-2">
                            <div class="col-5 fw-bold">Kelas:</div>
                            <div class="col-7" t-esc="state.santriData.kelas || '-'"></div>
                        </div>
                        
                        <div class="row mb-2">
                            <div class="col-5 fw-bold">Asrama:</div>
                            <div class="col-7" t-esc="state.santriData.asrama || '-'"></div>
                        </div>
                        
                        <div class="row mb-2">
                            <div class="col-5 fw-bold">Saldo Awal:</div>
                            <div class="col-7" t-esc="formatRupiah(state.santriData.saldoAwal)"></div>
                        </div>
                        
                        <div class="row mb-2">
                            <div class="col-5 fw-bold">Jenis Transaksi:</div>
                            <div class="col-7" t-esc="getJenisTransaksiLabel(state.santriData.jenisTransaksi)"></div>
                        </div>
                        
                        <div class="row mb-2">
                            <div class="col-5 fw-bold">Jumlah:</div>
                            <div class="col-7" t-esc="formatRupiah(state.santriData.jumlahTransaksi)"></div>
                        </div>
                        
                        <hr/>
                        
                        <div class="row">
                            <div class="col-5 fw-bold text-success">Saldo Akhir:</div>
                            <div class="col-7 fw-bold text-success" t-esc="formatRupiah(state.santriData.saldoAkhir)"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="modal-footer" style="padding: 25px 30px; background: #f8fafc; border: none;">
            <button type="button" class="btn btn-secondary" 
                    t-if="state.currentStep > 1"
                    t-on-click="previousStep"
                    style="border-radius: 10px; padding: 12px 24px;">
                ← Sebelumnya
            </button>
            
            <div class="flex-fill"></div>
            
            <button type="button" 
                    t-att-class="state.currentStep === state.totalSteps ? 'btn btn-success' : 'btn btn-primary'"
                    t-on-click="nextStep"
                    t-att-disabled="state.isLoading"
                    style="border-radius: 10px; padding: 12px 24px; background: linear-gradient(135deg, #28a745 0%, #20c997 100%); border: none;">
                <span t-if="state.isLoading" class="spinner-border spinner-border-sm me-2"></span>
                <span t-if="state.currentStep === state.totalSteps">✅ Selesai</span>
                <span t-else="">Selanjutnya →</span>
            </button>
        </div>
    </div>
</div>
`;

// Register the wizard as a client action
registry
  .category("actions")
  .add("custom_saldo_santri_wizard", CustomSaldoSantriWizard);

// CSS untuk styling tambahan (tambahkan ke file CSS terpisah atau dalam module)
const customWizardCSS = `
.wizard-step {
    animation: fadeIn 0.4s ease-in-out;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateX(20px); }
    to { opacity: 1; transform: translateX(0); }
}

.form-control:focus, .form-select:focus {
    border-color: #28a745 !important;
    box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.25) !important;
}

.btn-primary {
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%) !important;
    border: none !important;
    transition: all 0.3s ease !important;
}

.btn-primary:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(40, 167, 69, 0.4) !important;
}
`;

// Inject CSS
if (typeof document !== "undefined") {
  const style = document.createElement("style");
  style.textContent = customWizardCSS;
  document.head.appendChild(style);
}
