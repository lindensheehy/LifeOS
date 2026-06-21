export const VIRTUAL_HEIGHT = 500000;
export const ANCHOR_SCROLL = VIRTUAL_HEIGHT / 2;
export const ROW_HEIGHT = 130;

// --- INTERNAL STATE ---
export let viewport = null;
export let contentContainer = null;

// State mutators to be called by init.js
export function setViewport(el) { viewport = el; }
export function setContentContainer(el) { contentContainer = el; }