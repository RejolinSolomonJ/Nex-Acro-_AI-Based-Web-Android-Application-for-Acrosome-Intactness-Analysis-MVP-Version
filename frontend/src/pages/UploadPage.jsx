import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, X, Zap, Grid3X3, ArrowRight, User, Hash, Calendar, FileText, Loader2 } from 'lucide-react';
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
 * Validates if the image appears to be a microscopic sample instead of a generic natural photo.
 * Uses colorfulness metric and grayscale standard deviation.
 */
async function validateImageContent(file) {
    return new Promise((resolve) => {
        // Skip validation for HEIF/HEIC since browser Image() might fail to load it immediately
        if (file.type === 'image/heic' || file.name.match(/\.(heic|heif)$/i)) {
            resolve(true);
            return;
        }

        const url = URL.createObjectURL(file);
        const img = new Image();
        img.onload = () => {
            const canvas = document.createElement('canvas');
            const size = 150;
            canvas.width = size;
            canvas.height = size;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, size, size);
            URL.revokeObjectURL(url);

            try {
                const imgData = ctx.getImageData(0, 0, size, size).data;
                const total = size * size;

                let rgSum = 0, ybSum = 0, graySum = 0;
                let grays = new Float32Array(total), rgVals = new Float32Array(total), ybVals = new Float32Array(total);

                for (let i = 0, j = 0; j < total; i += 4, j++) {
                    const r = imgData[i], g = imgData[i + 1], b = imgData[i + 2];
                    const rg = Math.abs(r - g);
                    const yb = Math.abs(0.5 * (r + g) - b);
                    const gray = 0.299 * r + 0.587 * g + 0.114 * b;

                    rgVals[j] = rg; ybVals[j] = yb; grays[j] = gray;
                    rgSum += rg; ybSum += yb; graySum += gray;
                }

                const rgMean = rgSum / total, ybMean = ybSum / total, grayMean = graySum / total;

                let rgVarSum = 0, ybVarSum = 0, grayVarSum = 0;
                for (let j = 0; j < total; j++) {
                    rgVarSum += Math.pow(rgVals[j] - rgMean, 2);
                    ybVarSum += Math.pow(ybVals[j] - ybMean, 2);
                    grayVarSum += Math.pow(grays[j] - grayMean, 2);
                }

                const rgStd = Math.sqrt(rgVarSum / total);
                const ybStd = Math.sqrt(ybVarSum / total);
                const grayStd = Math.sqrt(grayVarSum / total);

                // Hasler and Suesstrunk color metric
                const colorfulness = Math.sqrt(Math.pow(rgStd, 2) + Math.pow(ybStd, 2)) + 0.3 * Math.sqrt(Math.pow(rgMean, 2) + Math.pow(ybMean, 2));

                // Microscopic samples: low color variance (mostly stained 1 color or dull)
                // Natural photos: Highly colorful (> 50-60) or huge global contrast (grayStd > 75)
                if (colorfulness > 55 || (colorfulness > 35 && grayStd > 75) || (colorfulness < 5 && grayStd > 85)) {
                    resolve(false);
                    return;
                }
                resolve(true);
            } catch (e) {
                console.warn("Validation error fallback", e);
                resolve(true);
            }
        };
        img.onerror = () => {
            URL.revokeObjectURL(url);
            resolve(true);
        };
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
        console.warn('Canvas fallback failed, using raw file:', e);
    }

    // 3️⃣ Last resort — return original file as-is
    return file;
}

export default function UploadPage() {
    const navigate = useNavigate();

    const [patientDetails, setPatientDetails] = useState({
        patientName: '',
        patientId: '',
        sampleId: '',
        date: new Date().toISOString().split('T')[0]
    });

    const [grids, setGrids] = useState({ 1: [], 2: [], 3: [], 4: [] });

    // Track which grids are currently converting HEIC files
    const [converting, setConverting] = useState({});

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setPatientDetails(prev => ({ ...prev, [name]: value }));
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
            // Validate images to reject dog/scenic photos or non-medical uploads
            for (const file of candidates) {
                const isValid = await validateImageContent(file);
                if (!isValid) {
                    alert(`Upload Rejected: The image "${file.name}" does not appear to be a valid microscopic clinical sample. Please upload actual acrosome sample images.`);
                    setConverting(prev => ({ ...prev, [gridId]: false }));
                    const input = document.getElementById(`fileInput-${gridId}`);
                    if (input) input.value = '';
                    return; // END PROCESS immediately
                }
            }

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

    return (
        <div className="upload-page animate-fade-in">
            <div className="page-header">
                <div>
                    <h1>New Analysis</h1>
                    <p className="text-muted text-sm">Upload up to 4 images per grid (16 total) and patient details</p>
                </div>
                <button
                    className={`btn ${isDetailsComplete && totalImages === 16 ? 'btn-primary' : 'btn-secondary'} start-analysis-btn`}
                    disabled={!isReady}
                    onClick={handleAnalyze}
                >
                    {isConverting ? <Loader2 size={18} className="animate-spin" /> : totalImages === 16 ? <Zap size={18} /> : <ArrowRight size={18} />}
                    {isConverting ? 'Converting...' : totalImages === 16 ? 'Start Full Analysis' : `Start Partial (${totalImages}/16)`}
                </button>
            </div>

            {/* Patient Details Form */}
            <div className="patient-details-card glass-card">
                <h3><User size={18} className="text-accent" /> Patient &amp; Sample Details</h3>
                <div className="pd-form-grid">
                    <div className="form-group">
                        <label>Patient Name</label>
                        <div className="input-wrap">
                            <User size={16} />
                            <input type="text" name="patientName" placeholder="e.g. Jane Doe" value={patientDetails.patientName} onChange={handleInputChange} />
                        </div>
                    </div>
                    <div className="form-group">
                        <label>Patient ID</label>
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
                    <div className="form-group">
                        <label>Date</label>
                        <div className="input-wrap">
                            <Calendar size={16} />
                            <input type="date" name="date" value={patientDetails.date} onChange={handleInputChange} />
                        </div>
                    </div>
                </div>
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
    );
}
