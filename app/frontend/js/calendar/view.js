import { 
    ROW_HEIGHT, 
    ANCHOR_SCROLL, 
    contentContainer,
    viewport
} from "./internal.js";
import { createDayElement } from "./core.js"; 
import { today, yearDisplay, btnTodayTop, btnTodayBottom } from "../core/const.js";

let currentStartWeek = null;
let currentEndWeek = null;

const todayDate = new Date(today);
const todayDayOfWeek = todayDate.getDay();
const anchorSunday = new Date(todayDate);
anchorSunday.setDate(todayDate.getDate() - todayDayOfWeek);
anchorSunday.setHours(0, 0, 0, 0);

const BUFFER_ABOVE = 4;
const BUFFER_BELOW = 8;

export function renderVirtualViewport(scrollTop) {

    const deltaY = scrollTop - ANCHOR_SCROLL;
    const currentTopWeekIndex = Math.floor(deltaY / ROW_HEIGHT);
    const startWeekOffset = currentTopWeekIndex - BUFFER_ABOVE;
    const endWeekOffset = currentTopWeekIndex + BUFFER_BELOW;

    if (currentStartWeek === startWeekOffset && currentEndWeek === endWeekOffset) return;

    const fragment = document.createDocumentFragment();

    for (let week = startWeekOffset; week <= endWeekOffset; week++) {
        for (let day = 0; day < 7; day++) {

            const cellDate = new Date(anchorSunday);
            cellDate.setDate(anchorSunday.getDate() + (week * 7) + day);
            
            const dayDiv = createDayElement(cellDate);
            fragment.appendChild(dayDiv);

        }
    }

    contentContainer.innerHTML = '';
    contentContainer.appendChild(fragment);

    const containerOffsetTop = ANCHOR_SCROLL + (startWeekOffset * ROW_HEIGHT);
    contentContainer.style.transform = `translateY(${containerOffsetTop}px)`;

    currentStartWeek = startWeekOffset;
    currentEndWeek = endWeekOffset;

    // --- YEAR LABEL LOGIC ---
    const topVisibleDate = new Date(anchorSunday);
    topVisibleDate.setDate(anchorSunday.getDate() + (currentTopWeekIndex * 7));
    
    const visibleRows = Math.ceil(viewport.clientHeight / ROW_HEIGHT);
    const bottomVisibleDate = new Date(anchorSunday);
    bottomVisibleDate.setDate(anchorSunday.getDate() + ((currentTopWeekIndex + visibleRows - 1) * 7));

    const topYear = topVisibleDate.getFullYear();
    const bottomYear = bottomVisibleDate.getFullYear();

    if (topYear === bottomYear) {
        yearDisplay.innerText = topYear;
    } else {
        yearDisplay.innerText = `${Math.min(topYear, bottomYear)} - ${Math.max(topYear, bottomYear)}`;
    }

    // --- JUMP TO TODAY LOGIC ---
    const centerOffset = (viewport.clientHeight / 2) - (ROW_HEIGHT / 2);
    const perfectCenterScroll = ANCHOR_SCROLL - centerOffset;
    
    const distanceFromCenter = scrollTop - perfectCenterScroll;

    const SCROLL_THRESHOLD = ROW_HEIGHT * 2; 

    if (distanceFromCenter < -SCROLL_THRESHOLD) {
        btnTodayBottom.classList.remove('hidden');
        btnTodayTop.classList.add('hidden');
    } else if (distanceFromCenter > SCROLL_THRESHOLD) {
        btnTodayTop.classList.remove('hidden');
        btnTodayBottom.classList.add('hidden');
    } else {
        btnTodayTop.classList.add('hidden');
        btnTodayBottom.classList.add('hidden');
    }
    
}