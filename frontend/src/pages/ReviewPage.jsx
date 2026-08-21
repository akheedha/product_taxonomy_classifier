import React, { useState } from 'react';
import FilterControls from '../components/results/FilterControls';
import ResultsTable from '../components/results/ResultsTable';

export default function ReviewPage({
  jobs = [],
  selectedJob,
  onJobChange,
  needsReviewOnly,
  onNeedsReviewChange,
  minConfidence,
  onMinConfidenceChange,
  searchTerm,
  onSearchChange,
  onResetFilters,
  results = [],
  resultsCount = 0,
  loading = false,
  expandedRowId,
  onToggleExpand,
  onApprove,
  onOverrideCategory,
  onBulkApprove,
  currentPage = 1,
  totalPages = 1,
  pageSize = 50,
  onPageChange,
  onPageSizeChange,
  sortBy = '',
  onSortByChange,
}) {
  const [viewMode, setViewMode] = useState('table'); // 'table' | 'grid'

  return (
    <div className="page-review">
      <div className="page-header">
        <div>
          <h2>Product Review Queue</h2>
          <p className="text-muted">
            Inspect AI category recommendations, compare original vs suggested taxonomies, review product specs, and approve or override.
          </p>
        </div>
      </div>

      {/* Filter & View Mode Toolbar */}
      <FilterControls
        jobs={jobs}
        selectedJob={selectedJob}
        onJobChange={onJobChange}
        needsReviewOnly={needsReviewOnly}
        onNeedsReviewChange={onNeedsReviewChange}
        minConfidence={minConfidence}
        onMinConfidenceChange={onMinConfidenceChange}
        searchTerm={searchTerm}
        onSearchChange={onSearchChange}
        totalCount={resultsCount}
        onResetFilters={onResetFilters}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        sortBy={sortBy}
        onSortByChange={onSortByChange}
      />

      {/* Paginated Results (Table or Card Grid) */}
      <ResultsTable
        results={results}
        loading={loading}
        expandedRowId={expandedRowId}
        onToggleExpand={onToggleExpand}
        onApprove={onApprove}
        onOverrideCategory={onOverrideCategory}
        onBulkApprove={onBulkApprove}
        currentPage={currentPage}
        totalPages={totalPages}
        pageSize={pageSize}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
        viewMode={viewMode}
      />
    </div>
  );
}
