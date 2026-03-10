import logoImg from '../assets/logo.png';
import './Logo.css';

export default function Logo({ size = 'md' }) {
    const heights = {
        sm: 36,
        md: 48,
        lg: 72,
        xl: 96,
    };
    const h = heights[size] || heights.md;

    return (
        <div className="logo-container">
            <img
                src={logoImg}
                alt="NexAcro"
                className="logo-icon animate-float"
                style={{ height: h, width: 'auto' }}
            />
        </div>
    );
}
