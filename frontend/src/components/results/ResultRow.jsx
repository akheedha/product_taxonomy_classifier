import React, { useState, useEffect } from 'react';
import {
  ChevronRight,
  Check,
  Image as ImageIcon,
  ExternalLink,
  Tag,
  FileText,
  Sliders,
  CheckCircle2,
  AlertCircle,
  Search,
  Copy,
  CheckCheck,
  Maximize2,
  ArrowRight,
  Sparkles
} from 'lucide-react';
import { searchCategories } from '../../services/taxonomy';

export default function ResultRow({
  item,
  isSelected = false,
  onToggleSelect,
  isExpanded,
  onToggleExpand,
  onApprove,
  onOverrideCategory,
  onOpenLightbox,
}) {
  const [selectedAlt, setSelectedAlt] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [savingOverride, setSavingOverride] = useState(false);
  const [copiedSku, setCopiedSku] = useState(false);

  const product = item.product || {};
  const predicted = item.predicted_category || {};
  const confidence = item.confidence || 0.0;
  const confidencePercent = (confidence * 100).toFixed(1);
  const alternatives = item.alternative_categories || [];
  const attributes = item.extracted_attributes || {};

  // Debounced category search in drawer
  useEffect(() => {
    if (!searchQuery.trim() || searchQuery.length < 2) {
      setSearchResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const data = await searchCategories(searchQuery.trim());
        const list = Array.isArray(data) ? data : data.results || [];
        setSearchResults(list.slice(0, 8));
      } catch (err) {
        console.error('Failed to search categories:', err);
      } finally {
        setIsSearching(false);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [searchQuery]);

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
    const allImgs =
      product.images && product.images.length > 0
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

  const handleGalleryThumbClick = (e, index) => {
    e.preventDefault();
    e.stopPropagation();
    if (product.images && product.images.length > 0 && onOpenLightbox) {
      onOpenLightbox(
        product.images,
        index,
        product.product_name,
        product.product_number,
        predicted.full_name || predicted.name
      );
    }
  };

  const handleOverrideSubmit = async (e) => {
    e.preventDefault();
    if (!selectedAlt) return;
    setSavingOverride(true);
    try {
      await onOverrideCategory(item.id, selectedAlt);
      setSelectedAlt('');
      setSearchQuery('');
    } finally {
      setSavingOverride(false);
    }
  };

  const handleSelectSearchedCategory = (cat) => {
    setSelectedAlt(cat.id || cat.category_id);
  };

  const allProductImages =
    product.images && product.images.length > 0
      ? product.images
      : product.primary_image
      ? [product.primary_image]
      : [];

  return (
    <React.Fragment>
      <tr
        className={`result-row ${isExpanded ? 'row-expanded' : ''} ${
          item.needs_manual_review ? 'row-needs-review' : ''
        } ${isSelected ? 'row-selected' : ''}`}
      >
        {/* Checkbox Column */}
        <td className="cell-checkbox col-checkbox" style={{ textAlign: 'center', width: '38px' }}>
          <input
            type="checkbox"
            checked={isSelected}
            onChange={onToggleSelect}
            aria-label={`Select product ${product.product_number}`}
            className="table-checkbox"
          />
        </td>

        {/* Expand Icon */}
        <td className="cell-expand col-expand" style={{ width: '36px' }}>
          <button
            type="button"
            className="btn-icon-expand"
            onClick={onToggleExpand}
            aria-expanded={isExpanded}
            title={isExpanded ? 'Hide details' : 'Show product details'}
          >
            <ChevronRight size={15} className={`expand-chevron ${isExpanded ? 'rotated' : ''}`} />
          </button>
        </td>

        {/* Thumbnail Image */}
        <td className="cell-thumb col-thumb" style={{ width: '52px' }}>
          <div
            className="thumb-wrapper"
            onClick={handleThumbnailClick}
            title={allProductImages.length > 0 ? 'Click to preview image' : ''}
            style={{ cursor: allProductImages.length > 0 ? 'pointer' : 'default' }}
          >
            {product.primary_image ? (
              <>
                <img
                  src={product.primary_image}
                  alt={product.product_name || 'Thumbnail'}
                  className="product-thumbnail"
                  loading="lazy"
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.style.display = 'none';
                    if (e.target.nextSibling) e.target.nextSibling.style.display = 'flex';
                  }}
                />
                <span className="thumb-zoom-hint">
                  <Maximize2 size={10} />
                </span>
              </>
            ) : null}
            <div
              className="no-image-placeholder"
              style={{ display: product.primary_image ? 'none' : 'flex' }}
            >
              <ImageIcon size={14} className="text-muted" />
            </div>
          </div>
        </td>

        {/* SKU / Product Number with 1-Click Copy */}
        <td className="cell-sku col-sku" style={{ width: '120px' }}>
          <div className="sku-container">
            <span className="sku-text font-mono">{product.product_number || 'N/A'}</span>
            <button
              type="button"
              className="btn-copy-sku"
              onClick={handleCopySku}
              title={copiedSku ? 'Copied!' : 'Copy SKU to clipboard'}
            >
              {copiedSku ? <CheckCheck size={12} className="text-success" /> : <Copy size={12} />}
            </button>
          </div>
        </td>

        {/* Product Title & Brand */}
        <td className="cell-title col-title">
          <div className="title-text font-medium" title={product.product_name}>
            {product.product_name || 'Untitled Product'}
          </div>
          {product.brand && <span className="brand-tag">{product.brand}</span>}
        </td>

        {/* Original Source Category */}
        <td className="cell-source-category col-source">
          {product.product_category ? (
            <div
              className="source-cat-wrapper"
              title={`${product.product_category}${
                product.product_sub_category ? ' / ' + product.product_sub_category : ''
              }`}
            >
              <span className="source-cat-main">{product.product_category}</span>
              {product.product_sub_category && (
                <span className="source-cat-sub">
                  <span className="breadcrumb-arrow">/</span>
                  {product.product_sub_category}
                </span>
              )}
            </div>
          ) : (
            <span className="text-muted italic">None</span>
          )}
        </td>

        {/* Suggested Category */}
        <td className="cell-prediction col-prediction">
          {predicted.full_name ? (
            <div className="predicted-breadcrumb font-medium" title={predicted.full_name}>
              {predicted.full_name}
            </div>
          ) : (
            <span className="text-warning italic">Not Categorized</span>
          )}
        </td>

        {/* Match Score */}
        <td className="cell-confidence col-confidence" style={{ width: '110px' }}>
          <div className="confidence-wrapper">
            <span className={`confidence-badge ${getConfidenceLevelClass(confidence)} font-mono`}>
              {confidencePercent}%
            </span>
            <div className="confidence-bar-bg">
              <div
                className={`confidence-bar-fill ${getConfidenceLevelClass(confidence)}`}
                style={{ width: `${Math.min(100, Math.max(5, confidence * 100))}%` }}
              ></div>
            </div>
          </div>
        </td>

        {/* Status */}
        <td className="cell-status col-status" style={{ width: '115px' }}>
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
        </td>

        {/* Actions */}
        <td className="cell-actions col-actions text-right" style={{ width: '145px' }}>
          <div className="action-buttons-group">
            {!item.approved && (
              <button
                type="button"
                className="btn btn-sm btn-success btn-approve"
                onClick={() => onApprove(item.id)}
                title="Approve this category recommendation"
              >
                <Check size={13} strokeWidth={2.5} />
                <span>Approve</span>
              </button>
            )}
            <button
              type="button"
              className={`btn btn-sm ${isExpanded ? 'btn-primary' : 'btn-secondary'} btn-details`}
              onClick={onToggleExpand}
              title={isExpanded ? 'Close details panel' : 'Open details panel'}
            >
              {isExpanded ? 'Hide' : 'Details'}
            </button>
          </div>
        </td>
      </tr>

      {/* Expandable Details Drawer */}
      {isExpanded && (
        <tr className="drawer-row">
          <td colSpan="10" className="drawer-cell">
            <div className="drawer-content">
              <div className="drawer-grid">
                {/* Column 1: Product Specifications */}
                <div className="drawer-col">
                  <div className="drawer-col-header">
                    <FileText size={15} className="text-primary" />
                    <h4>Product Details</h4>
                  </div>
                  <dl className="spec-list">
                    <dt>SKU Number:</dt>
                    <dd className="font-mono">{product.product_number || 'N/A'}</dd>

                    {product.brand && (
                      <React.Fragment>
                        <dt>Brand:</dt>
                        <dd>{product.brand}</dd>
                      </React.Fragment>
                    )}

                    {product.materials && (
                      <React.Fragment>
                        <dt>Materials:</dt>
                        <dd>{product.materials}</dd>
                      </React.Fragment>
                    )}

                    {product.product_color && (
                      <React.Fragment>
                        <dt>Color / Finish:</dt>
                        <dd>{product.product_color}</dd>
                      </React.Fragment>
                    )}

                    {(product.product_description || product.description) && (
                      <React.Fragment>
                        <dt>Description:</dt>
                        <dd className="desc-text">{product.product_description || product.description}</dd>
                      </React.Fragment>
                    )}

                    {product.bullets && (
                      <React.Fragment>
                        <dt>Key Features:</dt>
                        <dd className="desc-text">{product.bullets}</dd>
                      </React.Fragment>
                    )}

                    {product.product_dimensions && (
                      <React.Fragment>
                        <dt>Dimensions:</dt>
                        <dd>{product.product_dimensions}</dd>
                      </React.Fragment>
                    )}
                  </dl>
                </div>

                {/* Column 2: Detected Product Attributes & Gallery */}
                <div className="drawer-col">
                  <div className="drawer-col-header">
                    <Tag size={15} className="text-primary" />
                    <h4>Detected Attributes</h4>
                  </div>
                  {Object.keys(attributes).length > 0 ? (
                    <div className="attribute-chips">
                      {Object.entries(attributes).map(([attrName, attrData]) => (
                        <div key={attrName} className="attr-chip">
                          <span className="attr-name">{attrName}:</span>
                          <span className="attr-val">
                            {typeof attrData === 'object' ? attrData.value : attrData}
                          </span>
                          {typeof attrData === 'object' && attrData.confidence && (
                            <span className="attr-conf font-mono">
                              ({(attrData.confidence * 100).toFixed(0)}%)
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted text-sm">No specific attributes detected.</p>
                  )}

                  {product.images && product.images.length > 0 && (
                    <div className="multi-image-gallery">
                      <div className="gallery-header">
                        <h5>Product Images ({product.images.length}) - Click to preview</h5>
                      </div>
                      <div className="gallery-thumbnails">
                        {product.images.slice(0, 8).map((imgUrl, i) => (
                          <div
                            key={i}
                            className="gallery-thumb-link"
                            onClick={(e) => handleGalleryThumbClick(e, i)}
                            title="Click to preview full size image"
                          >
                            <img
                              src={imgUrl}
                              alt={`Product photo ${i + 1}`}
                              className="gallery-thumb"
                            />
                            <Maximize2 size={10} className="gallery-link-icon" />
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Column 3: Review Actions & Change Category */}
                <div className="drawer-col actions-col">
                  <div className="drawer-col-header">
                    <Sliders size={15} className="text-primary" />
                    <h4>Review &amp; Actions</h4>
                  </div>

                  <div className="current-status-box">
                    <div className="status-detail-row">
                      <span className="status-detail-label">Current Category:</span>
                      <span className="status-detail-value font-medium">
                        {predicted.name || 'Unassigned'}
                      </span>
                    </div>
                    <div className="status-detail-row">
                      <span className="status-detail-label">Match Score:</span>
                      <span className="status-detail-value font-mono">{confidencePercent}%</span>
                    </div>
                    <div className="status-detail-row">
                      <span className="status-detail-label">Status:</span>
                      <span className="status-detail-value">
                        {item.approved
                          ? 'Approved'
                          : item.needs_manual_review
                          ? 'Needs Review (Low Match)'
                          : 'Auto-Matched (High Match)'}
                      </span>
                    </div>
                    {item.reviewed_by && (
                      <div className="status-detail-row">
                        <span className="status-detail-label">Reviewed By:</span>
                        <span className="status-detail-value font-medium">{item.reviewed_by}</span>
                      </div>
                    )}
                  </div>

                  <form onSubmit={handleOverrideSubmit} className="override-form">
                    <label htmlFor={`override-select-${item.id}`} className="override-label">
                      Change to Another Category
                    </label>

                    {/* AI Alternative Suggestions */}
                    {alternatives.length > 0 && (
                      <select
                        id={`override-select-${item.id}`}
                        className="filter-select"
                        value={selectedAlt}
                        onChange={(e) => setSelectedAlt(e.target.value)}
                      >
                        <option value="">Choose AI alternative category...</option>
                        {alternatives.map((alt) => (
                          <option key={alt.category_id} value={alt.category_id}>
                            {alt.name} ({(alt.score * 100).toFixed(0)}% match) - {alt.full_name}
                          </option>
                        ))}
                      </select>
                    )}

                    {/* Live Search All Categories */}
                    <div className="category-search-box">
                      <div className="search-wrapper">
                        <Search size={13} className="search-icon" />
                        <input
                          type="text"
                          className="search-input"
                          placeholder="Or search all 5,000+ categories..."
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                        />
                      </div>

                      {searchResults.length > 0 && (
                        <div className="category-search-dropdown">
                          {searchResults.map((cat) => (
                            <div
                              key={cat.id}
                              className={`search-result-item ${
                                selectedAlt === cat.id ? 'selected' : ''
                              }`}
                              onClick={() => handleSelectSearchedCategory(cat)}
                            >
                              <div className="result-cat-name">{cat.name}</div>
                              <div className="result-cat-path">{cat.full_path || cat.full_name}</div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    <button
                      type="submit"
                      className="btn btn-sm btn-primary btn-override-submit"
                      disabled={!selectedAlt || savingOverride}
                    >
                      {savingOverride ? 'Saving Change...' : 'Save Category Change'}
                    </button>
                  </form>
                </div>
              </div>
            </div>
          </td>
        </tr>
      )}
    </React.Fragment>
  );
}
