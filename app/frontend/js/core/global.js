export let dropdownData = {};
export function setDropdownData(val) { dropdownData = val; }

export let currentDayKey = null;
export function setCurrentDayKey(val) { currentDayKey = val; }

export let isViewMode = false;
export function setViewMode(val) { isViewMode = val; }

export let hasUnsavedChanges = false;
export function setHasUnsavedChanges(val) { hasUnsavedChanges = val; }

export let pendingAction = null;
export function setPendingAction(val) { pendingAction = val; }

export let pendingTarget = null;
export function setPendingTarget(val) { pendingTarget = val; }

// --- SAFE MODE STATE ---
export let isSafeMode = true; // DEFAULT DENY POSTURE

export function setSafeMode(val) {
    if (isSafeMode !== val) {
        isSafeMode = val;
        // Dispatch an event so independent modules (like the data tab) can re-render
        window.dispatchEvent(new CustomEvent('safeModeToggled', { detail: val }));
    }
}