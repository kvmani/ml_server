// ===== pdf_merge_ui.js  (final tidy) =====
//  Replace entire file with this version  ▸ 2025‑08‑07

const dropZone        = document.getElementById('drop-zone');
const fileInput       = document.getElementById('file-input');
const fileList        = document.getElementById('file-list');
const mergeBtn        = document.getElementById('btn-merge');
const outputNameInput = document.getElementById('output-name');
const addFileBtn      = document.getElementById('btn-add-file');
const spinner         = document.createElement('div');
spinner.id = 'merge-spinner';
spinner.style.cssText = 'display:none;position:fixed;inset:0;z-index:1050;background:rgba(255,255,255,.6);'+
                        'align-items:center;justify-content:center;font-size:2rem;';
spinner.innerHTML = '<div class="spinner-border text-primary" role="status"></div>';
document.body.appendChild(spinner);

let files = [];                // [{file,range}]
let sortable = null;            // SortableJS instance

//----------------------------------
//  Utilities
//----------------------------------
const human = b => b>1048576? (b/1048576).toFixed(1)+' MB' : (b/1024).toFixed(1)+' KB';
const truncate = n => n.length>50? n.slice(0,47)+'…': n;
function showSpinner(on=true){ spinner.style.display = on? 'flex':'none'; }

//----------------------------------
//  File‑selection handlers
//----------------------------------
addFileBtn.onclick = () => fileInput.click();
fileInput.onchange = e => handleFiles(e.target.files);

dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('bg-info'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('bg-info'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('bg-info');
  handleFiles(e.dataTransfer.files);
});

function handleFiles(listLike){
  for(const f of listLike) if(f.type==='application/pdf') files.push({file:f, range:'all'});
  renderList();
}

//----------------------------------
//  Render previews + meta
//----------------------------------
function renderList(){
  fileList.innerHTML='';
  files.forEach((it,idx)=>{
    const card=document.createElement('div');
    card.className='file-card position-relative';
    card.dataset.index=idx;

    // delete btn
    const del=document.createElement('span');
    del.textContent='×';
    del.className='remove-btn position-absolute top-0 end-0 px-2';
    del.style.cssText='font-size:1.4rem;color:#d00;cursor:pointer;';
    del.onclick=()=>{files.splice(idx,1);renderList();};
    card.appendChild(del);

    // FileReader -> PDF.js preview
    const r=new FileReader();
    r.onload=()=>{
      pdfjsLib.getDocument({data:new Uint8Array(r.result)}).promise.then(pdf=>{
        pdf.getPage(1).then(p=>{
          const vp=p.getViewport({scale:1});
          const cv=document.createElement('canvas');
          cv.className='file-thumb mb-1';
          cv.height=180; cv.width=180*vp.width/vp.height;
          p.render({canvasContext:cv.getContext('2d'), viewport:p.getViewport({scale:cv.width/vp.width})});
          card.prepend(cv);
          const meta=document.createElement('div');
          meta.innerHTML=`<div class="fw-bold truncate-text" style="font-size:1rem;">${truncate(it.file.name.replace(/\.pdf$/i,''))}</div>
                          <div style="font-size:0.9rem;">${human(it.file.size)}</div>
                          <div style="font-size:0.9rem;">${pdf.numPages} pages</div>`;
          card.appendChild(meta);
          const inp=document.createElement('input');
          inp.className='form-control form-control-sm page-input mt-1';
          inp.value=it.range; inp.onchange=e=>{it.range=e.target.value};
          card.appendChild(inp);
        });
      });
    };
    r.readAsArrayBuffer(it.file);

    fileList.appendChild(card);
  });
  mergeBtn.disabled = !files.length;
  attachSortable();
}

//----------------------------------
//  Sortable attach/detach
//----------------------------------
function attachSortable(){
  if(sortable) sortable.destroy();
  sortable=new Sortable(fileList,{
    animation:150,
    onEnd:e=>{ if(e.oldIndex!==e.newIndex){ const m=files.splice(e.oldIndex,1)[0]; files.splice(e.newIndex,0,m); renderList(); } }
  });
}

//----------------------------------
//  Merge handler (type="button" on HTML)
//----------------------------------
mergeBtn.onclick = async ()=>{
  if(!files.length) return; // button disabled anyway
  showSpinner(true);
  const fd=new FormData();
  files.forEach((it,i)=>{fd.append(`file${i}`,it.file);fd.append(`range_file${i}`,it.range||'all');});
  fd.append('order',files.map((_,i)=>i).join(','));
  fd.append('output_name',outputNameInput.value||'merged.pdf');

  try{
    const res=await fetch('/pdf-tools/merge',{method:'POST',body:fd});
    const ct=res.headers.get('content-type')||'';
    let blob;
    if(ct.startsWith('application/pdf')) blob=await res.blob();
    else{
      const js=await res.json();
      if(!js.success) throw new Error(js.error||'Merge failed');
      blob=new Blob([Uint8Array.from(js.data.match(/.{1,2}/g).map(h=>parseInt(h,16)))],{type:'application/pdf'});
    }
    const a=document.createElement('a');
    a.href=URL.createObjectURL(blob);a.download=outputNameInput.value||'merged.pdf';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),5e3);
  }catch(err){ alert('Merge failed: '+err.message); }
  finally{ showSpinner(false); }
};
