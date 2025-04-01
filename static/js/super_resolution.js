document.addEventListener('DOMContentLoaded', function () {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const browseBtn = document.getElementById('browseBtn');
    const uploadForm = document.getElementById('uploadForm');

    const previewContainer = document.getElementById('previewContainer');
    const originalPreview = document.getElementById('originalImage'); // Merged with new
    const enhancedPreview = document.getElementById('flippedImage');  // Merged with new
    const downloadBtn = document.getElementById('downloadBtn');
    const loadingSpinner = document.getElementById('loadingSpinner'); // Spinner from new

    // Handle file input via browse
    fileInput.addEventListener('change', handleFiles);
    browseBtn.addEventListener('click', () => fileInput.click());

    // Unified file handler
    function handleFiles() {
        const files = fileInput.files;
        if (files.length === 0) return;

        const file = files[0];
        const validExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();

        if (!validExtensions.includes(fileExtension)) {
            alert('Please upload a valid image file (PNG, JPG, JPEG, GIF, BMP, TIFF, or WebP)');
            return;
        }

        // Prepare form data
        const formData = new FormData(uploadForm);
        formData.append('image', file);

        // UI setup
        previewContainer.classList.remove('d-none');
        loadingSpinner.style.display = 'block';
        downloadBtn.style.display = 'none';
        originalPreview.style.display = 'none';
        enhancedPreview.style.display = 'none';

        // Fetch from server
        fetch('/superres', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                loadingSpinner.style.display = 'none';

                if (data.success) {
                    originalPreview.src = data.original_image;
                    enhancedPreview.src = data.enhanced_image;

                    originalPreview.style.display = 'block';
                    enhancedPreview.style.display = 'block';

                    // Enable download
                    downloadBtn.href = data.enhanced_image;
                    downloadBtn.download = 'flipped_' + file.name;
                    downloadBtn.style.display = 'inline-block';
                } else {
                    alert(data.error || 'Error processing image');
                }
            })
            .catch(error => {
                loadingSpinner.style.display = 'none';
                console.error('Error:', error);
                alert('An error occurred while processing the image. Please try again.');
            });
    }

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
        dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
    });

    dropZone.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        fileInput.files = files;
        handleFiles();
    }
});
