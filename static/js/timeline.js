class Timeline {
    constructor() {
        this.items = [];
        this.selectedItemIndex = -1;
        this.preview = document.getElementById('preview');
        this.isDragging = false;
        this.dragStartIndex = -1;

        this.initializeSortable();
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
        const preview = document.getElementById('preview');

        // Clean up any existing preview elements
        const existingImg = preview.parentElement.querySelector('img.preview-image');
        if (existingImg) existingImg.remove();

        try {
            if (item.filename.match(/\.(jpg|jpeg|png|gif)$/i)) {
                // Handle image preview
                preview.style.display = 'none';
                const img = document.createElement('img');
                img.src = URL.createObjectURL(new Blob([Uint8Array.from(atob(item.file_data), c => c.charCodeAt(0))]));
                img.className = 'preview-image w-100';
                preview.parentElement.insertBefore(img, preview);

                // Remove image after duration
                setTimeout(() => {
                    URL.revokeObjectURL(img.src);
                    img.remove();
                    preview.style.display = 'block';
                }, item.duration * 1000);
            } else {
                // Handle video preview
                const videoBlob = new Blob([Uint8Array.from(atob(item.file_data), c => c.charCodeAt(0))], {type: 'video/mp4'});
                preview.src = URL.createObjectURL(videoBlob);
                preview.style.display = 'block';
                preview.load();
                preview.play()
                    .then(() => {
                        // Cleanup after video ends
                        preview.onended = () => {
                            URL.revokeObjectURL(preview.src);
                        };
                    })
                    .catch(error => {
                        console.error('Preview playback failed:', error);
                        URL.revokeObjectURL(preview.src);
                    });
            }
        } catch (error) {
            console.error('Preview failed:', error);
            preview.style.display = 'block';
        }
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
                                    <select class="form-control" onchange="window.timelineManager.updateTransition(${index}, this.value, 'start')">
                                        <option value="none">None</option>
                                        <option value="fade-in" ${item.startTransition === 'fade-in' ? 'selected' : ''}>Fade In</option>
                                        <option value="dissolve-in" ${item.startTransition === 'dissolve-in' ? 'selected' : ''}>Dissolve In</option>
                                        <option value="wipe-right" ${item.startTransition === 'wipe-right' ? 'selected' : ''}>Wipe Right</option>
                                        <option value="slide-right" ${item.startTransition === 'slide-right' ? 'selected' : ''}>Slide Right</option>
                                        <option value="rotate-in" ${item.startTransition === 'rotate-in' ? 'selected' : ''}>Rotate In</option>
                                        <option value="zoom-in" ${item.startTransition === 'zoom-in' ? 'selected' : ''}>Zoom In</option>
                                        <option value="blur-in" ${item.startTransition === 'blur-in' ? 'selected' : ''}>Blur In</option>
                                        <option value="matrix-in" ${item.startTransition === 'matrix-in' ? 'selected' : ''}>Digital Rain In</option>
                                        <option value="heart-in" ${item.startTransition === 'heart-in' ? 'selected' : ''}>Heart Wipe In</option>
                                        <option value="shatter-in" ${item.startTransition === 'shatter-in' ? 'selected' : ''}>Shatter In</option>
                                        <option value="glitch-in" ${item.startTransition === 'glitch-in' ? 'selected' : ''}>Glitch In</option>
                                        <option value="ripple-in" ${item.startTransition === 'ripple-in' ? 'selected' : ''}>Ripple In</option>
                                        <option value="pixelate-in" ${item.startTransition === 'pixelate-in' ? 'selected' : ''}>Pixelate In</option>
                                        <option value="circle-wipe-in" ${item.startTransition === 'circle-wipe-in' ? 'selected' : ''}>Circle Wipe In</option>
                                        <option value="swirl-in" ${item.startTransition === 'swirl-in' ? 'selected' : ''}>Swirl In</option>
                                        <option value="wave-in" ${item.startTransition === 'wave-in' ? 'selected' : ''}>Wave In</option>
                                        <option value="tile-in" ${item.startTransition === 'tile-in' ? 'selected' : ''}>Tile In</option>
                                        <option value="color-shift-in" ${item.startTransition === 'color-shift-in' ? 'selected' : ''}>Color Shift In</option>
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="form-group mb-3">
                                    <label>End Transition</label>
                                    <select class="form-control" onchange="window.timelineManager.updateTransition(${index}, this.value, 'end')">
                                        <option value="none">None</option>
                                        <option value="fade-out" ${item.endTransition === 'fade-out' ? 'selected' : ''}>Fade Out</option>
                                        <option value="dissolve-out" ${item.endTransition === 'dissolve-out' ? 'selected' : ''}>Dissolve Out</option>
                                        <option value="wipe-left" ${item.endTransition === 'wipe-left' ? 'selected' : ''}>Wipe Left</option>
                                        <option value="slide-left" ${item.endTransition === 'slide-left' ? 'selected' : ''}>Slide Left</option>
                                        <option value="rotate-out" ${item.endTransition === 'rotate-out' ? 'selected' : ''}>Rotate Out</option>
                                        <option value="zoom-out" ${item.endTransition === 'zoom-out' ? 'selected' : ''}>Zoom Out</option>
                                        <option value="blur-out" ${item.endTransition === 'blur-out' ? 'selected' : ''}>Blur Out</option>
                                        <option value="matrix-out" ${item.endTransition === 'matrix-out' ? 'selected' : ''}>Digital Rain Out</option>
                                        <option value="heart-out" ${item.endTransition === 'heart-out' ? 'selected' : ''}>Heart Wipe Out</option>
                                        <option value="shatter-out" ${item.endTransition === 'shatter-out' ? 'selected' : ''}>Shatter Out</option>
                                        <option value="glitch-out" ${item.endTransition === 'glitch-out' ? 'selected' : ''}>Glitch Out</option>
                                        <option value="ripple-out" ${item.endTransition === 'ripple-out' ? 'selected' : ''}>Ripple Out</option>
                                        <option value="pixelate-out" ${item.endTransition === 'pixelate-out' ? 'selected' : ''}>Pixelate Out</option>
                                        <option value="circle-wipe-out" ${item.endTransition === 'circle-wipe-out' ? 'selected' : ''}>Circle Wipe Out</option>
                                        <option value="swirl-out" ${item.endTransition === 'swirl-out' ? 'selected' : ''}>Swirl Out</option>
                                        <option value="wave-out" ${item.endTransition === 'wave-out' ? 'selected' : ''}>Wave Out</option>
                                        <option value="tile-out" ${item.endTransition === 'tile-out' ? 'selected' : ''}>Tile Out</option>
                                        <option value="color-shift-out" ${item.endTransition === 'color-shift-out' ? 'selected' : ''}>Color Shift Out</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        <div class="form-group mb-3">
                            <label>Filter Effect</label>
                            <select class="form-control" 
                                onchange="window.timelineManager.updateFilter(${index}, this.value)">
                                <option value="none" ${!item.filter || item.filter === 'none' ? 'selected' : ''}>No Filter</option>
                                <option value="grayscale" ${item.filter === 'grayscale' ? 'selected' : ''}>Black & White</option>
                                <option value="sepia" ${item.filter === 'sepia' ? 'selected' : ''}>Sepia Tone</option>
                                <option value="blur" ${item.filter === 'blur' ? 'selected' : ''}>Blur</option>
                                <option value="sharpen" ${item.filter === 'sharpen' ? 'selected' : ''}>Sharpen</option>
                                <option value="bright" ${item.filter === 'bright' ? 'selected' : ''}>Brighten</option>
                                <option value="dark" ${item.filter === 'dark' ? 'selected' : ''}>Darken</option>
                                <option value="contrast" ${item.filter === 'contrast' ? 'selected' : ''}>High Contrast</option>
                                <option value="mirror" ${item.filter === 'mirror' ? 'selected' : ''}>Mirror</option>
                                <option value="cartoon" ${item.filter === 'cartoon' ? 'selected' : ''}>Cartoon</option>
                                <option value="oil_painting" ${item.filter === 'oil_painting' ? 'selected' : ''}>Oil Painting</option>
                                <option value="rainbow" ${item.filter === 'rainbow' ? 'selected' : ''}>Rainbow</option>
                                <option value="neon" ${item.filter === 'neon' ? 'selected' : ''}>Neon Glow</option>
                                <option value="thermal" ${item.filter === 'thermal' ? 'selected' : ''}>Thermal Vision</option>
                                <option value="pencil_sketch" ${item.filter === 'pencil_sketch' ? 'selected' : ''}>Pencil Sketch</option>
                                <option value="invert" ${item.filter === 'invert' ? 'selected' : ''}>Invert</option>
                                <option value="emboss" ${item.filter === 'emboss' ? 'selected' : ''}>Emboss</option>
                                <option value="glitch" ${item.filter === 'glitch' ? 'selected' : ''}>Glitch</option>
                                <option value="pixelate" ${item.filter === 'pixelate' ? 'selected' : ''}>Pixelate</option>
                                <option value="edge_detect" ${item.filter === 'edge_detect' ? 'selected' : ''}>Edge Detect</option>
                                <option value="posterize" ${item.filter === 'posterize' ? 'selected' : ''}>Posterize</option>
                                <option value="solarize" ${item.filter === 'solarize' ? 'selected' : ''}>Solarize</option>
                                <option value="vignette" ${item.filter === 'vignette' ? 'selected' : ''}>Vignette</option>
                                <option value="halftone" ${item.filter === 'halftone' ? 'selected' : ''}>Halftone</option>
                                <option value="noise" ${item.filter === 'noise' ? 'selected' : ''}>Noise</option>
                                <option value="color_shift" ${item.filter === 'color_shift' ? 'selected' : ''}>Color Shift</option>
                            </select>
                        </div>
                        <div class="form-check mb-3">
                            <input type="checkbox" class="form-check-input" ${item.keepAudio ? 'checked' : ''}
                                onchange="window.timelineManager.updateAudio(${index}, this.checked)">
                            <label class="form-check-label">Keep Audio</label>
                        </div>
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
        if (duration > 0 && duration <= 72000) {
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