// Common functionality for the application

// Image comparison slider functionality
function initComparison() {
    const slider = document.querySelector('.comparison-slider');
    const beforeImage = document.querySelector('.original-image');
    const afterImage = document.querySelector('.enhanced-image');
    const sliderHandle = document.querySelector('.slider-handle');
    const beforeLabel = document.querySelector('.before-label');
    const afterLabel = document.querySelector('.after-label');

    if (!slider || !beforeImage || !afterImage || !sliderHandle) return;

    let isDragging = false;
    let startX;
    let sliderLeft;

    function updateSliderPosition(e) {
        const rect = slider.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const percentage = (x / rect.width) * 100;
        const clampedPercentage = Math.min(Math.max(percentage, 0), 100);
        
        sliderHandle.style.left = `${clampedPercentage}%`;
        afterImage.style.clipPath = `inset(0 ${100 - clampedPercentage}% 0 0)`;
        beforeLabel.style.left = `${clampedPercentage}%`;
        afterLabel.style.left = `${clampedPercentage}%`;
    }

    function startDragging(e) {
        isDragging = true;
        startX = e.clientX;
        sliderLeft = sliderHandle.offsetLeft;
        sliderHandle.classList.add('dragging');
    }

    function stopDragging() {
        isDragging = false;
        sliderHandle.classList.remove('dragging');
    }

    sliderHandle.addEventListener('mousedown', startDragging);
    document.addEventListener('mousemove', (e) => {
        if (isDragging) {
            updateSliderPosition(e);
        }
    });
    document.addEventListener('mouseup', stopDragging);
    document.addEventListener('mouseleave', stopDragging);

    // Touch events for mobile
    sliderHandle.addEventListener('touchstart', (e) => {
        isDragging = true;
        startX = e.touches[0].clientX;
        sliderLeft = sliderHandle.offsetLeft;
        sliderHandle.classList.add('dragging');
    });

    document.addEventListener('touchmove', (e) => {
        if (isDragging) {
            e.preventDefault();
            updateSliderPosition(e.touches[0]);
        }
    });

    document.addEventListener('touchend', stopDragging);
}

// File upload handling
function handleFileUpload(input, previewContainer, loadingState) {
    const file = input.files[0];
    if (!file) return;

    // Show loading state
    previewContainer.classList.remove('d-none');
    loadingState.classList.remove('d-none');
    previewContainer.classList.remove('loaded');

    // Create FormData
    const formData = new FormData();
    formData.append('file', file);

    // Send file to server
    fetch('/super_resolution', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update preview images
            const originalPreview = document.querySelector('.original-image');
            const enhancedPreview = document.querySelector('.enhanced-image');
            
            if (originalPreview && enhancedPreview) {
                originalPreview.src = data.original_image;
                enhancedPreview.src = data.enhanced_image;
                
                enhancedPreview.onload = () => {
                    previewContainer.classList.add('loaded');
                    loadingState.classList.add('d-none');
                    initComparison();
                };
            }
        } else {
            throw new Error(data.error || 'Upload failed');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        loadingState.classList.add('d-none');
        alert('An error occurred while processing the file. Please try again.');
    });
}

// Drag and drop functionality
function initDragAndDrop(dropZone, fileInput) {
    if (!dropZone || !fileInput) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
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
        dropZone.classList.add('highlight');
    }

    function unhighlight(e) {
        dropZone.classList.remove('highlight');
    }

    dropZone.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        fileInput.files = files;
        handleFileUpload(fileInput);
    }
}

// Form validation
function validateForm(form) {
    const fileInput = form.querySelector('input[type="file"]');
    if (!fileInput || !fileInput.files.length) {
        alert('Please select a file to upload');
        return false;
    }

    const file = fileInput.files[0];
    const maxSize = 16 * 1024 * 1024; // 16MB
    if (file.size > maxSize) {
        alert('File size exceeds 16MB limit');
        return false;
    }

    return true;
}

// Initialize all components when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize file upload handlers
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const previewContainer = this.closest('.upload-container').nextElementSibling;
            const loadingState = previewContainer.querySelector('.loading-state');
            handleFileUpload(this, previewContainer, loadingState);
        });
    });

    // Initialize drag and drop
    const dropZones = document.querySelectorAll('.drop-zone');
    dropZones.forEach(zone => {
        const fileInput = zone.querySelector('input[type="file"]');
        initDragAndDrop(zone, fileInput);
    });

    // Initialize form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
    });

    // Initialize tooltips
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        new bootstrap.Tooltip(tooltip);
    });
}); 