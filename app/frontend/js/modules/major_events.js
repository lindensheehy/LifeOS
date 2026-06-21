import { 
    createContainer,
    createContainerFlex,
    createAddButton,
    createTextDiv
} from "./../html_builders/primitives/index.js"
import { 
    createMajorEventRow
} from "./../html_builders/components/index.js"

function localRenderEdit() {
    const container = createContainerFlex({ 
        id: 'editor-major-events', 
        className: 'major-events-container' 
    });
    
    const rowsContainer = createContainer({ 
        id: 'major-events-rows-container' 
    });
    
    const addBtn = createAddButton('+ Add Major Event', () => {
        rowsContainer.appendChild(createMajorEventRow());
        rowsContainer.dispatchEvent(new Event('input', { bubbles: true }));
    });

    container.appendChild(rowsContainer);
    container.appendChild(addBtn);

    return container;
}

function localRenderView() {
    return createContainerFlex({ 
        id: 'view-major-events', 
        className: 'major-events-container' 
    });
}

function localExtract() {
    const rowsContainer = document.getElementById('major-events-rows-container');
    if (!rowsContainer) return [];

    const rows = rowsContainer.querySelectorAll('.major-event-row');
    const eventsData = [];

    rows.forEach(row => {
        const desc = row.querySelector('.major-event-input').value.trim();
        
        // Push the string directly to the array
        if (desc !== "") {
            eventsData.push(desc);
        }
    });

    return eventsData;
}

function localInjectEdit(data) {
    const rowsContainer = document.getElementById('major-events-rows-container');
    if (rowsContainer) {
        rowsContainer.innerHTML = ''; 
        if (Array.isArray(data)) {
            data.forEach(eventText => {
                rowsContainer.appendChild(createMajorEventRow(eventText));
            });
        }
    }
}

function localInjectView(data) {
    const viewContainer = document.getElementById('view-major-events');
    if (viewContainer) {
        viewContainer.innerHTML = ''; 
        
        if (Array.isArray(data) && data.length > 0) {
            data.forEach(eventText => {
                viewContainer.appendChild(
                    createTextDiv('• ' + eventText, { 
                        className: 'text-primary text-paragraph mb-6' 
                    })
                );
            });
            return true;
        } else {
            return false;
        }
    }
    return false;
}

export const MajorEventsModule = {
    renderEdit: localRenderEdit,
    renderView: localRenderView,
    extract: localExtract,
    injectEdit: localInjectEdit,
    injectView: localInjectView
};
