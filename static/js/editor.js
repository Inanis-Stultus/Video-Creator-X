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

    function validateFile(file) {
        // Check file size
        if (file.size > MAX_FILE_SIZE) {
            throw new Error(`File ${file.name} is too large. Maximum size is 16MB`);
        }

        // Check file type
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
                    startTransition: 'fade',
                    endTransition: 'fade'
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
});