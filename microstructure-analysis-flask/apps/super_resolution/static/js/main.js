document.addEventListener('DOMContentLoaded', function() {
    const uploadBox = document.getElementById('uploadBox');
    const fileInput = document.getElementById('fileInput');
    const originalContainer = document.getElementById('originalImageContainer');
    const processedContainer = document.getElementById('processedImageContainer');
    const enhanceBtn = document.getElementById('enhanceBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const comparisonSlider = document.getElementById('comparison-slider');
    const sliderHandle = comparisonSlider.querySelector('.slider-handle');

    // Initialize slider position
    let isSliding = false;
    let sliderPosition = 50;

    // Slider functionality
    function updateSliderPosition(clientX) {
        const rect = comparisonSlider.getBoundingClientRect();
        let position = ((clientX - rect.left) / rect.width) * 100;
        position = Math.min(Math.max(position, 0), 100);
        sliderPosition = position;
        
        sliderHandle.style.left = `${position}%`;
        originalContainer.style.clipPath = `polygon(0 0, ${position}% 0, ${position}% 100%, 0 100%)`;
    }

    // Mouse events for slider
    sliderHandle.addEventListener('mousedown', () => {
        isSliding = true;
    });

    document.addEventListener('mousemove', (e) => {
        if (!isSliding) return;
        updateSliderPosition(e.clientX);
    });

    document.addEventListener('mouseup', () => {
        isSliding = false;
    });

    // Touch events for slider
    sliderHandle.addEventListener('touchstart', (e) => {
        isSliding = true;
    });

    document.addEventListener('touchmove', (e) => {
        if (!isSliding) return;
        updateSliderPosition(e.touches[0].clientX);
    });

    document.addEventListener('touchend', () => {
        isSliding = false;
    });

    // Drag and drop handling
    uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadBox.classList.add('drag-over');
    });

    uploadBox.addEventListener('dragleave', () => {
        uploadBox.classList.remove('drag-over');
    });

    uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadBox.classList.remove('drag-over');
        const file = e.dataTransfer.files[0];
        handleFile(file);
    });

    // File input handling
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        handleFile(file);
    });

    function handleFile(file) {
        // Clear previous error messages
        clearFlashMessages();

        // Validate file
        if (!file) {
            showError('Please select a file');
            return;
        }

        if (!file.type.startsWith('image/')) {
            showError('Please upload an image file');
            return;
        }

        // Show original image preview
        const reader = new FileReader();
        reader.onload = (e) => {
            originalContainer.innerHTML = `<img src="${e.target.result}" alt="Original Image">`;
            processedContainer.innerHTML = '<p>Processing...</p>';
            enhanceBtn.disabled = false;
        };
        reader.readAsDataURL(file);

        // Upload and process image
        const formData = new FormData();
        formData.append('image', file);

        fetch('/super_resolution/process', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.details || data.error || 'Error processing image');
                });
            }
            return response.blob();
        })
        .then(blob => {
            const url = URL.createObjectURL(blob);
            processedContainer.innerHTML = `<img src="${url}" alt="Enhanced Image">`;
            downloadBtn.disabled = false;
            
            // Reset slider position
            updateSliderPosition(comparisonSlider.getBoundingClientRect().left + (comparisonSlider.offsetWidth * 0.5));
        })
        .catch(error => {
            processedContainer.innerHTML = '<p>No image processed</p>';
            showError(error.message);
        });
    }

    function showError(message) {
        const flashMessages = document.querySelector('.flash-messages');
        if (!flashMessages) return;

        const errorDiv = document.createElement('div');
        errorDiv.className = 'flash-message error';
        errorDiv.textContent = message;
        flashMessages.appendChild(errorDiv);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    function clearFlashMessages() {
        const flashMessages = document.querySelector('.flash-messages');
        if (flashMessages) {
            flashMessages.innerHTML = '';
        }
    }

    // Download button handling
    downloadBtn.addEventListener('click', () => {
        const processedImage = processedContainer.querySelector('img');
        if (processedImage) {
            const link = document.createElement('a');
            link.href = processedImage.src;
            link.download = 'enhanced_image.png';
            link.click();
        }
    });

    // Feedback form handling
    const feedbackForm = document.getElementById('feedbackForm');
    feedbackForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = new FormData(feedbackForm);
        
        fetch('/super_resolution/feedback', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showError(data.message); // Using showError for success message too
                feedbackForm.reset();
            } else {
                throw new Error(data.error);
            }
        })
        .catch(error => {
            showError(error.message);
        });
    });
}); 