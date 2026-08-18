/**
 * ============================================================================
 * SHOPIFY PRODUCT TAXONOMY CLASSIFIER - CURATOR REVIEW DASHBOARD
 * ============================================================================
 * Purpose:
 *   Root React application component managing global dashboard state, real-time
 *   background job auto-polling, catalog spreadsheet uploads (.xlsx/.xls/.csv),
 *   paginated classification results, and in-place curator actions (approvals & category overrides).
 *
 * Architecture:
 *   - App.jsx: Master orchestrator & state container.
 *   - SummaryBar.jsx: Top KPI metrics bar (Total, Approved %, Needing Review %, Errors).
 *   - FilterControls.jsx: Catalog uploader, job selector, confidence slider, keyword search.
 *   - ResultsTable.jsx: Paginated table displaying product details, predicted Shopify categories,
 *     extracted attributes, and in-place review actions.
 *   - ResultRow.jsx: Individual product row with expandable detail drawers and category override dropdowns.
 */

import React, { useState, useEffect, useCallback } from 'react';
import SummaryBar from './components/SummaryBar';
import FilterControls from './components/FilterControls';
import ResultsTable from './components/ResultsTable';

// Base REST API prefix (proxied to Django backend at http://localhost:8000 via Vite)
const API_BASE = '/api';

export default function App() {
  // ---------------------------------------------------------------------------
  // 1. FILTER & SELECTION STATE
  // ---------------------------------------------------------------------------
  const [jobs, setJobs] = useState([]);                      // List of historical classification jobs
  const [selectedJobId, setSelectedJobId] = useState(null);  // Selected job ID filter (or null for all)
  const [selectedJob, setSelectedJob] = useState(null);      // Full active job model (status, progress)
  const [needsReviewOnly, setNeedsReviewOnly] = useState(false); // Toggle: Only show items needing review
  const [minConfidence, setMinConfidence] = useState(0.0);   // Slider: Minimum confidence filter (0.0 to 1.0)
  const [categorySearch, setCategorySearch] = useState('');  // Keyword search (SKU, title, category, material)
  const [page, setPage] = useState(1);                       // Current active pagination page

  // ---------------------------------------------------------------------------
  // 2. DATA & LOADING STATE
  // ---------------------------------------------------------------------------
  const [results, setResults] = useState([]);                // Paginated array of classification results
  const [totalCount, setTotalCount] = useState(0);           // Total matching products count
  const [totalPages, setTotalPages] = useState(1);           // Total calculated pages (50 items/page)
  const [isLoading, setIsLoading] = useState(false);         // Table loading spinner state
  const [updatingId, setUpdatingId] = useState(null);        // Row ID currently undergoing PATCH update
  const [isStartingJob, setIsStartingJob] = useState(false); // Job launch button loading state
  const [isImporting, setIsImporting] = useState(false);     // Spreadsheet upload loading state
  const [importStatus, setImportStatus] = useState(null);    // Upload alert banner: {type, message}

  // ---------------------------------------------------------------------------
  // 3. KPI SUMMARY METRICS STATE
  // ---------------------------------------------------------------------------
  const [resultsSummary, setResultsSummary] = useState({
    total: 0,
    processed: 0,
    approved: 0,
    needsReview: 0,
    failed: 0,
  });

  // ---------------------------------------------------------------------------
  // 4. API FETCH HANDLERS
  // ---------------------------------------------------------------------------

  /**
   * Fetches list of all classification jobs from GET /api/jobs/.
   */
  const fetchJobs = async () => {
    try {
      const res = await fetch(`${API_BASE}/jobs/`);
      if (res.ok) {
        const data = await res.json();
        setJobs(data);
        if (data.length > 0 && !selectedJobId) {
          // Auto-select most recent job by default
          setSelectedJobId(data[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to load jobs:', err);
    }
  };

  /**
   * Fetches detailed progress of selected job from GET /api/jobs/{id}/.
   */
  const fetchJobDetail = useCallback(async (jobId) => {
    if (!jobId) {
      setSelectedJob(null);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/jobs/${jobId}/`);
      if (res.ok) {
        const data = await res.json();
        setSelectedJob(data);
      }
    } catch (err) {
      console.error('Failed to load job detail:', err);
    }
  }, []);

  /**
   * Fetches paginated classification results from GET /api/results/ matching active filters.
   */
  const fetchResults = useCallback(async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedJobId) params.append('job', selectedJobId);
      if (needsReviewOnly) params.append('needs_review', 'true');
      if (minConfidence > 0) params.append('min_confidence', minConfidence);
      if (categorySearch.trim()) params.append('category', categorySearch.trim());
      params.append('page', page);

      const res = await fetch(`${API_BASE}/results/?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setResults(data.results || []);
        setTotalCount(data.count || 0);
        setTotalPages(Math.ceil((data.count || 0) / 50) || 1);
      }
    } catch (err) {
      console.error('Failed to fetch results:', err);
    } finally {
      setIsLoading(false);
    }
  }, [selectedJobId, needsReviewOnly, minConfidence, categorySearch, page]);

  /**
   * Fetches aggregate KPI metrics from GET /api/results/summary/ matching active filters.
   */
  const fetchSummary = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (selectedJobId) params.append('job', selectedJobId);
      if (needsReviewOnly) params.append('needs_review', 'true');
      if (minConfidence > 0) params.append('min_confidence', minConfidence);
      if (categorySearch.trim()) params.append('search', categorySearch.trim());

      const res = await fetch(`${API_BASE}/results/summary/?${params.toString()}`);
      if (res.ok) {
        setResultsSummary(await res.json());
      }
    } catch (err) {
      console.error('Failed to fetch result summary:', err);
    }
  }, [selectedJobId, needsReviewOnly, minConfidence, categorySearch]);

  // Initial load
  useEffect(() => {
    fetchJobs();
  }, []);

  // Refresh results whenever filters or page changes
  useEffect(() => {
    fetchResults();
  }, [fetchResults]);

  // Refresh KPI summary cards whenever filters change
  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  // Refresh selected job detail when job ID changes
  useEffect(() => {
    fetchJobDetail(selectedJobId);
  }, [selectedJobId, fetchJobDetail]);

  // ---------------------------------------------------------------------------
  // 5. REAL-TIME AUTO-POLLING WHILE JOB IS ACTIVE
  // ---------------------------------------------------------------------------
  // If the current job is RUNNING or PENDING, poll every 1.5 seconds so that the
  // progress bar and newly completed products stream in without manual page reloads.
  useEffect(() => {
    if (!selectedJobId) return;
    const isRunning = selectedJob && (selectedJob.status === 'running' || selectedJob.status === 'pending');
    if (!isRunning) return;

    const interval = setInterval(() => {
      fetchJobDetail(selectedJobId);
      fetchResults();
      fetchSummary();
      fetchJobs();
    }, 1500);

    return () => clearInterval(interval);
  }, [selectedJobId, selectedJob?.status, fetchJobDetail, fetchResults, fetchSummary]);

  // ---------------------------------------------------------------------------
  // 6. IN-PLACE CURATOR ACTIONS (APPROVE & CATEGORY OVERRIDE)
  // ---------------------------------------------------------------------------

  /**
   * Approves a classification result via PATCH /api/results/{id}/.
   * Updates row state in-place without triggering full table reload.
   */
  const handleApprove = async (resultId) => {
    setUpdatingId(resultId);
    try {
      const res = await fetch(`${API_BASE}/results/${resultId}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          approved: true,
          reviewed_by: 'curator',
        }),
      });

      if (res.ok) {
        const updated = await res.json();
        setResults((prev) =>
          prev.map((item) => (item.id === resultId ? { ...item, ...updated } : item))
        );
        fetchSummary();
      }
    } catch (err) {
      console.error('Failed to approve result:', err);
    } finally {
      setUpdatingId(null);
    }
  };

  /**
   * Overrides predicted category with a curator-chosen category via PATCH /api/results/{id}/.
   */
  const handleOverride = async (resultId, overrideCatId) => {
    setUpdatingId(resultId);
    try {
      const res = await fetch(`${API_BASE}/results/${resultId}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          override_category_id: overrideCatId,
          approved: true,
          reviewed_by: 'curator',
        }),
      });

      if (res.ok) {
        const updated = await res.json();
        setResults((prev) =>
          prev.map((item) => (item.id === resultId ? { ...item, ...updated } : item))
        );
        fetchSummary();
      }
    } catch (err) {
      console.error('Failed to override category:', err);
    } finally {
      setUpdatingId(null);
    }
  };

  /**
   * Launches a new batch classification job via POST /api/jobs/.
   */
  const handleStartJob = async ({ limit = 100, all = false } = {}) => {
    setIsStartingJob(true);
    try {
      const res = await fetch(`${API_BASE}/jobs/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ limit, all, sync: false }),
      });

      if (res.ok) {
        const newJob = await res.json();
        await fetchJobs();
        setSelectedJobId(newJob.id);
        setSelectedJob(newJob);
        await fetchResults();
        await fetchSummary();
      } else {
        const errData = await res.json();
        alert(errData.detail || 'Could not start classification job.');
      }
    } catch (err) {
      console.error('Failed to start classification job:', err);
    } finally {
      setIsStartingJob(false);
    }
  };

  /**
   * Handles uploading a catalog file (.xlsx, .xls, .csv) and optionally
   * auto-triggering AI classification immediately.
   */
  const handleImportProducts = async ({ file, sheet, autoClassify = false, batchLimit = 100 }) => {
    if (!file) return;

    setIsImporting(true);
    setImportStatus({
      type: 'info',
      message: `Uploading and parsing "${file.name}"...`,
    });

    try {
      const formData = new FormData();
      formData.append('file', file);
      if (sheet) formData.append('sheet', sheet);

      const res = await fetch(`${API_BASE}/catalog/import/`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || data.error || 'Product import failed.');
      }

      if (autoClassify) {
        setImportStatus({
          type: 'info',
          message: `${data.filename} imported! Queuing AI classification job...`,
        });

        // Trigger job immediately
        const jobRes = await fetch(`${API_BASE}/jobs/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ limit: batchLimit || null, all: false, sync: false }),
        });

        if (jobRes.ok) {
          const newJob = await jobRes.json();
          await fetchJobs();
          setSelectedJobId(newJob.id);
          setSelectedJob(newJob);
          setImportStatus({
            type: 'success',
            message: `${data.filename} imported successfully! Classification Job #${newJob.id} started (${newJob.total_products} products queued).`,
          });
        } else {
          setImportStatus({
            type: 'success',
            message: `${data.filename} imported. Click "Run Batch" to begin classification.`,
          });
        }
      } else {
        setImportStatus({
          type: 'success',
          message: `${data.filename} imported successfully! Click "Run Batch" or "Run Remaining" to classify.`,
        });
      }

      await fetchJobs();
      await fetchResults();
      await fetchSummary();
    } catch (err) {
      setImportStatus({
        type: 'error',
        message: err.message || 'Product import failed.',
      });
    } finally {
      setIsImporting(false);
    }
  };

  // ---------------------------------------------------------------------------
  // 7. RENDER COMPONENT TREE
  // ---------------------------------------------------------------------------
  return (
    <div className="app-container">
      {/* Top Brand Header */}
      <header className="app-header">
        <div className="brand-section">
          <div className="brand-logo">ST</div>
          <div>
            <h1 className="brand-title">Shopify Taxonomy Classifier</h1>
            <div className="brand-subtitle">
              Product import, batch classification, and curator review
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            className="btn btn-page"
            onClick={() => {
              fetchJobs();
              fetchResults();
              fetchSummary();
              if (selectedJobId) fetchJobDetail(selectedJobId);
            }}
            title="Refresh dashboard"
          >
            Refresh
          </button>
        </div>
      </header>

      {/* Top KPI Metrics Bar */}
      <SummaryBar job={selectedJob} resultsSummary={resultsSummary} />

      {/* Catalog Uploader & Filter Controls */}
      <FilterControls
        jobs={jobs}
        selectedJob={selectedJobId}
        activeJobDetail={selectedJob}
        onSelectJob={(id) => {
          setSelectedJobId(id);
          setPage(1);
        }}
        needsReviewOnly={needsReviewOnly}
        onToggleNeedsReview={() => {
          setNeedsReviewOnly(!needsReviewOnly);
          setPage(1);
        }}
        minConfidence={minConfidence}
        onChangeMinConfidence={(val) => {
          setMinConfidence(val);
          setPage(1);
        }}
        categorySearch={categorySearch}
        onChangeCategorySearch={(val) => {
          setCategorySearch(val);
          setPage(1);
        }}
        onStartJob={handleStartJob}
        isStartingJob={isStartingJob}
        onImportProducts={handleImportProducts}
        isImporting={isImporting}
        importStatus={importStatus}
      />

      {/* Paginated Results Table with In-Place Reviews */}
      <ResultsTable
        results={results}
        page={page}
        totalPages={totalPages}
        totalCount={totalCount}
        onPageChange={(p) => setPage(p)}
        onApprove={handleApprove}
        onOverride={handleOverride}
        isLoading={isLoading}
        updatingId={updatingId}
        selectedJob={selectedJob}
        hasJobs={jobs.length > 0}
      />
    </div>
  );
}
