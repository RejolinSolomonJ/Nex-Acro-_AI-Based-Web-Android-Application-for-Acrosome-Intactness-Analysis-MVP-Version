import { useMemo, useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Download, Plus, CheckCircle, XCircle, Clock, Hash, User, FlaskConical, Loader2, AlertCircle } from 'lucide-react';
import { analyzeImages, generateReport, getAnalysisResult } from '../services/api';
import './ReportPage.css';

export default function ReportPage() {
    const navigate = useNavigate();
    const location = useLocation();

    // Two entry modes:
    // 1. { analysis } – standard navigation from ProcessingPage with fresh result
    // 2. { analysisId } – coming from History / Dashboard to view an old report
    const { grids, patientDetails, analysis: stateAnalysis, analysisId } = location.state || {};

    const [analysis, setAnalysis] = useState(() => {
        if (stateAnalysis) return stateAnalysis;
        try {
            const saved = localStorage.getItem('nexacro-latest-analysis');
            return saved ? JSON.parse(saved) : null;
        } catch (e) {
            return null;
        }
    });

    const [apiLoading, setApiLoading] = useState(!!analysisId && !analysis);
    const [apiError, setApiError] = useState(null);
    const [downloading, setDownloading] = useState(false);

    // ── Load record if only AnalysisID was provided (History/Dashboard) ──
    useEffect(() => {
        if (!analysisId || analysis) return;

        async function fetchResult() {
            setApiLoading(true);
            try {
                const result = await getAnalysisResult(analysisId);
                setAnalysis(result);
            } catch (err) {
                console.error('Fetch error:', err);
                setApiError(err.message || 'Could not load analysis record.');
            } finally {
                setApiLoading(false);
            }
        }
        fetchResult();
    }, [analysisId, analysis]);

    const report = useMemo(() => {
        if (!analysis) return null;
        const dateObj = new Date(analysis.created_at);
        return {
            date: dateObj.toLocaleDateString('en-GB', { year: 'numeric', month: 'long', day: 'numeric' }),
            time: dateObj.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
            sessionId: analysis.session_id,
            sampleId: analysis.sample_id || '—',
            patientId: analysis.patient_id || '—',
            total: analysis.total_images,
            intact: analysis.intact_count,
            damaged: analysis.damaged_count,
            intactPct: analysis.intact_percentage,
            damagedPct: analysis.damaged_percentage,
            processingMs: analysis.total_processing_time_ms,
            results: analysis.image_results || [],
        };
    }, [analysis]);

    const handleDownload = async () => {
        if (!analysis?.id) return;
        setDownloading(true);
        try {
            const data = await generateReport(analysis.id);
            if (data.download_url) {
                window.open(data.download_url, '_blank');
            }
        } catch (err) {
            alert('Failed to download PDF: ' + err.message);
        } finally {
            setDownloading(false);
        }
    };

    const handleNextPatient = () => {
        localStorage.removeItem('nexacro-latest-analysis');
        navigate('/upload');
    };

    // ── No state at all ──
    if (!analysisId && !analysis && !apiLoading) {
        return (
            <div className="report-page animate-fade-in">
                <div className="card" style={{ maxWidth: 480, margin: '100px auto', textAlign: 'center', padding: 40 }}>
                    <h2 className="text-muted">No Analysis Data</h2>
                    <p>Please perform an analysis first.</p>
                    <button className="btn btn-primary" onClick={handleNextPatient} style={{ marginTop: 20 }}>
                        Start New Analysis
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="report-page animate-fade-in">
            {/* ── Page Header ── */}
            <div className="page-header">
                <div>
                    <h1>Diagnostic Report</h1>
                    <p className="text-muted text-sm">
                        {apiLoading ? 'AI is analysing your images… this may take up to 60 seconds' : 'AI-generated acrosome intactness analysis'}
                    </p>
                </div>
                <div className="flex gap-3">
                    <button className="btn btn-secondary" onClick={handleNextPatient}>
                        <Plus size={16} /> Next Patient
                    </button>
                    <button
                        className="btn btn-primary"
                        onClick={handleDownload}
                        disabled={downloading || apiLoading || !!apiError}
                        title={apiLoading ? 'Waiting for analysis to complete…' : ''}
                    >
                        {downloading
                            ? <><Loader2 size={16} className="animate-spin" /> Preparing…</>
                            : apiLoading
                                ? <><Loader2 size={16} className="animate-spin" /> Analysing…</>
                                : <><Download size={16} /> Download PDF</>}
                    </button>
                </div>
            </div>

            {/* ── Error state ── */}
            {apiError && (
                <div className="card" style={{ maxWidth: 560, margin: '0 auto', textAlign: 'center', padding: 36 }}>
                    <AlertCircle size={40} style={{ color: 'var(--error)', marginBottom: 14 }} />
                    <h2 style={{ color: 'var(--error)' }}>Analysis Error</h2>
                    <p>{apiError}</p>
                    <button className="btn btn-secondary" onClick={() => navigate('/upload')} style={{ marginTop: 18 }}>
                        Go Back
                    </button>
                </div>
            )}

            {/* ── Loading skeleton ── */}
            {apiLoading && !apiError && (
                <div className="rpt-doc glass-card animate-fade-in-up">
                    <div className="rpt-band">
                        <span className="rpt-band-title">Acrosome Intactness Analysis Report</span>
                        <span className="rpt-band-sub">NexAcro AI Clinical Platform</span>
                    </div>
                    <div style={{ padding: '48px 32px', textAlign: 'center' }}>
                        <Loader2 size={48} className="animate-spin" style={{ color: 'var(--accent)', marginBottom: 20 }} />
                        <h2 style={{ marginBottom: 8 }}>Analysing Images…</h2>
                        <p className="text-muted">The AI is processing your images on the server.</p>
                        <p className="text-muted text-sm" style={{ marginTop: 8 }}>
                            HEIC / large images may take up to 60 seconds. Results will appear here automatically.
                        </p>
                        <div className="rpt-skeleton-bars" style={{ marginTop: 32 }}>
                            {[220, 160, 200, 140].map((w, i) => (
                                <div key={i} className="skeleton-bar" style={{ width: w }} />
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* ── Full report ── */}
            {report && !apiError && (
                <div className="rpt-doc glass-card animate-fade-in-up">
                    {/* Blue header band */}
                    <div className="rpt-band">
                        <span className="rpt-band-title">Acrosome Intactness Analysis Report</span>
                        <span className="rpt-band-sub">NexAcro AI Clinical Platform</span>
                    </div>

                    {/* Section 1 – Session Info */}
                    <div className="rpt-section">
                        <div className="rpt-section-title">1. Session Information</div>
                        <div className="rpt-kv-grid">
                            <div className="rpt-kv"><span className="rpt-kv-label"><Hash size={13} /> Session ID</span><span className="rpt-kv-val mono">{report.sessionId}</span></div>
                            <div className="rpt-kv"><span className="rpt-kv-label"><Clock size={13} /> Date &amp; Time</span><span className="rpt-kv-val">{report.date} · {report.time}</span></div>
                            <div className="rpt-kv"><span className="rpt-kv-label"><FlaskConical size={13} /> Sample ID</span><span className="rpt-kv-val">{report.sampleId}</span></div>
                            <div className="rpt-kv"><span className="rpt-kv-label"><User size={13} /> Patient ID</span><span className="rpt-kv-val">{report.patientId}</span></div>
                            <div className="rpt-kv"><span className="rpt-kv-label">Total Images</span><span className="rpt-kv-val">{report.total}</span></div>
                            <div className="rpt-kv"><span className="rpt-kv-label">Processing Time</span><span className="rpt-kv-val">{report.processingMs?.toFixed(0)} ms</span></div>
                        </div>
                    </div>

                    {/* Section 2 – Summary */}
                    <div className="rpt-section">
                        <div className="rpt-section-title">2. Analysis Summary</div>
                        <div className="rpt-big-nums">
                            <div className="rpt-big-num intact">
                                <span className="rpt-pct">{report.intactPct}%</span>
                                <span className="rpt-pct-label">Intact</span>
                            </div>
                            <div className="rpt-big-num damaged">
                                <span className="rpt-pct">{report.damagedPct}%</span>
                                <span className="rpt-pct-label">Damaged</span>
                            </div>
                        </div>
                        <div className="rpt-bar-wrap">
                            <div className="rpt-bar-track">
                                <div className="rpt-bar-fill" style={{ width: `${report.intactPct}%` }} />
                            </div>
                            <div className="rpt-bar-labels">
                                <span className="text-success">■ Intact {report.intactPct}%</span>
                                <span className="text-error">■ Damaged {report.damagedPct}%</span>
                            </div>
                        </div>
                        <div className="rpt-stats-grid">
                            {[
                                ['Total Analysed', report.total],
                                ['Intact Count', report.intact],
                                ['Damaged Count', report.damaged],
                            ].map(([lbl, val]) => (
                                <div className="rpt-stat" key={lbl}>
                                    <span className="rpt-stat-label">{lbl}</span>
                                    <span className="rpt-stat-val">{val}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Section 3 – Per-Image Table */}
                    <div className="rpt-section">
                        <div className="rpt-section-title">3. Individual Image Results</div>
                        <table className="rpt-table">
                            <thead>
                                <tr>
                                    <th style={{ width: '5%', textAlign: 'center' }}>#</th>
                                    <th style={{ width: '45%', textAlign: 'left' }}>Filename</th>
                                    <th style={{ width: '25%', textAlign: 'center' }}>Classification</th>
                                    <th style={{ width: '25%', textAlign: 'center' }}>Proc. Time</th>
                                </tr>
                            </thead>
                            <tbody>
                                {report.results.map((r, i) => (
                                    <tr key={i} className={i % 2 === 0 ? 'even' : ''}>
                                        <td style={{ textAlign: 'center' }}>{i + 1}</td>
                                        <td className="mono" style={{ fontSize: '0.78rem' }}>
                                            {r.original_filename?.length > 32 ? r.original_filename.slice(0, 29) + '…' : r.original_filename}
                                        </td>
                                        <td style={{ textAlign: 'center' }}>
                                            {r.classification?.toLowerCase() === 'intact'
                                                ? <span className="badge-cls intact"><CheckCircle size={13} /> Intact</span>
                                                : <span className="badge-cls damaged"><XCircle size={13} /> Damaged</span>}
                                        </td>
                                        <td style={{ textAlign: 'center' }}>{r.processing_time_ms?.toFixed(1)} ms</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Disclaimer */}
                    <div className="rpt-disclaimer">
                        <strong>Disclaimer:</strong> This report was generated by an AI-based analysis system and is intended to assist clinical
                        decision-making only. Results should be verified by a qualified medical specialist before use in diagnosis or treatment.
                    </div>
                </div>
            )}
        </div>
    );
}
