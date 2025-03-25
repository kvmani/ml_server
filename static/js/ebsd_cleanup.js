document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const browseBtn = document.getElementById('browseBtn');
    const uploadForm = document.getElementById('uploadForm');
    const previewContainer = document.getElementById('previewContainer');
    const originalPreview = document.getElementById('originalPreview');
    const enhancedPreview = document.getElementById('enhancedPreview');
    const downloadBtn = document.getElementById('downloadBtn');
    const loadingState = document.getElementById('loadingState');

    // Initialize JSZip
    const JSZip = window.JSZip;

    // Handle file selection
    fileInput.addEventListener('change', handleFiles);
    browseBtn.addEventListener('click', () => fileInput.click());

    function handleFiles() {
        const files = fileInput.files;
        if (files.length) {
            const file = files[0];
            const validExtensions = ['.ang', '.ctf', '.cpr', '.osc', '.h5', '.hdf5'];
            const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
            
            if (validExtensions.includes(fileExtension)) {
                const formData = new FormData(uploadForm);
                formData.append('ebsd_file', file);
                
                previewContainer.classList.remove('d-none');
                loadingState.classList.remove('d-none');
                downloadBtn.classList.add('d-none');
                
                fetch('/ebsd_cleanup', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        loadingState.classList.add('d-none');
                        
                        // Set image sources directly
                        originalPreview.src = data.original_map;
                        enhancedPreview.src = data.enhanced_map;
                        
                        // Make sure images are visible
                        originalPreview.style.display = 'block';
                        enhancedPreview.style.display = 'block';
                        
                        // Enable download button when images are loaded
                        enhancedPreview.onload = () => {
                            downloadBtn.classList.remove('d-none');
                        };
                        
                        // Set up download functionality
                        downloadBtn.onclick = () => {
                            window.location.href = '/download_processed_data';
                        };
                    } else {
                        alert(data.error || 'Error processing EBSD data');
                        loadingState.classList.add('d-none');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    loadingState.classList.add('d-none');
                    alert('An error occurred while processing the EBSD data. Please try again.');
                });
            } else {
                alert('Please upload a valid EBSD file (.ang, .ctf, .cpr, .osc, .h5, or .hdf5)');
            }
        }
    }

    // Handle drag and drop
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
