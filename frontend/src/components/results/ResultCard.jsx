import React, { useState } from 'react';
import {
  Check,
  Maximize2,
  Copy,
  CheckCheck,
  ArrowRight,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Image as ImageIcon,
  Tag
} from 'lucide-react';

export default function ResultCard({
  item,
  isSelected = false,
  onToggleSelect,
  isExpanded = false,
  onToggleExpand,
  onApprove,
  onOpenLightbox,
}) {
  const [copiedSku, setCopiedSku] = useState(false);

  const product = item.product || {};
  const predicted = item.predicted_category || {};
  const confidence = item.confidence || 0.0;
  const confidencePercent = (confidence * 100).toFixed(1);
  const attributes = item.extracted_attributes || {};

  const getConfidenceLevelClass = (score) => {
    if (score >= 0.70) return 'confidence-high';
    if (score >= 0.50) return 'confidence-med';
    return 'confidence-low';
  };

  const handleCopySku = (e) => {
    e.stopPropagation();
    if (!product.product_number) return;
    navigator.clipboard.writeText(product.product_number);
    setCopiedSku(true);
    setTimeout(() => setCopiedSku(false), 2000);
  };

  const handleThumbnailClick = (e) => {
    e.stopPropagation();
    const allImgs = product.images && product.images.length > 0
      ? product.images
      : product.primary_image
      ? [product.primary_image]
      : [];
    if (allImgs.length > 0 && onOpenLightbox) {
      onOpenLightbox(
        allImgs,
        0,
        product.product_name,
        product.product_number,
        predicted.full_name || predicted.name
      );
    }
  };

  const allProductImages = product.images && product.images.length > 0
    ? product.images
    : product.primary_image
    ? [product.primary_image]
    : [];

  return (
    <div
      className={`result-card-item card-panel ${isSelected ? 'card-selected' : ''} ${
        item.needs_manual_review ? 'card-needs-review' : ''
      } ${item.approved ? 'card-approved' : ''}`}
    >
      {/* Card Header with Checkbox, SKU & Status */}
      <div className="card-top-bar">
        <label className="card-checkbox-label" onClick={(e) => e.stopPropagation()}>
          <input
            type="checkbox"
            checked={isSelected}
            onChange={onToggleSelect}
            className="table-checkbox"
            aria-label={`Select product ${product.product_number}`}
          />
        </label>

        <div className="card-sku-pill">
          <span className="font-mono text-sm">{product.product_number || 'N/A'}</span>
          <button
            type="button"
            className="btn-copy-sku"
            onClick={handleCopySku}
            title={copiedSku ? 'Copied!' : 'Copy SKU'}
          >
            {copiedSku ? <CheckCheck size={11} className="text-success" /> : <Copy size={11} />}
          </button>
        </div>

        <div className="card-status-pill">
          {item.approved ? (
            <span className="status-pill status-approved">
              <span className="status-dot"></span>
              Approved
            </span>
          ) : item.needs_manual_review ? (
            <span className="status-pill status-review">
              <span className="status-dot"></span>
              Review
            </span>
          ) : (
            <span className="status-pill status-confident">
              <span className="status-dot"></span>
              Auto-Matched
            </span>
          )}
        </div>
      </div>

      {/* Product Image & Thumbnail Section */}
      <div className="card-media-wrapper" onClick={handleThumbnailClick}>
        {product.primary_image ? (
          <img
            src={product.primary_image}
            alt={product.product_name || 'Product thumbnail'}
            className="card-media-img"
            loading="lazy"
            onError={(e) => {
              e.target.onerror = null;
              e.target.style.display = 'none';
              if (e.target.nextSibling) e.target.nextSibling.style.display = 'flex';
            }}
          />
        ) : null}
        <div
          className="card-media-placeholder"
          style={{ display: product.primary_image ? 'none' : 'flex' }}
        >
          <ImageIcon size={32} className="text-muted" />
        </div>

        {allProductImages.length > 0 && (
          <button
            type="button"
            className="card-zoom-overlay-btn"
            onClick={handleThumbnailClick}
            title="Preview full image"
          >
            <Maximize2 size={13} />
            <span>Preview ({allProductImages.length})</span>
          </button>
        )}

        {product.brand && <span className="card-brand-badge">{product.brand}</span>}
      </div>

      {/* Product Title */}
      <div className="card-body-section">
        <h4 className="card-product-title" title={product.product_name}>
          {product.product_name || 'Untitled Product'}
        </h4>

        {/* Category Diff Box */}
        <div className="card-category-diff">
          <div className="diff-source-row">
            <span className="diff-tag-label">Source:</span>
            <span className="diff-source-val" title={product.product_category || 'None'}>
              {product.product_category
                ? `${product.product_category}${
                    product.product_sub_category ? ' / ' + product.product_sub_category : ''
                  }`
                : 'Unassigned'}
            </span>
          </div>

          <div className="diff-arrow-divider">
            <ArrowRight size={13} className="text-primary" />
          </div>

          <div className="diff-target-row">
            <span className="diff-tag-label">Suggested:</span>
            <span
              className="diff-target-val font-medium"
              title={predicted.full_name || predicted.name || 'Not categorized'}
            >
              {predicted.name || predicted.full_name || 'Not Categorized'}
            </span>
          </div>
        </div>

        {/* Confidence Meter Bar */}
        <div className="card-confidence-block">
          <div className="confidence-label-row">
            <span className="text-muted text-sm">Match Confidence</span>
            <span className={`confidence-badge ${getConfidenceLevelClass(confidence)} font-mono`}>
              {confidencePercent}%
            </span>
          </div>
          <div className="confidence-bar-bg">
            <div
              className={`confidence-bar-fill ${getConfidenceLevelClass(confidence)}`}
              style={{ width: `${Math.min(100, Math.max(5, confidence * 100))}%` }}
            ></div>
          </div>
        </div>

        {/* Quick Attributes Preview */}
        {Object.keys(attributes).length > 0 && (
          <div className="card-attributes-preview">
            {Object.entries(attributes).slice(0, 3).map(([k, v]) => (
              <span key={k} className="card-attr-tag">
                <strong>{k}:</strong> {typeof v === 'object' ? v.value : v}
              </span>
            ))}
            {Object.keys(attributes).length > 3 && (
              <span className="card-attr-tag-more">+{Object.keys(attributes).length - 3}</span>
            )}
          </div>
        )}
      </div>

      {/* Card Actions Footer */}
      <div className="card-footer-actions">
        {!item.approved && (
          <button
            type="button"
            className="btn btn-sm btn-success btn-card-approve"
            onClick={() => onApprove(item.id)}
            title="Approve suggested category"
          >
            <Check size={13} strokeWidth={2.5} />
            <span>Approve</span>
          </button>
        )}

        <button
          type="button"
          className={`btn btn-sm ${isExpanded ? 'btn-primary' : 'btn-secondary'} btn-card-details`}
          onClick={onToggleExpand}
        >
          <span>{isExpanded ? 'Close' : 'Details'}</span>
          {isExpanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
        </button>
      </div>
    </div>
  );
}
