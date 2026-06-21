import { populateTileUI } from "./core.js";
import { yearDisplay } from "../core/const.js";
import { viewport } from "./internal.js"; 

export const tileDataObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const dayDiv = entry.target;
            const dateKey = dayDiv.dataset.dateKey;
            
            populateTileUI(dayDiv, dateKey);
            
            observer.unobserve(dayDiv); 
        }
    });
}, {
    root: viewport,
    rootMargin: "200px 0px"
});
