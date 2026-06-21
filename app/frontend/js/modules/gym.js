import { 
    createContainer,
    createContainerFlex, 
    createAddButton,
    createTextDiv,
    createTextSpan,
    createLabel,
    createAutocomplete
} from "./../html_builders/primitives/index.js"
import { 
    createGymMovementBlock,
    createGymMovementViewRow,
    createLabeledInputRow
} from "./../html_builders/components/index.js"
import { dropdownData } from "../core/global.js";

function localRenderEdit() {
    const container = createContainerFlex({ 
        id: 'editor-gym', 
        className: 'gym-container' 
    });
    
    const dayRow = document.createElement('div');
    dayRow.className = 'labeled-input-row';
    
    const dayLabel = createLabel('Target Day:');
    const dayInput = createAutocomplete(dropdownData.gym_days || [], { 
        id: 'gym-day-input', 
        placeholder: 'e.g. arms, rest', 
        className: 'flex-grow-1' 
    });
    
    dayRow.append(dayLabel, dayInput, dayInput._hiddenDatalist);
    container.appendChild(dayRow);
    
    const blocksContainer = createContainer({ 
        id: 'gym-blocks-container' 
    });
    
    const addMovementBtn = createAddButton('+ Add Movement', () => {
        blocksContainer.appendChild(createGymMovementBlock("", [], dropdownData.gym_movements || []));
        blocksContainer.dispatchEvent(new Event('input', { bubbles: true }));
    });

    container.appendChild(blocksContainer);
    container.appendChild(addMovementBtn);

    return container;
}

function localRenderView() {
    const container = createContainerFlex({ 
        id: 'view-gym', 
        className: 'gym-container' 
    });

    // 1. Removed the flex-center. Let it left-align naturally!
    const dayWrapper = createContainer({ className: 'mb-10' });

    const dayDisplay = createTextSpan('', { 
        id: 'view-gym-day', 
        className: 'panel-badge' // 2. Use the new balanced class
    });
    
    dayWrapper.appendChild(dayDisplay);

    const movementsContainer = createContainer({ 
        id: 'view-gym-movements',
        className: 'flex-col-8' 
    });

    container.appendChild(dayWrapper);
    container.appendChild(movementsContainer);

    return container;
}

function localExtract() {
    const container = document.getElementById('editor-gym');
    if (!container) return { "day": "" };

    const dayInput = document.getElementById('gym-day-input');
    const dayVal = dayInput ? dayInput.value.trim() : '';

    const blocksContainer = container.querySelector('#gym-blocks-container');
    const blocks = blocksContainer ? blocksContainer.querySelectorAll('.gym-movement-block') : [];
    const movementsData = [];

    blocks.forEach(block => {
        const movementName = block.querySelector('.gym-movement-name').value.trim();
        const setRows = block.querySelectorAll('.gym-set-row');
        const setsData = [];

        setRows.forEach(row => {
            const weightVal = row.querySelector('.gym-weight-input').value;
            const repsVal = row.querySelector('.gym-reps-input').value;
            
            if (weightVal !== "" || repsVal !== "") {
                setsData.push({
                    "weight": weightVal === "" ? 0 : parseFloat(weightVal),
                    "reps": repsVal === "" ? 0 : parseInt(repsVal, 10)
                });
            }
        });

        if (movementName || setsData.length > 0) {
            movementsData.push({
                "movement": movementName,
                "sets": setsData
            });
        }
    });

    const gymPayload = { "day": dayVal };
    if (movementsData.length > 0) {
        gymPayload["movements"] = movementsData;
    }

    return gymPayload;
}

function localInjectEdit(data) {
    data = data || {};
    
    const dayInput = document.getElementById('gym-day-input');
    const blocksContainer = document.getElementById('gym-blocks-container');
    
    if (dayInput) dayInput.value = data.day || "";
    if (blocksContainer) {
        blocksContainer.innerHTML = '';
        if (data.movements && Array.isArray(data.movements)) {
            data.movements.forEach(m => {
                blocksContainer.appendChild(createGymMovementBlock(m.movement, m.sets, dropdownData.gym_movements || []));
            });
        }
    }
}

function localInjectView(data) {
    data = data || {};

    const viewDay = document.getElementById('view-gym-day');
    const viewMovements = document.getElementById('view-gym-movements');

    const dayText = data.day ? data.day.trim() : '';
    const isRestDay = dayText.toLowerCase() === 'rest';
    const isEmpty = dayText === '';

    if (viewDay) {
        if (isEmpty || isRestDay) {
            viewDay.innerText = isRestDay ? 'REST' : 'NO DATA';
            // 3. Swapped panel-badge-lg to panel-badge
            viewDay.className = 'panel-badge day-badge badge-gym badge-gym-rest'; 
        } else {
            viewDay.innerText = dayText;
            const safeClass = dayText.toLowerCase().replace(/\s+/g, '-');
            // 3. Swapped panel-badge-lg to panel-badge
            viewDay.className = `panel-badge day-badge badge-gym badge-gym-${safeClass}`;
        }
    }

    if (viewMovements) {
        viewMovements.innerHTML = ''; 
        
        if (data.movements && Array.isArray(data.movements) && data.movements.length > 0) {
            data.movements.forEach(m => {
                let setsString = '--';
                if (m.sets && Array.isArray(m.sets)) {
                    const setStrings = m.sets.map(s => {
                        const w = s.weight ? s.weight : 0;
                        const r = s.reps ? s.reps : 0;
                        return w > 0 ? `${w}x${r}` : `${r} reps`;
                    });
                    setsString = setStrings.join(', ');
                }
                const cleanName = m.movement || "Unknown Movement";
                viewMovements.appendChild(createGymMovementViewRow(cleanName, setsString));
            });
        } else if (!isRestDay && !isEmpty) {
            viewMovements.appendChild(
                createTextDiv('No movements recorded.', { className: 'text-secondary fs-14 text-italic' })
            );
        }
    }

    if (isRestDay || isEmpty) {
        return false;
    }
    return true;
}

export const GymModule = {
    renderEdit: localRenderEdit,
    renderView: localRenderView,
    extract: localExtract,
    injectEdit: localInjectEdit,
    injectView: localInjectView,
};
