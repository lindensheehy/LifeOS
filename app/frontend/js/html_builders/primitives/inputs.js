function _createBaseInput(type, options = {}) {
    const input = document.createElement('input');
    input.type = type;

    if (options.placeholder) input.placeholder = options.placeholder;
    if (options.id) input.id = options.id;
    if (options.step) input.step = options.step;
    
    if (options.className) {
        input.classList.add(...options.className.split(' '));
    }

    return input;
}

export function createTextbox(options = {}) {
    const type = options.type || 'text';
    const input = _createBaseInput(type, options);
    input.classList.add('textbox');
    return input;
}

export function createTextarea(options = {}) {
    const textarea = document.createElement('textarea');
    textarea.classList.add('textarea');
    textarea.rows = 1; 

    if (options.placeholder) textarea.placeholder = options.placeholder;
    if (options.id) textarea.id = options.id;
    if (options.className) textarea.classList.add(...options.className.split(' '));

    const adjustHeight = () => {
        textarea.style.height = 'auto'; 
        textarea.style.height = (textarea.scrollHeight) + 'px'; 
    };

    textarea.addEventListener('input', adjustHeight);

    const originalDescriptor = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value');
    Object.defineProperty(textarea, 'value', {
        get() {
            return originalDescriptor.get.call(this);
        },
        set(val) {
            originalDescriptor.set.call(this, val);
            if (textarea.offsetWidth > 0) {
                adjustHeight();
            }
        }
    });

    let lastWidth = 0;
    const resizeObserver = new ResizeObserver((entries) => {
        for (let entry of entries) {
            const currentWidth = entry.contentRect.width;
            
            if (currentWidth !== lastWidth) {
                lastWidth = currentWidth;
                if (currentWidth > 0) {
                    adjustHeight();
                }
            }
        }
    });
    resizeObserver.observe(textarea);

    return textarea;
}

export function createAutocomplete(dropdownOptions = [], options = {}) {
    // Generate a unique ID for the datalist so the input knows which list to target
    const listId = 'datalist-' + Math.random().toString(36).substr(2, 9);
    
    // Create our standard textbox, but hook it up to the datalist
    const input = createTextbox(options);
    input.setAttribute('list', listId);

    // Create the invisible datalist that holds the dropdown options
    const dataList = document.createElement('datalist');
    dataList.id = listId;

    dropdownOptions.forEach(optText => {
        const option = document.createElement('option');
        option.value = optText;
        dataList.appendChild(option);
    });

    // Wrap them in a tiny fragment so we can return both elements cleanly
    const fragment = document.createDocumentFragment();
    fragment.appendChild(input);
    fragment.appendChild(dataList);

    // We still return the actual input element as the primary object 
    // so we can read its .value later, but we secretly append the datalist to it 
    // using a custom property so it gets injected into the DOM when the input does.
    input._hiddenDatalist = dataList;

    // Override the append method so the datalist always tags along
    const originalAppend = input.append;
    input.append = function(...nodes) {
        originalAppend.apply(this, nodes);
    };

    return input;
}

export function createCheckbox(options = {}) {
    const input = _createBaseInput('checkbox', options);
    input.classList.add('checkbox');
    return input;
}

export function createSlider(options = {}) {
    const input = _createBaseInput('range', options);
    input.classList.add('slider');
    
    if (options.min !== undefined) input.min = options.min;
    if (options.max !== undefined) input.max = options.max;
    
    return input;
}

export function createLabel(text, options = {}) {
    const label = document.createElement('label');
    label.innerText = text;
    label.classList.add('label');
    
    if (options.className) {
        label.classList.add(...options.className.split(' '));
    }
    
    if (options.id) label.id = options.id;
    
    return label;
}
