/* ═══════════════════════════════════════════
   NexAcro Real API — FastAPI backend connection
   ═══════════════════════════════════════════ */

let rawUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
// Remove trailing slash if present to avoid double slashes like //api/...
const BASE_URL = rawUrl.endsWith('/') ? rawUrl.slice(0, -1) : rawUrl;

console.log('🔗 NexAcro API Connection:', BASE_URL);

async function handleResponse(response) {
    if (!response.ok) {
        let errorDetail = 'Unknown error occurred';
        try {
            const error = await response.json();
            errorDetail = error.detail || error.message || errorDetail;
        } catch (e) {
            // Not a JSON response
        }
        throw new Error(errorDetail);
    }
    return response.json();
}

// Helper to get headers with Auth
function getHeaders(isMultipart = false) {
    const token = localStorage.getItem('nexacro-token');
    const headers = {};
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    if (!isMultipart) {
        headers['Content-Type'] = 'application/json';
    }
    return headers;
}

// ── Auth ────────────────────────────────────
export async function loginApi(email, password) {
    const response = await fetch(`${BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
    });
    const data = await handleResponse(response);
    return data;
}

export async function registerApi(username, email, password, full_name) {
    const response = await fetch(`${BASE_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password, full_name }),
    });
    const data = await handleResponse(response);
    return data;
}

export async function getUserProfile() {
    const response = await fetch(`${BASE_URL}/api/auth/me`, {
        headers: getHeaders(),
    });
    return handleResponse(response);
}

export function logout() {
    localStorage.removeItem('nexacro-token');
    localStorage.removeItem('nexacro-user');
}

// ── Analytics ───────────────────────────────
export async function getAnalyticsSummary() {
    const response = await fetch(`${BASE_URL}/api/analytics/summary`, {
        headers: getHeaders(),
    });
    return handleResponse(response);
}

export async function getDetailedAnalytics(days = 30) {
    const response = await fetch(`${BASE_URL}/api/analytics/detailed?days=${days}`, {
        headers: getHeaders(),
    });
    return handleResponse(response);
}

// ── Analysis ────────────────────────────────
export async function analyzeImages(files, sampleId, patientId, notes, patientDetails = {}) {
    const formData = new FormData();

    // Support both single file and array of files
    if (Array.isArray(files)) {
        files.forEach(file => {
            formData.append('files', file);
        });
    } else {
        formData.append('files', files);
    }

    if (sampleId) formData.append('sample_id', sampleId);
    if (patientId) formData.append('patient_id', patientId);
    if (patientDetails.patientName) formData.append('patient_name', patientDetails.patientName);
    if (notes) formData.append('notes', notes);
    
    // Add additional fields
    if (patientDetails.age) formData.append('age', patientDetails.age);
    if (patientDetails.education) formData.append('education', patientDetails.education);
    if (patientDetails.occupation) formData.append('occupation', patientDetails.occupation);
    if (patientDetails.address) formData.append('address', patientDetails.address);
    if (patientDetails.height) formData.append('height', patientDetails.height);
    if (patientDetails.weight) formData.append('weight', patientDetails.weight);
    if (patientDetails.bmi) formData.append('bmi', patientDetails.bmi);

    // Boolean fields (Lifestyle & History)
    formData.append('is_alcoholic', patientDetails.alcohol ? 'true' : 'false');
    formData.append('is_smoker', patientDetails.smoking ? 'true' : 'false');
    formData.append('is_using_drugs', patientDetails.drugAbuse ? 'true' : 'false');
    formData.append('physical_activity', patientDetails.physicalActivity ? 'true' : 'false');
    formData.append('has_medical_history', patientDetails.hasMedicalHistory ? 'true' : 'false');
    formData.append('has_surgical_history', patientDetails.hasSurgicalHistory ? 'true' : 'false');

    // Details fields
    if (patientDetails.medicalHistoryDetails) formData.append('medical_history_details', patientDetails.medicalHistoryDetails);
    if (patientDetails.surgicalHistoryDetails) formData.append('surgical_history_details', patientDetails.surgicalHistoryDetails);
    if (patientDetails.sexualAbstinence) formData.append('sexual_abstinence', patientDetails.sexualAbstinence);
    if (patientDetails.sexualLubricants) formData.append('sexual_lubricants', patientDetails.sexualLubricants);
    if (patientDetails.sexualStdHistory) formData.append('sexual_std_history', patientDetails.sexualStdHistory);

    const response = await fetch(`${BASE_URL}/api/analysis/analyze`, {
        method: 'POST',
        headers: getHeaders(true), // multipart/form-data
        body: formData,
    });
    return handleResponse(response);
}

export async function getAnalysisResult(id) {
    const response = await fetch(`${BASE_URL}/api/analysis/result/${id}`, {
        headers: getHeaders(),
    });
    return handleResponse(response);
}

export async function listAnalyses(page = 1, pageSize = 20) {
    const response = await fetch(`${BASE_URL}/api/analysis/list?page=${page}&page_size=${pageSize}`, {
        headers: getHeaders(),
    });
    return handleResponse(response);
}

// ── Reports ─────────────────────────────────
export async function generateReport(analysisId, patientName) {
    const response = await fetch(`${BASE_URL}/api/reports/generate`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ 
            analysis_id: analysisId,
            patient_name: patientName
        }),
    });
    const data = await handleResponse(response);

    // Ensure download_url is absolute
    if (data.download_url && !data.download_url.startsWith('http')) {
        data.download_url = `${BASE_URL}${data.download_url}`;
    }

    return data;
}

// ── Pipeline Steps (Local Helper) ───────────
export function getPipelineSteps() {
    return [
        { id: 1, label: 'Upload Image', icon: 'upload' },
        { id: 2, label: 'Preprocess', icon: 'settings' },
        { id: 3, label: 'Split into 4 Grids', icon: 'grid' },
        { id: 4, label: 'Detect 4 Acrosomes per Grid', icon: 'scan' },
        { id: 5, label: 'Crop 16 Regions', icon: 'crop' },
        { id: 6, label: 'Classify Each', icon: 'layers' },
        { id: 7, label: 'Count Results', icon: 'hash' },
        { id: 8, label: 'Calculate Percentages', icon: 'percent' },
        { id: 9, label: 'Overlay Results', icon: 'image' },
        { id: 10, label: 'Generate Report', icon: 'file-text' },
    ];
}
