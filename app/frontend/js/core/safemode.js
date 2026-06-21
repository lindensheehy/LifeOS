import { isSafeMode, setSafeMode } from "./global.js";

export function init() {
    // 1. The Secret Keybind (Ctrl + Shift + Alt + P)
    window.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.shiftKey && e.altKey && e.code === 'KeyP') {
            e.preventDefault();
            setSafeMode(!isSafeMode);
        }
    });

    // 2. The 1-Minute Idle Timeout
    let idleTimer;
    const resetIdleTimer = () => {
        clearTimeout(idleTimer);
        // Only start the timer if we are currently unlocked
        if (!isSafeMode) {
            idleTimer = setTimeout(() => {
                setSafeMode(true);
            }, 60000); // 60 seconds
        }
    };

    // Attach to all standard interaction events
    const interactionEvents = ['mousemove', 'mousedown', 'wheel', 'touchstart', 'keydown'];
    interactionEvents.forEach(evt => {
        window.addEventListener(evt, resetIdleTimer, { passive: true });
    });

    // 3. The Focus Loss Fallback
    document.addEventListener('visibilitychange', () => {
        if (document.hidden && !isSafeMode) {
            setSafeMode(true);
        }
    });

    window.addEventListener('blur', () => {
        if (!isSafeMode) {
            setSafeMode(true);
        }
    });

    // Tie the timer loop into the state toggle
    window.addEventListener('safeModeToggled', () => {
        resetIdleTimer();
    });
    
    // Kickoff initial timer
    resetIdleTimer(); 

    window.dispatchEvent(new CustomEvent('safeModeToggled', { detail: isSafeMode }));
}