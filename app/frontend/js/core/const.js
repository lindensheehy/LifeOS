export const scrollContainer = document.querySelector('.calendar-container');
export const gridContainer = document.getElementById("calendar-days");
export const yearDisplay = document.getElementById("year-display");
export const btnTodayTop = document.getElementById("btn-today-top");
export const btnTodayBottom = document.getElementById("btn-today-bottom");
export const sectionsContainer = document.getElementById("sections-container");
export const saveStatus = document.getElementById("save-status");

export const daysOfWeek = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

export const visibleYears = new Map();

export const today = (() => {
    const d = new Date();
    if (d.getHours() < 4) d.setDate(d.getDate() - 1);
    return d;
})();
