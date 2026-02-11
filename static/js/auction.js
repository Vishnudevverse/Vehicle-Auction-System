/**
 * Vehicle Auction System — Frontend Logic with WebSocket Support
 */

document.addEventListener('DOMContentLoaded', () => {
    initCountdowns();
    initBidButtons();
    initWebSocket();
});

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   WEBSOCKET — Real-Time Updates
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
let ws = null;
let reconnectTimer = null;

function initWebSocket() {
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
    const url = `${protocol}://${location.host}/ws/auction`;

    ws = new WebSocket(url);

    ws.onopen = () => {
        updateWsStatus(true);
        if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
    };

    ws.onclose = () => {
        updateWsStatus(false);
        reconnectTimer = setTimeout(initWebSocket, 3000);   // auto-reconnect
    };

    ws.onerror = () => ws.close();

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);

        switch (msg.type) {
            case 'bid_update':
                handleBidUpdate(msg);
                break;
            case 'vehicle_removed':
                handleVehicleRemoved(msg);
                break;
            case 'vehicle_added':
                handleVehicleAdded(msg);
                break;
        }
    };
}

function updateWsStatus(connected) {
    const el = document.getElementById('wsStatus');
    if (!el) return;
    if (connected) {
        el.className = 'badge bg-success-subtle text-success-emphasis fs-6 px-3 py-2';
        el.innerHTML = '<i class="bi bi-wifi me-1"></i>Live Connected';
    } else {
        el.className = 'badge bg-danger-subtle text-danger-emphasis fs-6 px-3 py-2';
        el.innerHTML = '<i class="bi bi-wifi-off me-1"></i>Reconnecting…';
    }
}

/* ── Handle incoming bid update ─────────────── */
function handleBidUpdate(msg) {
    const priceEl = document.getElementById(`price-${msg.vehicle_id}`);
    if (priceEl) {
        const formatted = parseFloat(msg.current_price).toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
        priceEl.textContent = `$${formatted}`;

        // flash animation
        priceEl.classList.add('price-flash');
        setTimeout(() => priceEl.classList.remove('price-flash'), 1200);
    }

    // update button data attribute
    const btn = document.querySelector(`.bid-btn[data-vehicle-id="${msg.vehicle_id}"]`);
    if (btn) btn.dataset.currentPrice = msg.current_price;

    // show toast
    showToast(`${msg.bidder} bid $${parseFloat(msg.current_price).toLocaleString('en-US', {minimumFractionDigits:2})}`, 'success');
}

/* ── Handle vehicle removal (real-time) ───── */
function handleVehicleRemoved(msg) {
    const col = document.querySelector(`.vehicle-col[data-vehicle-id="${msg.vehicle_id}"]`);
    if (col) {
        col.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        col.style.opacity = '0';
        col.style.transform = 'scale(0.9)';
        setTimeout(() => col.remove(), 500);

        // update count
        updateActiveCount(-1);
        showToast('A vehicle was removed by admin', 'warning');
    }
}

/* ── Handle new vehicle added (real-time) ──── */
function handleVehicleAdded(msg) {
    const grid = document.getElementById('vehicleGrid');
    if (!grid) return;

    // remove empty state if present
    const empty = document.getElementById('emptyState');
    if (empty) empty.remove();

    const v = msg.vehicle;
    const desc = v.description ? v.description.substring(0, 100) + (v.description.length > 100 ? '…' : '') : '';
    const price = parseFloat(v.current_price).toLocaleString('en-US', {minimumFractionDigits:2});
    const startPrice = parseFloat(v.starting_price).toLocaleString('en-US', {minimumFractionDigits:2});

    // image or placeholder
    let imageHtml;
    if (v.image_url) {
        imageHtml = `<img src="${v.image_url}" class="card-img-top vehicle-img" alt="${v.title}" loading="lazy" />`;
    } else {
        const tpl = document.getElementById('placeholderSvg');
        imageHtml = tpl ? tpl.innerHTML : '<div class="card-img-top vehicle-img bg-body-secondary d-flex align-items-center justify-content-center" style="height:220px"><i class="bi bi-car-front display-4 text-body-tertiary"></i></div>';
    }

    // bid button depends on user role
    let bidHtml;
    if (typeof USER_IS_ADMIN !== 'undefined' && USER_IS_ADMIN) {
        bidHtml = `<button class="btn btn-secondary w-100" disabled><i class="bi bi-shield-lock me-1"></i>Admins Cannot Bid</button>`;
    } else if (typeof USER_LOGGED_IN !== 'undefined' && USER_LOGGED_IN) {
        bidHtml = `<button class="btn btn-primary w-100 bid-btn" data-vehicle-id="${v.id}" data-current-price="${v.current_price}" data-title="${v.title}"><i class="bi bi-hammer me-1"></i>Place Bid</button>`;
    } else {
        bidHtml = `<a href="/login" class="btn btn-outline-primary w-100"><i class="bi bi-box-arrow-in-right me-1"></i>Login to Bid</a>`;
    }

    const html = `
    <div class="col-lg-4 col-md-6 vehicle-col" data-vehicle-id="${v.id}" style="opacity:0;transform:translateY(20px);transition:all 0.5s ease;">
        <div class="card vehicle-card h-100 border-0 shadow-sm">
            <div class="card-img-wrapper position-relative overflow-hidden">
                ${imageHtml}
                <span class="badge bg-success position-absolute top-0 end-0 m-3 px-3 py-2 shadow">
                    <i class="bi bi-broadcast me-1"></i>LIVE
                </span>
            </div>
            <div class="card-body d-flex flex-column">
                <h5 class="card-title fw-bold mb-1">${v.title}</h5>
                <p class="card-text text-body-secondary small mb-3">${desc}</p>
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <div>
                        <small class="text-body-secondary d-block">Starting Price</small>
                        <span class="text-body-secondary">$${startPrice}</span>
                    </div>
                    <div class="text-end">
                        <small class="text-success d-block fw-semibold">Current Bid</small>
                        <span class="fs-5 fw-bold text-success" id="price-${v.id}">$${price}</span>
                    </div>
                </div>
                <div class="d-flex align-items-center mb-3">
                    <i class="bi bi-clock text-warning me-2"></i>
                    <small class="countdown text-warning fw-semibold" data-end="${v.auction_end}">Calculating…</small>
                </div>
                <div class="mt-auto">${bidHtml}</div>
            </div>
        </div>
    </div>`;

    grid.insertAdjacentHTML('beforeend', html);

    // animate in
    const newCol = grid.lastElementChild;
    requestAnimationFrame(() => {
        newCol.style.opacity = '1';
        newCol.style.transform = 'translateY(0)';
    });

    // re-init countdowns and bid buttons for new card
    initCountdowns();
    initBidButtons();
    updateActiveCount(1);
    showToast(`New auction: ${v.title}`, 'info');
}

function updateActiveCount(delta) {
    const el = document.getElementById('activeCount');
    if (el) el.textContent = parseInt(el.textContent || '0') + delta;
}

/* ── Toast Notifications ──────────────────── */
function showToast(message, type = 'info') {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '1090';
        document.body.appendChild(container);
    }

    const icons = { success: 'check-circle', warning: 'exclamation-triangle', info: 'info-circle', danger: 'x-circle' };
    const id = 'toast-' + Date.now();
    const html = `
    <div id="${id}" class="toast align-items-center text-bg-${type} border-0" role="alert">
        <div class="d-flex">
            <div class="toast-body">
                <i class="bi bi-${icons[type] || 'info-circle'} me-1"></i>${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    </div>`;

    container.insertAdjacentHTML('beforeend', html);
    const toastEl = document.getElementById(id);
    new bootstrap.Toast(toastEl, { delay: 4000 }).show();
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}


/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   COUNTDOWN TIMERS
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
function initCountdowns() {
    const countdowns = document.querySelectorAll('.countdown');

    function update() {
        const now = new Date();
        countdowns.forEach(el => {
            const end = new Date(el.dataset.end);
            const diff = end - now;

            if (diff <= 0) {
                el.textContent = 'Auction Ended';
                el.classList.remove('text-warning');
                el.classList.add('text-danger');
                return;
            }

            const d = Math.floor(diff / 86400000);
            const h = Math.floor((diff % 86400000) / 3600000);
            const m = Math.floor((diff % 3600000) / 60000);
            const s = Math.floor((diff % 60000) / 1000);

            let parts = [];
            if (d > 0) parts.push(`${d}d`);
            parts.push(`${h}h ${m}m ${s}s`);
            el.textContent = parts.join(' ');
        });
    }

    update();
    setInterval(update, 1000);
}


/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   BID MODAL LOGIC
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
function initBidButtons() {
    const modalEl = document.getElementById('bidModal');
    if (!modalEl) return;

    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    const titleEl   = document.getElementById('modalVehicleTitle');
    const priceEl   = document.getElementById('modalCurrentPrice');
    const amountInput = document.getElementById('bidAmount');
    const alertEl   = document.getElementById('bidAlert');
    const confirmBtn = document.getElementById('confirmBid');

    let activeVehicleId = null;

    // Open modal on card button click
    document.querySelectorAll('.bid-btn').forEach(btn => {
        // remove old listener by cloning
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);

        newBtn.addEventListener('click', () => {
            activeVehicleId = newBtn.dataset.vehicleId;
            const currentPrice = parseFloat(newBtn.dataset.currentPrice);
            titleEl.textContent = newBtn.dataset.title;
            priceEl.textContent = `$${currentPrice.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
            amountInput.value = '';
            amountInput.min = currentPrice + 100;
            amountInput.placeholder = `Min $${(currentPrice + 100).toLocaleString()}`;
            alertEl.className = 'd-none';
            modal.show();
        });
    });

    // Submit bid — remove old listener by re-cloning
    const newConfirm = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirm, confirmBtn);

    newConfirm.addEventListener('click', async () => {
        const amount = parseFloat(amountInput.value);
        if (!amount || amount <= 0) {
            showBidAlert('Please enter a valid bid amount.', 'danger');
            return;
        }

        newConfirm.disabled = true;
        newConfirm.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Placing…';

        try {
            const res = await fetch('/api/bids', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    vehicle_id: parseInt(activeVehicleId),
                    amount: amount,
                }),
            });

            const data = await res.json();

            if (!res.ok) {
                showBidAlert(data.detail || 'Bid failed. Try again.', 'danger');
                return;
            }

            showBidAlert('Bid placed successfully!', 'success');
            setTimeout(() => modal.hide(), 1200);
        } catch {
            showBidAlert('Network error. Please try again.', 'danger');
        } finally {
            newConfirm.disabled = false;
            newConfirm.innerHTML = '<i class="bi bi-check-lg me-1"></i>Confirm Bid';
        }
    });

    function showBidAlert(msg, type) {
        alertEl.className = `alert alert-${type}`;
        alertEl.innerHTML = `<i class="bi bi-${type === 'success'
            ? 'check-circle' : 'exclamation-triangle'} me-1"></i>${msg}`;
    }
}
