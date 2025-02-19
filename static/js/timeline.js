class Timeline {
    constructor() {
        this.items = [];
        this.selectedItemIndex = -1;
        this.isDragging = false;
        this.dragStartIndex = -1;
        this.previewElement = document.getElementById('preview');

        this.initializeSortable();
        this.initializePreview();
    }

    initializeSortable() {
        const timelineContainer = document.getElementById('timeline');

        timelineContainer.addEventListener('dragstart', (e) => {
            if (e.target.classList.contains('timeline-item')) {
                this.isDragging = true;
                this.dragStartIndex = Array.from(timelineContainer.children)
                    .indexOf(e.target);
                e.target.classList.add('dragging');
            }
        });

        timelineContainer.addEventListener('dragend', (e) => {
            if (e.target.classList.contains('timeline-item')) {
                this.isDragging = false;
                e.target.classList.remove('dragging');
                this.updateTimelineOrder();
            }
        });

        timelineContainer.addEventListener('dragover', (e) => {
            e.preventDefault();
            if (!this.isDragging) return;

            const draggingItem = timelineContainer.querySelector('.dragging');
            const siblings = [...timelineContainer.querySelectorAll('.timeline-item:not(.dragging)')];

            const nextSibling = siblings.find(sibling => {
                return e.clientY < sibling.getBoundingClientRect().top + sibling.offsetHeight / 2;
            });

            timelineContainer.insertBefore(draggingItem, nextSibling);
        });
    }

    initializePreview() {
        // Initialize preview functionality
        this.previewElement = document.getElementById('preview');
        this.previewOverlay = document.createElement('div');
        this.previewOverlay.className = 'preview-overlay';
        this.previewElement.parentElement.appendChild(this.previewOverlay);
    }

    updateTimelineOrder() {
        const timelineContainer = document.getElementById('timeline');
        const newOrder = Array.from(timelineContainer.children)
            .map(item => parseInt(item.dataset.index));

        // Create a new array with the reordered items
        const reorderedItems = newOrder.map(index => this.items[index]);
        this.items = reorderedItems;

        // Update the UI to reflect the new order
        this.updateUI();
    }

    previewItem(index) {
        if (index < 0 || index >= this.items.length) return;

        const item = this.items[index];
        this.selectedItemIndex = index;

        // Get the preview container
        const previewContainer = document.getElementById('preview-container');
        const previewElement = document.getElementById('preview');

        try {
            // Clean up any existing preview
            while (previewContainer.firstChild) {
                previewContainer.firstChild.remove();
            }

            // Create new preview element based on file type
            let mediaElement;
            const isImage = item.filename.match(/\.(jpg|jpeg|png|gif)$/i);

            if (isImage) {
                mediaElement = document.createElement('img');
                mediaElement.className = 'preview-media';
                mediaElement.src = URL.createObjectURL(this.base64ToBlob(item.file_data, item.mime_type));
            } else {
                mediaElement = document.createElement('video');
                mediaElement.className = 'preview-media';
                mediaElement.src = URL.createObjectURL(this.base64ToBlob(item.file_data, item.mime_type));
                mediaElement.controls = true;
                mediaElement.autoplay = true;
            }

            // Add the media element to the container
            previewContainer.appendChild(mediaElement);

            // Clean up the object URL after the media loads
            mediaElement.onload = () => URL.revokeObjectURL(mediaElement.src);
            mediaElement.onerror = (error) => {
                console.error('Preview failed:', error);
                this.showPreviewError();
            };

        } catch (error) {
            console.error('Preview failed:', error);
            this.showPreviewError();
        }
    }

    base64ToBlob(base64, mimeType) {
        const byteCharacters = atob(base64);
        const byteArrays = [];

        for (let offset = 0; offset < byteCharacters.length; offset += 512) {
            const slice = byteCharacters.slice(offset, offset + 512);
            const byteNumbers = new Array(slice.length);

            for (let i = 0; i < slice.length; i++) {
                byteNumbers[i] = slice.charCodeAt(i);
            }

            const byteArray = new Uint8Array(byteNumbers);
            byteArrays.push(byteArray);
        }

        return new Blob(byteArrays, { type: mimeType });
    }

    showPreviewError() {
        const previewContainer = document.getElementById('preview-container');
        const errorMessage = document.createElement('div');
        errorMessage.className = 'preview-error';
        errorMessage.textContent = 'Preview failed to load';
        previewContainer.appendChild(errorMessage);
    }

    calculateTotalDuration() {
        return this.items.reduce((total, item) => total + parseFloat(item.duration), 0);
    }

    updateUI() {
        const timelineContainer = document.getElementById('timeline');
        timelineContainer.innerHTML = '';

        this.items.forEach((item, index) => {
            const element = document.createElement('div');
            element.className = 'timeline-item';
            element.draggable = true;
            element.dataset.index = index;
            element.innerHTML = `
                <div class="card bg-dark">
                    <div class="card-body">
                        <h5 class="card-title">${item.filename}</h5>
                        <div class="form-group mb-3">
                            <label>Duration (seconds)</label>
                            <input type="number" class="form-control" value="${item.duration}" 
                                onchange="window.timelineManager.updateDuration(${index}, this.value)" 
                                min="0.1" max="300" step="0.1">
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="form-group mb-3">
                                    <label>Start Transition</label>
                                    <select class="form-control" 
                                        onchange="window.timelineManager.updateTransition(${index}, this.value, 'start')">
                                        <option value="none">None</option>
                                        <option value="fade" ${item.startTransition === 'fade' ? 'selected' : ''}>Fade</option>
                                        <option value="dissolve" ${item.startTransition === 'dissolve' ? 'selected' : ''}>Dissolve</option>
                                        <option value="slide" ${item.startTransition === 'slide' ? 'selected' : ''}>Slide</option>
                                        <option value="zoom" ${item.startTransition === 'zoom' ? 'selected' : ''}>Zoom</option>
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="form-group mb-3">
                                    <label>End Transition</label>
                                    <select class="form-control" 
                                        onchange="window.timelineManager.updateTransition(${index}, this.value, 'end')">
                                        <option value="none">None</option>
                                        <option value="fade" ${item.endTransition === 'fade' ? 'selected' : ''}>Fade</option>
                                        <option value="dissolve" ${item.endTransition === 'dissolve' ? 'selected' : ''}>Dissolve</option>
                                        <option value="slide" ${item.endTransition === 'slide' ? 'selected' : ''}>Slide</option>
                                        <option value="zoom" ${item.endTransition === 'zoom' ? 'selected' : ''}>Zoom</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        <div class="form-group mb-3">
                            <label>Filter</label>
                            <select class="form-control" 
                                onchange="window.timelineManager.updateFilter(${index}, this.value)">
                                <option value="none">None</option>
                                <option value="grayscale" ${item.filter === 'grayscale' ? 'selected' : ''}>Grayscale</option>
                                <option value="sepia" ${item.filter === 'sepia' ? 'selected' : ''}>Sepia</option>
                                <option value="blur" ${item.filter === 'blur' ? 'selected' : ''}>Blur</option>
                                <option value="bright" ${item.filter === 'bright' ? 'selected' : ''}>Bright</option>
                                <option value="dark" ${item.filter === 'dark' ? 'selected' : ''}>Dark</option>
                                <option value="contrast" ${item.filter === 'contrast' ? 'selected' : ''}>High Contrast</option>
                                <option value="mirror" ${item.filter === 'mirror' ? 'selected' : ''}>Mirror</option>
                                <option value="invert" ${item.filter === 'invert' ? 'selected' : ''}>Invert</option>
                            </select>
                        </div>
                        <div class="form-check mb-3">
                            <input type="checkbox" class="form-check-input" ${item.keepAudio ? 'checked' : ''}
                                onchange="window.timelineManager.updateAudio(${index}, this.checked)">
                            <label class="form-check-label">Keep Audio</label>
                        </div>
                        <button class="btn btn-primary btn-sm me-2" 
                            onclick="window.timelineManager.previewItem(${index})">Preview</button>
                        <button class="btn btn-danger btn-sm" 
                            onclick="window.timelineManager.removeItem(${index})">Remove</button>
                    </div>
                </div>
            `;
            timelineContainer.appendChild(element);
        });

        this.updateDurationDisplay();
    }

    updateDuration(index, value) {
        const duration = parseFloat(value);
        if (duration > 0 && duration <= 300) {
            this.items[index].duration = duration;
            this.updateUI();
        }
    }

    updateAudio(index, value) {
        this.items[index].keepAudio = value;
        this.updateUI();
    }

    updateFilter(index, value) {
        this.items[index].filter = value;
        this.updateUI();
    }

    removeItem(index) {
        this.items.splice(index, 1);
        this.updateUI();
    }

    updateTransition(index, value, position) {
        if (position === 'start') {
            this.items[index].startTransition = value;
        } else {
            this.items[index].endTransition = value;
        }
        this.updateUI();
    }

    updateDurationDisplay() {
        const totalDuration = this.calculateTotalDuration();
        const durationDisplay = document.createElement('div');
        durationDisplay.className = 'text-muted mt-2 duration-display';
        durationDisplay.textContent = `Total Duration: ${totalDuration.toFixed(1)}s`;

        const existingDisplay = document.querySelector('.duration-display');
        if (existingDisplay) {
            existingDisplay.remove();
        }
        document.getElementById('timeline').appendChild(durationDisplay);
    }
}

// Initialize timeline functionality
const timelineManager = new Timeline();

// Add preview controls
document.getElementById('timeline').addEventListener('click', (e) => {
    const timelineItem = e.target.closest('.timeline-item');
    if (timelineItem) {
        const index = parseInt(timelineItem.dataset.index);
        timelineManager.previewItem(index);
    }
});

// Export timeline manager for use in editor.js
window.timelineManager = timelineManager;