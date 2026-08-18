/**
 * ============================================================================
 * RESULT ROW COMPONENT (WITH EXPANDABLE DETAIL DRAWER & OVERRIDES)
 * ============================================================================
 * Purpose:
 *   Renders a single classified product row in the review table.
 *
 * Key Capabilities:
 *   1. Product Thumbnail & Metadata Display: SKU, title, brand, materials, color.
 *   2. Breadcrumb Shopify Category: Shows full hierarchical taxonomy path + Level + ID.
 *   3. Confidence Score Color Badge:
 *      - Green: >= 75%
 *      - Yellow: 55% - 74%
 *      - Red: < 55%
 *   4. Status Indicators: Approved, Needs Review, High Confidence, Failed.
 *   5. In-Place Curator Review Actions:
 *      - "Approve": Marks item approved, clearing review flag.
 *      - "Override": Interactive dropdown showing top 3 AI alternative categories
 *        with confidence scores, plus a custom Shopify GID input for manual mapping.
 *      - "Details": Expands drawer displaying extracted RapidFuzz attributes and full SKU details.
 */

import React, { useState, useRef, useEffect } from 'react';

export default function ResultRow({
  result,       // ClassificationResult object from backend
  onApprove,    // Approval callback
  onOverride,   // Category override callback
  isUpdating,   // Boolean indicating whether this row is actively saving a PATCH request
}) {
  const [isExpanded, setIsExpanded] = useState(false);          // Drawer open/close state
  const [showOverride, setShowOverride] = useState(false);      // Override dropdown visibility
  const [customCategoryId, setCustomCategoryId] = useState(''); // Custom Shopify Category ID input
  const dropdownRef = useRef(null);

  const product = result.product || {};
  const category = result.predicted_category;
  const conf = result.confidence || 0;

  // ---------------------------------------------------------------------------
  // Helper: Returns color-coded badge for confidence score
  // ---------------------------------------------------------------------------
  const getConfidenceBadge = (score) => {
    if (score >= 0.75) {
      return <span className="badge badge-green">{(score * 100).toFixed(1)}%</span>;
    } else if (score >= 0.55) {
      return <span className="badge badge-yellow">{(score * 100).toFixed(1)}%</span>;
    } else {
      return <span className="badge badge-red">{(score * 100).toFixed(1)}%</span>;
    }
  };

  // Close override dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowOverride(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Handle clicking an AI-suggested alternative category
  const handleSelectAlternative = (catId) => {
    onOverride(result.id, catId);
    setShowOverride(false);
  };

  // Handle submitting a custom category ID manually
  const handleCustomSubmit = (e) => {
    e.preventDefault();
    if (customCategoryId.trim()) {
      onOverride(result.id, customCategoryId.trim());
      setCustomCategoryId('');
      setShowOverride(false);
    }
  };

  const primaryImage = product.primary_image || (product.images && product.images[0]);
  const attributes = result.extracted_attributes ? Object.entries(result.extracted_attributes) : [];
  const alternatives = result.alternative_categories || [];
  const categoryShortId = category?.id ? category.id.split('/').pop() : null;

  return (
    <>
    {/* Main Table Row */}
    <tr
      className={`result-row ${isExpanded ? 'is-expanded' : ''}`}
      onClick={() => setIsExpanded((prev) => !prev)}
      title="Click row to toggle product details & detected attributes"
    >
      {/* 1. Product Thumbnail & Basic Info */}
      <td>
        <div className="product-cell">
          {primaryImage ? (
            <img
              src={primaryImage}
              alt={product.product_name}
              className="product-thumb"
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />
          ) : (
            <div
              className="product-thumb"
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '10px',
                color: '#64748b',
              }}
            >
              No Img
            </div>
          )}

          <div>
            <div className="product-sku">{product.product_number || 'SKU-N/A'}</div>
            <div className="product-title" title={product.product_name}>
              {product.product_name || 'Untitled Product'}
            </div>
            {product.brand && <div className="product-brand">{product.brand}</div>}
            <div className="product-meta">
              {product.materials ? `Material: ${product.materials.substring(0, 35)}...` : ''}
              {product.product_color ? ` • Color: ${product.product_color}` : ''}
            </div>
          </div>
        </div>
      </td>

      {/* 2. Predicted Shopify Taxonomy Category */}
      <td>
        {category ? (
          <div>
            <div className="category-breadcrumb">{category.full_name}</div>
            <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>
              Level {category.level} • ID: {categoryShortId}
            </div>
          </div>
        ) : (
          <span style={{ color: '#ef4444', fontStyle: 'italic' }}>Unclassified</span>
        )}
      </td>

      {/* 3. Confidence Score Badge */}
      <td>{getConfidenceBadge(conf)}</td>

      {/* 4. Review Status & Flag */}
      <td>
        {result.status === 'failed' ? (
          <span className="badge badge-red" title={result.error_message || 'Classification failed'}>
            Failed
          </span>
        ) : result.approved ? (
          <span className="badge badge-approved">
            Approved {result.reviewed_by ? `(${result.reviewed_by})` : ''}
          </span>
        ) : result.needs_manual_review ? (
          <span className="badge badge-review">Needs Review</span>
        ) : (
          <span className="badge badge-green">High Confidence</span>
        )}
      </td>

      {/* 5. Curator Actions: Details, Approve, and Override Dropdown */}
      <td>
        <div className="row-actions" onClick={(e) => e.stopPropagation()}>
          {/* Expand Drawer Button */}
          <button
            className="btn btn-expand"
            onClick={() => setIsExpanded((prev) => !prev)}
            type="button"
          >
            {isExpanded ? 'Hide' : 'Details'}
          </button>

          {/* In-Place Approve Button */}
          <button
            className={`btn btn-approve ${result.approved ? 'approved' : ''}`}
            onClick={() => onApprove(result.id)}
            disabled={isUpdating || result.approved}
            title={result.approved ? 'Already approved' : 'Mark as Approved'}
          >
            {result.approved ? 'Approved' : 'Approve'}
          </button>

          {/* Category Override Dropdown Container */}
          <div className="override-container" ref={dropdownRef}>
            <button
              className="btn btn-override"
              onClick={() => setShowOverride(!showOverride)}
              disabled={isUpdating}
            >
              Override
            </button>

            {showOverride && (
              <div className="override-dropdown-menu">
                <div className="override-header">Suggested Alternatives</div>

                {/* List AI-generated candidate categories */}
                {result.alternative_categories && result.alternative_categories.length > 0 ? (
                  result.alternative_categories.map((alt) => (
                    <div
                      key={alt.category_id}
                      className="override-option"
                      onClick={() => handleSelectAlternative(alt.category_id)}
                    >
                      <div className="override-option-name">{alt.name}</div>
                      <div className="override-option-path">{alt.full_name}</div>
                      <div className="override-option-score">
                        Score: {(alt.score * 100).toFixed(1)}%
                      </div>
                    </div>
                  ))
                ) : (
                  <div style={{ padding: '6px 8px', fontSize: '11px', color: '#64748b' }}>
                    No automated alternatives available.
                  </div>
                )}

                {/* Custom Category ID fallback input */}
                <form onSubmit={handleCustomSubmit} style={{ marginTop: '8px', paddingTop: '6px', borderTop: '1px solid var(--border)' }}>
                  <div style={{ fontSize: '10px', color: '#94a3b8', marginBottom: '4px' }}>
                    Or enter Shopify Category ID:
                  </div>
                  <input
                    type="text"
                    className="override-search-input"
                    placeholder="gid://shopify/TaxonomyCategory/..."
                    value={customCategoryId}
                    onChange={(e) => setCustomCategoryId(e.target.value)}
                  />
                </form>
              </div>
            )}
          </div>
        </div>
      </td>
    </tr>

    {/* Expandable Detail Drawer */}
    {isExpanded && (
      <tr className="result-detail-row">
        <td colSpan="5">
          <div className="result-detail-panel">
            {/* Raw Input Metadata Used */}
            <div className="detail-section">
              <div className="detail-title">Product Data Used</div>
              <div className="detail-grid">
                <div><span>SKU</span>{product.product_number || 'Not provided'}</div>
                <div><span>Brand</span>{product.brand || 'Not provided'}</div>
                <div><span>Source Type</span>{[product.product_category, product.product_sub_category].filter(Boolean).join(' > ') || 'Not provided'}</div>
                <div><span>Images</span>{product.images?.length ? `${product.images.length} available` : 'No image'}</div>
              </div>
            </div>

            {/* Extracted RapidFuzz Taxonomy Attributes */}
            <div className="detail-section">
              <div className="detail-title">Detected Attributes</div>
              {attributes.length > 0 ? (
                <div className="attribute-list">
                  {attributes.map(([name, value]) => (
                    <div key={name} className="attribute-item">
                      <span>{name}</span>
                      <strong>{value.value}</strong>
                      <em>{((value.confidence || 0) * 100).toFixed(0)}%</em>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="detail-empty">No category attributes detected for this result.</div>
              )}
            </div>

            {/* Top Alternative Category Recommendations */}
            <div className="detail-section">
              <div className="detail-title">Alternative Categories</div>
              {alternatives.length > 0 ? (
                <div className="alternative-list">
                  {alternatives.map((alt) => (
                    <button
                      key={alt.category_id}
                      className="alternative-item"
                      onClick={() => handleSelectAlternative(alt.category_id)}
                      type="button"
                    >
                      <span>{alt.full_name}</span>
                      <strong>{(alt.score * 100).toFixed(1)}%</strong>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="detail-empty">No alternative suggestions stored for this result.</div>
              )}
            </div>

            {/* Error Message Section if Failed */}
            {result.error_message && (
              <div className="detail-section">
                <div className="detail-title">Error</div>
                <div className="detail-error">{result.error_message}</div>
              </div>
            )}
          </div>
        </td>
      </tr>
    )}
    </>
  );
}
