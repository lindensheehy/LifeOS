export default class ModalController {
    constructor(dataTabInstance) {
        this.dataTab = dataTabInstance;

        // Private state replacing the old global pending variables
        this.pendingAction = null;
        this.pendingTarget = null;

        // DOM References (populated in initModal)
        this.modalOverlay = null;
        this.abandonBtn = null;
        this.saveExitBtn = null;
        this.closeXBtn = null;
    }

    /**
     * Called exactly once by DataTab.init()
     */
    initModal() {
        this.modalOverlay = document.getElementById('unsaved-modal');
        this.closeXBtn = document.getElementById('modal-close-x');
        this.abandonBtn = document.getElementById('modal-abandon');
        this.saveExitBtn = document.getElementById('modal-save-exit');

        if (!this.modalOverlay) {
            console.warn("ModalController: Modal DOM elements not found.");
            return;
        }

        if (this.closeXBtn) this.closeXBtn.addEventListener('click', () => this.hideModal());
        if (this.abandonBtn) this.abandonBtn.addEventListener('click', () => this.handleConfirm());
        if (this.saveExitBtn) this.saveExitBtn.addEventListener('click', () => this.handleSaveAndContinue());
    }

    // ==========================================
    // INTERCEPTORS (Called by DataTab)
    // ==========================================

    /**
     * Used when the user tries to toggle View/Edit mode with unsaved changes.
     */
    showUnsavedWarning() {
        this.pendingAction = 'toggleMode';
        this.pendingTarget = null;
        this.displayModal();
    }

    /**
     * Used when the user clicks a new calendar day with unsaved changes.
     * Note: DataTab should pass the full `e.detail` payload so we can resume the exact event.
     */
    interceptNavigation(action, eventPayload) {
        this.pendingAction = action;
        this.pendingTarget = eventPayload;
        this.displayModal();
    }

    // ==========================================
    // LIFECYCLE & RESOLUTION
    // ==========================================

    displayModal() {
        if (!this.dataTab.saveManager.hasUnsavedChanges) return;
        if (this.modalOverlay) {
            this.modalOverlay.style.display = 'flex';
        }
    }

    hideModal() {
        if (this.modalOverlay) {
            this.modalOverlay.style.display = 'none';
        }
        this.pendingAction = null;
        this.pendingTarget = null;
    }

    /**
     * Executes when the user clicks "Abandon changes".
     * Discards edits, clears the blocker, and resumes the pending action.
     */
    handleConfirm() {
        // Capture before hideModal() clears them
        const action = this.pendingAction;
        const target = this.pendingTarget;
        this.hideModal();

        this.dataTab.saveManager.updateEditSnapshot();
        this.dataTab.saveManager.setSaveUIState('CLEAN');

        if (action === 'switchDay') {
            this.dataTab.handleCalendarClick({ detail: target });
        } else if (action === 'toggleMode') {
            this.dataTab.setMode(true);
        }
    }

    /**
     * Executes when the user clicks "Save and exit".
     * Persists edits first, then resumes the pending action.
     */
    async handleSaveAndContinue() {
        try {
            await this.dataTab.saveManager.executeSave();

            const action = this.pendingAction;
            const target = this.pendingTarget;
            this.hideModal();

            if (action === 'switchDay') {
                this.dataTab.handleCalendarClick({ detail: target });
            } else if (action === 'toggleMode') {
                this.dataTab.setMode(true);
            }
        } catch (err) {
            // Leave modal open so the user can see the save error
        }
    }
}
