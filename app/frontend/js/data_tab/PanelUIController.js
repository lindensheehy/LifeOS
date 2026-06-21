import { MODULE_LIST } from "../modules/master.js";
import { createDivider } from "../html_builders/primitives/index.js";

const fullMonthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

export default class PanelUIController {
    
    constructor(broker) {
        
        this.broker = broker;

        this.modeToggleBtn = document.getElementById('mode-toggle-btn');
        this.mainContent = document.querySelector('.main-content');
        this.panelEventsWrapper = document.getElementById('panel-events-wrapper');
        this.panelDateHeader = document.getElementById("panel-date");
        this.sectionsContainer = document.getElementById('sections-container');
        this.parkingLot = document.getElementById('safe-mode-parking-lot');

        // Structure: Map<moduleId, { block, edit, view, divider, isRestricted }>
        this.moduleNodes = new Map();

        this.broker.register('PanelUIController', {
            'set_render_mode': (isViewMode) => this.updateModeUI(isViewMode),
            'set_safe_mode': (isLocked) => this.updateSafeModeUI(isLocked),
            'select_day': (date) => this.handleDaySelection(date)
        });

        this.buildSectionsUI();
        this.setupNativeListeners();

    }

    // ==========================================
    // INITIALIZATION & LISTENERS
    // ==========================================

    setupNativeListeners() {
        if (this.modeToggleBtn) {
            this.modeToggleBtn.addEventListener('click', () => {
                this.broker.send('DataTab', 'intent_toggle_mode');
            });
        }

        if (this.panelEventsWrapper) {
            this.panelEventsWrapper.addEventListener('input', () => this.broker.send('DataTab', 'intent_ui_mutated'));
            this.panelEventsWrapper.addEventListener('change', () => this.broker.send('DataTab', 'intent_ui_mutated'));
        }
    }

    // ==========================================
    // DOM GENERATION (Private)
    // ==========================================

    buildSectionsUI() {
        MODULE_LIST.forEach(({ id, module, showInSafeMode }) => {
            const editContainer = module.renderEdit();
            let viewContainer = module.renderView();

            if (!editContainer && !viewContainer) return;

            const block = document.createElement('div');
            block.className = 'section-block';
            // We can keep the ID for CSS styling, but we will never query by it again
            block.id = `section-block-${id}`; 
            
            const headerWrapper = document.createElement('div');
            headerWrapper.className = 'section-header';
            
            const title = document.createElement('span');
            title.innerText = id.replace('_', ' '); 
            
            const errorLabel = document.createElement('span');
            errorLabel.className = 'section-error';
            errorLabel.id = `error-${id}`;
            errorLabel.innerText = "Invalid JSON syntax";
            errorLabel.style.display = 'none';
            
            headerWrapper.appendChild(title);
            headerWrapper.appendChild(errorLabel);
            block.appendChild(headerWrapper);

            if (editContainer) {
                editContainer.classList.add('mode-edit-container');
                block.appendChild(editContainer);
            }

            if (!viewContainer) {
                viewContainer = document.createElement('div');
                viewContainer.innerText = "View mode not yet implemented.";
                viewContainer.style.color = 'var(--text-secondary)';
                viewContainer.style.fontStyle = 'italic';
                viewContainer.style.padding = '10px';
            }
            viewContainer.classList.add('mode-view-container');

            block.appendChild(viewContainer);

            const divider = createDivider();
            block.appendChild(divider);

            this.sectionsContainer.appendChild(block);

            // CACHE DIRECT MEMORY REFERENCES
            this.moduleNodes.set(id, {
                block: block,
                edit: editContainer,
                view: viewContainer,
                divider: divider,
                errorLabel: errorLabel,
                isRestricted: !showInSafeMode
            });
        });
    }

    // ==========================================
    // UI MUTATIONS (Commanded by Broker)
    // ==========================================

    updateModeUI(isViewMode) {
        if (this.modeToggleBtn) {
            this.modeToggleBtn.innerText = isViewMode ? "Edit" : "View";
        }

        // Zero DOM traversal. Just rip through the memory references.
        this.moduleNodes.forEach((nodes) => {
            if (nodes.edit) {
                isViewMode ? nodes.edit.classList.add('mode-hidden') : nodes.edit.classList.remove('mode-hidden');
            }
            if (nodes.view) {
                isViewMode ? nodes.view.classList.remove('mode-hidden') : nodes.view.classList.add('mode-hidden');
            }
        });
    }

    updateSafeModeUI(isLocked) {
        if (!this.parkingLot || !this.sectionsContainer) return;

        if (isLocked) {
            this.mainContent.classList.add('safe-mode-active');
        } else {
            this.mainContent.classList.remove('safe-mode-active');
        }

        MODULE_LIST.forEach(({ id }) => {
            const nodes = this.moduleNodes.get(id);
            if (!nodes) return;

            const target = (isLocked && nodes.isRestricted) ? this.parkingLot : this.sectionsContainer;
            target.appendChild(nodes.block);
        });
        
        this.cleanUpDividers();
    }

    handleDaySelection(date) {
        if (this.panelDateHeader && date) {
            const [year, month, day] = date.split('-');
            const dateObj = new Date(year, parseInt(month) - 1, day);
            this.panelDateHeader.innerText = `${fullMonthNames[dateObj.getMonth()]} ${dateObj.getDate()}, ${dateObj.getFullYear()}`;
        }
        
        this.mainContent.classList.add('panel-open');
    }

    cleanUpDividers() {
        const visibleNodes = [];

        MODULE_LIST.forEach(({ id }) => {
            const nodes = this.moduleNodes.get(id);
            if (!nodes) return;
            if (nodes.block.parentElement === this.sectionsContainer && nodes.block.style.display !== 'none') {
                visibleNodes.push(nodes);
            }
        });

        visibleNodes.forEach((nodes, index) => {
            nodes.divider.style.display = index < visibleNodes.length - 1 ? 'block' : 'none';
        });
    }
}