// Private base builder - NOT exported!
function _createBaseText(tag, text = "", options = {}) {
    const el = document.createElement(tag);
    el.innerText = text;

    if (options.id) el.id = options.id;

    // Apply utility classes (e.g., 'text-secondary fw-600 text-uppercase')
    if (options.className) {
        el.classList.add(...options.className.split(' '));
    }

    // Keep minWidth as a dynamic inline style since it's a layout edge-case
    if (options.minWidth) el.style.minWidth = options.minWidth;

    return el;
}

export function createTextSpan(text, options = {}) {
    return _createBaseText('span', text, options);
}

export function createTextDiv(text, options = {}) {
    return _createBaseText('div', text, options);
}