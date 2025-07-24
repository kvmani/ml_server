// Simple drag-and-drop form handling for hydride segmentation

document.addEventListener('DOMContentLoaded', function () {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('image');
    const browseBtn = document.getElementById('browse-button');
    const fileName = document.getElementById('file-name');
    const algoSelect = document.getElementById('algorithm');
    const convFields = document.getElementById('conv-fields');

    if (!dropZone || !fileInput) {
        return;
    }

    browseBtn.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', updateFileName);

    function updateFileName() {
        if (fileInput.files.length) {
            fileName.textContent = fileInput.files[0].name;
        } else {
            fileName.textContent = '';
        }
    }

    ['dragenter', 'dragover'].forEach(evt => {
        dropZone.addEventListener(evt, (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(evt => {
        dropZone.addEventListener(evt, (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            updateFileName();
        }
    });

    function toggleParams() {
        convFields.style.display = algoSelect.value === 'conventional' ? 'block' : 'none';
    }

    algoSelect.addEventListener('change', toggleParams);
    toggleParams();
});
