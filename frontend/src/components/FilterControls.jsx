/**
 * ============================================================================
 * FILTER CONTROLS & CATALOG UPLOAD COMPONENT
 * ============================================================================
 * Purpose:
 *   Provides the top control surface for curators and operators:
 *     1. Spreadsheet Ingestion: Uploads .xlsx, .xls, or .csv catalogs.
 *     2. One-Click "Upload & Classify": Ingests catalog and immediately starts Celery worker.
 *     3. Live Job Progress Banner: Shows real-time spinner, processed counts, and animated progress bar.
 *     4. Filter Suite: Job run selector, "Needs Review Only" toggle, confidence threshold slider,
 *        and keyword search across product attributes.
 */

import React, { useState } from 'react';

export default function FilterControls({
  jobs,                    // Array of classification jobs
  selectedJob,             // Current selected job ID
  activeJobDetail,         // Detailed model for active job (includes progress %)
  onSelectJob,             // Job switch callback
  needsReviewOnly,         // Boolean: whether needs-review filter is active
  onToggleNeedsReview,     // Callback to toggle needs-review filter
  minConfidence,           // Number: 0.0 to 1.0 minimum confidence
  onChangeMinConfidence,   // Callback for confidence slider
  categorySearch,          // String: active search query
  onChangeCategorySearch,  // Callback for search input
  onStartJob,              // Callback to launch classification job
  isStartingJob,           // Boolean: job launch in-flight
  onImportProducts,        // Callback to upload spreadsheet
  isImporting,             // Boolean: file upload in-flight
  importStatus,            // Object: {type: 'info'|'success'|'error', message: string}
}) {
  // Local state for batch size and file upload inputs
  const [batchLimit, setBatchLimit] = useState(100);
  const [productFile, setProductFile] = useState(null);
  const [sheetName, setSheetName] = useState('');

  // Check if selected job is currently running in background
  const isJobActive = activeJobDetail && (activeJobDetail.status === 'running' || activeJobDetail.status === 'pending');

  return (
    <div className="filter-card">
      {/* ---------------------------------------------------------------------- */}
      {/* SECTION 1: SPREADSHEET UPLOAD & INGESTION PANEL                        */}
      {/* ---------------------------------------------------------------------- */}
      <div className="import-panel">
        <div className="form-group import-file">
          <label className="form-label">Upload Catalog Spreadsheet (.xlsx, .xls, .csv)</label>
          <input
            type="file"
            className="file-input"
            accept=".csv,.xlsx,.xls,.xlsm"
            onChange={(e) => setProductFile(e.target.files?.[0] || null)}
          />
        </div>

        <div className="form-group import-sheet">
          <label className="form-label">Sheet (Optional)</label>
          <input
            type="text"
            className="text-input"
            placeholder="0 or Sheet1"
            value={sheetName}
            onChange={(e) => setSheetName(e.target.value)}
          />
        </div>

        <div className="import-actions" style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
          {/* One-click Upload & Immediate Classification */}
          <button
            className="btn btn-primary"
            onClick={() => onImportProducts({
              file: productFile,
              sheet: sheetName.trim(),
              autoClassify: true,
              batchLimit: Math.max(1, batchLimit || 100)
            })}
            disabled={isImporting || !productFile || isStartingJob}
            title="Import the spreadsheet and immediately start AI classification"
          >
            {isImporting ? 'Processing...' : '⚡ Upload & Classify'}
          </button>

          {/* Import Only (Without launching job) */}
          <button
            className="btn btn-secondary"
            onClick={() => onImportProducts({
              file: productFile,
              sheet: sheetName.trim(),
              autoClassify: false,
            })}
            disabled={isImporting || !productFile}
            title="Import products without starting classification yet"
          >
            Import Only
          </button>
        </div>

        {/* Upload status alert banner */}
        {importStatus && (
          <div className={`import-status ${importStatus.type}`} style={{ gridColumn: '1 / -1' }}>
            {importStatus.message}
          </div>
        )}
      </div>

      {/* ---------------------------------------------------------------------- */}
      {/* SECTION 2: LIVE ASYNC JOB PROGRESS BANNER                              */}
      {/* ---------------------------------------------------------------------- */}
      {isJobActive && (
        <div style={{
          background: '#eff6ff',
          border: '1px solid #bfdbfe',
          borderRadius: '6px',
          padding: '12px 16px',
          marginBottom: '16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '16px'
        }}>
          <div>
            <div style={{ fontWeight: 650, color: '#1e40af', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="loading-spinner" style={{ width: '14px', height: '14px', borderWidth: '2px' }} />
              Classification Job #{activeJobDetail.id} is {activeJobDetail.status.toUpperCase()}
            </div>
            <div style={{ fontSize: '12px', color: '#3b82f6', marginTop: '3px' }}>
              Processed {activeJobDetail.processed_count} of {activeJobDetail.total_products} items ({activeJobDetail.progress_percentage}% completed)
            </div>
          </div>
          <div style={{ width: '180px', background: '#dbeafe', borderRadius: '999px', height: '8px', overflow: 'hidden' }}>
            <div style={{
              background: '#2563eb',
              height: '100%',
              width: `${activeJobDetail.progress_percentage}%`,
              transition: 'width 0.3s ease'
            }} />
          </div>
        </div>
      )}

      {/* ---------------------------------------------------------------------- */}
      {/* SECTION 3: CURATOR FILTERS & BATCH EXECUTION                           */}
      {/* ---------------------------------------------------------------------- */}
      <div className="filter-grid">
        {/* Job Selection Dropdown */}
        <div className="form-group">
          <label className="form-label">Classification Run / Job</label>
          <select
            className="select-input"
            value={selectedJob || ''}
            onChange={(e) => onSelectJob(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">All Classification Jobs</option>
            {jobs.map((j) => (
              <option key={j.id} value={j.id}>
                Job #{j.id} ({j.status}) - {j.processed_count}/{j.total_products} items
              </option>
            ))}
          </select>
        </div>

        {/* Needs Review Only Toggle Switch */}
        <div
          className="toggle-container"
          onClick={onToggleNeedsReview}
          title="Filter only products requiring curator review"
        >
          <div className={`toggle-switch ${needsReviewOnly ? 'active' : ''}`}>
            <div className="toggle-knob" />
          </div>
          <span className="toggle-label">Needs Review Only</span>
        </div>

        {/* Confidence Threshold Range Slider */}
        <div className="form-group">
          <label className="form-label">
            Min Confidence: <span className="slider-val">{(minConfidence * 100).toFixed(0)}%</span>
          </label>
          <div className="slider-container">
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={minConfidence}
              onChange={(e) => onChangeMinConfidence(parseFloat(e.target.value))}
              className="range-slider"
            />
          </div>
        </div>

        {/* Category / Keyword Search Input */}
        <div className="form-group">
          <label className="form-label">Search Category / Title</label>
          <input
            type="text"
            className="text-input"
            placeholder="Search category, SKU, materials..."
            value={categorySearch}
            onChange={(e) => onChangeCategorySearch(e.target.value)}
          />
        </div>

        {/* Batch Size Input */}
        <div className="form-group">
          <label className="form-label">Batch Size</label>
          <input
            type="number"
            className="text-input"
            min="1"
            max="10000"
            step="50"
            value={batchLimit}
            onChange={(e) => setBatchLimit(Number(e.target.value))}
          />
        </div>

        {/* Trigger Job Action Buttons */}
        <div className="job-actions">
          <button
            className="btn btn-primary"
            onClick={() => onStartJob({ limit: Math.max(1, batchLimit || 1), all: false })}
            disabled={isStartingJob || isJobActive}
          >
            {isStartingJob ? 'Queuing...' : 'Run Batch'}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => onStartJob({ limit: null, all: false })}
            disabled={isStartingJob || isJobActive}
          >
            Run Remaining
          </button>
        </div>
      </div>
    </div>
  );
}
