import { 
    createContainer,
    createContainerFlex,
    createAddButton,
    createTextDiv,
} from "./../html_builders/primitives/index.js"
import { 
    createCodingProjectBlockEdit,
    createCodingProjectBlockView
} from "./../html_builders/components/index.js"
import { dropdownData } from "../core/global.js";

function localRenderEdit() {
    const container = createContainerFlex({ 
        id: 'editor-coding', 
        className: 'coding-container' 
    });
    
    const blocksContainer = createContainer({ 
        id: 'coding-blocks-container' 
    });
    
    const addProjectBtn = createAddButton('+ Add Project', () => {
        blocksContainer.appendChild(createCodingProjectBlockEdit({}, dropdownData.coding_projects || []));
        blocksContainer.dispatchEvent(new Event('input', { bubbles: true }));
    });

    container.appendChild(blocksContainer);
    container.appendChild(addProjectBtn);

    return container;
}

function localRenderView() {
    const container = createContainerFlex({ 
        id: 'view-coding', 
        className: 'coding-container' 
    });
    const projectsContainer = createContainerFlex({ 
        id: 'view-coding-projects' 
    });

    container.appendChild(projectsContainer);

    return container;
}

function localExtract() {
    const blocksContainer = document.getElementById('coding-blocks-container');
    const blocks = blocksContainer.querySelectorAll('.coding-project-block');
    const codingData = [];

    blocks.forEach(block => {
        const projectName = block.querySelector('.coding-project-name').value.trim();
        const taskName = block.querySelector('.coding-task-input').value.trim();
        const timeVal = block.querySelector('.coding-time-input').value;
        
        const detailRows = block.querySelectorAll('.coding-detail-row');
        const detailsData = [];

        detailRows.forEach(row => {
            const detailText = row.querySelector('.coding-detail-input').value.trim();
            if (detailText !== "") {
                detailsData.push(detailText);
            }
        });

        // Only save the block if there is actual input
        if (projectName || taskName || detailsData.length > 0 || timeVal !== "") {
            codingData.push({
                "project": projectName,
                "task": taskName,
                "time spent": timeVal === "" ? 0 : parseFloat(timeVal),
                "details": detailsData
            });
        }
    });

    return codingData;
}

function localInjectEdit(data) {
    const blocksContainer = document.getElementById('coding-blocks-container');
    if (blocksContainer) {
        blocksContainer.innerHTML = ''; 
        if (Array.isArray(data)) {
            data.forEach(project => {
                blocksContainer.appendChild(createCodingProjectBlockEdit(project, dropdownData.coding_projects || []));
            });
        }
    }
}

function localInjectView(data) {
    const viewProjects = document.getElementById('view-coding-projects');
    if (viewProjects) {
        viewProjects.innerHTML = ''; 
        
        if (Array.isArray(data) && data.length > 0) {
            data.forEach(project => {
                viewProjects.appendChild(createCodingProjectBlockView(project));
            });
            return true; // Tell dispatcher to show this section
        } else {
            return false; // Tell dispatcher to hide this section
        }
    }
    return false;
}

export const CodingModule = {
    renderEdit: localRenderEdit,
    renderView: localRenderView,
    extract: localExtract,
    injectEdit: localInjectEdit,
    injectView: localInjectView
};
