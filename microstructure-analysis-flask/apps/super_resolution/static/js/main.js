document.addEventListener('DOMContentLoaded', function() {
    const uploadBox = document.getElementById('uploadBox');
    const fileInput = document.getElementById('fileInput');
    const originalContainer = document.getElementById('originalImageContainer');
    const processedContainer = document.getElementById('processedImageContainer');
    const buttonContainer = document.getElementById('button-container');
    const comparisonSlider = document.getElementById('comparison-slider');
    const sliderHandle = document.createElement('div');
    let processedImageBlob = null;
    let uploadedFile = null;

    // Add slider handle functionality
    sliderHandle.classList.add('slider-handle');
    comparisonSlider.appendChild(sliderHandle);

    let isSliding = false;
    let startX = 0;
    let startPosition = 50;

    function updateSliderPosition(clientX) {
        const rect = comparisonSlider.getBoundingClientRect();
        const deltaX = clientX - startX;
        let newPosition = startPosition + (deltaX / rect.width * 100);
        newPosition = Math.min(Math.max(newPosition, 0), 100);

        sliderHandle.style.left = `${newPosition}%`;
        processedContainer.style.clipPath = `polygon(0 0, ${newPosition}% 0, ${newPosition}% 100%, 0 100%)`;
        originalContainer.style.clipPath = `polygon(${newPosition}% 0, 100% 0, 100% 100%, ${newPosition}% 100%)`;

        if (newPosition > 50 && !processedContainer.dataset.loaded) {
            processImage();
        }
    }

    function startSliding(e) {
        isSliding = true;
        startX = e.type.includes('mouse') ? e.clientX : e.touches[0].clientX;
        startPosition = parseFloat(sliderHandle.style.left) || 50;
    }

    function stopSliding() {
        isSliding = false;
    }

    sliderHandle.addEventListener('mousedown', startSliding);
    document.addEventListener('mousemove', (e) => {
        if (isSliding) updateSliderPosition(e.clientX);
    });
    document.addEventListener('mouseup', stopSliding);

    sliderHandle.addEventListener('touchstart', startSliding);
    document.addEventListener('touchmove', (e) => {
        if (isSliding) updateSliderPosition(e.touches[0].clientX);
    });
    document.addEventListener('touchend', stopSliding);

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

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        handleFile(file);
    });

    function handleFile(file) {
        if (!file) return;
        if (!file.type.startsWith('image/')) return;

        uploadedFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            originalContainer.innerHTML = `
                <div class="image-wrapper" style="max-width: 400px; max-height: 250px; margin: auto;">
                    <img src="${e.target.result}" alt="Original Image" class="image-before" style="width: 100%; height: auto; object-fit: contain;">
                    <span class="image-label before-label">Before</span>
                </div>
            `;
            processedContainer.innerHTML = '<div class="loading">Slide to enhance...</div>';
            processedContainer.dataset.loaded = "false";
        };
        reader.readAsDataURL(file);
    }

    function processImage() {
        if (!uploadedFile) return;

        const formData = new FormData();
        formData.append('image', uploadedFile);

        fetch('/super_resolution/process', {
            method: 'POST',
            body: formData
        })
        .then(response => response.blob())
        .then(blob => {
            processedImageBlob = blob;
            const url = URL.createObjectURL(blob);
            
            processedContainer.innerHTML = `
                <div class="image-wrapper" style="max-width: 400px; max-height: 250px; margin: auto;">
                    <img src="${url}" alt="Enhanced Image" class="image-after" style="width: 100%; height: auto; object-fit: contain; transform: scaleX(-1);">
                    <span class="image-label after-label">After</span>
                </div>
            `;
            processedContainer.dataset.loaded = "true";
        })
        .catch(error => {
            processedContainer.innerHTML = '<div class="error">Error processing image</div>';
        });
    }

    // Feedback form handling
    const feedbackForm = document.querySelector('.feedback-form');
    if (feedbackForm) {
        feedbackForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const feedbackText = feedbackForm.querySelector('textarea[name="feedback"]').value.trim();
            if (!feedbackText) {
                showNotification('Please enter your feedback', 'error');
                return;
            }

            const formData = new URLSearchParams();
            formData.append('feedback', feedbackText);

            fetch('/super_resolution/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData.toString()
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification(data.message, 'success');
                    feedbackForm.querySelector('textarea').value = ''; // Clear the textarea
                } else {
                    showNotification(data.error || 'Error submitting feedback', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Error submitting feedback', 'error');
            });
        });
    }

    // Notification function
    function showNotification(message, type = 'success') {
        // Remove any existing notifications
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(notification => notification.remove());

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Remove notification after 3 seconds
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
});


