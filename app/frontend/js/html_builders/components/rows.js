import { 
    createTextbox,
    createTextarea,
    createCheckbox,
    createSlider,
    createLabel,
    createTrashButton,
    createTextSpan,
    createTextDiv,
    createViewRow,
    createWrapRow, 
    createListRow,
} from "./../primitives/index.js"

export function createNumberRow(labelText, inputId) {
    const row = document.createElement('div');
    row.className = 'eval-row'; 
    
    const input = createTextbox({ type: 'number', id: inputId, step: 'any' }); 
    
    // Using the 'label-fixed' class we created in inputs.css for alignment
    row.append(createLabel(labelText, { className: 'label-fixed' }), input);
    return row;
}

export function createCheckboxRow(labelText, inputId) {
    const row = document.createElement('div');
    row.className = 'eval-row'; 
    
    const input = createCheckbox({ id: inputId });
    
    row.append(createLabel(labelText, { className: 'label-fixed' }), input);
    return row;
}

export function createSliderRow(labelText, metricKey) {
    const row = document.createElement('div');
    row.className = 'eval-row';

    const slider = createSlider({ 
        min: '0', 
        max: '10', 
        step: '1', 
        className: 'eval-slider' 
    });
    slider.dataset.metric = metricKey;

    // Utilizing the minWidth property you already built into text.js!
    const valueDisplay = createTextSpan("5", { 
        className: 'eval-value fw-600 ml-10 text-monospace',
        minWidth: '24px' 
    }); 

    const updateColors = (val) => {
        const pct = (val / 10) * 100;
        slider.style.setProperty('--slider-pct', `${pct}%`);

        valueDisplay.classList.remove('text-accent-red', 'text-accent-orange', 'text-accent-green', 'text-accent-emerald', 'text-secondary');
        slider.classList.remove('slider-red', 'slider-orange', 'slider-green', 'slider-emerald');

        if (val <= 2) {
            valueDisplay.classList.add('text-accent-red');
            slider.classList.add('slider-red');
        } else if (val <= 5) {
            valueDisplay.classList.add('text-accent-orange');
            slider.classList.add('slider-orange');
        } else if (val <= 7) {
            valueDisplay.classList.add('text-accent-green');
            slider.classList.add('slider-green');
        } else {
            valueDisplay.classList.add('text-accent-emerald');
            slider.classList.add('slider-emerald');
        }
    };

    slider.addEventListener('input', (e) => {
        const val = parseInt(e.target.value, 10);
        valueDisplay.innerText = val;
        updateColors(val);
    });

    slider._updateColors = updateColors;

    row.append(createLabel(labelText, { className: 'label-fixed' }), slider, valueDisplay);
    return row;
}

export function createEventRow(time = "", description = "") {
    const row = document.createElement('div');
    row.className = 'dynamic-row flex-row-8 mb-8'; 
    row.style.alignItems = 'flex-start';

    const timeInput = createTextbox({ 
        type: 'number', 
        placeholder: 'Time', 
        className: 'event-time-input w-70' 
    });
    timeInput.value = time;

    const descInput = createTextarea({ 
        placeholder: 'What happened?', 
        className: 'event-desc-input flex-grow-1' 
    });
    descInput.value = description;

    const deleteBtn = createTrashButton(() => { 
        row.remove(); 
    });

    row.append(timeInput, descInput, deleteBtn);
    return row;
}

export function createGymSetRow(weight = "", reps = "") {
    const row = document.createElement('div');
    row.className = 'gym-set-row flex-row-center-8 mb-6'; 

    const weightInput = createTextbox({ 
        type: 'number', 
        placeholder: 'lbs', 
        className: 'gym-weight-input w-70', 
        step: 'any' 
    });
    weightInput.value = weight;

    const repsInput = createTextbox({ 
        type: 'number', 
        placeholder: 'reps', 
        className: 'gym-reps-input w-70' 
    });
    repsInput.value = reps;

    const deleteBtn = createTrashButton(() => { 
        row.remove(); 
    });

    row.append(weightInput, repsInput, deleteBtn);
    return row;
}

export function createCodingDetailRow(detailText = "") {
    const row = document.createElement('div');
    row.className = 'coding-detail-row flex-row-8 mb-6';
    row.style.alignItems = 'flex-start';

    const detailInput = createTextarea({ 
        placeholder: 'Detail', 
        className: 'coding-detail-input flex-grow-1' 
    });
    detailInput.value = detailText;

    const deleteBtn = createTrashButton(() => { 
        row.remove(); 
    });

    row.append(detailInput, deleteBtn);
    return row;
}

export function createKeyValueViewRow(labelText, valueText, valueColorClass) {
    const row = createViewRow();

    const labelSpan = createTextSpan(labelText, { 
        className: 'text-secondary fw-500 text-capitalize' 
    });

    // valueColorClass expects a utility class like 'text-accent-blue'
    const valSpan = createTextSpan(valueText, { 
        className: `${valueColorClass} fw-700` 
    });

    row.appendChild(labelSpan);
    row.appendChild(valSpan);
    
    return row;
}

export function createEventViewRow(timeText, descriptionText) {
    const row = createListRow();

    const timeSpan = createTextSpan(timeText, { 
        className: 'text-secondary fw-600 text-monospace w-50' 
    });

    const descDiv = createTextDiv(descriptionText, { 
        className: 'text-primary text-paragraph' 
    });

    row.appendChild(timeSpan);
    row.appendChild(descDiv);
    
    return row;
}

export function createDenseDataWrapRow(titleText, items) {
    const row = createWrapRow();

    if (titleText) {
        const title = createTextDiv(titleText, { 
            className: 'text-secondary fw-600 fs-12 text-uppercase mb-6 w-100' 
        });
        row.appendChild(title);
    }

    items.forEach(item => {
        const wrapper = document.createElement('div');
        wrapper.className = 'flex-row-center-6 fs-14';

        const label = createTextSpan(item.label + ':', { className: 'text-secondary' });
        const value = createTextSpan('--', { className: 'text-primary fw-500', id: item.id });

        wrapper.appendChild(label);
        wrapper.appendChild(value);
        row.appendChild(wrapper);
    });

    return row;
}

export function createLabeledInputRow(labelText, inputId, placeholder) {
    const row = document.createElement('div');
    row.className = 'labeled-input-row';

    const label = createLabel(labelText);
    
    const input = createTextbox({ 
        id: inputId, 
        placeholder: placeholder, 
        className: 'flex-grow-1' 
    });

    row.appendChild(label);
    row.appendChild(input);
    return row;
}

export function createGymMovementViewRow(nameText, setsText) {
    const row = createViewRow(); 

    const nameSpan = createTextSpan(nameText, { 
        className: 'text-primary fw-600 text-capitalize' 
    });

    const setsSpan = createTextSpan(setsText, { 
        className: 'text-secondary text-monospace' 
    });

    row.appendChild(nameSpan);
    row.appendChild(setsSpan);
    
    return row;
}

export function createMajorEventRow(description = "") {
    const row = document.createElement('div');
    row.className = 'major-event-row flex-row-center-8 mb-8'; 

    const descInput = createTextbox({ 
        placeholder: 'What happened?', 
        className: 'major-event-input flex-grow-1' 
    });
    descInput.value = description;

    const deleteBtn = createTrashButton(() => { 
        row.remove(); 
    });

    row.append(descInput, deleteBtn);
    return row;
}
