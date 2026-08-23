// Common functionality for the application
// Maximum upload size will be fetched from the backend
window.uploadMaxSize = 10 * 1024 * 1024;

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
        fileInput.dispatchEvent(new Event('change', {bubbles: true}));
    }
}

// Form validation
function validateForm(form) {
    const fileInput = form.querySelector('input[type="file"]');
    // Shared pages also contain ordinary forms (feedback, filters, admin forms).
    if (!fileInput) return true;
    if (!fileInput.files.length) {
        alert('Please select a file to upload');
        return false;
    }

    const file = fileInput.files[0];
    if (file.size > window.uploadMaxSize) {
        alert(`File size exceeds ${window.uploadMaxSize / (1024 * 1024)}MB limit`);
        return false;
    }

    return true;
}

// Initialize all components when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Fetch upload limits from backend
    fetch('/api/upload_config')
        .then(resp => resp.json())
        .then(cfg => {
            if (cfg.max_size) {
                window.uploadMaxSize = cfg.max_size;
            }
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
