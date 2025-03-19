// document.addEventListener('DOMContentLoaded', function() {
//     const uploadBox = document.getElementById('uploadBox');
//     const fileInput = document.getElementById('fileInput');
//     const originalContainer = document.getElementById('originalImageContainer');
//     const processedContainer = document.getElementById('processedImageContainer');
//     const comparisonSlider = document.getElementById('comparison-slider');
//     const sliderHandle = comparisonSlider.querySelector('.slider-handle');
//     const buttonContainer = document.getElementById('button-container');

//     // Initialize slider position
//     let isSliding = false;
//     let sliderPosition = 50;
//     let startX = 0;
//     let startPosition = 0;
//     let processedImageBlob = null;

//     // Slider functionality with improved touch and mouse handling
//     function updateSliderPosition(clientX) {
//         const rect = comparisonSlider.getBoundingClientRect();
//         const deltaX = clientX - startX;
//         let newPosition = startPosition + (deltaX / rect.width * 100);
//         newPosition = Math.min(Math.max(newPosition, 0), 100);
//         sliderPosition = newPosition;
        
//         sliderHandle.style.left = `${newPosition}%`;
//         processedContainer.style.clipPath = `polygon(0 0, ${newPosition}% 0, ${newPosition}% 100%, 0 100%)`;
//     }

//     function startSliding(e) {
//         isSliding = true;
//         startX = e.type.includes('mouse') ? e.clientX : e.touches[0].clientX;
//         startPosition = sliderPosition;
//         sliderHandle.classList.add('active');
//     }

//     function stopSliding() {
//         isSliding = false;
//         sliderHandle.classList.remove('active');
//     }

//     // Mouse events for slider
//     sliderHandle.addEventListener('mousedown', startSliding);
//     document.addEventListener('mousemove', (e) => {
//         if (!isSliding) return;
//         e.preventDefault();
//         updateSliderPosition(e.clientX);
//     });
//     document.addEventListener('mouseup', stopSliding);

//     // Touch events for slider
//     sliderHandle.addEventListener('touchstart', startSliding);
//     document.addEventListener('touchmove', (e) => {
//         if (!isSliding) return;
//         e.preventDefault();
//         updateSliderPosition(e.touches[0].clientX);
//     });
//     document.addEventListener('touchend', stopSliding);

//     // Prevent default touch behavior
//     sliderHandle.addEventListener('touchstart', (e) => e.preventDefault(), { passive: false });

//     // Drag and drop handling with improved visual feedback
//     uploadBox.addEventListener('dragover', (e) => {
//         e.preventDefault();
//         uploadBox.classList.add('drag-over');
//     });

//     uploadBox.addEventListener('dragleave', () => {
//         uploadBox.classList.remove('drag-over');
//     });

//     uploadBox.addEventListener('drop', (e) => {
//         e.preventDefault();
//         uploadBox.classList.remove('drag-over');
//         const file = e.dataTransfer.files[0];
//         handleFile(file);
//     });

//     // File input handling
//     fileInput.addEventListener('change', (e) => {
//         const file = e.target.files[0];
//         handleFile(file);
//     });

//     function handleFile(file) {
//         // Clear previous error messages and buttons
//         clearFlashMessages();
//         if (buttonContainer) {
//             buttonContainer.innerHTML = '';
//         }

//         // Validate file
//         if (!file) {
//             showError('Please select a file');
//             return;
//         }

//         if (!file.type.startsWith('image/')) {
//             showError('Please upload an image file');
//             return;
//         }

//         // Show original image preview
//         const reader = new FileReader();
//         reader.onload = (e) => {
//             // Display original image on the right side
//             originalContainer.innerHTML = `
//                 <img src="${e.target.result}" alt="Original Image" style="width: 100%; height: 100%; object-fit: cover;">
//                 <div class="image-label after-label">Original Image (Right)</div>
//             `;
//             processedContainer.innerHTML = '<div class="loading">Processing image...</div>';
            
//             // Reset slider position
//             sliderPosition = 50;
//             sliderHandle.style.left = '50%';
//             processedContainer.style.clipPath = 'polygon(0 0, 50% 0, 50% 100%, 0 100%)';
//         };
//         reader.readAsDataURL(file);

//         // Upload and process image
//         const formData = new FormData();
//         formData.append('image', file);

//         fetch('/super_resolution/process', {
//             method: 'POST',
//             body: formData
//         })
//         .then(response => {
//             if (!response.ok) {
//                 return response.json().then(data => {
//                     throw new Error(data.details || data.error || 'Error processing image');
//                 });
//             }
//             return response.blob();
//         })
//         .then(blob => {
//             processedImageBlob = blob;
//             const url = URL.createObjectURL(blob);
            
//             // Display processed image on the left side
//             processedContainer.innerHTML = `
//                 <img src="${url}" alt="Enhanced Image" style="width: 100%; height: 100%; object-fit: cover;">
//                 <div class="image-label before-label">Enhanced Image (Left)</div>
//             `;
            
//             // Add download button below the image container
//             if (buttonContainer) {
//                 buttonContainer.innerHTML = `
//                     <button class="download-btn" onclick="downloadImage()">Download Enhanced Image</button>
//                 `;
//             }
            
//             // Reset slider position
//             sliderPosition = 50;
//             sliderHandle.style.left = '50%';
//             processedContainer.style.clipPath = 'polygon(0 0, 50% 0, 50% 100%, 0 100%)';
//         })
//         .catch(error => {
//             processedContainer.innerHTML = '<div class="error">Error processing image</div>';
//             showError(error.message);
//         });
//     }

//     // Add download function to window object for button click
//     window.downloadImage = function() {
//         if (!processedImageBlob) {
//             showError('No enhanced image available to download');
//             return;
//         }

//         const link = document.createElement('a');
//         const url = URL.createObjectURL(processedImageBlob);
//         link.href = url;
//         link.download = 'enhanced_image.png';
        
//         document.body.appendChild(link);
//         link.click();
//         document.body.removeChild(link);
        
//         URL.revokeObjectURL(url);
//     };

//     function showError(message) {
//         const flashMessages = document.querySelector('.flash-messages');
//         if (!flashMessages) return;

//         const errorDiv = document.createElement('div');
//         errorDiv.className = 'flash-message error';
//         errorDiv.textContent = message;
//         flashMessages.appendChild(errorDiv);

//         // Auto-remove after 5 seconds
//         setTimeout(() => {
//             errorDiv.remove();
//         }, 5000);
//     }

//     function clearFlashMessages() {
//         const flashMessages = document.querySelector('.flash-messages');
//         if (flashMessages) {
//             flashMessages.innerHTML = '';
//         }
//     }
// });

document.addEventListener('DOMContentLoaded', function() {
    const uploadBox = document.getElementById('uploadBox');
    const fileInput = document.getElementById('fileInput');
    const originalContainer = document.getElementById('originalImageContainer');
    const processedContainer = document.getElementById('processedImageContainer');
    const buttonContainer = document.getElementById('button-container');
    let processedImageBlob = null;

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

        const reader = new FileReader();
        reader.onload = (e) => {
            // Upload the image to the BEFORE section
            originalContainer.innerHTML = `
                <div class="image-wrapper">
                    <img src="${e.target.result}" alt="Original Image" class="image-before">
                    <span class="image-label before-label">Before</span>
                </div>
            `;
            processedContainer.innerHTML = '<div class="loading">Processing image...</div>';
        };
        reader.readAsDataURL(file);

        const formData = new FormData();
        formData.append('image', file);

        fetch('/super_resolution/process', {
            method: 'POST',
            body: formData
        })
        .then(response => response.blob())
        .then(blob => {
            processedImageBlob = blob;
            const url = URL.createObjectURL(blob);
            
            // Apply flip transformation to the AFTER section
            processedContainer.innerHTML = `
                <div class="image-wrapper">
                    <img src="${url}" alt="Flipped Image" class="image-after" style="transform: scaleX(-1);">
                    <span class="image-label after-label">After</span>
                </div>
            `;

            if (buttonContainer) {
                buttonContainer.innerHTML = `
                    <button class="enhance-btn" onclick="downloadImage()">Enhance Image</button>
                    <button class="download-btn" onclick="downloadImage()">Download</button>
                `;
            }
        })
        .catch(error => {
            processedContainer.innerHTML = '<div class="error">Error processing image</div>';
        });
    }

    window.downloadImage = function() {
        if (!processedImageBlob) return;
        const link = document.createElement('a');
        const url = URL.createObjectURL(processedImageBlob);
        link.href = url;
        link.download = 'flipped_image.png';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };
});
