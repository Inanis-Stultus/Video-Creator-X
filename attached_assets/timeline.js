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
            if (item.filepath.match(/\.(jpg|jpeg|png)$/i)) {
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

    updateItemEffects(index, effects) {
        if (index >= 0 && index < this.items.length) {
            this.items[index].effects = effects;
            this.updateUI();
        }
    }

    addTransition(index, transitionType) {
        if (index >= 0 && index < this.items.length - 1) {
            this.items[index].transition = transitionType;
            this.updateUI();
        }
    }

    calculateTotalDuration() {
        return this.items.reduce((total, item) => total + parseFloat(item.duration), 0);
    }

    updateUI() {
        const event = new CustomEvent('timelineUpdated', { detail: { items: this.items } });
        document.dispatchEvent(event);
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