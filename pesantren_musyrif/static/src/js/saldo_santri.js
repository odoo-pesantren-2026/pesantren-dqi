import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

// API Base URL - sesuaikan dengan Express.js server Anda
const API_BASE_URL = "http://localhost:3000/api"; // Ganti dengan URL server Express.js

let selectedSantri = null;
let santriData = [];
let isLoading = false;

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

// API Functions
async function fetchSantriData(searchTerm = "", status = "all") {
  try {
    isLoading = true;
    updateLoadingState(true);

    const url = new URL(`${API_BASE_URL}/santri`);
    if (searchTerm) url.searchParams.append("search", searchTerm);
    if (status !== "all") url.searchParams.append("status", status);

    console.log("Fetching data from:", url.toString());

    const response = await fetch(url.toString(), {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },

      mode: "cors",
      credentials: "omit",
    });

    console.log("Response status:", response.status);
    console.log("Response headers:", response.headers);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log("Response data:", data);

    if (data && data.success) {
      santriData = data.data || [];
      return santriData;
    } else {
      console.error("API Error:", data?.message || "Unknown error");
      showNotification("Gagal memuat data santri", "error");
      return [];
    }
  } catch (error) {
    console.error("Network Error:", error);
    showNotification(`Gagal terhubung ke server: ${error.message}`, "error");
    return [];
  } finally {
    isLoading = false;
    updateLoadingState(false);
  }
}

async function updateSantriSaldo(santriId, amount, type) {
  try {
    const response = await fetch(`${API_BASE_URL}/santri/${santriId}/saldo`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      mode: "cors",
      credentials: "omit",
      body: JSON.stringify({
        amount: amount,
        type: type,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    if (data && data.success) {
      return data.data;
    } else {
      throw new Error(data?.message || "Gagal update saldo");
    }
  } catch (error) {
    console.error("Update Saldo Error:", error);
    throw error;
  }
}

async function updateSantriStatus(santriId, status) {
  try {
    const response = await fetch(`${API_BASE_URL}/santri/${santriId}/status`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      mode: "cors",
      credentials: "omit",
      body: JSON.stringify({
        status: status,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    if (data && data.success) {
      return data.data;
    } else {
      throw new Error(data?.message || "Gagal update status");
    }
  } catch (error) {
    console.error("Update Status Error:", error);
    throw error;
  }
}

async function transferSaldo(fromId, toNis, amount, description) {
  try {
    const response = await fetch(`${API_BASE_URL}/santri/transfer`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      mode: "cors",
      credentials: "omit",
      body: JSON.stringify({
        fromId: fromId,
        toNis: toNis,
        amount: amount,
        description: description,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    if (data && data.success) {
      return data.data;
    } else {
      throw new Error(data?.message || "Gagal transfer saldo");
    }
  } catch (error) {
    console.error("Transfer Error:", error);
    throw error;
  }
}

function showNotification(message, type = "info") {
  console.log("Berhasil");
  // Menggunakan notification service Odoo
  //   const notification = registry.category("services").get("notification");
  //   if (notification) {
  //     notification.add(message, {
  //       type: type, // success, warning, danger, info
  //       sticky: false,
  //     });
  //   } else {
  //     // Fallback ke alert jika service tidak tersedia
  //     alert(message);
  //   }
}

function updateLoadingState(loading) {
  const loadingElements = document.querySelectorAll(".loading-spinner");
  loadingElements.forEach((el) => {
    el.style.display = loading ? "block" : "none";
  });
}

function renderSantriList(searchTerm = "") {
  if (isLoading) {
    return `
      <div class="d-flex justify-content-center p-4">
        <div class="spinner-border loading-spinner" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>
    `;
  }

  if (santriData.length === 0) {
    return `
      <div class="text-center text-muted p-4">
        <i class="fa fa-user-slash fa-3x mb-3"></i>
        <h5>Tidak ada data santri</h5>
        <p>Belum ada data santri yang tersedia</p>
      </div>
    `;
  }

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
                            <p class="text-muted mb-2">
                              <i class="fa fa-map-marker-alt me-1"></i>
                              ${
                                selectedSantri.alamat || "Alamat tidak tersedia"
                              }
                            </p>
                            <p class="text-muted mb-2">
                              <i class="fa fa-city me-1"></i>
                              ${selectedSantri.kota || ""}, ${
    selectedSantri.provinsi || ""
  }
                            </p>
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
                            <h4 class="text-primary">${
                              selectedSantri.transaksiPerBulan || 0
                            }</h4>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card border-success">
                        <div class="card-body text-center">
                            <i class="fa fa-arrow-up text-success fa-2x mb-2"></i>
                            <h6>Total Top Up</h6>
                            <h4 class="text-success">${formatCurrency(
                              selectedSantri.totalTopUp || 0
                            )}</h4>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card border-info">
                        <div class="card-body text-center">
                            <i class="fa fa-clock text-info fa-2x mb-2"></i>
                            <h6>Terakhir Aktif</h6>
                            <h4 class="text-info">${
                              selectedSantri.lastActivity || "Tidak diketahui"
                            }</h4>
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
                                
                                <div class="mb-3">
                                    <select class="form-select" id="statusFilter" onchange="filterByStatus(this.value)">
                                        <option value="all">Semua Status</option>
                                        <option value="aktif">Aktif</option>
                                        <option value="non-aktif">Non-Aktif</option>
                                    </select>
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
                    <button type="button" class="btn btn-info" onclick="refreshData()">
                        <i class="fa fa-refresh me-2"></i>Refresh Data
                    </button>
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
                            <label class="form-label">Transfer Ke (NIS):</label>
                            <input type="text" class="form-control" id="transferTo" placeholder="Masukkan NIS penerima" />
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Jumlah Transfer:</label>
                            <div class="input-group">
                                <span class="input-group-text">Rp</span>
                                <input type="number" class="form-control" id="transferAmount" placeholder="0" />
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Keterangan (opsional):</label>
                            <textarea class="form-control" id="transferDescription" rows="3" placeholder="Masukkan keterangan transfer"></textarea>
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

window.searchSantri = async function (term) {
  await fetchSantriData(
    term,
    document.getElementById("statusFilter")?.value || "all"
  );
  document.getElementById("santriList").innerHTML = renderSantriList(term);
};

window.filterByStatus = async function (status) {
  await fetchSantriData(
    document.getElementById("searchInput")?.value || "",
    status
  );
  document.getElementById("santriList").innerHTML = renderSantriList(
    document.getElementById("searchInput")?.value || ""
  );
};

window.refreshData = async function () {
  selectedSantri = null;
  await fetchSantriData();
  document.getElementById("santriList").innerHTML = renderSantriList();
  document.getElementById("santriDetail").innerHTML = renderSantriDetail();
  showNotification("Data berhasil diperbarui", "success");
};

window.openTransferModal = function () {
  if (!selectedSantri) return;

  document.getElementById("transferFrom").value = selectedSantri.nama;
  document.getElementById("transferSaldo").value = formatCurrency(
    selectedSantri.saldo
  );
  document.getElementById("transferTo").value = "";
  document.getElementById("transferAmount").value = "";
  document.getElementById("transferDescription").value = "";

  // Show modal using Bootstrap
  const modal = new bootstrap.Modal(document.getElementById("transferModal"));
  modal.show();
};

window.processTransfer = async function () {
  const transferTo = document.getElementById("transferTo").value;
  const transferAmount = parseFloat(
    document.getElementById("transferAmount").value
  );
  const transferDescription = document.getElementById(
    "transferDescription"
  ).value;

  if (!transferTo || !transferAmount || transferAmount <= 0) {
    showNotification("Mohon isi semua field dengan benar!", "warning");
    return;
  }

  if (transferAmount > selectedSantri.saldo) {
    showNotification("Saldo tidak mencukupi!", "warning");
    return;
  }

  try {
    const result = await transferSaldo(
      selectedSantri.id,
      transferTo,
      transferAmount,
      transferDescription
    );

    // Update local data
    const senderIndex = santriData.findIndex((s) => s.id === selectedSantri.id);
    if (senderIndex !== -1) {
      santriData[senderIndex] = result.sender;
      selectedSantri = result.sender;
    }

    // Update receiver if found in current data
    const receiverIndex = santriData.findIndex((s) => s.nis === transferTo);
    if (receiverIndex !== -1) {
      santriData[receiverIndex] = result.receiver;
    }

    // Update display
    document.getElementById("santriDetail").innerHTML = renderSantriDetail();
    document.getElementById("santriList").innerHTML = renderSantriList(
      document.getElementById("searchInput").value
    );

    // Close modal
    bootstrap.Modal.getInstance(
      document.getElementById("transferModal")
    ).hide();

    showNotification(
      `Transfer berhasil! Jumlah: ${formatCurrency(
        transferAmount
      )} ke NIS: ${transferTo}`,
      "success"
    );
  } catch (error) {
    showNotification(`Gagal transfer: ${error.message}`, "danger");
  }
};

window.topUpSaldo = async function () {
  const amount = prompt("Masukkan jumlah top up:");
  if (amount && !isNaN(amount) && parseFloat(amount) > 0) {
    try {
      const updatedSantri = await updateSantriSaldo(
        selectedSantri.id,
        parseFloat(amount),
        "topup"
      );

      // Update local data
      const index = santriData.findIndex((s) => s.id === selectedSantri.id);
      if (index !== -1) {
        santriData[index] = updatedSantri;
        selectedSantri = updatedSantri;
      }

      // Update display
      document.getElementById("santriDetail").innerHTML = renderSantriDetail();
      document.getElementById("santriList").innerHTML = renderSantriList(
        document.getElementById("searchInput").value
      );

      showNotification(
        `Top up berhasil! Saldo ditambah ${formatCurrency(parseFloat(amount))}`,
        "success"
      );
    } catch (error) {
      showNotification(`Gagal top up: ${error.message}`, "danger");
    }
  }
};

window.lihatRiwayat = function () {
  showNotification("Fitur riwayat transaksi akan segera hadir!", "info");
};

window.blokirSaldo = async function () {
  const newStatus = selectedSantri.status === "aktif" ? "non-aktif" : "aktif";
  const confirmMsg = `Apakah Anda yakin ingin ${
    newStatus === "aktif" ? "mengaktifkan" : "memblokir"
  } akun ${selectedSantri.nama}?`;

  if (!confirm(confirmMsg)) return;

  try {
    const updatedSantri = await updateSantriStatus(
      selectedSantri.id,
      newStatus
    );

    // Update local data
    const index = santriData.findIndex((s) => s.id === selectedSantri.id);
    if (index !== -1) {
      santriData[index] = updatedSantri;
      selectedSantri = updatedSantri;
    }

    // Update display
    document.getElementById("santriDetail").innerHTML = renderSantriDetail();
    document.getElementById("santriList").innerHTML = renderSantriList(
      document.getElementById("searchInput").value
    );

    showNotification(
      `Status berhasil diubah menjadi ${newStatus.toUpperCase()}`,
      "success"
    );
  } catch (error) {
    showNotification(`Gagal mengubah status: ${error.message}`, "danger");
  }
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

    console.log("Custom wizard Odoo 18 dengan Express.js integration dibuka");

    // Load initial data
    await fetchSantriData();

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
