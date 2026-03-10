import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
    Check, Loader2, Upload, Settings, Grid3X3, ScanSearch, AlertCircle
} from 'lucide-react';
import { analyzeImages } from '../services/api';
import './ProcessingPage.css';

const STEPS = [
    { id: 1, icon: Upload, label: 'Uploading Images' },
    { id: 2, icon: Settings, label: 'Preprocessing & Validation' },
    { id: 3, icon: Grid3X3, label: 'Splitting into Grids' },
    { id: 4, icon: ScanSearch, label: 'Running AI Classification' },
];

export default function ProcessingPage() {
    const navigate = useNavigate();
    const location = useLocation();
    const { grids, patientDetails } = location.state || {};

    const [currentStep, setCurrentStep] = useState(0);
    const [apiResult, setApiResult] = useState(null);
    const [error, setError] = useState(null);
    const hasStarted = useRef(false);
    const hasNavigated = useRef(false);

    // Guard – must have data
    useEffect(() => {
        if (!grids || !patientDetails) {
            navigate('/upload');
        }
    }, [grids, patientDetails, navigate]);

    // ── Perform REAL API Request ──
    useEffect(() => {
        if (!grids || !patientDetails || hasStarted.current) return;
        hasStarted.current = true;

        async function runAnalysis() {
            try {
                const files = Object.values(grids || {}).flat().map(item => item?.file).filter(Boolean);
                if (!files.length) throw new Error('No valid files to analyze.');

                const result = await analyzeImages(
                    files,
                    patientDetails?.sampleId || '',
                    patientDetails?.patientId || '',
                    `Patient: ${patientDetails?.patientName || 'Unknown'}`
                );

                setApiResult(result);
                localStorage.setItem('nexacro-latest-analysis', JSON.stringify(result));
            } catch (err) {
                console.error('Processing error:', err);
                setError(err.message || 'Analysis failed. Please try again.');
            }
        }
        runAnalysis();
    }, [grids, patientDetails]);

    // 4-step animation: one step every 750ms
    // If apiResult arrives early, we fast-forward the animation
    useEffect(() => {
        if (apiResult && currentStep < STEPS.length) {
            setCurrentStep(STEPS.length);
            return;
        }

        if (currentStep < STEPS.length && !error) {
            const t = setTimeout(() => setCurrentStep(s => s + 1), 750);
            return () => clearTimeout(t);
        }
    }, [currentStep, error, apiResult]);

    // After animation finishes AND API responds, navigate to report
    useEffect(() => {
        if (currentStep >= STEPS.length && apiResult && !hasNavigated.current) {
            hasNavigated.current = true;
            // Short delay for visual polish
            const t = setTimeout(() => {
                navigate('/report', {
                    state: { analysis: apiResult }
                });
            }, 300);
            return () => clearTimeout(t);
        }
    }, [currentStep, apiResult, navigate]);

    const done = currentStep >= STEPS.length;

    return (
        <div className="processing-page animate-fade-in">
            <div className="page-header">
                <div>
                    <h1>AI Processing</h1>
                    <p className="text-muted text-sm">Preparing your analysis…</p>
                </div>
            </div>

            <div className="processing-layout">
                {/* Stepper */}
                <div className="stepper-section glass-card">
                    <div className="stepper">
                        {STEPS.map((step, i) => {
                            const Icon = step.icon;
                            const isDone = i < currentStep;
                            const isCurrent = i === currentStep && !done;
                            return (
                                <div key={step.id} className={`step ${isDone ? 'done' : ''} ${isCurrent ? 'current' : ''}`}>
                                    <div className="step-indicator">
                                        <div className="step-circle">
                                            {isDone ? <Check size={16} /> :
                                                isCurrent ? <Loader2 size={16} className="animate-spin" /> :
                                                    <Icon size={16} />}
                                        </div>
                                        {i < STEPS.length - 1 && <div className="step-line" />}
                                    </div>
                                    <div className="step-content">
                                        <span className="step-label">{step.label}</span>
                                        {isDone && <span className="step-status badge badge-success">Complete</span>}
                                        {isCurrent && <span className="step-status badge badge-info">Processing…</span>}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Center visual */}
                <div className="processing-visual glass-card">
                    {error ? (
                        <div className="error-container animate-fade-in-up">
                            <div className="error-icon"><AlertCircle size={48} /></div>
                            <h2>Analysis Failed</h2>
                            <p className="text-muted">{error}</p>
                            <button className="btn btn-secondary" onClick={() => navigate('/upload')} style={{ marginTop: 18 }}>
                                Try Again
                            </button>
                        </div>
                    ) : !done ? (
                        <div className="nucleus-container">
                            <div className="nucleus-ring ring-1" />
                            <div className="nucleus-ring ring-2" />
                            <div className="nucleus-ring ring-3" />
                            <div className="nucleus-core">
                                <Loader2 size={32} className="animate-spin" />
                            </div>
                            <p className="processing-text">{STEPS[currentStep]?.label || 'Finishing…'}</p>
                            <p className="processing-progress">{currentStep}/{STEPS.length} steps</p>
                        </div>
                    ) : !apiResult ? (
                        <div className="complete-container animate-fade-in-up">
                            <div className="nucleus-core">
                                <Loader2 size={32} className="animate-spin" />
                            </div>
                            <h2>Finalizing...</h2>
                            <p className="text-muted">Waiting for AI to finish classification</p>
                        </div>
                    ) : (
                        <div className="complete-container animate-fade-in-up">
                            <div className="complete-icon"><Check size={48} /></div>
                            <h2>Ready!</h2>
                            <p className="text-muted">Loading your report…</p>
                            <Loader2 size={22} className="animate-spin" style={{ marginTop: 12, color: 'var(--accent)' }} />
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
