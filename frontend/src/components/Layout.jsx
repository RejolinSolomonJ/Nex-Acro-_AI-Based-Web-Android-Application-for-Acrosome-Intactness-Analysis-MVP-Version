import { useState, useRef, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import { Menu, LogOut, ChevronDown } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './Layout.css';

export default function Layout() {
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [userMenuOpen, setUserMenuOpen] = useState(false);
    const { user, logout } = useAuth();
    const menuRef = useRef(null);

    useEffect(() => {
        function handleClickOutside(event) {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setUserMenuOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    return (
        <div className="layout">
            <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
            <div className="layout-main">
                <header className="top-bar">
                    <button className="menu-btn btn-icon btn-ghost" onClick={() => setSidebarOpen(true)}>
                        <Menu size={22} />
                    </button>
                    <div className="top-bar-right" ref={menuRef}>
                        <div className="user-profile-wrap" onClick={() => setUserMenuOpen(!userMenuOpen)}>
                            <div className="user-info">
                                <div className="user-avatar">
                                    {(user?.full_name || user?.username || 'D')[0].toUpperCase()}
                                </div>
                                <div className="user-details">
                                    <span className="user-name">{user?.full_name || user?.username || 'Doctor'}</span>
                                    <span className="user-role">{user?.role || 'doctor'}</span>
                                </div>
                                <ChevronDown size={14} className={`menu-chevron ${userMenuOpen ? 'open' : ''}`} />
                            </div>

                            {userMenuOpen && (
                                <div className="user-dropdown card animate-slide-up">
                                    <div className="dropdown-header">
                                        <p className="dropdown-name">{user?.full_name || user?.username || 'Doctor'}</p>
                                        <p className="dropdown-email">{user?.email || 'doctor@nexacro.ai'}</p>
                                    </div>
                                    <div className="dropdown-divider" />
                                    <button className="dropdown-item logout" onClick={logout}>
                                        <LogOut size={16} />
                                        <span>Sign Out</span>
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </header>
                <main className="content">
                    <Outlet />
                </main>
                <footer className="global-footer">
                    <p>
                        Copyright © 2026 Nexacro . All Rights Reserved. | Developed by Lin's Infotech Company Ltd.
                    </p>
                </footer>
            </div>

            {/* Acrosome particle background */}
            <div className="acrosome-bg">
                {Array.from({ length: 20 }, (_, i) => (
                    <div
                        key={i}
                        className="particle"
                        style={{
                            left: `${Math.random() * 100}%`,
                            top: `${Math.random() * 100}%`,
                            animationDelay: `${Math.random() * 5}s`,
                        }}
                    />
                ))}
            </div>
        </div>
    );
}
