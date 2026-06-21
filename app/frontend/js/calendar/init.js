import { 
    ANCHOR_SCROLL, 
    ROW_HEIGHT,
    setViewport, 
    setContentContainer,
    viewport 
} from "./internal.js";
import { 
    btnTodayTop, 
    btnTodayBottom 
} from "../core/const.js";
import { renderVirtualViewport } from "./view.js";

export function init() {

    const vp = document.getElementById("calendar-viewport");
    const container = document.getElementById("calendar-content");
    setViewport(vp);
    setContentContainer(container);

    const centerOffset = (vp.clientHeight / 2) - (ROW_HEIGHT / 2);
    const targetScroll = ANCHOR_SCROLL - centerOffset;

    vp.scrollTop = targetScroll;

    renderVirtualViewport(vp.scrollTop);

    const scrollToToday = () => {
        const currentCenterOffset = (vp.clientHeight / 2) - (ROW_HEIGHT / 2);
        vp.scrollTo({
            top: ANCHOR_SCROLL - currentCenterOffset,
            behavior: "smooth"
        });
    };

    btnTodayTop.addEventListener("click", scrollToToday);
    btnTodayBottom.addEventListener("click", scrollToToday);

    let isTicking = false;
    vp.addEventListener("scroll", () => {
        if (!isTicking) {
            window.requestAnimationFrame(() => {
                renderVirtualViewport(vp.scrollTop);
                isTicking = false;
            });
            isTicking = true;
        }
    }, { passive: true }); 

    const todayTile = document.querySelector('.day.today');
    if (todayTile) todayTile.click();
    
}