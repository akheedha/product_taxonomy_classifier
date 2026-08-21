import React, { useEffect } from 'react';
import { X, Command, Keyboard, Check, Eye, ListFilter, ArrowUpDown } from 'lucide-react';

export default function KeyboardShortcutsModal({ isOpen, onClose }) {
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const shortcutGroups = [
    {
      title: 'Navigation & Browsing',
      icon: <ArrowUpDown size={15} />,
      shortcuts: [
        { key: 'J / ↓', description: 'Navigate to next product in review queue' },
        { key: 'K / ↑', description: 'Navigate to previous product' },
        { key: 'E / Space', description: 'Expand / Collapse product details drawer' },
        { key: 'Tab', description: 'Cycle through interactive controls' },
      ],
    },
    {
      title: 'Review & Curation Actions',
      icon: <Check size={15} />,
      shortcuts: [
        { key: 'A', description: 'Quick-Approve highlighted product category' },
        { key: 'X', description: 'Toggle checkbox selection on highlighted item' },
        { key: 'Esc', description: 'Close active drawer, modal, or image preview' },
      ],
    },
    {
      title: 'Global & Modal Shortcuts',
      icon: <Keyboard size={15} />,
      shortcuts: [
        { key: '?', description: 'Open this Keyboard Shortcuts cheat sheet' },
        { key: '← / →', description: 'Previous / Next photo when viewing image lightbox' },
      ],
    },
  ];

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-dialog shortcuts-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-group">
            <div className="modal-icon-badge">
              <Keyboard size={18} />
            </div>
            <div>
              <h3>Keyboard Shortcuts</h3>
              <p className="text-muted text-sm">Supercharge your review workflow with fast hotkeys</p>
            </div>
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close shortcuts modal"
          >
            <X size={18} />
          </button>
        </div>

        <div className="modal-body shortcuts-list-grid">
          {shortcutGroups.map((group, idx) => (
            <div key={idx} className="shortcut-group-card">
              <div className="shortcut-group-header">
                <span className="group-icon">{group.icon}</span>
                <h4>{group.title}</h4>
              </div>
              <div className="shortcuts-rows">
                {group.shortcuts.map((item, sIdx) => (
                  <div key={sIdx} className="shortcut-item">
                    <span className="shortcut-desc">{item.description}</span>
                    <kbd className="shortcut-key font-mono">{item.key}</kbd>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="modal-footer">
          <span className="text-muted text-sm">Press <kbd className="shortcut-key font-mono">Esc</kbd> or click outside to dismiss</span>
          <button type="button" className="btn btn-primary btn-sm" onClick={onClose}>
            Got It
          </button>
        </div>
      </div>
    </div>
  );
}
