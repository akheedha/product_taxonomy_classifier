import React, { useState, useEffect } from 'react';
import {
  X,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Maximize
} from 'lucide-react';

export default function ImageLightbox({
  isOpen,
  onClose,
  images = [],
  currentIndex = 0,
  onIndexChange,
  productTitle = '',
  productSku = '',
  categoryName = '',
}) {
  const [zoomLevel, setZoomLevel] = useState(1);

  // Reset zoom when image index changes or modal opens
  useEffect(() => {
    setZoomLevel(1);
  }, [currentIndex, isOpen]);

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowLeft' && currentIndex > 0) {
        onIndexChange(currentIndex - 1);
      }
      if (e.key === 'ArrowRight' && currentIndex < images.length - 1) {
        onIndexChange(currentIndex + 1);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, currentIndex, images.length, onClose, onIndexChange]);

  if (!isOpen || images.length === 0) return null;

  const currentImage = images[currentIndex] || images[0];

  const handleZoomIn = () => setZoomLevel((prev) => Math.min(3, prev + 0.3));
  const handleZoomOut = () => setZoomLevel((prev) => Math.max(0.6, prev - 0.3));
  const handleZoomReset = () => setZoomLevel(1);

  return (
    <div className="lightbox-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="lightbox-dialog" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="lightbox-header">
          <div className="lightbox-info">
            <h3 className="lightbox-title">{productTitle || 'Product Preview'}</h3>
            <div className="lightbox-meta">
              {productSku && <span className="lightbox-sku font-mono">SKU: {productSku}</span>}
              {categoryName && <span className="lightbox-cat">{categoryName}</span>}
              {images.length > 1 && (
                <span className="text-muted font-mono">
                  ({currentIndex + 1} / {images.length})
                </span>
              )}
            </div>
          </div>
          <div className="lightbox-actions">
            <a
              href={currentImage}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-sm btn-secondary lightbox-ext-btn"
              title="Open raw full-resolution image in new tab"
            >
              <ExternalLink size={13} />
              <span>Full Size</span>
            </a>
            <button
              type="button"
              className="lightbox-close-btn"
              onClick={onClose}
              aria-label="Close preview"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Main Image Viewport with Zoom */}
        <div className="lightbox-image-container">
          {images.length > 1 && (
            <button
              type="button"
              className="lightbox-nav-btn nav-prev"
              disabled={currentIndex === 0}
              onClick={() => onIndexChange(currentIndex - 1)}
              aria-label="Previous image"
            >
              <ChevronLeft size={24} />
            </button>
          )}

          <img
            src={currentImage}
            alt={productTitle || 'Product full view'}
            className="lightbox-main-img"
            style={{ transform: `scale(${zoomLevel})` }}
          />

          {images.length > 1 && (
            <button
              type="button"
              className="lightbox-nav-btn nav-next"
              disabled={currentIndex === images.length - 1}
              onClick={() => onIndexChange(currentIndex + 1)}
              aria-label="Next image"
            >
              <ChevronRight size={24} />
            </button>
          )}

          {/* Zoom floating controls */}
          <div className="lightbox-zoom-controls">
            <button
              type="button"
              className="lightbox-zoom-btn"
              onClick={handleZoomOut}
              title="Zoom out"
            >
              <ZoomOut size={14} />
            </button>
            <button
              type="button"
              className="lightbox-zoom-btn"
              onClick={handleZoomReset}
              title="Reset zoom"
            >
              {Math.round(zoomLevel * 100)}%
            </button>
            <button
              type="button"
              className="lightbox-zoom-btn"
              onClick={handleZoomIn}
              title="Zoom in"
            >
              <ZoomIn size={14} />
            </button>
          </div>
        </div>

        {/* Thumbnail Strip */}
        {images.length > 1 && (
          <div className="lightbox-thumbs-strip">
            {images.map((img, idx) => (
              <button
                key={idx}
                type="button"
                className={`lightbox-thumb-btn ${idx === currentIndex ? 'active' : ''}`}
                onClick={() => onIndexChange(idx)}
              >
                <img src={img} alt={`Thumb ${idx + 1}`} className="lightbox-thumb-img" />
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
