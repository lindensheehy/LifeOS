import MessageBroker from "../core/message_broker.js";
import SaveManager from "./SaveManager.js";
import ModalController from "./ModalController.js";
import SafeModeManager from "./SafeModeManager.js";
import PanelUIController from "./PanelUIController.js";
import { today, saveStatus } from "../core/const.js";
import { MODULE_LIST } from "../modules/master.js";
import { getSectionData } from "../core/cache.js";
import { setViewMode, setCurrentDayKey } from "../core/global.js";

export default class DataTab {
    
    constructor() {

        this.state = {
            currentDayKey: null,
            isViewMode: false,
        };

        this.broker = new MessageBroker();

        this.saveManager = new SaveManager(this);
        this.modalController = new ModalController(this);
        this.safeModeManager = new SafeModeManager(this);
        this.panelUI = new PanelUIController(this.broker);

        // Expose DOM refs so SafeModeManager can access them via this.dataTab
        this.mainContent = this.panelUI.mainContent;
        this.sectionsContainer = this.panelUI.sectionsContainer;

        this.broker.register('DataTab', {
            'intent_toggle_mode': () => this._handleModeToggleIntent(),
            'intent_ui_mutated': () => this.saveManager.triggerUnsaved(),
        });

        this.modalController.initModal();

        window.addEventListener('safeModeToggled', () => {
            this.broker.send('PanelUIController', 'set_safe_mode', this.safeModeManager.isLocked);
        });

        window.addEventListener('calendarTileClicked', (e) => this.handleCalendarClick(e));

        window.addEventListener('keydown', (e) => this.saveManager.handleKeyboardShortcuts(e));

        const closePanelBtn = document.getElementById('close-panel');
        if (closePanelBtn) {
            closePanelBtn.addEventListener('click', () => {
                this.panelUI.mainContent.classList.remove('panel-open');
            });
        }

        this.broker.send('PanelUIController', 'set_safe_mode', this.safeModeManager.isLocked);

    }

    // ==========================================
    // CALENDAR NAVIGATION
    // ==========================================

    async handleCalendarClick(e) {
        const { dayDiv, dateKey, dateObj } = e.detail;

        // Intercept if there are unsaved changes and user is switching to a different day
        if (this.saveManager.hasUnsavedChanges && !dayDiv.classList.contains('selected')) {
            this.modalController.interceptNavigation('switchDay', e.detail);
            return;
        }

        const previouslySelected = document.querySelector('.day.selected');
        if (previouslySelected) previouslySelected.classList.remove('selected');
        dayDiv.classList.add('selected');

        this.state.currentDayKey = dateKey;
        setCurrentDayKey(dateKey);

        this.broker.send('PanelUIController', 'select_day', dateKey);

        const todayCompare = new Date(today);
        todayCompare.setHours(0, 0, 0, 0);
        await this.setMode(dateObj < todayCompare);

        this.saveManager.finalizeStateAfterNavigation();
    }

    // ==========================================
    // MODE MANAGEMENT
    // ==========================================

    _handleModeToggleIntent() {
        if (this.safeModeManager.isLocked) return;

        if (!this.state.isViewMode && this.saveManager.hasUnsavedChanges) {
            this.modalController.showUnsavedWarning();
        } else {
            this.setMode(!this.state.isViewMode);
        }
    }

    async setMode(view) {
        this.state.isViewMode = view;
        setViewMode(view);

        this.broker.send('PanelUIController', 'set_render_mode', view);

        if (saveStatus) saveStatus.style.display = view ? 'none' : 'inline-block';

        if (this.state.currentDayKey) {
            await this._loadAndInjectData(this.state.currentDayKey);
        }
    }

    // ==========================================
    // DATA INJECTION
    // ==========================================

    async _loadAndInjectData(dateKey) {
        const keysToFetch = MODULE_LIST.map(m => m.id);
        const sectionDataList = await getSectionData(dateKey, keysToFetch);

        MODULE_LIST.forEach(({ id, module }) => {
            const nodes = this.panelUI.moduleNodes.get(id);
            const sectionData = sectionDataList[id] || {};

            module.injectEdit(sectionData);
            const hasData = module.injectView(sectionData);

            if (nodes) {
                if (nodes.errorLabel) nodes.errorLabel.style.display = 'none';

                if (this.state.isViewMode && hasData === false) {
                    nodes.block.style.display = 'none';
                } else {
                    nodes.block.style.display = 'block';
                }
            }
        });

        this.cleanUpDividers();
    }

    // ==========================================
    // DIVIDER COORDINATION
    // ==========================================

    cleanUpDividers() {
        this.panelUI.cleanUpDividers();
    }

}
