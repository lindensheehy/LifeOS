// The internal L2 Cache (RAM)
const memoryCache = new Map();

// The Inflight Tracker (prevents duplicate network requests)
const pendingMonthFetches = new Map();

/**
 * Internal helper: Fetches a whole month (Cache Line) and coalesces duplicate requests.
 */
async function fetchAndCacheMonth(yearMonth) {
    if (pendingMonthFetches.has(yearMonth)) {
        return pendingMonthFetches.get(yearMonth);
    }

    const fetchPromise = (async () => {
        try {
            const response = await fetch(`/api/journal/month/${yearMonth}`);
            if (!response.ok) throw new Error(`Backend returned ${response.status}`);
            
            const monthData = await response.json(); 
            
            for (const [dayStr, payload] of Object.entries(monthData)) {
                const fullDateKey = `${yearMonth}-${dayStr}`;
                memoryCache.set(fullDateKey, payload);
            }
        } catch (error) {
            console.error(`Cache Miss Failed for month ${yearMonth}:`, error);
        } finally {
            pendingMonthFetches.delete(yearMonth);
        }
    })();

    pendingMonthFetches.set(yearMonth, fetchPromise);
    return fetchPromise;
}

/**
 * L1 Abstraction: Request specific sections for a day.
 */
export async function getSectionData(dateStr, requestedSections) {
    if (!memoryCache.has(dateStr)) {
        const yearMonth = dateStr.substring(0, 7); 
        
        await fetchAndCacheMonth(yearMonth);
        
        // Failsafe: Replaced { owned: {}, imported: {} } with a flat {}
        if (!memoryCache.has(dateStr)) {
            memoryCache.set(dateStr, {});
        }
    }

    const fullDay = memoryCache.get(dateStr);
    const sections = Array.isArray(requestedSections) ? requestedSections : [requestedSections];
    const result = {};

    // Completely flattened read logic
    sections.forEach(sec => {
        if (fullDay[sec] !== undefined) {
            result[sec] = fullDay[sec];
        } else {
            result[sec] = null; 
        }
    });

    return Array.isArray(requestedSections) ? result : result[requestedSections];
}

/**
 * Bulk preload data.
 */
export async function prefetchRange(startDateStr, endDateStr) {
    const startD = new Date(startDateStr);
    const endD = new Date(endDateStr);
    const monthsToFetch = new Set();
    
    let current = new Date(startD);
    current.setDate(1); 
    while (current <= endD) {
        const y = current.getFullYear();
        const m = String(current.getMonth() + 1).padStart(2, '0');
        monthsToFetch.add(`${y}-${m}`);
        current.setMonth(current.getMonth() + 1);
    }

    const fetchPromises = Array.from(monthsToFetch).map(ym => fetchAndCacheMonth(ym));
    await Promise.all(fetchPromises);
    
    console.log(`Prefetched ${monthsToFetch.size} months into L2 Cache.`);
}

/**
 * Write-Through Cache: Update local RAM immediately.
 */
export function updateCache(dateStr, section, payload) {
    // Replaced { owned: {}, imported: {} } with a flat {}
    if (!memoryCache.has(dateStr)) {
        memoryCache.set(dateStr, {});
    }
    const dayData = memoryCache.get(dateStr);
    
    // Completely flattened write logic
    dayData[section] = payload;
}

/**
 * Save a specific section to the backend.
 */
export async function saveSectionData(dateStr, section, payload) {
    updateCache(dateStr, section, payload);

    const response = await fetch(`/api/journal/${dateStr}/${section}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    if (!response.ok) throw new Error(`Failed to save ${section}`);
    return await response.json();
}