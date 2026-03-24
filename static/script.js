document.addEventListener('DOMContentLoaded', () => {
    const processBtn = document.getElementById('processBtn');
    const uploadBtn = document.getElementById('uploadBtn');
    const fileInput = document.getElementById('fileInput');
    const clearBtn = document.getElementById('clearBtn');

    const tableHeader = document.getElementById('tableHeader');
    const tableBody = document.getElementById('tableBody');
    const loader = document.getElementById('loader');

    // Drawer elements
    const detailDrawer = document.getElementById('detailDrawer');
    const drawerOverlay = document.getElementById('drawerOverlay');
    const drawerContent = document.getElementById('drawerContent');
    const closeDrawerBtn = document.getElementById('closeDrawer');

    // UI Dialog elements
    const modalOverlay = document.getElementById('modalOverlay');
    const customModal = document.getElementById('customModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalMessage = document.getElementById('modalMessage');
    const modalConfirmBtn = document.getElementById('modalConfirm');
    const modalCancelBtn = document.getElementById('modalCancel');
    const toast = document.getElementById('toast');

    let invoiceData = [];

    // UI Dialog Helpers
    function showToast(msg) {
        toast.innerText = msg;
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 3000);
    }

    function showConfirm(title, message) {
        return new Promise((resolve) => {
            modalTitle.innerText = title;
            modalMessage.innerText = message;
            customModal.style.display = 'block';
            modalOverlay.style.display = 'block';
            setTimeout(() => customModal.classList.add('open'), 10);

            const onConfirm = () => {
                cleanup();
                resolve(true);
            };
            const onCancel = () => {
                cleanup();
                resolve(false);
            };
            const cleanup = () => {
                customModal.classList.remove('open');
                setTimeout(() => {
                    customModal.style.display = 'none';
                    modalOverlay.style.display = 'none';
                }, 200);
                modalConfirmBtn.removeEventListener('click', onConfirm);
                modalCancelBtn.removeEventListener('click', onCancel);
                modalOverlay.removeEventListener('click', onCancel);
            };

            modalConfirmBtn.addEventListener('click', onConfirm);
            modalCancelBtn.addEventListener('click', onCancel);
            modalOverlay.addEventListener('click', onCancel);
        });
    }

    // Load initial data
    loadTableData();

    let wasProcessing = false;

    processBtn.addEventListener('click', async () => {
        const confirmed = await showConfirm('Process Emails', 'Start processing all unread emails? This will scan for invoices and send your daily digest.');
        if (!confirmed) return;
        
        try {
            const resp = await fetch('/api/process', { method: 'POST' });
            if (!resp.ok) throw new Error('Failed to start processing');
            
            checkStatus(); // Start polling immediately
        } catch (err) {
            console.error(err);
            alert('Error starting process: ' + err.message);
        }
    });

    async function checkStatus() {
        try {
            const resp = await fetch('/api/status');
            const data = await resp.json();
            
            if (data.is_processing) {
                processBtn.disabled = true;
                loader.style.display = 'inline-block';
                wasProcessing = true;
                setTimeout(checkStatus, 3000); // Poll every 3 seconds
            } else {
                if (wasProcessing) {
                    processBtn.disabled = false;
                    loader.style.display = 'none';
                    await loadTableData();
                    showToast('Sync Complete: Your dashboard has been updated.');
                    wasProcessing = false;
                }
            }
        } catch (err) {
            console.error('Status check failed', err);
        }
    }

    // Check status on page load in case a process is already underway
    checkStatus();

    uploadBtn.addEventListener('click', () => fileInput.click());

    clearBtn.addEventListener('click', async () => {
        const confirmed = await showConfirm('Clear Dashboard', 'Are you sure you want to delete all stored invoice data? This cannot be undone.');
        if (!confirmed) return;
        
        try {
            const resp = await fetch('/api/invoices', { method: 'DELETE' });
            if (!resp.ok) throw new Error('Clear failed');
            
            invoiceData = [];
            tableBody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 4rem; color: var(--text-muted);">No invoices found. Click "Fetch" or "Upload" to get started.</td></tr>';
            showToast('Dashboard cleared successfully.');
        } catch (err) {
            console.error(err);
            showToast('Error clearing data: ' + err.message);
        }
    });

    fileInput.addEventListener('change', async (e) => {
        const files = e.target.files;
        if (!files || files.length === 0) return;

        uploadBtn.disabled = true;
        loader.style.display = 'inline-block';

        try {
            for (const file of files) {
                const formData = new FormData();
                formData.append('file', file);

                const resp = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });

                if (!resp.ok) throw new Error(`Failed to upload ${file.name}`);
            }
            showToast('Upload and processing complete!');
            await loadTableData();
        } catch (err) {
            console.error(err);
            showToast('Error: ' + err.message);
        } finally {
            uploadBtn.disabled = false;
            loader.style.display = 'none';
            fileInput.value = ''; // Reset
        }
    });

    closeDrawerBtn.addEventListener('click', closeDetails);
    drawerOverlay.addEventListener('click', closeDetails);

    function closeDetails() {
        detailDrawer.classList.remove('open');
        drawerOverlay.style.display = 'none';
    }

    function formatLineItems(text) {
        if (!text || text === 'N/A') return 'No line items recorded.';
        
        // Try to split by numbered items (e.g. 1. Item 2. Item)
        const parts = text.split(/(?=\d+\.\s+)/).filter(p => p.trim());
        if (parts.length <= 1) return text.replace(/\\n/g, '<br>');

        return `
            <table class="line-items-table">
                <thead>
                    <tr><th>#</th><th>Description & Details</th></tr>
                </thead>
                <tbody>
                    ${parts.map(p => {
                        const match = p.match(/^(\d+)\.\s+(.*)/);
                        if (!match) return `<tr><td>-</td><td>${p}</td></tr>`;
                        return `<tr><td>${match[1]}</td><td>${match[2]}</td></tr>`;
                    }).join('')}
                </tbody>
            </table>
        `;
    }

    function openDetails(index) {
        const row = invoiceData[index];
        const localPath = row['Local File Path'];
        const gmailLink = row['Source Email Link'];

        // 1. Update Info Panel
        drawerContent.innerHTML = `
            <div class="detail-group">
                <div class="detail-label">Vendor</div>
                <div class="detail-value" style="font-size: 1.5rem; font-weight: 800;">${row['Vendor Name']}</div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-top: 1rem;">
                <div class="detail-group">
                    <div class="detail-label">Invoice #</div>
                    <div class="detail-value">${row['Invoice Number']}</div>
                </div>
                <div class="detail-group">
                    <div class="detail-label">Status</div>
                    <span class="status-tag ${row['Extraction Status'] === 'SUCCESS' ? 'status-success' : 'status-failed'}">${row['Extraction Status']}</span>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
                <div class="detail-group">
                    <div class="detail-label">Date</div>
                    <div class="detail-value">${row['Invoice Date']}</div>
                </div>
                <div class="detail-group">
                    <div class="detail-label">Due Date</div>
                    <div class="detail-value">${row['Due Date']}</div>
                </div>
            </div>

            <div class="detail-group">
                <div class="detail-label">Recipient Client</div>
                <div class="detail-value">${row['Client Name']}</div>
            </div>

            <hr style="border: none; border-top: 1px solid var(--table-border); margin: 2rem 0;">

            <div class="detail-group">
                <div class="detail-label">Extracted Line Items</div>
                <div class="line-item-container">${formatLineItems(row['Line Items (Summary)'])}</div>
            </div>

            <div style="background: linear-gradient(135deg, #fffbeb 0%, #fff7ed 100%); padding: 1.5rem; border-radius: 1rem; border: 1px solid #fed7aa; margin-top: 2rem;">
                 <div class="detail-label" style="color: #9a3412;">Final Total</div>
                 <div class="detail-value" style="font-size: 2.25rem; font-weight: 900; color: #c2410c;">${row['Final Total']}</div>
                 <div class="detail-label" style="margin-top:0.5rem; color: #9a3412; opacity: 0.8;">Subtotal: ${row['Subtotal']} | Tax: ${row['Tax']}</div>
            </div>

            <div style="margin-top: 2.5rem; padding-top: 1.5rem; border-top: 1px solid var(--table-border);">
               <div class="detail-label">Source Link</div>
               ${gmailLink && gmailLink !== 'N/A' ? `
                    <a href="${gmailLink}" target="_blank" class="action-icon-btn" style="margin-top:8px;">
                        📩 Open in Gmail
                    </a>
                ` : '<div class="detail-value">Manual Upload</div>'}
            </div>
        `;

        // 2. Update Preview Panel
        const drawerPreview = document.getElementById('drawerPreview');
        if (localPath) {
            const ext = localPath.split('.').pop().toLowerCase();
            
            if (['jpg', 'jpeg', 'png', 'webp', 'gif'].includes(ext)) {
                drawerPreview.innerHTML = `
                    <div class="detail-label" style="margin-bottom: 10px;">Document Preview</div>
                    <div style="flex:1; overflow: auto; background: white; border-radius: 12px; display: flex; justify-content: center; align-items: flex-start; padding: 20px;">
                        <img src="${localPath}" style="max-width: 100%; height: auto; box-shadow: 0 0 20px rgba(0,0,0,0.1);">
                    </div>
                `;
            } else if (ext === 'pdf') {
                drawerPreview.innerHTML = `
                    <div class="detail-label" style="margin-bottom: 10px;">Document Preview (PDF)</div>
                    <iframe src="${localPath}" class="preview-frame"></iframe>
                `;
            } else if (ext === 'csv' || ext === 'txt') {
                drawerPreview.innerHTML = `<div class="detail-label" style="margin-bottom: 10px;">Document Preview (CSV)</div>`;
                const csvLoader = document.createElement('div');
                csvLoader.className = 'preview-frame';
                csvLoader.style.cssText = 'display:flex; align-items:center; justify-content:center; color:#64748b;';
                csvLoader.textContent = 'Rendering Document...';
                drawerPreview.appendChild(csvLoader);

                fetch(`${localPath}?t=${new Date().getTime()}`)
                    .then(r => {
                        if (!r.ok) throw new Error('File not found');
                        return r.text();
                    })
                    .then(txt => {
                        const csvRows = txt.trim().split('\n');
                        let tableHtml = '<table>';
                        csvRows.forEach((csvRow, i) => {
                            const cells = csvRow.split(',').map(c => c.trim().replace(/^"|"$/g, ''));
                            tableHtml += '<tr>';
                            cells.forEach(cell => {
                                tableHtml += i === 0 ? `<th>${cell}</th>` : `<td>${cell}</td>`;
                            });
                            tableHtml += '</tr>';
                        });
                        tableHtml += '</table>';

                        const csvHtml = `<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
                            body { font-family: Calibri, Arial, sans-serif; font-size: 10pt; padding: 20px; background: white; color: #1e293b; }
                            table { width: 100%; border-collapse: collapse; }
                            th { background: #f8fafc; font-weight: 700; text-align: left; padding: 8px 12px; border: 1px solid #cbd5e1; font-size: 0.75rem; text-transform: uppercase; color: #64748b; }
                            td { padding: 8px 12px; border: 1px solid #e2e8f0; }
                            tr:nth-child(even) td { background: #f8fafc; }
                        </style></head><body>${tableHtml}</body></html>`;

                        csvLoader.remove();
                        const iframe = document.createElement('iframe');
                        iframe.className = 'preview-frame';
                        iframe.srcdoc = csvHtml;
                        drawerPreview.appendChild(iframe);
                    })
                    .catch(err => {
                        console.error("CSV preview error:", err);
                        csvLoader.remove();
                        drawerPreview.innerHTML += '<div class="no-preview">Could not render document.</div>';
                    });
            } else if (ext === 'docx' || ext === 'doc') {
                drawerPreview.innerHTML = `<div class="detail-label" style="margin-bottom: 10px;">Document Preview (Word)</div>`;
                const docLoader = document.createElement('div');
                docLoader.className = 'preview-frame';
                docLoader.style.cssText = 'display:flex; align-items:center; justify-content:center; color:#64748b;';
                docLoader.textContent = 'Rendering Word Document...';
                drawerPreview.appendChild(docLoader);

                fetch(`${localPath}?t=${new Date().getTime()}`)
                    .then(r => {
                        if (!r.ok) throw new Error('File not found');
                        return r.arrayBuffer();
                    })
                    .then(arrayBuffer => mammoth.convertToHtml({ arrayBuffer }))
                    .then(result => {
                        const docHtml = `<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
                            body { font-family: Calibri, Arial, sans-serif; font-size: 11pt; line-height: 1.6; padding: 40px 60px; color: #1e293b; background: white; }
                            table { width: 100%; border-collapse: collapse; margin: 1em 0; }
                            th, td { border: 1px solid #cbd5e1; padding: 8px 12px; }
                            th { background: #f8fafc; font-weight: 700; text-align: left; }
                            img { max-width: 100%; }
                            h1, h2, h3 { margin: 0.75em 0 0.25em; }
                            p { margin-bottom: 0.4em; }
                        </style></head><body>${result.value || '<p>Document appears to be empty.</p>'}</body></html>`;

                        docLoader.remove();
                        const iframe = document.createElement('iframe');
                        iframe.className = 'preview-frame';
                        iframe.srcdoc = docHtml;
                        drawerPreview.appendChild(iframe);
                    })
                    .catch(err => {
                        console.error("DOCX preview error:", err);
                        docLoader.remove();
                        drawerPreview.innerHTML += `
                            <div class="no-preview">
                                <div style="font-size: 3rem; margin-bottom: 1rem;">📄</div>
                                <p>Could not render document.</p>
                                <a href="${localPath}" target="_blank" class="action-icon-btn" style="margin-top: 1rem;">Download Original Invoice</a>
                            </div>
                        `;
                    });
            } else {
                drawerPreview.innerHTML = `
                    <div class="no-preview">
                        <div style="font-size: 3rem; margin-bottom: 1rem;">📄</div>
                        <p>Direct preview not supported for <strong>.${ext}</strong>.</p>
                        <a href="${localPath}" target="_blank" class="action-icon-btn" style="margin-top: 1rem;">Download Original Invoice</a>
                    </div>
                `;
            }
        } else {
            drawerPreview.innerHTML = '<div class="no-preview">Original document not available for preview.</div>';
        }

        detailDrawer.classList.add('open');
        drawerOverlay.style.display = 'block';
    }

    async function loadTableData() {
        try {
            const resp = await fetch('/api/invoices');
            invoiceData = await resp.json();

            if (!invoiceData || invoiceData.length === 0) return;

            // Updated Column subset for the main table (Cleaner view)
            const displayKeys = ['Vendor Name', 'Final Total', 'Due Date', 'Payment Status', 'Extraction Status'];
            tableHeader.innerHTML = `
                ${displayKeys.map(k => `<th>${k}</th>`).join('')}
                <th>Action</th>
            `;

            // Render Rows
            tableBody.innerHTML = invoiceData.map((row, idx) => {
                const vendorInitial = row['Vendor Name'] ? row['Vendor Name'].charAt(0) : '?';
                return `<tr>
                    <td>
                        <div class="vendor-cell">
                            <div class="vendor-icon">${vendorInitial}</div>
                            <div style="font-weight: 700;">${row['Vendor Name']}</div>
                        </div>
                    </td>
                    <td><span class="amount-primary">${row['Final Total']}</span></td>
                    <td>${row['Due Date']}</td>
                    <td>${row['Payment Status']}</td>
                    <td><span class="status-tag ${row['Extraction Status'] === 'SUCCESS' ? 'status-success' : 'status-failed'}">${row['Extraction Status']}</span></td>
                    <td>
                        <button class="email-link" onclick="openDetails(${idx})" style="background:none; border:none; cursor:pointer;">View Details</button>
                    </td>
                </tr>`;
            }).join('');

        } catch (err) {
            console.error('Failed to load table:', err);
        }
    }

    // Global toggle because of inline onclick
    window.openDetails = openDetails;
});
