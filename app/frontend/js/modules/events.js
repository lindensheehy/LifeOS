import { 
    createContainer,
    createContainerFlex,
    createAddButton,
    createTextDiv,
} from "./../html_builders/primitives/index.js"
import { 
    createEventRow,
    createEventViewRow
} from "./../html_builders/components/index.js"

function localRenderEdit() {
    // Updated to use options object
    const container = createContainerFlex({ 
        id: 'editor-events', 
        className: 'events-container' 
    });
    
    // Replaced manual DOM creation and inline styles with our primitive!
    // We can just use an empty container because the rows themselves 
    // provide the spacing via the .mb-8 class we added in components.
    const rowsContainer = createContainer({ 
        id: 'events-rows-container' 
    });
    
    const addBtn = createAddButton('+ Add Event', () => {
        rowsContainer.appendChild(createEventRow());
        rowsContainer.dispatchEvent(new Event('input', { bubbles: true }));
    });

    container.appendChild(rowsContainer);
    container.appendChild(addBtn);

    return container;
}

function localRenderView() {
    // Updated to use options object
    return createContainerFlex({ 
        id: 'view-events', 
        className: 'events-container' 
    });
}

function localExtract() {
    const rowsContainer = document.getElementById('events-rows-container');
    const rows = rowsContainer.querySelectorAll('.dynamic-row');
    const eventsData = [];

    rows.forEach(row => {
        const timeVal = row.querySelector('.event-time-input').value;
        const desc = row.querySelector('.event-desc-input').value.trim();
        
        // Only push to the array if at least one field has data
        if (timeVal !== "" || desc !== "") {
            eventsData.push({ 
                "time": timeVal === "" ? 0 : parseInt(timeVal, 10), 
                "description": desc 
            });
        }
    });

    return eventsData;
}

function localInjectEdit(data) {
    const rowsContainer = document.getElementById('events-rows-container');
    if (rowsContainer) {
        rowsContainer.innerHTML = ''; 
        if (Array.isArray(data)) {
            data.forEach(event => {
                rowsContainer.appendChild(createEventRow(event.time, event.description));
            });
        }
    }
}

function localInjectView(data) {
    const viewContainer = document.getElementById('view-events');
    if (viewContainer) {
        viewContainer.innerHTML = ''; 
        
        if (Array.isArray(data) && data.length > 0) {
            const sortedEvents = [...data].sort((a, b) => (a.time || 0) - (b.time || 0));

            sortedEvents.forEach(event => {
                const t = event.time !== undefined ? String(event.time).padStart(4, '0') : '0000';
                const timeFormatted = `${t.slice(0, -2)}:${t.slice(-2)}`;
                const descFormatted = event.description || '--';

                viewContainer.appendChild(createEventViewRow(timeFormatted, descFormatted));
            });
            return true;
        } else {
            return false;
        }
    }
    return false;
}

export const EventsModule = {
    renderEdit: localRenderEdit,
    renderView: localRenderView,
    extract: localExtract,
    injectEdit: localInjectEdit,
    injectView: localInjectView
};
