import { 
    createContainerFlex,
    createListRow,
    createTextSpan,
    createTextDiv
} from "./../html_builders/primitives/index.js"

function localRenderEdit() {

    const container = createContainerFlex({ id: 'editor-transactions' });
    
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.attributeName === 'class') {
                const isEditMode = !container.classList.contains('mode-hidden');
                const sectionBlock = container.closest('.section-block');
                
                if (sectionBlock) {
                    if (isEditMode) {
                        // Force hide the entire section (including the header) in Edit mode
                        sectionBlock.style.display = 'none';
                    } else {
                        // In View mode, check the dataset count we set in inject()
                        const viewContainer = document.getElementById('view-transactions');
                        const txCount = parseInt(viewContainer?.dataset?.count || "0", 10);
                        sectionBlock.style.display = txCount > 0 ? 'block' : 'none';
                    }
                }
            }
        });
    });
    
    observer.observe(container, { attributes: true });
    return container;
}

function localRenderView() {
    return createContainerFlex({ id: 'view-transactions' });
}

function localExtract() {
    // Read-only module, we don't extract anything for the POST request
    return null; 
}

function localInject(data) {

    return false;

    // We now receive the exact array of transactions directly from the L2 Cache
    const dailyTx = Array.isArray(data) ? data : [];
    
    const viewContainer = document.getElementById('view-transactions');
    if (!viewContainer) return;
    
    viewContainer.innerHTML = ''; 
    
    // Stamp the count onto the DOM so the edit-mode observer can read it later
    viewContainer.dataset.count = dailyTx.length;
    
    const sectionBlock = viewContainer.closest('.section-block');

    if (dailyTx.length > 0) {
        // Only force display if we are currently in view mode
        if (sectionBlock && !viewContainer.classList.contains('mode-hidden')) {
            sectionBlock.style.display = 'block';
        }

        dailyTx.forEach(tx => {
            const row = createListRow();
            row.style.alignItems = 'center'; 
            
            const isIncome = tx.amount > 0;
            const amountStr = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Math.abs(tx.amount));
            const prefix = isIncome ? '+' : '-';
            
            const amountSpan = createTextSpan(`${prefix}${amountStr}`, {
                className: `fw-600 text-monospace w-70 ${isIncome ? 'text-accent-green' : 'text-primary'}`
            });
            
            const detailsDiv = createContainerFlex();
            detailsDiv.style.gap = '2px'; 
            
            const descSpan = createTextDiv(tx.description, { 
                className: 'text-primary fw-500 fs-14 text-capitalize' 
            });
            const bankSpan = createTextDiv(`${tx.bank_company} • ${tx.account_type}`, { 
                className: 'text-secondary fs-12 text-uppercase' 
            });
            
            detailsDiv.appendChild(descSpan);
            detailsDiv.appendChild(bankSpan);
            
            row.appendChild(amountSpan);
            row.appendChild(detailsDiv);
            
            viewContainer.appendChild(row);
        });
    } else {
        if (sectionBlock) sectionBlock.style.display = 'none';
    }
}

export const TransactionsModule = {
    renderEdit: localRenderEdit,
    renderView: localRenderView,
    extract: localExtract,
    inject: localInject
};