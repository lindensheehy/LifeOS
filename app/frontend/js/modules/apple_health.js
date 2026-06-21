import { 
    createContainerFlex,
    createListRow,
    createTextSpan,
    createTextDiv
} from "./../html_builders/primitives/index.js"

function localRenderEdit() {

    const container = createContainerFlex({ id: 'editor-apple-health' });
    
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.attributeName === 'class') {
                const isEditMode = !container.classList.contains('mode-hidden');
                const sectionBlock = container.closest('.section-block');
                
                if (sectionBlock) {
                    if (isEditMode) {
                        // Force hide the entire section in Edit mode (Read-Only Data)
                        sectionBlock.style.display = 'none';
                    } else {
                        // In View mode, check the dataset count
                        const viewContainer = document.getElementById('view-apple-health');
                        const recordCount = parseInt(viewContainer?.dataset?.count || "0", 10);
                        sectionBlock.style.display = recordCount > 0 ? 'block' : 'none';
                    }
                }
            }
        });
    });
    
    observer.observe(container, { attributes: true });
    return container;
}

function localRenderView() {
    return createContainerFlex({ id: 'view-apple-health' });
}

function localExtract() {
    // Read-only module
    return null; 
}

function localInject(data) {

    return false;

    const dailyRecords = Array.isArray(data) ? data : [];
    
    const viewContainer = document.getElementById('view-apple-health');
    if (!viewContainer) return;
    
    viewContainer.innerHTML = ''; 
    viewContainer.dataset.count = dailyRecords.length;
    
    const sectionBlock = viewContainer.closest('.section-block');

    if (dailyRecords.length > 0) {
        if (sectionBlock && !viewContainer.classList.contains('mode-hidden')) {
            sectionBlock.style.display = 'block';
        }

        // --- Aggregation Layer ---
        // Crush hundreds of micro-records into daily totals/averages
        const summary = {};
        
        dailyRecords.forEach(record => {
            const type = record.type;
            const val = parseFloat(record.value) || 0;
            
            if (!summary[type]) {
                summary[type] = { total: 0, count: 0, unit: record.unit };
            }
            summary[type].total += val;
            summary[type].count += 1;
        });

        // --- Render the Aggregated Data ---
        Object.keys(summary).sort().forEach(type => {
            const stat = summary[type];
            let displayValue;
            
            // Define keywords for metrics that MUST be averaged instead of summed
            const averageKeywords = ['Rate', 'Percentage', 'Speed', 'Length', 'Exposure'];
            const shouldAverage = averageKeywords.some(keyword => type.includes(keyword));

            if (shouldAverage) {
                // Average these values
                displayValue = (stat.total / stat.count).toFixed(2);
            } else if (type.includes('Distance')) {
                // Sum, but keep decimals for distance
                displayValue = stat.total.toFixed(2); 
            } else {
                // Sum, and round to whole numbers (Steps, Calories, Flights Climbed)
                displayValue = Math.round(stat.total); 
            }

            const row = createListRow();
            row.style.alignItems = 'center'; 
            
            // Format the UI to match your transactions layout
            const valueSpan = createTextSpan(`${displayValue} ${stat.unit}`, {
                className: 'fw-600 text-monospace w-70 text-primary'
            });
            
            const detailsDiv = createContainerFlex();
            detailsDiv.style.gap = '2px'; 
            
            // Clean up camel case (e.g. "StepCount" -> "Step Count")
            const formattedType = type.replace(/([A-Z])/g, ' $1').trim();
            
            const typeSpan = createTextDiv(formattedType, { 
                className: 'text-primary fw-500 fs-14 text-capitalize' 
            });
            
            const countSpan = createTextDiv(`${stat.count} raw records`, { 
                className: 'text-secondary fs-12 text-uppercase' 
            });
            
            detailsDiv.appendChild(typeSpan);
            detailsDiv.appendChild(countSpan);
            
            row.appendChild(valueSpan);
            row.appendChild(detailsDiv);
            
            viewContainer.appendChild(row);
        });
        
    } else {
        if (sectionBlock) sectionBlock.style.display = 'none';
    }
}

export const AppleHealthModule = {
    renderEdit: localRenderEdit,
    renderView: localRenderView,
    extract: localExtract,
    inject: localInject
};