import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, X, Zap, Grid3X3, ArrowRight, User, Hash, Calendar, FileText, Loader2, Briefcase, Ruler, Activity, Info } from 'lucide-react';
import heic2any from 'heic2any';
import './UploadPage.css';

/** Try to convert file via canvas (works for any browser-renderable format). */
function canvasConvert(file) {
    return new Promise((resolve, reject) => {
        const url = URL.createObjectURL(file);
        const img = new Image();
        img.onload = () => {
            const canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth;
            canvas.height = img.naturalHeight;
            canvas.getContext('2d').drawImage(img, 0, 0);
            URL.revokeObjectURL(url);
            canvas.toBlob(blob => {
                if (!blob) { reject(new Error('Canvas toBlob failed')); return; }
                resolve(new File([blob], file.name.replace(/\.[^.]+$/, '.jpg'), { type: 'image/jpeg' }));
            }, 'image/jpeg', 0.9);
        };
        img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('Image load failed')); };
        img.src = url;
    });
}

/**
 * Convert a file to a JPEG-compatible File.
 * Strategy: heic2any → canvas drawImage → raw file (best-effort).
 */
async function toCompatible(file) {
    const isHeic =
        file.type === 'image/heic' ||
        file.type === 'image/heif' ||
        file.name.match(/\.(heic|heif)$/i);

    // 1️⃣ Try heic2any for known HEIC files
    if (isHeic) {
        try {
            const blob = await heic2any({ blob: file, toType: 'image/jpeg', quality: 0.9 });
            const outBlob = Array.isArray(blob) ? blob[0] : blob;
            return new File([outBlob], file.name.replace(/\.(heic|heif)$/i, '.jpg'), { type: 'image/jpeg' });
        } catch (e) {
            console.warn('heic2any failed, trying canvas fallback:', e);
        }
    }

    // 2️⃣ Canvas fallback — works for any format the browser can decode natively
    try {
        return await canvasConvert(file);
    } catch (e) {
        console.warn('Canvas conversion failed, using raw file:', e);
    }

    // 3️⃣ Last resort — return original file as-is
    return file;
}

export default function UploadPage() {
    const navigate = useNavigate();

    const [activeTab, setActiveTab] = useState('details');

    const [patientDetails, setPatientDetails] = useState({
        date: new Date().toISOString().split('T')[0],
        patientName: '',
        patientId: '',
        sampleId: '',
        age: '',
        education: '',
        occupation: '',
        address: '',
        height: '',
        weight: '',
        bmi: '',
        hasMedicalHistory: false,
        medicalHistoryDetails: '',
        hasSurgicalHistory: false,
        surgicalHistoryDetails: '',
        sexualAbstinence: '',
        sexualLubricants: '',
        sexualStdHistory: '',
        smoking: false,
        alcohol: false,
        drugAbuse: false,
        physicalActivity: false
    });

    const [grids, setGrids] = useState({ 1: [], 2: [], 3: [], 4: [] });

    // Track which grids are currently converting HEIC files
    const [converting, setConverting] = useState({});

    const handleInputChange = (e) => {
        const { name, value, type, checked } = e.target;
        const val = type === 'checkbox' ? checked : value;
        setPatientDetails(prev => {
            const updated = { ...prev, [name]: val };
            
            // Auto-calculate BMI if height and weight are present
            if (name === 'height' || name === 'weight') {
                const h = name === 'height' ? parseFloat(value) : parseFloat(prev.height);
                const w = name === 'weight' ? parseFloat(value) : parseFloat(prev.weight);
                
                if (h > 0 && w > 0) {
                    const bmiVal = (w / ((h / 100) * (h / 100))).toFixed(1);
                    updated.bmi = bmiVal;
                } else {
                    updated.bmi = '';
                }
            }
            
            return updated;
        });
    };

    const handleFiles = async (gridId, files) => {
        if (!files || files.length === 0) return;

        const candidates = Array.from(files).filter(f =>
            f.type.startsWith('image/') ||
            f.name.match(/\.(jpg|jpeg|png|bmp|tiff|tif|heic|heif|webp|avif)$/i)
        );
        if (candidates.length === 0) return;

        // Mark this grid as converting
        setConverting(prev => ({ ...prev, [gridId]: true }));

        try {
            // Convert any HEIC files to JPEG (with fallbacks)
            const converted = await Promise.all(candidates.map(toCompatible));

            setGrids(prev => {
                const currentFiles = prev[gridId];
                const slotsLeft = 4 - currentFiles.length;
                const filesToAdd = converted.slice(0, slotsLeft);
                if (filesToAdd.length === 0) return prev;

                const newGridFiles = [...currentFiles];
                filesToAdd.forEach(file => {
                    newGridFiles.push({
                        file,
                        preview: URL.createObjectURL(file),
                        name: file.name,
                        id: Math.random().toString(36).substr(2, 9)
                    });
                });
                return { ...prev, [gridId]: newGridFiles };
            });
        } catch (err) {
            console.error('Image processing error:', err);
        } finally {
            setConverting(prev => ({ ...prev, [gridId]: false }));
            const input = document.getElementById(`fileInput-${gridId}`);
            if (input) input.value = '';
        }
    };

    const removeFile = (gridId, fileId, e) => {
        e.stopPropagation();
        setGrids(prev => ({
            ...prev,
            [gridId]: prev[gridId].filter(f => f.id !== fileId)
        }));
    };

    const totalImages = Object.values(grids).reduce((acc, curr) => acc + curr.length, 0);
    const isDetailsComplete = patientDetails.patientName && patientDetails.patientId && patientDetails.sampleId && patientDetails.date;
    const isConverting = Object.values(converting).some(Boolean);
    const isReady = isDetailsComplete && totalImages > 0 && !isConverting;

    const handleAnalyze = () => {
        if (isReady) {
            navigate('/processing', { state: { grids, patientDetails } });
        }
    };

    const nextTab = () => {
        setActiveTab('images');
        window.scrollTo(0, 0);
    };

    const prevTab = () => {
        setActiveTab('details');
        window.scrollTo(0, 0);
    };

    return (
        <div className="upload-page animate-fade-in">
            <div className="page-header">
                <div>
                    <h1>New Analysis</h1>
                    <p className="text-muted text-sm">Upload up to 4 images per grid (16 total) and patient details</p>
                </div>
                <div className="tab-navigation">
                    <button 
                        className={`tab-btn ${activeTab === 'details' ? 'active' : ''}`}
                        onClick={() => setActiveTab('details')}
                    >
                        1. Patient & Sample Details
                    </button>
                    <button 
                        className={`tab-btn ${activeTab === 'images' ? 'active' : ''}`}
                        onClick={() => setActiveTab('images')}
                    >
                        2. Upload Images
                    </button>
                </div>
                <div className="header-actions">
                    {activeTab === 'images' && (
                        <button
                            className={`btn ${isDetailsComplete && totalImages === 16 ? 'btn-primary' : 'btn-secondary'} start-analysis-btn`}
                            disabled={!isReady}
                            onClick={handleAnalyze}
                        >
                            {isConverting ? <Loader2 size={18} className="animate-spin" /> : totalImages === 16 ? <Zap size={18} /> : <ArrowRight size={18} />}
                            {isConverting ? 'Converting...' : totalImages === 16 ? 'Start Full Analysis' : `Start Partial (${totalImages}/16)`}
                        </button>
                    )}
                </div>
            </div>

            {activeTab === 'details' && (
                <div className="patient-details-content animate-fade-in">
                    {/* Section 1: Date */}
                    <div className="patient-details-card glass-card">
                        <h3><Calendar size={18} className="text-accent" /> (1) Date</h3>
                        <div className="pd-form-grid">
                            <div className="form-group">
                                <label>Date</label>
                                <div className="input-wrap">
                                    <Calendar size={16} />
                                    <input type="date" name="date" value={patientDetails.date} onChange={handleInputChange} />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Section 2: Patient Details */}
                    <div className="patient-details-card glass-card">
                        <h3><User size={18} className="text-accent" /> (2) Patient Details</h3>
                        <div className="pd-form-grid">
                            <div className="form-group">
                                <label>Name</label>
                                <div className="input-wrap">
                                    <User size={16} />
                                    <input type="text" name="patientName" placeholder="e.g. Jane Doe" value={patientDetails.patientName} onChange={handleInputChange} />
                                </div>
                            </div>
                            <div className="form-group">
                                <label>Pt ID</label>
                                <div className="input-wrap">
                                    <Hash size={16} />
                                    <input type="text" name="patientId" placeholder="e.g. PT-10024" value={patientDetails.patientId} onChange={handleInputChange} />
                                </div>
                            </div>
                            <div className="form-group">
                                <label>Sample ID</label>
                                <div className="input-wrap">
                                    <FileText size={16} />
                                    <input type="text" name="sampleId" placeholder="e.g. SMP-2023X" value={patientDetails.sampleId} onChange={handleInputChange} />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Section 3: Demographic Details */}
                    <div className="patient-details-card glass-card">
                        <h3><Activity size={18} className="text-accent" /> (3) Patient Demographic Details</h3>
                        <div className="pd-form-grid">
                            <div className="form-group">
                                <label>Age</label>
                                <div className="input-wrap">
                                    <Activity size={16} />
                                    <input type="number" name="age" placeholder="Age" value={patientDetails.age} onChange={handleInputChange} />
                                </div>
                            </div>
                            <div className="form-group">
                                <label>Education</label>
                                <div className="input-wrap">
                                    <FileText size={16} />
                                    <input type="text" name="education" placeholder="Education" value={patientDetails.education} onChange={handleInputChange} />
                                </div>
                            </div>
                            <div className="form-group">
                                <label>Occupation</label>
                                <div className="input-wrap">
                                    <Briefcase size={16} />
                                    <input type="text" name="occupation" placeholder="Occupation" value={patientDetails.occupation} onChange={handleInputChange} />
                                </div>
                            </div>
                            <div className="form-group full-width">
                                <label>Address</label>
                                <textarea 
                                    name="address" 
                                    placeholder="Full Address" 
                                    className="custom-textarea"
                                    value={patientDetails.address} 
                                    onChange={handleInputChange}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Section 4: Anthropometry */}
                    <div className="patient-details-card glass-card">
                        <h3><Ruler size={18} className="text-accent" /> (4) Anthropometry</h3>
                        <div className="pd-form-grid">
                            <div className="form-group">
                                <label>Ht (cm)</label>
                                <div className="input-wrap">
                                    <Ruler size={16} />
                                    <input type="number" name="height" placeholder="Height" value={patientDetails.height} onChange={handleInputChange} />
                                </div>
                            </div>
                            <div className="form-group">
                                <label>Wt (kg)</label>
                                <div className="input-wrap">
                                    <Activity size={16} />
                                    <input type="number" name="weight" placeholder="Weight" value={patientDetails.weight} onChange={handleInputChange} />
                                </div>
                            </div>
                            <div className="form-group">
                                <label>BMI</label>
                                <div className="input-wrap readonly-input">
                                    <Info size={16} />
                                    <input type="text" name="bmi" value={patientDetails.bmi} readOnly placeholder="Auto" />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Section 5 & 6: Medical and Surgical History */}
                    <div className="patient-details-row">
                        <div className="patient-details-card glass-card split">
                            <h3><Activity size={18} className="text-accent" /> (5) Medical History</h3>
                            <div className="history-row">
                                <div className="switch-group">
                                    <label className="switch">
                                        <input type="checkbox" name="hasMedicalHistory" checked={patientDetails.hasMedicalHistory} onChange={handleInputChange} />
                                        <span className="slider"></span>
                                    </label>
                                    <span>{patientDetails.hasMedicalHistory ? 'Yes' : 'No'}</span>
                                </div>
                                <input 
                                    type="text" 
                                    name="medicalHistoryDetails" 
                                    placeholder="Details if Yes..." 
                                    className="custom-input"
                                    value={patientDetails.medicalHistoryDetails} 
                                    onChange={handleInputChange} 
                                />
                            </div>
                        </div>
                        <div className="patient-details-card glass-card split">
                            <h3><Activity size={18} className="text-accent" /> (6) Surgical History</h3>
                            <div className="history-row">
                                <div className="switch-group">
                                    <label className="switch">
                                        <input type="checkbox" name="hasSurgicalHistory" checked={patientDetails.hasSurgicalHistory} onChange={handleInputChange} />
                                        <span className="slider"></span>
                                    </label>
                                    <span>{patientDetails.hasSurgicalHistory ? 'Yes' : 'No'}</span>
                                </div>
                                <input 
                                    type="text" 
                                    name="surgicalHistoryDetails" 
                                    placeholder="Details if Yes..." 
                                    className="custom-input"
                                    value={patientDetails.surgicalHistoryDetails} 
                                    onChange={handleInputChange} 
                                />
                            </div>
                        </div>
                    </div>

                    {/* Section 7: Sexual History */}
                    <div className="patient-details-card glass-card">
                        <h3><User size={18} className="text-accent" /> (7) Sexual History</h3>
                        <div className="pd-form-grid">
                            <div className="form-group">
                                <label>Abstinence</label>
                                <input type="text" name="sexualAbstinence" className="custom-input no-icon" placeholder="Abstinence details" value={patientDetails.sexualAbstinence} onChange={handleInputChange} />
                            </div>
                            <div className="form-group">
                                <label>Use of Lubricants</label>
                                <input type="text" name="sexualLubricants" className="custom-input no-icon" placeholder="e.g. Yes/No/Details" value={patientDetails.sexualLubricants} onChange={handleInputChange} />
                            </div>
                            <div className="form-group">
                                <label>History of STD</label>
                                <input type="text" name="sexualStdHistory" className="custom-input no-icon" placeholder="History of STD" value={patientDetails.sexualStdHistory} onChange={handleInputChange} />
                            </div>
                        </div>
                    </div>

                    {/* Section 8: Lifestyle */}
                    <div className="patient-details-card glass-card">
                        <h3><Activity size={18} className="text-accent" /> (8) Lifestyle</h3>
                        <div className="lifestyle-switches-grid">
                            <div className="switch-group">
                                <label className="switch">
                                    <input type="checkbox" name="smoking" checked={patientDetails.smoking} onChange={handleInputChange} />
                                    <span className="slider"></span>
                                </label>
                                <span>Smoking (Yes/No)</span>
                            </div>
                            <div className="switch-group">
                                <label className="switch">
                                    <input type="checkbox" name="alcohol" checked={patientDetails.alcohol} onChange={handleInputChange} />
                                    <span className="slider"></span>
                                </label>
                                <span>Alcohol (Yes/No)</span>
                            </div>
                            <div className="switch-group">
                                <label className="switch">
                                    <input type="checkbox" name="drugAbuse" checked={patientDetails.drugAbuse} onChange={handleInputChange} />
                                    <span className="slider"></span>
                                </label>
                                <span>Drug Abuse (Yes/No)</span>
                            </div>
                            <div className="switch-group">
                                <label className="switch">
                                    <input type="checkbox" name="physicalActivity" checked={patientDetails.physicalActivity} onChange={handleInputChange} />
                                    <span className="slider"></span>
                                </label>
                                <span>Physical Activity (Yes/No)</span>
                            </div>
                        </div>
                    </div>

                    <div className="form-footer">
                        <button className="btn btn-primary next-step-btn" onClick={nextTab}>
                            Upload Images <ArrowRight size={18} />
                        </button>
                    </div>
                </div>
            )}

            {activeTab === 'images' && (
                <div className="upload-images-content animate-fade-in">
                    <div className="upload-header">
                        <button className="btn-text back-btn" onClick={prevTab}>
                             <ArrowRight size={18} style={{ transform: 'rotate(180deg)' }} /> Back to Details
                        </button>
                        <p className="text-muted">Total images uploaded: {totalImages}/16</p>
                    </div>

            <div className="grid-upload-container">
                {[1, 2, 3, 4].map(gridId => {
                    const gridImages = grids[gridId];
                    const isFull = gridImages.length === 4;
                    const isGridConverting = converting[gridId];

                    return (
                        <div key={gridId} className="grid-upload-box glass-card animate-fade-in-up" style={{ animationDelay: `${gridId * 100}ms` }}>
                            <div className="gu-header">
                                <Grid3X3 size={18} className="text-accent" />
                                <h3>Grid {gridId} Images ({gridImages.length}/4)</h3>
                                {isGridConverting && <span style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.8rem', color: 'var(--accent)' }}><Loader2 size={14} className="animate-spin" /> Converting...</span>}
                            </div>

                            <div
                                className={`gu-zone ${gridImages.length > 0 ? 'has-images' : ''} ${isGridConverting ? 'converting' : ''}`}
                                onClick={() => !isFull && !isGridConverting && document.getElementById(`fileInput-${gridId}`).click()}
                                onDragOver={(e) => e.preventDefault()}
                                onDrop={(e) => {
                                    e.preventDefault();
                                    if (!isFull && !isGridConverting && e.dataTransfer.files) {
                                        handleFiles(gridId, e.dataTransfer.files);
                                    }
                                }}
                            >
                                {isGridConverting ? (
                                    <div className="gu-empty">
                                        <Loader2 size={32} className="animate-spin" style={{ color: 'var(--accent)' }} />
                                        <p>Converting images...</p>
                                        <span className="gu-hint">HEIC → JPEG conversion in progress</span>
                                    </div>
                                ) : gridImages.length > 0 ? (
                                    <div className="gu-gallery">
                                        {gridImages.map((img, i) => (
                                            <div key={img.id} className="gu-thumb-wrap" onClick={(e) => e.stopPropagation()}>
                                                <img src={img.preview} alt={`Grid ${gridId} - img ${i + 1}`} className="gu-thumb" />
                                                <button className="gu-remove-thumb" onClick={(e) => removeFile(gridId, img.id, e)}>
                                                    <X size={14} />
                                                </button>
                                            </div>
                                        ))}
                                        {!isFull && (
                                            <div className="gu-add-more" onClick={(e) => { e.stopPropagation(); document.getElementById(`fileInput-${gridId}`).click(); }}>
                                                <Upload size={20} />
                                                <span>Add</span>
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <div className="gu-empty">
                                        <div className="gu-icon-wrap">
                                            <Upload size={24} />
                                        </div>
                                        <p>Click or drag up to 4 images for Grid {gridId}</p>
                                        <span className="gu-hint">Supports HEIC, JPG, PNG, BMP and more</span>
                                    </div>
                                )}
                            </div>

                            {/* Input OUTSIDE overflow:hidden zone so it is not clipped */}
                            <input
                                id={`fileInput-${gridId}`}
                                type="file"
                                multiple
                                accept="image/*"
                                style={{ display: 'none' }}
                                onChange={(e) => handleFiles(gridId, e.target.files)}
                            />
                        </div>
                    );
                })}
            </div>
                </div>
            )}
        </div>
    );
}
