import { setDropdownData } from "./core/global.js"
import { today } from "./core/const.js"
import { prefetchRange } from "./core/cache.js"
import { formatDateStr } from "./core/util.js";

import * as heartbeat from "./core/heartbeat.js";
import * as safemode from "./core/safemode.js";
import * as calendar from "./calendar/init.js"
import DataTab from "./data_tab/DataTab.js"

(function applyEnv() {
    const isDev  = window.location.port === '5001';
    const emoji  = isDev ? '🛠️' : '🪴';
    const svg    = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">${emoji}</text></svg>`;

    document.title = isDev ? 'LifeOS - DEV BUILD' : 'LifeOS';

    let link = document.querySelector("link[rel~='icon']");
    if (!link) {
        link = document.createElement('link');
        link.rel = 'icon';
        document.head.appendChild(link);
    }
    link.type = 'image/svg+xml';
    link.href = `data:image/svg+xml,${encodeURIComponent(svg)}`;
}());

export var datatab = null;

async function main() {

    const startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
    const endDate = new Date(today.getFullYear(), today.getMonth() + 2, 0);

    try {

        const dropdownPromise = fetch('/api/dropdowns')
            .then(res => res.json())
            .then(dropdowns => setDropdownData(dropdowns));
        
        const prefetchPromise = prefetchRange(formatDateStr(startDate), formatDateStr(endDate));

        await Promise.all([dropdownPromise, prefetchPromise]);
        
    } catch (error) {
        console.error("Failed to initialize app data:", error);
    }

    heartbeat.init();
    safemode.init();
    datatab = new DataTab();
    
    calendar.init();
    
}

main();