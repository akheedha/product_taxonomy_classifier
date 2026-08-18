/**
 * ============================================================================
 * RESULTS TABLE & PAGINATION COMPONENT
 * ============================================================================
 * Purpose:
 *   Renders the main interactive catalog table:
 *     - Displays 50 product rows per page.
 *     - Handles loading spinners, in-progress job status cards, and empty state guides.
 *     - Provides pagination controls (Previous / Page X of Y / Next).
 *     - Passes approval and category override events down to individual rows.
 */

import React from 'react';
import ResultRow from './ResultRow';

export default function ResultsTable({
  results,        // Array of 50 classification result items for the current page
  page,           // Active page number
  totalPages,     // Total calculated pages
  totalCount,     // Total matching products count
  onPageChange,   // Callback when user clicks Prev/Next
  onApprove,      // Callback to approve a result
  onOverride,     // Callback to override category
  isLoading,      // Boolean: whether data fetch is in progress
  updatingId,     // Row ID undergoing PATCH update
  selectedJob,    // Active ClassificationJob model
  hasJobs,        // Boolean: whether any historical jobs exist
}) {
  // ---------------------------------------------------------------------------
  // 1. INITIAL LOADING SPINNER
  // ---------------------------------------------------------------------------
  if (isLoading && (!results || results.length === 0)) {
    return (
      <div className="table-card">
        <div className="state-container">
          <div className="loading-spinner" />
          <div style={{ fontWeight: 600, color: '#111827' }}>Loading taxonomy classification results...</div>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // 2. EMPTY / PROCESSING STATES
  // ---------------------------------------------------------------------------
  if (!results || results.length === 0) {
    const isJobActive = selectedJob && (selectedJob.status === 'running' || selectedJob.status === 'pending');

    // State A: Active job currently running in background
    if (isJobActive) {
      return (
        <div className="table-card">
          <div className="state-container" style={{ padding: '64px 20px' }}>
            <div className="loading-spinner" style={{ width: '36px', height: '36px' }} />
            <div style={{ fontWeight: 650, color: '#1e40af', fontSize: '15px' }}>
              Classification Job #{selectedJob.id} is in progress...
            </div>
            <div style={{ fontSize: '13px', color: '#64748b' }}>
              Processed {selectedJob.processed_count} of {selectedJob.total_products} items ({selectedJob.progress_percentage}%). Results will stream in automatically.
            </div>
          </div>
        </div>
      );
    }

    // State B: Brand new clean instance (no catalog uploaded yet)
    if (!hasJobs && totalCount === 0) {
      return (
        <div className="table-card">
          <div className="state-container" style={{ padding: '72px 24px' }}>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              background: '#eff6ff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '22px',
              marginBottom: '8px'
            }}>
              📊
            </div>
            <div style={{ fontWeight: 650, color: '#111827', fontSize: '16px' }}>
              No Product Catalog Data Loaded
            </div>
            <div style={{ fontSize: '13px', color: '#64748b', maxWidth: '440px', textAlign: 'center', lineHeight: '1.5' }}>
              Select and upload your Excel spreadsheet (<strong>.xlsx</strong>, <strong>.xls</strong>, or <strong>.csv</strong>) in the panel above, then click <strong>"⚡ Upload & Classify"</strong> to run automated category & attribute extraction.
            </div>
          </div>
        </div>
      );
    }

    // State C: Filter returned 0 results
    return (
      <div className="table-card">
        <div className="state-container">
          <div style={{ fontWeight: 600, color: '#111827' }}>No results match the current filters</div>
          <div style={{ fontSize: '13px' }}>Try loosening your confidence threshold or clearing search criteria.</div>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // 3. PAGINATED TABLE RENDER
  // ---------------------------------------------------------------------------
  const startIdx = (page - 1) * 50 + 1;
  const endIdx = Math.min(page * 50, totalCount);

  return (
    <div className="table-card">
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: '32%' }}>Product & Details</th>
              <th style={{ width: '34%' }}>Predicted Shopify Category & Attributes</th>
              <th style={{ width: '12%' }}>Confidence</th>
              <th style={{ width: '12%' }}>Status</th>
              <th style={{ width: '10%' }}>Review Action</th>
            </tr>
          </thead>
          <tbody>
            {results.map((result) => (
              <ResultRow
                key={result.id}
                result={result}
                onApprove={onApprove}
                onOverride={onOverride}
                isUpdating={updatingId === result.id}
              />
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="pagination-footer">
        <div className="page-info">
          Showing <strong>{startIdx}</strong>–<strong>{endIdx}</strong> of <strong>{totalCount}</strong> products
        </div>

        <div className="page-buttons">
          <button
            className="btn-page"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
          >
            Previous
          </button>
          <span style={{ fontSize: '12px', display: 'flex', alignItems: 'center', color: '#94a3b8', padding: '0 8px' }}>
            Page {page} of {totalPages || 1}
          </span>
          <button
            className="btn-page"
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
