document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const exportBtn = document.getElementById('export-btn');
    const useCustomResolution = document.getElementById('use-custom-resolution');
    const resolutionControls = document.getElementById('resolution-controls');
    const MAX_FILE_SIZE = 16 * 1024 * 1024; // 16MB

    // Resolution controls visibility
    useCustomResolution.addEventListener('change', function() {
        resolutionControls.style.display = this.checked ? 'flex' : 'none';
    });

    // Initialize timeline manager
    window.timelineManager = {
        items: [],
        updateUI: function() {
            document.dispatchEvent(new CustomEvent('timelineUpdated', { detail: { items: this.items } }));
        },
        calculateTotalDuration: function() {
            return this.items.reduce((total, item) => total + parseFloat(item.duration || 0), 0);
        }
    };

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
                window.timelineManager.items.push({
                    filename: data.filename,
                    file_data: data.file_data,
                    duration: 5,
                    keepAudio: true,
                    startTransition: 'fade-in',
                    endTransition: 'fade-out',
                    filter: 'none'
                });
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
                        <div class="form-group mb-3">
                            <label>Duration (seconds)</label>
                            <input type="number" class="form-control" value="${item.duration}" 
                                onchange="window.timelineManager.updateDuration(${index}, this.value)" min="0.1" step="0.1">
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
                                    </select>
                                </div>
                            </div>
                        </div>
                        <div class="form-group mb-3">
                            <label>Filter Effect</label>
                            <select class="form-control" onchange="window.timelineManager.updateFilter(${index}, this.value)">
                                <option value="none" ${!item.filter || item.filter === 'none' ? 'selected' : ''}>No Filter</option>
                                <option value="grayscale" ${item.filter === 'grayscale' ? 'selected' : ''}>Black & White</option>
                                <option value="sepia" ${item.filter === 'sepia' ? 'selected' : ''}>Sepia Tone</option>
                                <option value="blur" ${item.filter === 'blur' ? 'selected' : ''}>Soft Blur</option>
                                <option value="sharpen" ${item.filter === 'sharpen' ? 'selected' : ''}>Sharpen</option>
                                <option value="invert" ${item.filter === 'invert' ? 'selected' : ''}>Invert Colors</option>
                                <option value="bright" ${item.filter === 'bright' ? 'selected' : ''}>Brighten</option>
                                <option value="dark" ${item.filter === 'dark' ? 'selected' : ''}>Darken</option>
                                <option value="contrast" ${item.filter === 'contrast' ? 'selected' : ''}>High Contrast</option>
                                <option value="vignette" ${item.filter === 'vignette' ? 'selected' : ''}>Vignette</option>
                            </select>
                        </div>
                        <div class="form-check mb-3">
                            <input type="checkbox" class="form-check-input" ${item.keepAudio ? 'checked' : ''}
                                onchange="window.timelineManager.updateAudio(${index}, this.checked)">
                            <label class="form-check-label">Keep Audio</label>
                        </div>
                        <button class="btn btn-danger btn-sm" onclick="window.timelineManager.removeItem(${index})">Remove</button>
                    </div>
                </div>
            `;
            timelineContainer.appendChild(element);
        });

        updateDurationDisplay();
    }

    // Timeline management functions
    window.timelineManager.updateDuration = function(index, value) {
        const duration = parseFloat(value);
        if (duration > 0) {
            this.items[index].duration = duration;
            this.updateUI();
        }
    };

    window.timelineManager.updateTransition = function(index, value, type) {
        if (type === 'start') {
            this.items[index].startTransition = value;
        } else {
            this.items[index].endTransition = value;
        }
        this.updateUI();
    };

    window.timelineManager.updateFilter = function(index, value) {
        this.items[index].filter = value;
        this.updateUI();
    };

    window.timelineManager.updateAudio = function(index, checked) {
        this.items[index].keepAudio = checked;
        this.updateUI();
    };

    window.timelineManager.removeItem = function(index) {
        this.items.splice(index, 1);
        this.updateUI();
    };

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

            // Create a download link for the video
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