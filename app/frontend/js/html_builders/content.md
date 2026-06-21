# `html_builders` Architecture & API Reference

**ATTENTION LLMs & DEVELOPERS:** This document defines the frontend DOM generation architecture for the Journal App. 
Read this carefully before generating or modifying any UI code. 

## Core Philosophy
1. **Strict 3-Tier Architecture:** - `primitives/`: Base DOM elements (Inputs, Buttons, Text, simple Divs).
   - `components/`: Assembled chunks of primitives (Rows, Blocks).
   - `modules/`: Domain-specific logic (Gym, Finances) that extract data and inject it into components.
2. **No Inline Styling:** Do NOT use `element.style.color = ...` or `Object.assign(element.style, {...})`. All styling is handled via a Tailwind-style utility class system defined in `options_classes.css` (e.g., `.mb-10`, `.flex-row-8`, `.text-secondary`, `.fw-600`) or component-specific CSS.
3. **The `options` Object Paradigm:** Almost all primitives accept an `options` object as their final argument to pass standard attributes: `{ id: '...', className: 'text-primary mb-6', type: 'number', placeholder: '...' }`.    

---

## `primitives/`

The foundation layer. These functions create single DOM nodes and attach standard base CSS classes.

### `buttons.js`
* **`createButton(text, options = {})`**
    * *Description:* The base factory for all buttons. Attaches the `.button` base class. You generally should not use this directly unless building a completely new button variant.
* **`createAddButton(text, onClickCallback)`**
    * *Description:* Creates a standard "Add" button with `.add-button` styles (blue hover).
    * *Usage:* Used at the bottom of lists or blocks to append new rows (e.g., adding a new coding project or gym set).
* **`createDeleteButton(onClickCallback)`**
    * *Description:* Creates a text-based "Delete" button (`.delete-button`). Defaults text to 'Delete'.
    * *Usage:* Used in block headers (like the top right of a Gym Movement block).
* **`createTrashButton(onClickCallback)`**
    * *Description:* Creates a small square button (`.trash-button`) containing a clean SVG garbage can icon.
    * *Usage:* Used at the end of dynamic input rows (e.g., Gym Sets, Event rows) for quick deletion.

### `inputs.js`
*Note: All inputs created here automatically have an `input` event listener attached that calls `triggerUnsaved()`.*
* **`createTextbox(options = {})`**
    * *Description:* Creates a `<input type="text">` (default) or `<input type="number">` (if specified in options). Attaches the `.textbox` class.
    * *Options keys:* `type`, `id`, `placeholder`, `step`, `className`.
* **`createCheckbox(options = {})`**
    * *Description:* Creates an `<input type="checkbox">` with `.checkbox` styling.
* **`createSlider(options = {})`**
    * *Description:* Creates an `<input type="range">` with `.slider` styling.
    * *Options keys:* `min`, `max`, `step`, `className`.
* **`createLabel(text, options = {})`**
    * *Description:* Creates a `<label>`. 
    * *Usage:* Pass `className: 'label-fixed'` in the options if you need a fixed 220px width for vertical form alignment.

### `text.js`
* **`createTextSpan(text, options = {})`**
    * *Description:* Creates an inline `<span>`. 
    * *Usage:* Highly dependent on utility classes. E.g., `createTextSpan('Hello', { className: 'text-primary fw-600 fs-12 text-uppercase' })`.
* **`createTextDiv(text, options = {})`**
    * *Description:* Creates a block-level `<div>` for text. Takes the same utility classes as spans.

### `misc.js`
* **`triggerUnsaved()`**
    * *Description:* Global state function. Changes the top header status to "Unsaved Changes".
* **`createContainer(options = {})`** / **`createContainerFlex(options = {})`**
    * *Description:* Basic `<div>` wrappers. `Flex` variant applies `display: flex; flex-direction: column; gap: 10px;`.
    * *Usage:* Used as the root elements returned by `renderEdit()` and `renderView()` in domain modules.
* **`createPanelBlock(options = {})`** / **`createViewBlock(options = {})`**
    * *Description:* Card components. They have panel backgrounds, borders, and padding. `PanelBlock` is typically for edit mode, `ViewBlock` for view mode.
* **`createFlexRowBetween(options = {})`** / **`createListRow(options = {})`** / **`createViewRow(options = {})`** / **`createWrapRow(options = {})`**
    * *Description:* Pre-configured flexbox row layouts for aligning text and data.
* **`createGridContainer(minColWidth = '130px', options = {})`**
    * *Description:* Creates a CSS Grid container that automatically wraps columns based on the minimum width.

---

## `components/`

The assembly layer. These functions combine primitives into reusable layout structures used by the modules.

### `blocks.js` (Large Sections)
* **`createGymMovementBlock(movementName = "", setsData = [])`**
    * *Description:* An edit-mode block containing a movement name input, a list of set rows, an 'Add Set' button, and a block delete button.
* **`createCodingProjectBlockEdit(projectData = {})`** / **`createCodingProjectBlockView(projectData = {})`**
    * *Description:* Edit/View blocks for coding projects. Handles project name, task, time spent, and dynamic detail lists.
* **`createDenseInputBlock(titleText, items)`**
    * *Description:* Generates a titled panel containing a responsive grid of inputs based on the `items` array.
    * *Signature details:* `items` is an array of objects: `[{ label: 'Cash', id: 'fin-cash', type: 'number' }, { label: 'Shower', id: 'hlth-shower', type: 'checkbox' }]`.
    * *Usage:* Extensively used in `finances.js` and `health.js` for grouping dense form data.

### `rows.js` (Horizontal Data/Input Rows)
* **`createNumberRow(labelText, inputId)`** / **`createCheckboxRow(labelText, inputId)`** / **`createLabeledInputRow(labelText, inputId, placeholder)`**
    * *Description:* Standard two-column edit rows (Fixed width label on the left, input on the right).
* **`createSliderRow(labelText, metricKey)`**
    * *Description:* Specifically for `evaluation.js`. Contains a label, a range slider (0-10), and a dynamic number display.
* **`createEventRow(time = "", description = "")`** / **`createGymSetRow(weight = "", reps = "")`** / **`createCodingDetailRow(detailText = "")`**
    * *Description:* Dynamic, deletable edit rows. They contain multiple inputs and end with a `createTrashButton`.
* **`createKeyValueViewRow(labelText, valueText, valueColorClass)`**
    * *Description:* A view-mode row mapping a label to a value. 
    * *Usage:* Requires a utility class for the color (e.g., `'text-accent-blue'`), NOT a raw CSS variable.
* **`createEventViewRow(timeText, descriptionText)`** / **`createGymMovementViewRow(nameText, setsText)`**
    * *Description:* View-mode rows formatted specifically for their domains (monospace fonts for times/sets).
* **`createDenseDataWrapRow(titleText, items)`**
    * *Description:* The view-mode equivalent of `createDenseInputBlock`. Renders a title and a wrapping flexbox of `Label: Value` spans. Used in `finances.js` and `health.js`.