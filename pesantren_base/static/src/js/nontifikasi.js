import { registry } from "@web/core/registry";

registry.category("actions").add("custom_notif_popup", async (env, action) => {
    const { params } = action;
    const title = params.title || "Perhatian !";
    const message = params.message || "Pin Harus Berupa Angka";

    // Create modal backdrop
    const backdrop = document.createElement("div");
    backdrop.className = "modal-backdrop fade show";
    document.body.appendChild(backdrop);

    // Create modal dialog
    const modalHtml = `
        <div class="modal fade show" style="display: block; padding-right: 16px;">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="close" id="close-custom-modal">
                            <span aria-hidden="true">×</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <p>${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-success" id="btn-close-custom-modal">Tutup</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Add modal to DOM
    const modalContainer = document.createElement("div");
    modalContainer.innerHTML = modalHtml;
    document.body.appendChild(modalContainer);

    // Add event listeners to close buttons
    const closeBtn = document.getElementById("close-custom-modal");
    const closeBtnFooter = document.getElementById("btn-close-custom-modal");

    const closeModal = () => {
        document.body.removeChild(backdrop);
        document.body.removeChild(modalContainer);
    };

    closeBtn.addEventListener("click", closeModal);
    closeBtnFooter.addEventListener("click", closeModal);

    return {
        close: closeModal,
    };
});
