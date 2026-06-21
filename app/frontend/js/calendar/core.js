import { tileDataObserver } from "./observers.js";
import { today } from "../core/const.js";
import { getSectionData } from "../core/cache.js";
import { parseDateStr, formatDateStr } from "../core/util.js";

const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

let todayElement = null;
export function setTodayElement(val) { todayElement = val; }


export function createDayElement(dateInput) {
    
    let dateObj, dateKey;
    if (dateInput instanceof Date) {
        dateObj = dateInput;
        dateKey = formatDateStr(dateObj); // Derive string
    } else {
        dateKey = dateInput;
        dateObj = parseDateStr(dateKey); // Derive object
    }
    
    const dayDiv = document.createElement("div");
    dayDiv.classList.add("day");
    dayDiv.dataset.year = dateObj.getFullYear();
    dayDiv.dataset.dateKey = dateKey;
    
    if (dateObj.getDay() === 0 || dateObj.getDay() === 6) {
        dayDiv.classList.add("weekend");
    }

    const numSpan = document.createElement("span");
    numSpan.classList.add("day-number");
    numSpan.innerText = `${monthNames[dateObj.getMonth()]} ${dateObj.getDate()}`;
    dayDiv.appendChild(numSpan);

    if (dateKey === formatDateStr(today)) {
        dayDiv.classList.add("today");
        setTodayElement(dayDiv);

        const progressContainer = document.createElement('div');
        progressContainer.className = 'day-progress-container';
        
        const progressBar = document.createElement('div');
        progressBar.className = 'day-progress-bar';
        
        progressContainer.appendChild(progressBar);
        dayDiv.appendChild(progressContainer);

        const updateProgress = () => {
            const now = new Date();
            const totalMinutesInDay = 24 * 60;
            const currentMinutes = (now.getHours() * 60) + now.getMinutes();
            progressBar.style.width = `${(currentMinutes / totalMinutesInDay) * 100}%`;
        };

        updateProgress();
        setInterval(updateProgress, 60000);
    }
    
    // --- THE FIX: EVENT DRIVEN ARCHITECTURE ---
    // Instead of controlling the data tab, we just broadcast a global event.
    dayDiv.addEventListener("click", () => {
        window.dispatchEvent(new CustomEvent('calendarTileClicked', {
            detail: { dayDiv, dateKey, dateObj }
        }));
    });

    tileDataObserver.observe(dayDiv);

    return dayDiv;
}

export async function populateTileUI(dayDiv, dateKey) {
    const existingScore = dayDiv.querySelector('.day-score');
    if (existingScore) existingScore.remove();
    
    const existingBadges = dayDiv.querySelector('.day-badges');
    if (existingBadges) existingBadges.remove();

    const existingProfit = dayDiv.querySelector('.day-profit');
    if (existingProfit) existingProfit.remove();

    const dayData = await getSectionData(dateKey, ["evaluation", "coding", "gym", "transactions"]);
    if (!dayData) return;

    if (dayData.transactions && Array.isArray(dayData.transactions) && dayData.transactions.length > 0) {
        const netProfit = dayData.transactions.reduce((sum, tx) => sum + tx.amount, 0);
        
        const profitSpan = document.createElement("span");
        profitSpan.className = "day-profit fw-600 fs-13 text-monospace";
        
        const isPositive = netProfit > 0;
        const prefix = isPositive ? "+" : (netProfit < 0 ? "-" : "");
        const formattedAmount = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Math.abs(netProfit));
        
        profitSpan.innerText = `${prefix}${formattedAmount}`;
        
        if (netProfit > 0) {
            profitSpan.classList.add("text-accent-green");
        } else if (netProfit < 0) {
            profitSpan.classList.add("text-accent-red");
        } else {
            profitSpan.classList.add("text-secondary");
        }
        
        dayDiv.appendChild(profitSpan);
    }

    if (dayData.evaluation) {
        const vals = Object.values(dayData.evaluation);
        if (vals.length > 0) {
            const avg = vals.reduce((a, b) => a + b, 0) / vals.length;
            const scoreSpan = document.createElement("span");
            scoreSpan.className = "day-score";
            
            scoreSpan.innerText = avg % 1 === 0 ? avg : avg.toFixed(1);

            if (avg <= 2) {
                scoreSpan.classList.add("score-low");       
            } else if (avg <= 5) {
                scoreSpan.classList.add("score-mid");       
            } else if (avg <= 7) {
                scoreSpan.classList.add("score-high");      
            } else {
                scoreSpan.classList.add("score-emerald");   
            }
            dayDiv.appendChild(scoreSpan);
        }
    }

    const badgesContainer = document.createElement("div");
    badgesContainer.className = "day-badges";

    if (dayData.coding && Array.isArray(dayData.coding)) {
        const totalHours = dayData.coding.reduce((sum, proj) => {
            const hrs = parseFloat(proj["time spent"]);
            return sum + (isNaN(hrs) ? 0 : hrs);
        }, 0);

        if (totalHours > 0) {
            const codingBadge = document.createElement("span");
            codingBadge.className = "day-badge badge-coding";
            codingBadge.innerText = `</> ${totalHours}h`;
            badgesContainer.appendChild(codingBadge);
        }
    }

    if (dayData.gym && dayData.gym.day && dayData.gym.day.trim() !== "") {
        const gymDay = dayData.gym.day.trim().toLowerCase();
        const gymBadge = document.createElement("span");
        
        const safeClass = gymDay.replace(/\s+/g, '-');
        gymBadge.className = `day-badge badge-gym badge-gym-${safeClass}`;
        gymBadge.innerText = gymDay;
        badgesContainer.appendChild(gymBadge);
    }

    if (badgesContainer.children.length > 0) {
        dayDiv.appendChild(badgesContainer);
    }
}
