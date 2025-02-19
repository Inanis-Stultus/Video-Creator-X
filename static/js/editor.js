document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const exportBtn = document.getElementById('export-btn');
    const useCustomResolution = document.getElementById('use-custom-resolution');
    const resolutionControls = document.getElementById('resolution-controls');
    const MAX_FILE_SIZE = 16 * 1024 * 1024; // 16MB

    // Initialize timeline manager with AI-generated timeline
    window.timelineManager = {
        items: [],
        aiTimeline: null,
        currentAiIndex: 0,

        init: function() {
            const visualTimeline = localStorage.getItem('visualTimeline');
            if (visualTimeline) {
                try {
                    // Parse the AI-generated timeline
                    this.aiTimeline = JSON.parse(visualTimeline);
                    // Sort by timestamp if available
                    if (Array.isArray(this.aiTimeline)) {
                        this.aiTimeline.sort((a, b) => {
                            const timeA = a.timestamp.split(':').map(Number);
                            const timeB = b.timestamp.split(':').map(Number);
                            return (timeA[0] * 60 + timeA[1]) - (timeB[0] * 60 + timeB[1]);
                        });
                    }
                } catch (error) {
                    console.error('Error parsing visual timeline:', error);
                    alert('Error loading the visual timeline. Please try generating it again.');
                }
            }
        },

        updateUI: function() {
            document.dispatchEvent(new CustomEvent('timelineUpdated', { detail: { items: this.items } }));
        },

        calculateTotalDuration: function() {
            return this.items.reduce((total, item) => total + parseFloat(item.duration || 0), 0);
        },

        getNextTimelineItem: function() {
            if (!this.aiTimeline || this.currentAiIndex >= this.aiTimeline.length) {
                return null;
            }
            return this.aiTimeline[this.currentAiIndex++];
        }
    };

    // Initialize timeline manager
    window.timelineManager.init();

    // Resolution controls visibility
    useCustomResolution.addEventListener('change', function() {
        resolutionControls.style.display = this.checked ? 'flex' : 'none';
    });

    // File upload handling
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', async (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        handleFiles(e.dataTransfer.files);
    });

    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    exportBtn.addEventListener('click', exportVideo);

    // Listen for timeline updates
    document.addEventListener('timelineUpdated', (e) => {
        updateTimelineUI(e.detail.items);
    });

    function validateFile(file) {
        if (file.size > MAX_FILE_SIZE) {
            throw new Error(`File ${file.name} is too large. Maximum size is 16MB`);
        }
        const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'video/mp4'];
        if (!allowedTypes.includes(file.type)) {
            throw new Error(`File ${file.name} has unsupported type. Allowed types: JPG, PNG, GIF, MP4`);
        }
        return true;
    }

    async function handleFiles(files) {
        for (let file of files) {
            try {
                validateFile(file);
                await uploadFile(file);
            } catch (error) {
                showAlert(error.message, 'warning');
            }
        }
    }

    async function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.success) {
                // Get next timeline item from AI-generated timeline
                const timelineItem = window.timelineManager.getNextTimelineItem();
                if (timelineItem) {
                    window.timelineManager.items.push({
                        filename: data.filename,
                        file_data: data.file_data,
                        duration: parseFloat(timelineItem.duration) || 5,
                        keepAudio: true,
                        startTransition: timelineItem.startTransition || 'fade-in',
                        endTransition: timelineItem.endTransition || 'fade-out',
                        filter: timelineItem.filter || 'none'
                    });
                } else {
                    // Fallback if no AI timeline item is available
                    window.timelineManager.items.push({
                        filename: data.filename,
                        file_data: data.file_data,
                        duration: 5,
                        keepAudio: true,
                        startTransition: 'fade-in',
                        endTransition: 'fade-out',
                        filter: 'none'
                    });
                }
                window.timelineManager.updateUI();
                showAlert(`File ${file.name} uploaded successfully`, 'success');
            } else {
                showAlert('Error uploading file: ' + data.error, 'danger');
            }
        } catch (error) {
            showAlert('Upload failed: ' + error, 'danger');
        }
    }

    function updateTimelineUI(items) {
        const timelineContainer = document.getElementById('timeline');
        timelineContainer.innerHTML = '';

        items.forEach((item, index) => {
            const element = document.createElement('div');
            element.className = 'timeline-item';
            element.draggable = true;
            element.dataset.index = index;
            element.innerHTML = `
                <div class="card bg-dark">
                    <div class="card-body">
                        <h5 class="card-title">${item.filename}</h5>
                        <div class="mb-3">
                            <label class="form-label">Duration: ${item.duration}s</label>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Start Transition: ${item.startTransition}</label>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">End Transition: ${item.endTransition}</label>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Filter: ${item.filter}</label>
                        </div>
                    </div>
                </div>
            `;
            timelineContainer.appendChild(element);
        });

        updateDurationDisplay();
    }

    function updateDurationDisplay() {
        const totalDuration = window.timelineManager.calculateTotalDuration();
        const durationDisplay = document.createElement('div');
        durationDisplay.className = 'text-muted mt-2 duration-display';
        durationDisplay.textContent = `Total Duration: ${totalDuration.toFixed(1)}s`;

        const existingDisplay = document.querySelector('.duration-display');
        if (existingDisplay) {
            existingDisplay.remove();
        }
        document.getElementById('timeline').appendChild(durationDisplay);
    }

    function showAlert(message, type) {
        const alertContainer = document.getElementById('alert-container');
        if (!alertContainer) return;

        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        alertContainer.appendChild(alert);
        setTimeout(() => alert.remove(), 5000);
    }

    async function exportVideo() {
        if (window.timelineManager.items.length === 0) {
            showAlert('Timeline is empty!', 'warning');
            return;
        }

        const totalDuration = window.timelineManager.calculateTotalDuration();
        if (totalDuration > 300) { // 5 minutes max
            showAlert('Video duration cannot exceed 5 minutes', 'warning');
            return;
        }

        const exportBtn = document.getElementById('export-btn');
        exportBtn.disabled = true;
        exportBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Processing...';

        try {
            const useCustomResolution = document.getElementById('use-custom-resolution').checked;
            const requestData = {
                timeline: window.timelineManager.items
            };

            if (useCustomResolution) {
                const width = parseInt(document.getElementById('width').value);
                const height = parseInt(document.getElementById('height').value);

                if (isNaN(width) || isNaN(height) || width < 240 || height < 240 || width > 3840 || height > 2160) {
                    showAlert('Invalid resolution values. Width: 240-3840px, Height: 240-2160px', 'warning');
                    return;
                }

                requestData.resolution = { width, height };
            }

            const response = await fetch('/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `output_${Date.now()}.mp4`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            showAlert('Export successful!', 'success');
        } catch (error) {
            showAlert('Export failed: ' + error, 'danger');
        } finally {
            exportBtn.disabled = false;
            exportBtn.innerHTML = 'Export Video';
        }
    }
});