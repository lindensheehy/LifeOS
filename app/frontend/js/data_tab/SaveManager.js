import { currentDayKey, isViewMode } from "../core/global.js";
import { saveStatus } from "../core/const.js";
import { MODULE_LIST } from "../modules/master.js";
import { saveSectionData } from "../core/cache.js";
import { populateTileUI } from "../calendar/core.js";

export default class SaveManager {
    constructor(dataTabInstance) {
        this.dataTab = dataTabInstance;
        
        // Single source of truth for unsaved changes in the application
        this._hasUnsavedChanges = false;
        this.editSnapshot = {}; 
    }

    // Expose the boolean safely to the facade and ModalController.
    // Also cross-checks the status pill: if the pill shows "No Changes", the answer is always false
    // regardless of the internal flag (guards against the flag getting set spuriously after a save).
    get hasUnsavedChanges() {
        if (saveStatus && !saveStatus.classList.contains('unsaved')) return false;
        return this._hasUnsavedChanges;
    }

    // ==========================================
    // STATE & UI UPDATES
    // ==========================================

    /**
     * Triggered by 'input' and 'change' events delegated from DataTab.
     */
    triggerUnsaved(e) {
        // Optimization: Ignore inputs if we are in view mode or already marked as unsaved
        if (isViewMode || this._hasUnsavedChanges) return;

        this._hasUnsavedChanges = true;
        this.setSaveUIState('UNSAVED');
    }

    setSaveUIState(state) {
        if (!saveStatus) return;

        switch (state) {
            case 'CLEAN':
                saveStatus.innerText = "No Changes";
                saveStatus.classList.remove('unsaved');
                break;
            case 'UNSAVED':
                saveStatus.innerText = "Unsaved Changes";
                saveStatus.classList.add('unsaved');
                break;
            case 'ERROR':
                saveStatus.innerText = "Save failed!";
                saveStatus.classList.add('unsaved');
                break;
        }
    }

    updateEditSnapshot() {
        this._hasUnsavedChanges = false;
        // If you were doing deep-equality checks against a snapshot object before,
        // you would populate this.editSnapshot here.
        // For now, resetting the boolean is the critical step.
    }

    finalizeStateAfterNavigation() {
        this.updateEditSnapshot();
        this.setSaveUIState('CLEAN');
    }

    // ==========================================
    // KEYBOARD INTERCEPTION
    // ==========================================

    handleKeyboardShortcuts(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault(); // Stop the browser's "Save Page" dialog
            
            // Prevent saving if locked in View Mode
            if (isViewMode) return; 
            
            this.executeSave();
        }
    }

    // ==========================================
    // CORE EXECUTOR
    // ==========================================

    /**
     * Replaces the old saveCurrentDayData() function.
     * Iterates modules, validates data, handles UI error states, and pushes to cache.
     */
    executeSave() {
        if (!currentDayKey) return Promise.resolve(); 

        let hasError = false;
        const savePromises = []; 
        
        MODULE_LIST.forEach(({ id, module }) => {
            const errorLabel = document.getElementById(`error-${id}`);
            const inputContainer = document.getElementById(`editor-${id}`);
            
            try {
                // Extract blindly. The module contract handles its own formatting.
                const sectionPayload = module.extract();
                
                // Clear previous error states
                if (errorLabel) errorLabel.style.display = 'none';
                if (inputContainer && inputContainer.tagName === 'TEXTAREA') {
                    inputContainer.style.border = "1px solid transparent";
                }

                if (sectionPayload !== null) {
                    savePromises.push(saveSectionData(currentDayKey, id, sectionPayload));
                }
            } catch (err) {
                // Validation failure inside the module's extract() function
                hasError = true;
                if (errorLabel) errorLabel.style.display = 'block';
                if (inputContainer) inputContainer.style.border = "1px solid var(--accent-red)";
            }
        });

        if (hasError) return Promise.reject("Validation Error");

        // UI Update: Optimistically show saving, or wait for promise resolution
        return Promise.all(savePromises)
            .then(() => {
                this.setSaveUIState('CLEAN');
                this.updateEditSnapshot(); 

                // Tell the calendar to update its preview UI for the current day
                const selectedTile = document.querySelector('.day.selected');
                if (selectedTile) {
                    populateTileUI(selectedTile, currentDayKey);
                }
            })
            .catch(err => {
                console.error("SaveManager: Failed to save to cache", err);
                this.setSaveUIState('ERROR');
            });
    }
}