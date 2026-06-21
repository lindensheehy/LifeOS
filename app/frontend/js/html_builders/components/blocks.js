import { 
    createAddButton,
    createDeleteButton,
    createCopyButton,
    createPanelBlock, 
    createGridContainer, 
    createTextSpan,
    createTextDiv,
    createViewBlock,
    createFlexRowBetween,
    createTextbox,
    createCheckbox,
    createAutocomplete
} from "./../primitives/index.js"
import { 
    createGymSetRow,
    createCodingDetailRow
} from "./index.js"

export function createGymMovementBlock(movementName = "", setsData = [], movementOptions = []) {
    const block = createPanelBlock({ className: 'gym-movement-block mb-12' });

    const headerRow = document.createElement('div');
    headerRow.className = 'flex-row-8 mb-10';

    // SWAPPED: createTextbox -> createAutocomplete
    const nameInput = createAutocomplete(movementOptions, { 
        placeholder: 'Movement', 
        className: 'gym-movement-name flex-grow-1' 
    });
    nameInput.value = movementName;

    const deleteBlockBtn = createDeleteButton(() => { 
        block.remove(); 
    });

    // ADDED: nameInput._hiddenDatalist
    headerRow.append(nameInput, nameInput._hiddenDatalist, deleteBlockBtn);

    const setsContainer = document.createElement('div');
    setsContainer.className = 'gym-sets-container pl-10'; 
    
    if (setsData && setsData.length > 0) {
        setsData.forEach(set => setsContainer.appendChild(createGymSetRow(set.weight, set.reps)));
    } else {
        setsContainer.appendChild(createGymSetRow());
    }

    const addSetBtn = createAddButton('+ Add Set', () => { 
        setsContainer.appendChild(createGymSetRow()); 
    });
    addSetBtn.classList.add('ml-10');

    block.append(headerRow, setsContainer, addSetBtn);
    return block;
}

export function createCodingProjectBlockEdit(projectData = {}, projectOptions = []) {
    const block = createPanelBlock({ className: 'coding-project-block mb-12' });

    const headerRow = document.createElement('div');
    headerRow.className = 'flex-row-8 mb-10';

    // SWAPPED: createTextbox -> createAutocomplete
    const nameInput = createAutocomplete(projectOptions, { 
        placeholder: 'Project Name', 
        className: 'coding-project-name flex-grow-1' 
    });
    nameInput.value = projectData.project || "";

    const deleteBlockBtn = createDeleteButton(() => { 
        block.remove(); 
    });

    // ADDED: nameInput._hiddenDatalist
    headerRow.append(nameInput, nameInput._hiddenDatalist, deleteBlockBtn);

    const metaRow = document.createElement('div');
    metaRow.className = 'flex-row-10 mb-10';

    const taskInput = createTextbox({ 
        placeholder: 'Main task', 
        className: 'coding-task-input flex-grow-1' 
    });
    taskInput.value = projectData.task || "";

    const timeInput = createTextbox({ 
        type: 'number', 
        placeholder: 'Hours', 
        className: 'coding-time-input', 
        step: 'any' 
    });
    timeInput.style.width = '80px'; 
    timeInput.value = projectData["time spent"] !== undefined ? projectData["time spent"] : "";

    metaRow.append(taskInput, timeInput);

    const detailsLabel = createTextDiv("Details:", { 
        className: 'fs-12 fw-600 text-secondary mb-6' 
    });

    const detailsContainer = document.createElement('div');
    detailsContainer.className = 'coding-details-container pl-10';
    
    const detailsList = projectData.details || [];
    if (detailsList.length > 0) {
        detailsList.forEach(detail => detailsContainer.appendChild(createCodingDetailRow(detail)));
    } else {
        detailsContainer.appendChild(createCodingDetailRow());
    }

    const addDetailBtn = createAddButton('+ Add Detail', () => { 
        detailsContainer.appendChild(createCodingDetailRow()); 
    });
    addDetailBtn.classList.add('ml-10', 'mt-4');

    block.append(headerRow, metaRow, detailsLabel, detailsContainer, addDetailBtn);
    return block;
}

export function createCodingProjectBlockView(projectData = {}) {
    const block = createViewBlock();

    // Header: Project Name (Left) | Time Spent (Right)
    const header = createFlexRowBetween();
    
    const titleSpan = createTextSpan(projectData.project || "UNTITLED PROJECT", {
        className: 'text-primary fw-700 text-uppercase'
    });

    const hrs = projectData["time spent"];
    const timeSpan = createTextSpan(hrs ? `</> ${hrs}h` : '', {
        className: 'text-accent-blue fw-600'
    });

    header.appendChild(titleSpan);
    header.appendChild(timeSpan);
    block.appendChild(header);

    // Main Task
    if (projectData.task) {
        const taskDiv = createTextDiv(projectData.task, {
            className: 'text-primary fw-500'
        });
        block.appendChild(taskDiv);
    }

    // Details
    if (projectData.details && Array.isArray(projectData.details) && projectData.details.length > 0) {
        const detailsDiv = createTextDiv("• " + projectData.details.join('\n• '), {
            className: 'text-secondary fs-13 text-paragraph'
        });
        block.appendChild(detailsDiv);
    }

    return block;
}

export function createDenseInputBlock(titleText, items) {
    const group = createPanelBlock();

    if (titleText) {
        const title = createTextDiv(titleText, {
            className: 'text-secondary fw-600 fs-12 text-uppercase mb-12'
        });
        group.appendChild(title);
    }

    const grid = createGridContainer('130px');

    items.forEach(item => {
        const wrapper = document.createElement('div');
        wrapper.className = 'flex-col-6';

        const label = createTextDiv(item.label, {
            className: 'text-secondary fs-12 whitespace-nowrap'
        });

        let input;
        if (item.type === 'checkbox') {
            input = createCheckbox({ id: item.id });
        } else {
            input = createTextbox({
                type: item.type || 'number',
                id: item.id,
                step: 'any',
                className: 'w-100 bg-base'
            });
        }

        wrapper.appendChild(label);
        wrapper.appendChild(input);
        grid.appendChild(wrapper);
    });

    group.appendChild(grid);
    return group;
}

export function createDenseInputBlockWithCopy(titleText, items) {
    const group = createPanelBlock();

    if (titleText) {
        const title = createTextDiv(titleText, {
            className: 'text-secondary fw-600 fs-12 text-uppercase mb-12'
        });
        group.appendChild(title);
    }

    const grid = createGridContainer('130px');

    items.forEach(item => {
        const wrapper = document.createElement('div');
        wrapper.className = 'flex-col-6';

        // Wrap the label and copy button in a flexible row
        const labelRow = createFlexRowBetween({ className: 'w-100' });

        const label = createTextDiv(item.label, {
            className: 'text-secondary fs-12 whitespace-nowrap'
        });
        labelRow.appendChild(label);

        if (item.copyId) {
            // Built using the official primitive, hidden by default via utility class
            const copyBtn = createCopyButton({
                id: item.copyId,
                className: 'd-none' 
            });
            
            labelRow.appendChild(copyBtn);
        }

        let input;
        if (item.type === 'checkbox') {
            input = createCheckbox({ id: item.id });
        } else {
            input = createTextbox({
                type: item.type || 'number',
                id: item.id,
                step: 'any',
                className: 'w-100 bg-base'
            });
        }

        wrapper.appendChild(labelRow);
        wrapper.appendChild(input);
        grid.appendChild(wrapper);
    });

    group.appendChild(grid);
    return group;
}
