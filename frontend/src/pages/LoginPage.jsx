import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Eye, EyeOff, Mail, Lock } from 'lucide-react';
import Logo from '../components/Logo';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { loginApi } from '../services/api';
import { Sun, Moon } from 'lucide-react';
import './LoginPage.css';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPass, setShowPass] = useState(false);
    const [remember, setRemember] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const { login } = useAuth();
    const { theme, toggleTheme } = useTheme();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            const data = await loginApi(email, password);
            login(
                { id: data.user_id, username: data.username, role: data.role, email, full_name: data.full_name },
                data.access_token
            );
            navigate('/dashboard');
        } catch (err) {
            setError(err.message || 'Login failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-page">
            {/* Particle background */}
            <div className="acrosome-bg">
                {Array.from({ length: 30 }, (_, i) => (
                    <div
                        key={i}
                        className="particle"
                        style={{
                            left: `${Math.random() * 100}%`,
                            top: `${Math.random() * 100}%`,
                            animationDelay: `${Math.random() * 5}s`,
                            width: `${4 + Math.random() * 6}px`,
                            height: `${4 + Math.random() * 6}px`,
                        }}
                    />
                ))}
            </div>

            {/* Theme toggle */}
            <button className="login-theme-toggle btn-icon btn-ghost" onClick={toggleTheme}>
                {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
            </button>

            <div className="login-card glass-card animate-fade-in-up">
                <div className="login-header">
                    <Logo size="lg" />
                    <p className="login-tagline">AI-Based Acrosome Intactness Analysis for IVF Excellence</p>
                </div>

                <form className="login-form" onSubmit={handleSubmit}>
                    <div className="form-field">
                        <label htmlFor="email">Email Address</label>
                        <div className="input-with-icon">
                            <Mail size={18} className="input-icon" />
                            <input
                                id="email"
                                type="email"
                                placeholder="doctor@ivfclinic.com"
                                value={email}
                                onChange={e => setEmail(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <div className="form-field">
                        <label htmlFor="password">Password</label>
                        <div className="input-with-icon">
                            <Lock size={18} className="input-icon" />
                            <input
                                id="password"
                                type={showPass ? 'text' : 'password'}
                                placeholder="Enter your password"
                                value={password}
                                onChange={e => setPassword(e.target.value)}
                                required
                            />
                            <button
                                type="button"
                                className="pass-toggle"
                                onClick={() => setShowPass(!showPass)}
                            >
                                {showPass ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                    </div>

                    <div className="login-options">
                        <label className="remember-me">
                            <input
                                type="checkbox"
                                checked={remember}
                                onChange={e => setRemember(e.target.checked)}
                            />
                            <span>Remember me</span>
                        </label>
                    </div>

                    {error && <div className="login-error">{error}</div>}

                    <button
                        type="submit"
                        className="btn btn-primary btn-lg w-full login-btn"
                        disabled={loading}
                    >
                        {loading ? (
                            <span className="spinner" />
                        ) : (
                            'Sign In'
                        )}
                    </button>

                    <div className="register-link-container" style={{ marginTop: '1rem', textAlign: 'center', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                        <span>Don't have an account? </span>
                        <Link to="/register" style={{ color: 'var(--primary-accent)', fontWeight: 500, textDecoration: 'none' }}>Sign Up</Link>
                    </div>
                </form>

                <p className="login-footer-text">
                    Copyright © 2026 Nexacro . All Rights Reserved. | Developed by Lin's Infotech Company Ltd.
                </p>
            </div>
        </div>
    );
}
