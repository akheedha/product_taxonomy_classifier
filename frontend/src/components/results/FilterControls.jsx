import React from 'react';
import {
  Search,
  RotateCcw,
  X,
  Filter,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  LayoutList,
  LayoutGrid,
  ArrowDownUp,
  AlertCircle
} from 'lucide-react';

export default function FilterControls({
  jobs = [],
  selectedJob = '',
  onJobChange,
  needsReviewOnly = false,
  onNeedsReviewChange,
  minConfidence = 0.0,
  onMinConfidenceChange,
  searchTerm = '',
  onSearchChange,
  totalCount = 0,
  onResetFilters,
  viewMode = 'table',
  onViewModeChange,
  sortBy = '',
  onSortByChange,
}) {
  const hasActiveFilters =
    selectedJob !== '' ||
    needsReviewOnly ||
    minConfidence > 0 ||
    searchTerm !== '' ||
    sortBy !== '';

  const activeFiltersCount = [
    selectedJob !== '',
    needsReviewOnly,
    minConfidence > 0,
    searchTerm !== '',
    sortBy !== '',
  ].filter(Boolean).length;

  return (
    <div className="filter-panel">
      {/* Quick Filter Presets Row & View Switcher */}
      <div className="filter-presets-row">
        <span className="preset-label">Quick Presets:</span>
        <button
          type="button"
          className={`preset-pill ${!needsReviewOnly && minConfidence === 0 ? 'active' : ''}`}
          onClick={() => {
            onNeedsReviewChange(false);
            onMinConfidenceChange(0.0);
          }}
        >
          All Products
        </button>

        <button
          type="button"
          className={`preset-pill pill-warning ${needsReviewOnly ? 'active' : ''}`}
          onClick={() => {
            onNeedsReviewChange(!needsReviewOnly);
          }}
        >
          <AlertTriangle size={12} />
          <span>Needs Review</span>
        </button>

        <button
          type="button"
          className={`preset-pill pill-success ${minConfidence === 0.7 && !needsReviewOnly ? 'active' : ''}`}
          onClick={() => {
            onNeedsReviewChange(false);
            onMinConfidenceChange(minConfidence === 0.7 ? 0.0 : 0.7);
          }}
        >
          <CheckCircle2 size={12} />
          <span>High Match (≥70%)</span>
        </button>

        <button
          type="button"
          className={`preset-pill ${minConfidence === 0.9 && !needsReviewOnly ? 'active' : ''}`}
          onClick={() => {
            onNeedsReviewChange(false);
            onMinConfidenceChange(minConfidence === 0.9 ? 0.0 : 0.9);
          }}
        >
          <Sparkles size={12} />
          <span>Top Matches (≥90%)</span>
        </button>

        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px' }}>
          {/* View Mode Switcher (Table vs Grid) */}
          <div className="view-switcher-group" role="group" aria-label="View mode">
            <button
              type="button"
              className={`view-btn ${viewMode === 'table' ? 'active' : ''}`}
              onClick={() => onViewModeChange && onViewModeChange('table')}
              title="Table View"
            >
              <LayoutList size={14} />
              <span>Table</span>
            </button>
            <button
              type="button"
              className={`view-btn ${viewMode === 'grid' ? 'active' : ''}`}
              onClick={() => onViewModeChange && onViewModeChange('grid')}
              title="Card Grid View"
            >
              <LayoutGrid size={14} />
              <span>Cards</span>
            </button>
          </div>
        </div>
      </div>

      <div className="filter-row">
        {/* Job Batch Selector */}
        <div className="filter-group">
          <label htmlFor="job-select" className="filter-label">
            Product Batch
          </label>
          <select
            id="job-select"
            className="filter-select"
            value={selectedJob}
            onChange={(e) => onJobChange(e.target.value)}
          >
            <option value="">All Batches / Full Catalog</option>
            {jobs.map((job) => (
              <option key={job.id} value={job.id}>
                Batch #{job.id} - {job.status.toUpperCase()} ({job.processed_count}/{job.total_products} items)
              </option>
            ))}
          </select>
        </div>

        {/* Sort Selector */}
        {onSortByChange && (
          <div className="filter-group">
            <label htmlFor="sort-select" className="filter-label">
              Sort By
            </label>
            <select
              id="sort-select"
              className="filter-select"
              value={sortBy}
              onChange={(e) => onSortByChange(e.target.value)}
            >
              <option value="">Default (Status / ID)</option>
              <option value="conf_asc">Match Score (Lowest First)</option>
              <option value="conf_desc">Match Score (Highest First)</option>
              <option value="name_asc">Product Name (A-Z)</option>
              <option value="sku_asc">SKU Number</option>
            </select>
          </div>
        )}

        {/* Confidence Threshold Slider */}
        <div className="filter-group slider-group">
          <div className="slider-header">
            <label htmlFor="confidence-slider" className="filter-label">
              Min Match Score
            </label>
            <span className="slider-value font-mono">{(minConfidence * 100).toFixed(0)}%</span>
          </div>
          <input
            id="confidence-slider"
            type="range"
            min="0"
            max="1"
            step="0.05"
            className="filter-slider"
            value={minConfidence}
            onChange={(e) => onMinConfidenceChange(parseFloat(e.target.value))}
          />
        </div>

        {/* Text Search */}
        <div className="filter-group search-group">
          <label htmlFor="search-input" className="filter-label">
            Search Products
          </label>
          <div className="search-wrapper">
            <Search size={14} className="search-icon" />
            <input
              id="search-input"
              type="text"
              className="search-input"
              placeholder="Search by SKU, title, brand, category..."
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
            />
            {searchTerm && (
              <button
                type="button"
                className="search-clear-btn"
                onClick={() => onSearchChange('')}
                title="Clear search"
              >
                <X size={13} />
              </button>
            )}
          </div>
        </div>

        {/* Reset Button */}
        <div className="filter-group button-group">
          <button
            type="button"
            className="btn btn-secondary btn-reset"
            onClick={onResetFilters}
            disabled={!hasActiveFilters}
            title="Reset all filters"
          >
            <RotateCcw size={13} />
            <span>Reset</span>
            {activeFiltersCount > 0 && <span className="active-filters-badge font-mono">{activeFiltersCount}</span>}
          </button>
        </div>
      </div>

      <div className="filter-summary-bar">
        <div>
          Showing <span className="highlight-count font-mono">{totalCount.toLocaleString()}</span> products
          {needsReviewOnly && <span className="text-warning font-medium"> (Needs Review Only)</span>}
          {minConfidence > 0 && (
            <span className="text-primary font-medium"> (≥{(minConfidence * 100).toFixed(0)}% Match)</span>
          )}
        </div>
      </div>
    </div>
  );
}
