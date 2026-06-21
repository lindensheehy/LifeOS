import { isSafeMode } from "../core/global.js";
import { MODULE_LIST } from "../modules/master.js";

export default class SafeModeManager {
    constructor(dataTabInstance) {
        // Hold a reference to the parent Facade so we can request recalculations (like dividers)
        this.dataTab = dataTabInstance;
        
        // Ensure the parking lot exists in the DOM the moment this class spins up
        this.parkingLot = this.getOrCreateParkingLot();
    }

    /**
     * Exposes the locked state to the parent DataTab.
     * We pass through the global state so DataTab doesn't have to import it directly,
     * maintaining this manager as the single source of truth for Safe Mode logic within the tab.
     */
    get isLocked() {
        return isSafeMode;
    }

    /**
     * Creates the hidden parking lot div if it doesn't exist.
     * This prevents null reference errors if the HTML file is missing the element.
     */
    getOrCreateParkingLot() {
        let lot = document.getElementById('safe-mode-parking-lot');
        if (!lot) {
            lot = document.createElement('div');
            lot.id = 'safe-mode-parking-lot';
            lot.style.display = 'none'; // Strictly hidden
            document.body.appendChild(lot);
        }
        return lot;
    }

    /**
     * Executes the physical DOM shifting when Safe Mode is toggled.
     * Triggered by the DataTab facade listening to the global 'safeModeToggled' event.
     */
    handleToggle() {
        // Pull DOM references from the parent facade
        const mainContent = this.dataTab.mainContent;
        const sectionsContainer = this.dataTab.sectionsContainer;

        if (!this.parkingLot || !sectionsContainer) {
            console.warn("SafeModeManager: Required DOM elements missing during toggle.");
            return;
        }

        if (this.isLocked) {
            // LOCKDOWN: Sweep all restricted blocks into the hidden parking lot
            mainContent.classList.add('safe-mode-active');
            
            // Note: We only query inside sectionsContainer to avoid grabbing elements outside the Data Tab
            const restrictedModules = sectionsContainer.querySelectorAll('.safe-restricted');
            restrictedModules.forEach(block => {
                this.parkingLot.appendChild(block);
            });
        } else {
            // RESTORE: Pull parked items out and guarantee perfect top-to-bottom order
            mainContent.classList.remove('safe-mode-active');
            
            MODULE_LIST.forEach(({ id }) => {
                // By selecting by ID, it finds the element regardless of if it's in the lot or the container
                const block = document.getElementById(`section-block-${id}`);
                if (block) {
                    // appendChild naturally moves the node from the parking lot back to the container,
                    // and re-sorts already-safe items to match the MODULE_LIST array order.
                    sectionsContainer.appendChild(block);
                }
            });
        }
        
        // Inform the parent Facade that the DOM has physically changed so it can fix the CSS dividers
        this.dataTab.cleanUpDividers();
    }
}