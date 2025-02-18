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
});

async function handleFiles(files) {
    const MAX_FILE_SIZE = 16 * 1024 * 1024; // 16MB

    for (let file of files) {
        if (file.size > MAX_FILE_SIZE) {
            showAlert(`File ${file.name} is too large. Maximum size is 16MB`, 'warning');
            continue;
        }
        await uploadFile(file);
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
                filepath: data.filepath,
                filename: data.filename,
                duration: 5,
                keepAudio: true,
                startTransition: 'fade',  // Default start transition
                endTransition: 'fade'     // Default end transition
            });
            window.timelineManager.updateUI();
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
                            onchange="updateDuration(${index}, this.value)" min="0.1" step="0.1">
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group mb-3">
                                <label>Start Transition</label>
                                <select class="form-control" onchange="updateTransition(${index}, this.value, 'start')">
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
                                <select class="form-control" onchange="updateTransition(${index}, this.value, 'end')">
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
                            onchange="updateAudio(${index}, this.checked)">
                        <label class="form-check-label">Keep Audio</label>
                    </div>
                    <button class="btn btn-danger btn-sm" onclick="removeItem(${index})">Remove</button>
                </div>
            </div>
        `;
        timelineContainer.appendChild(element);
    });

    updateDurationDisplay();
}

function updateDuration(index, value) {
    const duration = parseFloat(value);
    if (duration > 0) {
        window.timelineManager.items[index].duration = duration;
        window.timelineManager.updateUI();
    }
}

function updateAudio(index, value) {
    window.timelineManager.items[index].keepAudio = value;
    window.timelineManager.updateUI();
}

function removeItem(index) {
    window.timelineManager.items.splice(index, 1);
    window.timelineManager.updateUI();
}

function updateTransition(index, value, position) {
    if (position === 'start') {
        window.timelineManager.items[index].startTransition = value;
    } else {
        window.timelineManager.items[index].endTransition = value;
    }
    window.timelineManager.updateUI();
}

async function exportVideo() {
    if (window.timelineManager.items.length === 0) {
        showAlert('Timeline is empty!', 'warning');
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

            if (isNaN(width) || isNaN(height) || width < 240 || height < 240) {
                showAlert('Invalid resolution values', 'warning');
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

        const data = await response.json();
        if (data.success) {
            window.location.href = `/download/${data.output}`;
            showAlert('Export successful!', 'success');
        } else {
            showAlert('Export failed: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Export failed: ' + error, 'danger');
    } finally {
        exportBtn.disabled = false;
        exportBtn.innerHTML = 'Export Video';
    }
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
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    alertContainer.appendChild(alert);
    setTimeout(() => alert.remove(), 5000);
}