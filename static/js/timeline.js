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

        try {
            if (item.filename.match(/\.(jpg|jpeg|png)$/i)) {
                // Handle image preview
                preview.style.display = 'none';
                const img = document.createElement('img');
                img.src = `/download/${item.filename}`;
                img.className = 'w-100';
                preview.parentElement.insertBefore(img, preview);
                setTimeout(() => {
                    img.remove();
                    preview.style.display = 'block';
                }, item.duration * 1000);
            } else {
                // Handle video/gif preview
                preview.src = `/download/${item.filename}`;
                preview.load();
                preview.play().catch(error => {
                    console.error('Preview playback failed:', error);
                });
            }
        } catch (error) {
            console.error('Preview failed:', error);
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
                                    <select class="form-control" 
                                        onchange="window.timelineManager.updateTransition(${index}, this.value, 'start')">
                                        <option value="fade" ${item.startTransition === 'fade' ? 'selected' : ''}>Fade</option>
                                        <option value="slide" ${item.startTransition === 'slide' ? 'selected' : ''}>Slide</option>
                                        <option value="zoom" ${item.startTransition === 'zoom' ? 'selected' : ''}>Zoom</option>
                                        <option value="none" ${item.startTransition === 'none' ? 'selected' : ''}>None</option>
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="form-group mb-3">
                                    <label>End Transition</label>
                                    <select class="form-control" 
                                        onchange="window.timelineManager.updateTransition(${index}, this.value, 'end')">
                                        <option value="fade" ${item.endTransition === 'fade' ? 'selected' : ''}>Fade</option>
                                        <option value="slide" ${item.endTransition === 'slide' ? 'selected' : ''}>Slide</option>
                                        <option value="zoom" ${item.endTransition === 'zoom' ? 'selected' : ''}>Zoom</option>
                                        <option value="none" ${item.endTransition === 'none' ? 'selected' : ''}>None</option>
                                    </select>
                                </div>
                            </div>
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
        if (duration > 0 && duration <= 300) {
            this.items[index].duration = duration;
            this.updateUI();
        }
    }

    updateAudio(index, value) {
        this.items[index].keepAudio = value;
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