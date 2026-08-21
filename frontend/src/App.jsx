/**
 * SHOPIFY PRODUCT TAXONOMY CLASSIFIER - APPLICATION ENTRYPOINT
 */

import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useSearchParams } from 'react-router-dom';
import Navbar from './components/common/Navbar';
import DashboardPage from './pages/DashboardPage';
import ReviewPage from './pages/ReviewPage';
import ImportPage from './pages/ImportPage';
import TaxonomyPage from './pages/TaxonomyPage';
import { ToastProvider, useToast } from './components/common/Toast';
import { ThemeProvider } from './context/ThemeContext';
import {
  getJobs,
  getJob,
  getResultSummary,
  getResults,
  createJob,
  updateResultReview
} from './services/classification';
import { usePolling } from './hooks/usePolling';

function ReviewPageWrapper({ jobs, onApprove, onOverrideCategory, onBulkApprove }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const { addToast } = useToast();

  const selectedJob = searchParams.get('job') || '';
  const needsReviewOnly = searchParams.get('needs_review') === 'true';
  const minConfidence = parseFloat(searchParams.get('min_conf') || '0.0');
  const searchTerm = searchParams.get('search') || '';
  const sortBy = searchParams.get('sort') || '';
  const currentPage = parseInt(searchParams.get('page') || '1', 10);
  const pageSize = parseInt(searchParams.get('page_size') || '50', 10);

  const [results, setResults] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [expandedRowId, setExpandedRowId] = useState(null);

  const updateParam = (key, value) => {
    const newParams = new URLSearchParams(searchParams);
    if (value === null || value === undefined || value === '' || value === false || value === 0.0) {
      newParams.delete(key);
    } else {
      newParams.set(key, value);
    }
    if (key !== 'page') {
      newParams.delete('page');
    }
    setSearchParams(newParams);
  };

  const fetchResults = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (selectedJob) params.job = selectedJob;
      if (needsReviewOnly) params.needs_review = true;
      if (minConfidence > 0) params.min_conf = minConfidence;
      if (searchTerm) params.search = searchTerm;
      if (currentPage > 1) params.page = currentPage;

      const data = await getResults(params);
      let list = data.results || [];

      // Client-side sort support if requested
      if (sortBy === 'conf_asc') {
        list = [...list].sort((a, b) => (a.confidence || 0) - (b.confidence || 0));
      } else if (sortBy === 'conf_desc') {
        list = [...list].sort((a, b) => (b.confidence || 0) - (a.confidence || 0));
      } else if (sortBy === 'name_asc') {
        list = [...list].sort((a, b) =>
          (a.product?.product_name || '').localeCompare(b.product?.product_name || '')
        );
      } else if (sortBy === 'sku_asc') {
        list = [...list].sort((a, b) =>
          (a.product?.product_number || '').localeCompare(b.product?.product_number || '')
        );
      }

      setResults(list);
      setTotalCount(data.count || 0);
      setTotalPages(Math.ceil((data.count || 0) / pageSize) || 1);
    } catch (err) {
      console.error('Failed to load review results:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedJob, needsReviewOnly, minConfidence, searchTerm, currentPage, pageSize, sortBy]);

  useEffect(() => {
    fetchResults();
  }, [fetchResults]);

  const handleToggleExpand = (id) => {
    setExpandedRowId(expandedRowId === id ? null : id);
  };

  const handleApproveAction = async (resultId) => {
    await onApprove(resultId);
    addToast({
      type: 'success',
      title: 'Product Approved',
      message: 'The category recommendation has been confirmed.',
    });
    fetchResults();
  };

  const handleOverrideAction = async (resultId, catId) => {
    await onOverrideCategory(resultId, catId);
    addToast({
      type: 'success',
      title: 'Category Updated',
      message: 'Product category was successfully modified and approved.',
    });
    fetchResults();
  };

  const handleBulkApproveAction = async (ids) => {
    await onBulkApprove(ids);
    addToast({
      type: 'success',
      title: 'Batch Approval Complete',
      message: `Successfully approved ${ids.length} products.`,
    });
    fetchResults();
  };

  const handleResetFilters = () => {
    setSearchParams(new URLSearchParams());
  };

  return (
    <ReviewPage
      jobs={jobs}
      selectedJob={selectedJob}
      onJobChange={(val) => updateParam('job', val)}
      needsReviewOnly={needsReviewOnly}
      onNeedsReviewChange={(val) => updateParam('needs_review', val)}
      minConfidence={minConfidence}
      onMinConfidenceChange={(val) => updateParam('min_conf', val)}
      searchTerm={searchTerm}
      onSearchChange={(val) => updateParam('search', val)}
      sortBy={sortBy}
      onSortByChange={(val) => updateParam('sort', val)}
      onResetFilters={handleResetFilters}
      results={results}
      resultsCount={totalCount}
      loading={loading}
      expandedRowId={expandedRowId}
      onToggleExpand={handleToggleExpand}
      onApprove={handleApproveAction}
      onOverrideCategory={handleOverrideAction}
      onBulkApprove={handleBulkApproveAction}
      currentPage={currentPage}
      totalPages={totalPages}
      pageSize={pageSize}
      onPageChange={(page) => updateParam('page', page)}
      onPageSizeChange={(size) => updateParam('page_size', size)}
    />
  );
}

function MainAppContent() {
  const [jobs, setJobs] = useState([]);
  const [activeJob, setActiveJob] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const { addToast } = useToast();

  const fetchJobsList = useCallback(async () => {
    try {
      const data = await getJobs();
      const jobList = Array.isArray(data) ? data : data.results || [];
      setJobs(jobList);

      const running = jobList.find((j) => j.status === 'running' || j.status === 'pending');
      setActiveJob(running || null);
    } catch (err) {
      console.error('Failed to fetch jobs:', err);
    }
  }, []);

  const fetchSummaryData = useCallback(async () => {
    setLoadingSummary(true);
    try {
      const data = await getResultSummary();
      setSummary(data);
    } catch (err) {
      console.error('Failed to fetch result summary:', err);
    } finally {
      setLoadingSummary(false);
    }
  }, []);

  useEffect(() => {
    fetchJobsList();
    fetchSummaryData();
  }, [fetchJobsList, fetchSummaryData]);

  // Live polling when active job is running
  usePolling(
    () => {
      fetchJobsList();
      fetchSummaryData();
    },
    2000,
    activeJob !== null
  );

  const handleLaunchJob = async (limit = 0) => {
    try {
      const newJob = await createJob(limit, false);
      setActiveJob(newJob);
      fetchJobsList();
      addToast({
        type: 'info',
        title: 'Categorization Started',
        message: 'Product categorization batch has been started.',
      });
    } catch (err) {
      addToast({
        type: 'error',
        title: 'Launch Failed',
        message: `Could not launch job: ${err.message}`,
      });
    }
  };

  const handleApprove = async (resultId) => {
    await updateResultReview(resultId, { approved: true, reviewed_by: 'curator' });
    fetchSummaryData();
  };

  const handleOverrideCategory = async (resultId, categoryId) => {
    await updateResultReview(resultId, {
      category_id: categoryId,
      approved: true,
      reviewed_by: 'curator',
    });
    fetchSummaryData();
  };

  const handleBulkApprove = async (resultIds) => {
    await Promise.all(
      resultIds.map((id) =>
        updateResultReview(id, { approved: true, reviewed_by: 'curator' })
      )
    );
    fetchSummaryData();
  };

  return (
    <div className="app-layout">
      <Navbar activeJob={activeJob} />
      <main className="main-content">
        <Routes>
          <Route
            path="/"
            element={
              <DashboardPage
                summary={summary}
                jobs={jobs}
                activeJob={activeJob}
                loading={loadingSummary}
                onLaunchJob={handleLaunchJob}
              />
            }
          />
          <Route
            path="/review"
            element={
              <ReviewPageWrapper
                jobs={jobs}
                onApprove={handleApprove}
                onOverrideCategory={handleOverrideCategory}
                onBulkApprove={handleBulkApprove}
              />
            }
          />
          <Route
            path="/import"
            element={<ImportPage onRefreshJobs={fetchJobsList} />}
          />
          <Route
            path="/taxonomy"
            element={<TaxonomyPage />}
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <ToastProvider>
          <MainAppContent />
        </ToastProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}
