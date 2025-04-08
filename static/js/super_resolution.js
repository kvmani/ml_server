document.addEventListener('DOMContentLoaded', function () {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const browseBtn = document.getElementById('browseBtn');
    const uploadForm = document.getElementById('uploadForm');

    const previewContainer = document.getElementById('previewContainer');
    const originalImage = document.getElementById('originalImage');
    const flippedImage = document.getElementById('flippedImage');
    const downloadBtn = document.getElementById('downloadBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');

    async function checkModelStatus() {
        try {
            const response = await fetch('/api/check_model_status');
            const data = await response.json();
            return data.running;
        } catch (error) {
            console.error('Error checking model status:', error);
            return false;
        }
    }

    async function handleFiles() {
        const files = fileInput.files;
        if (!files.length) return;

        const file = files[0];
        const validExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();

        if (!validExtensions.includes(fileExtension)) {
            alert('Please upload a valid image file');
            return;
        }

        // Show loading state immediately
        previewContainer.classList.remove('d-none');
        loadingSpinner.style.display = 'block';
        downloadBtn.style.display = 'none';

        try {
            // Check if ML model is running
            const modelRunning = await checkModelStatus();
            if (!modelRunning) {
                throw new Error('ML Model is not running. Please try again later.');
            }

            const formData = new FormData();
            formData.append('image', file);

            const response = await fetch('/super_resolution', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Display both original and flipped images
                originalImage.src = data.original_image;
                flippedImage.src = data.enhanced_image;
                
                // Show download button and set correct filename
                downloadBtn.href = data.enhanced_image;
                downloadBtn.download = 'flipped_' + file.name;
                downloadBtn.style.display = 'inline-block';
            } else {
                throw new Error(data.error || 'Processing failed');
            }
        } catch (error) {
            console.error('Error:', error);
            alert(error.message || 'Error processing image. Please try again.');
        } finally {
            loadingSpinner.style.display = 'none';
        }
    }

    fileInput.addEventListener('change', handleFiles);
    browseBtn.addEventListener('click', () => fileInput.click());

    // Drag-and-drop support
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        dropZone.classList.add('dragover');
    }

    function unhighlight(e) {
        dropZone.classList.remove('dragover');
    }

    dropZone.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        fileInput.files = files;
        handleFiles();
    }
});
