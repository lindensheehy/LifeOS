import { saveStatus } from '../../core/const.js';
import { setHasUnsavedChanges, isViewMode } from '../../core/global.js';

export function createDivider() {
    const divider = document.createElement('div');
    divider.className = 'section-divider';
    return divider;
}

function _createBaseDiv(options = {}) {
    const div = document.createElement('div');
    
    if (options.id) div.id = options.id;
    if (options.className) div.classList.add(...options.className.split(' '));
    
    return div;
}

export function createContainer(options = {}) {
    return _createBaseDiv(options);
}

export function createContainerFlex(options = {}) {
    const div = _createBaseDiv(options);
    div.classList.add('container-flex');
    return div;
}

export function createViewBlock(options = {}) {
    const div = _createBaseDiv(options);
    div.classList.add('view-block');
    return div;
}

export function createFlexRowBetween(options = {}) {
    const div = _createBaseDiv(options);
    div.classList.add('flex-row-between');
    return div;
}

export function createViewRow(options = {}) {
    const div = _createBaseDiv(options);
    div.classList.add('view-row');
    return div;
}

export function createListRow(options = {}) {
    const div = _createBaseDiv(options);
    div.classList.add('list-row');
    return div;
}

export function createPanelBlock(options = {}) {
    const div = _createBaseDiv(options);
    div.classList.add('panel-block');
    return div;
}

export function createGridContainer(minColWidth = '130px', options = {}) {
    const div = _createBaseDiv(options);
    div.classList.add('grid-container');
    div.style.gridTemplateColumns = `repeat(auto-fill, minmax(${minColWidth}, 1fr))`;
    return div;
}

export function createWrapRow(options = {}) {
    const div = _createBaseDiv(options);
    div.classList.add('wrap-row');
    return div;
}
