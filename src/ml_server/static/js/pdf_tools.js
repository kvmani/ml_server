document.addEventListener('DOMContentLoaded', () => {
    const addBtn = document.getElementById('addFileBtn');
    const list = document.getElementById('fileList');
    const form = document.getElementById('mergeForm');
    const status = document.getElementById('mergeStatus');
    const placeholder = '/static/images/preview_unavailable.svg';

    function createItem(input) {
        const div = document.createElement('div');
        div.className = 'pdf-item card p-2 mb-2';
        div.appendChild(input);

        const canvas = document.createElement('canvas');
        canvas.className = 'pdf-preview mb-1';
        div.appendChild(canvas);
        const info = document.createElement('div');
        info.className = 'small text-center';
        div.appendChild(info);

        list.appendChild(div);

        const reader = new FileReader();
        reader.onload = async e => {
            try {
                const pdf = await pdfjsLib.getDocument({data: e.target.result}).promise;
                const page = await pdf.getPage(1);
                const viewport = page.getViewport({scale: 1});
                const scale = 100 / viewport.height;
                const v = page.getViewport({scale});
                canvas.width = v.width;
                canvas.height = v.height;
                await page.render({canvasContext: canvas.getContext('2d'), viewport: v}).promise;
                info.textContent = `${input.files[0].name} (${pdf.numPages} pages)`;
            } catch (err) {
                const img = document.createElement('img');
                img.src = placeholder;
                img.className = 'mb-1';
                canvas.replaceWith(img);
                info.textContent = input.files[0].name;
            }
        };
        reader.readAsArrayBuffer(input.files[0]);
    }

    if (addBtn) {
        addBtn.addEventListener('click', () => {
            const input = document.createElement('input');
            input.type = 'file';
            input.name = 'files';
            input.accept = 'application/pdf';
            input.classList.add('d-none');
            input.addEventListener('change', () => input.files.length && createItem(input));
            form.appendChild(input);
            input.click();
        });
    }

    if (list) {
        new Sortable(list, {animation: 150});
    }

    form?.addEventListener('submit', () => {
        if (status) {
            status.textContent = '🔄 Please wait while your PDF files are being merged…';
        }
    });
});
