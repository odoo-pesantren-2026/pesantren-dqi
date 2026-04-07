import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

// Dummy data untuk testing
const DUMMY_SANTRI_DATA = [
  {
    id: 1,
    nama: "Muhammad Naufal Raihan",
    nis: "182374",
    kelas: "XI - Rekayasa Perangkat Lunak - A",
    saldo: 850000,
    status: "aktif",
  },
  {
    id: 2,
    nama: "Ahmad Rizki Pratama",
    nis: "182375",
    kelas: "XI - Teknik Komputer Jaringan",
    saldo: 1200000,
    status: "aktif",
  },
  {
    id: 3,
    nama: "Siti Nurhaliza",
    nis: "182376",
    kelas: "XI - Multimedia",
    saldo: 450000,
    status: "non-aktif",
  },
  {
    id: 4,
    nama: "Budi Santoso",
    nis: "182377",
    kelas: "XI - Akuntansi",
    saldo: 75000,
    status: "aktif",
  },
];

let selectedSantri = null;
let santriData = [...DUMMY_SANTRI_DATA];

function formatCurrency(amount) {
  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    minimumFractionDigits: 0,
  }).format(amount);
}

function getStatusBadge(status) {
  const isActive = status === "aktif";
  const badgeClass = isActive ? "badge bg-success" : "badge bg-secondary";
  const statusText = isActive ? "Aktif" : "Non-Aktif";
  return `<span class="${badgeClass}">${statusText}</span>`;
}

function getSaldoColor(saldo) {
  if (saldo > 500000) return "text-success";
  if (saldo > 100000) return "text-warning";
  return "text-danger";
}

function renderSantriList(searchTerm = "") {
  const filteredData = santriData.filter(
    (santri) =>
      santri.nama.toLowerCase().includes(searchTerm.toLowerCase()) ||
      santri.nis.includes(searchTerm)
  );

  return filteredData
    .map(
      (santri) => `
        <div class="card mb-2 santri-card ${
          selectedSantri?.id === santri.id
            ? "border-primary bg-primary bg-opacity-10"
            : ""
        }" 
             style="cursor: pointer;" onclick="selectSantri(${santri.id})">
            <div class="card-body p-3">
                <div class="d-flex align-items-center">
                    <div class="avatar me-3">
                        <div class="rounded-circle bg-success d-flex align-items-center justify-content-center" 
                             style="width: 40px; height: 40px;">
                            <i class="fa fa-user text-white"></i>
                        </div>
                    </div>
                    <div class="flex-grow-1">
                        <h6 class="mb-1">${santri.nama}</h6>
                        <small class="text-muted">NIS: ${santri.nis}</small>
                        <div class="mt-1">
                            ${getStatusBadge(santri.status)}
                        </div>
                    </div>
                </div>
                <div class="mt-2">
                    <small class="text-muted">Saldo:</small>
                    <div class="fw-bold ${getSaldoColor(santri.saldo)}">
                        ${formatCurrency(santri.saldo)}
                    </div>
                </div>
            </div>
        </div>
    `
    )
    .join("");
}

function renderSantriDetail() {
  if (!selectedSantri) {
    return `
            <div class="d-flex align-items-center justify-content-center h-100">
                <div class="text-center text-muted">
                    <i class="fa fa-user-graduate fa-5x mb-3"></i>
                    <h4>Pilih Santri</h4>
                    <p>Silakan pilih santri dari daftar untuk melihat detail saldo</p>
                </div>
            </div>
        `;
  }

  return `
        <div class="p-4">
            <!-- Header Info -->
            <div class="row mb-4">
                <div class="col-12">
                    <div class="d-flex align-items-center mb-3">
                        <div class="avatar me-3">
                            <div class="rounded-circle bg-primary d-flex align-items-center justify-content-center" 
                                 style="width: 80px; height: 80px;">
                                <i class="fa fa-user-graduate text-white fa-2x"></i>
                            </div>
                        </div>
                        <div>
                            <h3 class="mb-1">${selectedSantri.nama}</h3>
                            <p class="text-muted mb-1">NIS: ${
                              selectedSantri.nis
                            }</p>
                            <p class="text-muted mb-2">${
                              selectedSantri.kelas
                            }</p>
                            ${getStatusBadge(selectedSantri.status)}
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Saldo Card -->
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="card bg-success text-white">
                        <div class="card-body text-center">
                            <i class="fa fa-wallet fa-3x mb-3"></i>
                            <h2 class="mb-1">${formatCurrency(
                              selectedSantri.saldo
                            )}</h2>
                            <h5>Saldo Tersedia</h5>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card ${
                      selectedSantri.status === "aktif"
                        ? "bg-success"
                        : "bg-secondary"
                    } text-white">
                        <div class="card-body text-center">
                            <i class="fa ${
                              selectedSantri.status === "aktif"
                                ? "fa-check-circle"
                                : "fa-times-circle"
                            } fa-3x mb-3"></i>
                            <h2 class="mb-1">${selectedSantri.status.toUpperCase()}</h2>
                            <h5>Status Akun</h5>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Action Buttons -->
            <div class="row mb-4">
                <div class="col-12">
                    <h5 class="mb-3"><i class="fa fa-cogs me-2"></i>Aksi Saldo</h5>
                    <div class="row g-2">
                        <div class="col-md-6">
                            <button class="btn btn-primary btn-lg w-100" onclick="openTransferModal()">
                                <i class="fa fa-paper-plane me-2"></i>
                                Transfer Saldo
                            </button>
                        </div>
                        <div class="col-md-6">
                            <button class="btn btn-success btn-lg w-100" onclick="topUpSaldo()">
                                <i class="fa fa-plus-circle me-2"></i>
                                Top Up Saldo
                            </button>
                        </div>
                        <div class="col-md-6">
                            <button class="btn btn-info btn-lg w-100" onclick="lihatRiwayat()">
                                <i class="fa fa-history me-2"></i>
                                Riwayat Transaksi
                            </button>
                        </div>
                        <div class="col-md-6">
                            <button class="btn btn-warning btn-lg w-100" onclick="blokirSaldo()">
                                <i class="fa fa-lock me-2"></i>
                                ${
                                  selectedSantri.status === "aktif"
                                    ? "Blokir"
                                    : "Aktifkan"
                                } Saldo
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Quick Stats -->
            <div class="row">
                <div class="col-12 mb-3">
                    <h5><i class="fa fa-chart-bar me-2"></i>Statistik Cepat</h5>
                </div>
                <div class="col-md-4">
                    <div class="card border-primary">
                        <div class="card-body text-center">
                            <i class="fa fa-shopping-cart text-primary fa-2x mb-2"></i>
                            <h6>Transaksi Bulan Ini</h6>
                            <h4 class="text-primary">15</h4>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card border-success">
                        <div class="card-body text-center">
                            <i class="fa fa-arrow-up text-success fa-2x mb-2"></i>
                            <h6>Total Top Up</h6>
                            <h4 class="text-success">${formatCurrency(
                              2500000
                            )}</h4>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card border-info">
                        <div class="card-body text-center">
                            <i class="fa fa-clock text-info fa-2x mb-2"></i>
                            <h6>Terakhir Aktif</h6>
                            <h4 class="text-info">2 jam lalu</h4>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function createWizardHTML() {
  return `
        <div class="modal-dialog modal-xl">
            <div class="modal-content">
                <div class="modal-header bg-primary text-white">
                    <h4 class="modal-title">
                        <i class="fa fa-wallet me-2"></i>
                        Kelola Saldo Santri
                    </h4>
                    <button type="button" class="btn-close btn-close-white" onclick="closeWizard()"></button>
                </div>
                
                <div class="modal-body p-0">
                    <div class="row g-0" style="min-height: 600px;">
                        <!-- Sidebar Daftar Santri -->
                        <div class="col-md-4 border-end bg-light">
                            <div class="p-3">
                                <div class="input-group mb-3">
                                    <span class="input-group-text">
                                        <i class="fa fa-search"></i>
                                    </span>
                                    <input 
                                        type="text" 
                                        class="form-control" 
                                        placeholder="Cari santri..."
                                        id="searchInput"
                                        oninput="searchSantri(this.value)"
                                    />
                                </div>
                                
                                <div class="santri-list" id="santriList" style="max-height: 500px; overflow-y: auto;">
                                    ${renderSantriList()}
                                </div>
                            </div>
                        </div>
                        
                        <!-- Detail Santri & Actions -->
                        <div class="col-md-8" id="santriDetail">
                            ${renderSantriDetail()}
                        </div>
                    </div>
                </div>
                
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="closeWizard()">Tutup</button>
                    ${
                      selectedSantri
                        ? `
                        <button type="button" class="btn btn-primary">
                            <i class="fa fa-save me-2"></i>Simpan Perubahan
                        </button>
                    `
                        : ""
                    }
                </div>
            </div>
        </div>
        
        <!-- Transfer Modal -->
        <div class="modal fade" id="transferModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title">
                            <i class="fa fa-paper-plane me-2"></i>
                            Transfer Saldo
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label">Dari:</label>
                            <input type="text" class="form-control" id="transferFrom" readonly />
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Saldo Tersedia:</label>
                            <input type="text" class="form-control" id="transferSaldo" readonly />
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Transfer Ke:</label>
                            <input type="text" class="form-control" id="transferTo" placeholder="Nama atau NIS penerima" />
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Jumlah Transfer:</label>
                            <div class="input-group">
                                <span class="input-group-text">Rp</span>
                                <input type="number" class="form-control" id="transferAmount" placeholder="0" />
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Batal</button>
                        <button type="button" class="btn btn-primary" onclick="processTransfer()">
                            <i class="fa fa-paper-plane me-2"></i>Kirim Transfer
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Global functions for event handlers
window.selectSantri = function (id) {
  selectedSantri = santriData.find((s) => s.id === id);
  document.getElementById("santriDetail").innerHTML = renderSantriDetail();
  document.getElementById("santriList").innerHTML = renderSantriList(
    document.getElementById("searchInput").value
  );
};

window.searchSantri = function (term) {
  document.getElementById("santriList").innerHTML = renderSantriList(term);
};

window.openTransferModal = function () {
  if (!selectedSantri) return;

  document.getElementById("transferFrom").value = selectedSantri.nama;
  document.getElementById("transferSaldo").value = formatCurrency(
    selectedSantri.saldo
  );
  document.getElementById("transferTo").value = "";
  document.getElementById("transferAmount").value = "";

  // Show modal using Bootstrap
  const modal = new bootstrap.Modal(document.getElementById("transferModal"));
  modal.show();
};

window.processTransfer = function () {
  const transferTo = document.getElementById("transferTo").value;
  const transferAmount = parseFloat(
    document.getElementById("transferAmount").value
  );

  if (!transferTo || !transferAmount || transferAmount <= 0) {
    alert("Mohon isi semua field dengan benar!");
    return;
  }

  if (transferAmount > selectedSantri.saldo) {
    alert("Saldo tidak mencukupi!");
    return;
  }

  // Update saldo
  selectedSantri.saldo -= transferAmount;

  // Update display
  document.getElementById("santriDetail").innerHTML = renderSantriDetail();
  document.getElementById("santriList").innerHTML = renderSantriList(
    document.getElementById("searchInput").value
  );

  // Close modal
  bootstrap.Modal.getInstance(document.getElementById("transferModal")).hide();

  alert(
    `Transfer berhasil!\nJumlah: ${formatCurrency(
      transferAmount
    )}\nKe: ${transferTo}`
  );
};

window.topUpSaldo = function () {
  const amount = prompt("Masukkan jumlah top up:");
  if (amount && !isNaN(amount) && parseFloat(amount) > 0) {
    selectedSantri.saldo += parseFloat(amount);
    document.getElementById("santriDetail").innerHTML = renderSantriDetail();
    document.getElementById("santriList").innerHTML = renderSantriList(
      document.getElementById("searchInput").value
    );
    alert(
      `Top up berhasil! Saldo ditambah ${formatCurrency(parseFloat(amount))}`
    );
  }
};

window.lihatRiwayat = function () {
  alert("Fitur riwayat transaksi akan segera hadir!");
};

window.blokirSaldo = function () {
  const newStatus = selectedSantri.status === "aktif" ? "non-aktif" : "aktif";
  selectedSantri.status = newStatus;

  // Update data di array
  const index = santriData.findIndex((s) => s.id === selectedSantri.id);
  santriData[index].status = newStatus;

  document.getElementById("santriDetail").innerHTML = renderSantriDetail();
  document.getElementById("santriList").innerHTML = renderSantriList(
    document.getElementById("searchInput").value
  );

  alert(`Status berhasil diubah menjadi ${newStatus.toUpperCase()}`);
};

window.closeWizard = function () {
  // Close the modal
  const modal = document.querySelector(".modal");
  if (modal) {
    modal.remove();
  }
};

// Register the wizard action
registry
  .category("actions")
  .add("custom_saldo_santri_wizard", async (env, action) => {
    const { params } = action;

    console.log("custom wizard odoo18 dibuka");

    const modalElement = document.createElement("div");
    modalElement.className = "modal fade show";
    modalElement.style.display = "block";
    modalElement.style.backgroundColor = "rgba(0,0,0,0.5)";
    modalElement.innerHTML = createWizardHTML();

    document.body.appendChild(modalElement);

    selectedSantri = null;

    modalElement.addEventListener("click", function (e) {
      if (e.target === modalElement) {
        closeWizard();
      }
    });
  });
