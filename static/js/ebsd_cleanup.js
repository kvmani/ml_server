document.addEventListener('DOMContentLoaded', function () {
  const dropZone = document.getElementById('dropZone');
  const fileInput = document.getElementById('fileInput');
  const browseBtn = document.getElementById('browseBtn');
  const uploadForm = document.getElementById('uploadForm');
  const previewContainer = document.getElementById('previewContainer');
  const originalPreview = document.getElementById('originalPreview');
  const enhancedPreview = document.getElementById('enhancedPreview');
  const downloadBtn = document.getElementById('downloadBtn');
  const loadingState = document.getElementById('loadingState');

  fileInput.addEventListener('change', handleFiles);
  browseBtn.addEventListener('click', () => fileInput.click());

  function pollStatus(taskId) {
    fetch(`/ebsd_cleanup_status/${taskId}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.status && data.status !== 'SUCCESS') {
          setTimeout(() => pollStatus(taskId), 1000);
        } else if (data.success) {
          loadingState.classList.add('d-none');
          originalPreview.src = data.original_map;
          enhancedPreview.src = data.enhanced_map;
          enhancedPreview.onload = () => downloadBtn.classList.remove('d-none');
        } else {
          loadingState.classList.add('d-none');
          alert(data.error || 'Error processing EBSD data');
        }
      })
      .catch(() => {
        loadingState.classList.add('d-none');
        alert('Failed to retrieve processing status');
      });
  }

  function handleFiles() {
    const files = fileInput.files;
    if (!files.length) return;
    const file = files[0];
    const valid = ['.ang', '.ctf', '.cpr', '.osc', '.h5', '.hdf5'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!valid.includes(ext)) {
      alert('Please upload a valid EBSD file (.ang, .ctf, .cpr, .osc, .h5, .hdf5)');
      return;
    }

    const formData = new FormData(uploadForm);
    formData.append('ebsd_file', file);
    previewContainer.classList.remove('d-none');
    loadingState.classList.remove('d-none');
    downloadBtn.classList.add('d-none');

    fetch('/ebsd_cleanup', { method: 'POST', body: formData })
      .then((r) => r.json())
      .then((data) => {
        if (data.task_id) {
          pollStatus(data.task_id);
        } else if (data.success) {
          loadingState.classList.add('d-none');
          originalPreview.src = data.original_map;
          enhancedPreview.src = data.enhanced_map;
          enhancedPreview.onload = () => downloadBtn.classList.remove('d-none');
        } else {
          loadingState.classList.add('d-none');
          alert(data.error || 'Error processing EBSD data');
        }
      })
      .catch(() => {
        loadingState.classList.add('d-none');
        alert('An error occurred while processing the EBSD data.');
      });
  }

  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach((e) => {
    dropZone.addEventListener(e, preventDefaults, false);
    document.body.addEventListener(e, preventDefaults, false);
  });
  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  ['dragenter', 'dragover'].forEach((e) => dropZone.addEventListener(e, highlight, false));
  ['dragleave', 'drop'].forEach((e) => dropZone.addEventListener(e, unhighlight, false));
  function highlight() {
    dropZone.classList.add('dragover');
  }
  function unhighlight() {
    dropZone.classList.remove('dragover');
  }
  dropZone.addEventListener('drop', handleDrop, false);
  function handleDrop(e) {
    const files = e.dataTransfer.files;
    fileInput.files = files;
    handleFiles();
  }
});
