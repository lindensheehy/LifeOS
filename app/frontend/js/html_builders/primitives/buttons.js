export function createButton(text, options = {}) {
    const btn = document.createElement('button');
    btn.innerText = text;
    
    // Always attach the base class
    btn.classList.add('button');

    // Apply the specific modifier class based on the caller
    if (options.className) {
        // Split by whitespace and spread into add() so multiple classes work!
        btn.classList.add(...options.className.trim().split(/\s+/));
    }

    if (options.id) {
        btn.id = options.id;
    }

    if (options.onClick) {
        btn.addEventListener('click', options.onClick);
    }

    return btn;
}

export function createAddButton(text, onClickCallback) {
    return createButton(text, {
        className: 'add-button',
        onClick: onClickCallback
    });
}

export function createDeleteButton(onClickCallback) {
    // Defaults text to 'Delete', used in blocks.js headers
    return createButton('Delete', {
        className: 'delete-button',
        onClick: onClickCallback
    });
}

export function createTrashButton(onClickCallback) {
    // Empty text, used for dynamic rows
    const btn = createButton('', {
        className: 'trash-button',
        onClick: onClickCallback
    });

    // Inject the SVG garbage can icon
    btn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            <line x1="10" y1="11" x2="10" y2="17"></line>
            <line x1="14" y1="11" x2="14" y2="17"></line>
        </svg>
    `;

    return btn;
}

export function createCopyButton(options = {}) {
    return createButton('PREV', {
        className: `copy-button ${options.className || ''}`,
        id: options.id,
        onClick: options.onClick
    });
}
