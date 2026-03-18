/* ═══════════════════════════════════════════
   NexAcro Mock API — Simulated backend data
   Matches FastAPI schemas from backend
   ═══════════════════════════════════════════ */

const delay = (ms) => new Promise(r => setTimeout(r, ms));

// ── Auth ────────────────────────────────────
export async function loginApi(email, password) {
    await delay(800);
    if (!email || !password) throw new Error('Email and password required');
    return {
        access_token: 'mock-jwt-token-' + Date.now(),
        token_type: 'bearer',
        user_id: 'usr_001',
        username: 'dr.sharma',
        role: 'doctor',
        full_name: 'Dr. Priya Sharma',
        email: email,
    };
}

export async function registerApi(username, email, password, full_name) {
    await delay(800);
    if (!username || !email || !password) throw new Error('Fields missing');
    return {
        access_token: 'mock-jwt-token-' + Date.now(),
        token_type: 'bearer',
        user_id: 'usr_new',
        username: username,
        role: 'doctor',
        full_name: full_name || username,
        email: email,
    };
}

export async function getUserProfile() {
    await delay(300);
    return {
        id: 'usr_001',
        username: 'dr.sharma',
        email: 'dr.sharma@ivfclinic.com',
        full_name: 'Dr. Priya Sharma',
        role: 'doctor',
        is_active: true,
        created_at: '2026-01-15T10:30:00Z',
    };
}

// ── Analytics ───────────────────────────────
export async function getAnalyticsSummary() {
    await delay(500);
    return {
        total_analyses: 1284,
        total_images_processed: 20544,
        overall_intact_percentage: 72.4,
        overall_damaged_percentage: 27.6,
        analyses_today: 8,
        analyses_this_week: 42,
        analyses_this_month: 156,
    };
}

export async function getDetailedAnalytics(days = 30) {
    await delay(600);
    const daily_stats = [];
    const now = new Date();
    for (let i = days; i >= 0; i--) {
        const d = new Date(now);
        d.setDate(d.getDate() - i);
        daily_stats.push({
            date: d.toISOString().split('T')[0],
            analyses_count: Math.floor(Math.random() * 12) + 2,
            images_count: Math.floor(Math.random() * 80) + 16,
            avg_intact_percentage: Math.round((60 + Math.random() * 30) * 100) / 100,
        });
    }
    return {
        summary: await getAnalyticsSummary(),
        daily_stats,
    };
}

// ── Analysis ────────────────────────────────
function generateMockImageResults(count = 16) {
    const results = [];
    for (let i = 0; i < count; i++) {
        const isIntact = Math.random() > 0.3;
        results.push({
            filename: `acrosome_${i + 1}.png`,
            original_filename: `sample_region_${i + 1}.png`,
            classification: isIntact ? 'Intact' : 'Damaged',
            processing_time_ms: Math.round(Math.random() * 50 + 20),
        });
    }
    return results;
}

export async function analyzeImages(files, sampleId, patientId, notes) {
    // Simulate processing pipeline
    const results = generateMockImageResults(16);
    const intactCount = results.filter(r => r.classification === 'Intact').length;
    const damagedCount = results.length - intactCount;

    return {
        id: 'ana_' + Date.now(),
        session_id: 'sess_' + Math.random().toString(36).substr(2, 12),
        total_images: results.length,
        intact_count: intactCount,
        damaged_count: damagedCount,
        intact_percentage: Math.round((intactCount / results.length) * 10000) / 100,
        damaged_percentage: Math.round((damagedCount / results.length) * 10000) / 100,
        image_results: results,
        sample_id: sampleId || 'SMP-' + Math.floor(Math.random() * 9000 + 1000),
        patient_id: patientId || null,
        notes: notes || null,
        created_at: new Date().toISOString(),
        total_processing_time_ms: Math.round(Math.random() * 800 + 400),
    };
}

export async function getAnalysisResult(id) {
    await delay(400);
    const results = generateMockImageResults(16);
    const intactCount = results.filter(r => r.classification === 'Intact').length;
    return {
        id,
        session_id: 'sess_abc123',
        total_images: 16,
        intact_count: intactCount,
        damaged_count: 16 - intactCount,
        intact_percentage: Math.round((intactCount / 16) * 10000) / 100,
        damaged_percentage: Math.round(((16 - intactCount) / 16) * 10000) / 100,
        image_results: results,
        sample_id: 'SMP-2048',
        patient_id: 'PT-001',
        notes: 'Standard IVF analysis',
        created_at: new Date().toISOString(),
        total_processing_time_ms: 623,
    };
}

export async function listAnalyses(page = 1, pageSize = 20) {
    await delay(500);
    const analyses = [];
    for (let i = 0; i < pageSize; i++) {
        const idx = (page - 1) * pageSize + i;
        const d = new Date();
        d.setDate(d.getDate() - idx);
        const intactPct = Math.round((55 + Math.random() * 40) * 100) / 100;
        analyses.push({
            id: `ana_${1000 + idx}`,
            session_id: `sess_${Math.random().toString(36).substr(2, 8)}`,
            total_images: 16,
            intact_percentage: intactPct,
            damaged_percentage: Math.round((100 - intactPct) * 100) / 100,
            sample_id: `SMP-${2000 + idx}`,
            patient_id: idx % 3 === 0 ? `PT-${100 + idx}` : null,
            notes: idx % 2 === 0 ? `Patient: John Doe ${idx}` : null,
            created_at: d.toISOString(),
        });
    }
    return {
        total: 156,
        page,
        page_size: pageSize,
        analyses,
    };
}

// ── Reports ─────────────────────────────────
export async function generateReport(analysisId) {
    await delay(1000);
    return {
        report_id: 'rpt_' + Date.now(),
        analysis_id: analysisId,
        filename: `report_${analysisId}.pdf`,
        download_url: `/api/reports/download/report_${analysisId}.pdf`,
        generated_at: new Date().toISOString(),
    };
}

// ── Pipeline Steps (for Processing Page simulation) ──
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
