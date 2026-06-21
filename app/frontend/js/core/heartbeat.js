import { 
    createContainer, 
    createTextDiv 
} from "../html_builders/primitives/index.js";

const PING_INTERVAL_MS = 8000; // Check every 8 seconds
const TIMEOUT_MS = 4000;       // Max wait time for a response
const MAX_STRIKES = 3;

let strikeCount = 0;
let isOffline = false;
let overlayElement = null;

function buildOverlay() {
    const overlay = createContainer({ id: 'server-down-overlay' });
    
    // Combining your utility classes with our specific modal class
    const modal = createContainer({ 
        className: 'panel-block server-down-modal flex-center flex-col-8' 
    });

    modal.appendChild(createTextDiv('SERVER OFFLINE', { 
        className: 'text-accent-red fw-700 fs-18 text-uppercase' 
    }));
    
    modal.appendChild(createTextDiv('Waiting for network connection...', { 
        className: 'text-secondary fs-14' 
    }));

    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    
    return overlay;
}

function handleFailure() {
    strikeCount++;
    if (strikeCount >= MAX_STRIKES && !isOffline) {
        isOffline = true;
        overlayElement.classList.add('active');
    }
}

function handleSuccess() {
    strikeCount = 0;
    if (isOffline) {
        isOffline = false;
        overlayElement.classList.remove('active');
    }
}

async function pingServer() {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

        // Replace this endpoint with whatever tiny route you setup in Flask
        const response = await fetch('/api/heartbeat', { 
            method: 'GET',
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);

        if (response.ok) {
            handleSuccess();
        } else {
            handleFailure();
        }
    } catch (err) {
        // Catches network errors (server down) or AbortController timeouts
        handleFailure();
    }
}

export function init() {
    overlayElement = buildOverlay();
    
    // Run the first check immediately, then start the loop
    pingServer();
    setInterval(pingServer, PING_INTERVAL_MS);
}