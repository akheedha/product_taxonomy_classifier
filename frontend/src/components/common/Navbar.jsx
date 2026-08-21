import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  CheckSquare,
  UploadCloud,
  FolderTree,
  Activity,
  Sun,
  Moon,
  Sparkles
} from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

export default function Navbar({ activeJob }) {
  const { theme, toggleTheme, isDark } = useTheme();

  return (
    <header className="app-header">
      <div className="header-container">
        {/* Brand Logo & Title */}
        <NavLink to="/" className="header-brand">
          <div className="brand-logo">
            <Sparkles size={18} strokeWidth={2.2} />
          </div>
          <div>
            <h1 className="brand-title">Shopify Product Classifier</h1>
            <span className="brand-subtitle">Smart Product Categorization & Review</span>
          </div>
        </NavLink>

        {/* Navigation Tabs */}
        <nav className="nav-tabs" aria-label="Main Navigation">
          <NavLink
            to="/"
            end
            className={({ isActive }) => `nav-tab ${isActive ? 'active' : ''}`}
          >
            <LayoutDashboard size={15} strokeWidth={2} className="tab-icon" />
            <span>Overview</span>
          </NavLink>
          <NavLink
            to="/review"
            className={({ isActive }) => `nav-tab ${isActive ? 'active' : ''}`}
          >
            <CheckSquare size={15} strokeWidth={2} className="tab-icon" />
            <span>Review Queue</span>
          </NavLink>
          <NavLink
            to="/import"
            className={({ isActive }) => `nav-tab ${isActive ? 'active' : ''}`}
          >
            <UploadCloud size={15} strokeWidth={2} className="tab-icon" />
            <span>Import Products</span>
          </NavLink>
          <NavLink
            to="/taxonomy"
            className={({ isActive }) => `nav-tab ${isActive ? 'active' : ''}`}
          >
            <FolderTree size={15} strokeWidth={2} className="tab-icon" />
            <span>Category Directory</span>
          </NavLink>
        </nav>

        {/* Right Tools (Active Job Badge, Theme Switcher) */}
        <div className="header-right-tools">
          {activeJob && (
            <div className="header-status-badge">
              <Activity size={14} className="spin-slow" />
              <span className="pulse-indicator"></span>
              <span className="font-mono">
                Batch #{activeJob.id} ({activeJob.progress_percentage || 0}%)
              </span>
            </div>
          )}

          {/* Theme Toggle (Dark / Light) */}
          <button
            type="button"
            className="header-tool-btn"
            onClick={toggleTheme}
            title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            aria-label="Toggle theme"
          >
            {isDark ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>
      </div>
    </header>
  );
}
