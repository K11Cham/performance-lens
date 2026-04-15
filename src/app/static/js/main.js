let currentStep = 1;
const totalSteps = 4;
let formData = { name: '', email: '', password: '', level: '', file: null };

// --- TRANSITIONS ---
function goToStep(step) {
    if (step === currentStep) return;
    const curr = document.getElementById('step' + currentStep);
    const next = document.getElementById('step' + step);
    const fwd = step > currentStep;

    next.style.transition = 'none';
    next.style.opacity = '0';
    next.style.transform = fwd ? 'translateX(40px)' : 'translateX(-40px)';
    next.offsetHeight;

    const t = 'opacity 0.3s ease, transform 0.3s ease';
    next.style.transition = t;
    curr.style.transition = t;

    next.style.opacity = '1';
    next.style.transform = 'translateX(0)';
    next.style.pointerEvents = 'all';

    curr.style.opacity = '0';
    curr.style.transform = fwd ? 'translateX(-40px)' : 'translateX(40px)';
    curr.style.pointerEvents = 'none';

    currentStep = step;
    updateProgress();
    if (step === 4) triggerCheckAnim();
}

function updateProgress() {
    document.getElementById('progressFill').style.width = ((currentStep - 1) / (totalSteps - 1)) * 100 + '%';
    document.getElementById('stepLabel').textContent = currentStep + ' / ' + totalSteps;
}

function triggerCheckAnim() {
    const c = document.getElementById('checkAnim');
    c.classList.remove('pop');
    void c.offsetWidth;
    c.classList.add('pop');
}

// --- FLOATING LABELS ---
function setupFloatingLabels() {
    const inputs = document.querySelectorAll('.input-field');
    inputs.forEach(input => {
        // Check initial state (handles browser autofill)
        if (input.value.trim() !== '') input.classList.add('has-value');

        input.addEventListener('input', () => {
            input.classList.toggle('has-value', input.value.trim() !== '');
        });
        
        // Force check on focus too, just in case
        input.addEventListener('focus', () => {
            input.classList.add('has-value');
        });
        
        input.addEventListener('blur', () => {
            if (input.value.trim() === '') input.classList.remove('has-value');
        });
    });
}

// --- INIT ---
window.addEventListener('DOMContentLoaded', () => {
    const s1 = document.getElementById('step1');
    if(s1) {
        s1.style.transition = 'none';
        s1.style.opacity = '1';
        s1.style.transform = 'translateX(0)';
        s1.style.pointerEvents = 'all';
    }
    setupFloatingLabels();
    setupUploadZone();
});

// --- PROFILE ---
function handleProfile(e) {
    e.preventDefault();
    formData.name = document.getElementById('fullName').value.trim();
    formData.email = document.getElementById('email').value.trim();
    formData.password = document.getElementById('password').value;
    if (formData.name && formData.email && formData.password.length >= 6) goToStep(3);
    return false;
}

// --- ACADEMICS ---
function selectLevel(el) {
    document.querySelectorAll('.level-card').forEach(c => c.classList.remove('selected'));
    el.classList.add('selected');
    formData.level = el.dataset.level;
}

function setupUploadZone() {
    const zone = document.getElementById('uploadZone');
    const input = document.getElementById('fileInput');
    if (!zone || !input) return;

    zone.addEventListener('click', () => input.click());
    ['dragenter', 'dragover'].forEach(evt => { zone.addEventListener(evt, e => { e.preventDefault(); zone.classList.add('dragover'); }); });
    ['dragleave', 'drop'].forEach(evt => { zone.addEventListener(evt, e => { e.preventDefault(); zone.classList.remove('dragover'); }); });
    
    zone.addEventListener('drop', e => { if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]); });
    input.addEventListener('change', () => { if (input.files.length) handleFile(input.files[0]); });
}

function handleFile(file) {
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!['.csv', '.xls', '.xlsx'].includes(ext)) { alert('Please upload a CSV or Excel file.'); return; }

    formData.file = file;
    const zone = document.getElementById('uploadZone');
    zone.classList.add('has-file');
    document.getElementById('uploadIcon').innerHTML = '<i class="fa-solid fa-file-circle-check text-emerald-500 text-3xl"></i>';
    document.getElementById('uploadText').innerHTML = '<span class="font-medium text-sm" style="color: var(--color-success)">' + file.name + '</span>';
    document.getElementById('uploadSubtext').textContent = 'Click to change file';
}

function handleAcademics() {
    const err = document.getElementById('academicsError');
    if (!formData.level || !formData.file) { err.classList.remove('hidden'); return; }
    err.classList.add('hidden');

    const map = { 'high-school': 'High School', 'undergrad': 'Undergraduate', 'postgrad': 'Postgraduate' };
    document.getElementById('summaryLevel').textContent = map[formData.level];
    document.getElementById('summaryFile').textContent = formData.file.name;
    document.getElementById('doneName').textContent = formData.name.split(' ')[0];
    goToStep(4);
}

function handleFinish() {
    /* 
    const data = new FormData();
    data.append('file', formData.file);
    data.append('name', formData.name);
    data.append('email', formData.email);
    data.append('password', formData.password);
    data.append('level', formData.level);
    fetch('/api/onboarding', { method: 'POST', body: data }).then(r => { if (r.ok) window.location.href = '/dashboard'; });
    */
    window.location.href = '{{ url_for("dashboard") }}';
}