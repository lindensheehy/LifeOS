import { 
    createContainerFlex,
    createTextDiv,
    createTextarea
} from "./../html_builders/primitives/index.js"

function localRenderEdit() {
    const container = createContainerFlex({ 
        id: 'editor-notes', 
        className: 'notes-container' 
    });

    const notesInput = createTextarea({ 
        id: 'notes-input', 
        placeholder: 'Any other thoughts or notes?' 
    });

    container.appendChild(notesInput);
    return container;
}

function localRenderView() {
    return createContainerFlex({ 
        id: 'view-notes', 
        className: 'notes-container' 
    });
}

function localExtract() {
    const input = document.getElementById('notes-input');
    // Just return the raw string (or an empty string if nothing is written)
    return input ? input.value.trim() : "";
}

function localInjectEdit(data) {
    const notesText = typeof data === 'string' ? data : "";

    const notesInput = document.getElementById('notes-input');
    if (notesInput) {
        notesInput.value = notesText;
    }
}

function localInjectView(data) {
    const notesText = typeof data === 'string' ? data : "";

    const viewContainer = document.getElementById('view-notes');
    if (viewContainer) {
        viewContainer.innerHTML = ''; 

        if (notesText !== "") {
            const notesDiv = createTextDiv(notesText, { 
                className: 'text-primary text-paragraph' 
            });
            notesDiv.style.whiteSpace = 'pre-wrap'; 
            
            viewContainer.appendChild(notesDiv);
            return true;
        } else {
            return false;
        }
    }
    return false;
}

export const NotesModule = {
    renderEdit: localRenderEdit,
    renderView: localRenderView,
    extract: localExtract,
    injectEdit: localInjectEdit,
    injectView: localInjectView
};
