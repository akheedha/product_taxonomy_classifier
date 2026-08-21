import React, { useState, useEffect, useCallback } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  Inbox,
  Loader2,
  CheckCircle2,
  X,
  Sparkles,
  Download,
  CheckSquare
} from 'lucide-react';
import ResultRow from './ResultRow';
import ResultCard from './ResultCard';
import ImageLightbox from '../common/ImageLightbox';

export default function ResultsTable({
  results = [],
  loading = false,
  expandedRowId = null,
  onToggleExpand,
  onApprove,
  onOverrideCategory,
  onBulkApprove,
  currentPage = 1,
  totalPages = 1,
  pageSize = 50,
  onPageChange,
  onPageSizeChange,
  viewMode = 'table',
}) {
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [bulkApproving, setBulkApproving] = useState(false);

  // Lightbox state
  const [lightbox, setLightbox] = useState({
    isOpen: false,
    images: [],
    currentIndex: 0,
    productTitle: '',
    productSku: '',
    categoryName: '',
  });

  const unapprovedResults = results.filter((r) => !r.approved);
  const allCurrentPageSelected =
    unapprovedResults.length > 0 &&
    unapprovedResults.every((r) => selectedIds.has(r.id));

  const handleToggleSelectAll = () => {
    if (allCurrentPageSelected) {
      setSelectedIds(new Set());
    } else {
      const newSelected = new Set(selectedIds);
      unapprovedResults.forEach((r) => newSelected.add(r.id));
      setSelectedIds(newSelected);
    }
  };

  const handleToggleSelectRow = (id) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const handleExecuteBulkApprove = async () => {
    if (selectedIds.size === 0 || !onBulkApprove) return;
    setBulkApproving(true);
    try {
      await onBulkApprove(Array.from(selectedIds));
      setSelectedIds(new Set());
    } finally {
      setBulkApproving(false);
    }
  };

  // Export selected items as CSV
  const handleExportSelectedCSV = () => {
    const itemsToExport =
      selectedIds.size > 0
        ? results.filter((r) => selectedIds.has(r.id))
        : results;

    const headers = [
      'ID',
      'SKU',
      'Product Name',
      'Brand',
      'Original Category',
      'Suggested Category',
      'Confidence Score',
      'Status',
    ];

    const csvRows = [
      headers.join(','),
      ...itemsToExport.map((item) => {
        const p = item.product || {};
        const c = item.predicted_category || {};
        return [
          `"${item.id}"`,
          `"${p.product_number || ''}"`,
          `"${(p.product_name || '').replace(/"/g, '""')}"`,
          `"${(p.brand || '').replace(/"/g, '""')}"`,
          `"${(p.product_category || '').replace(/"/g, '""')}"`,
          `"${(c.full_name || c.name || '').replace(/"/g, '""')}"`,
          `"${((item.confidence || 0) * 100).toFixed(1)}%"`,
          `"${item.approved ? 'Approved' : item.needs_manual_review ? 'Needs Review' : 'Auto-Matched'}"`,
        ].join(',');
      }),
    ];

    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `taxonomy_export_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleOpenLightbox = (images, index, title, sku, category) => {
    setLightbox({
      isOpen: true,
      images,
      currentIndex: index,
      productTitle: title,
      productSku: sku,
      categoryName: category,
    });
  };

  const handleCloseLightbox = () => {
    setLightbox((prev) => ({ ...prev, isOpen: false }));
  };

  if (loading && results.length === 0) {
    return (
      <div className="table-container card-panel">
        <div className="loading-spinner-container">
          <Loader2 size={32} className="spinner-icon" />
          <p>Loading products from catalog...</p>
        </div>
      </div>
    );
  }

  if (!loading && results.length === 0) {
    return (
      <div className="table-container card-panel empty-state">
        <div className="empty-icon-box">
          <Inbox size={32} strokeWidth={1.5} />
        </div>
        <h3>No Products Found</h3>
        <p>No products match your current search or filter criteria. Try adjusting or resetting filters.</p>
      </div>
    );
  }

  return (
    <div>
      {/* Floating Sticky Bulk Actions Bar */}
      {selectedIds.size > 0 && (
        <div className="bulk-action-bar">
          <div className="bulk-info">
            <span className="bulk-count-badge font-mono">{selectedIds.size}</span>
            <span className="bulk-text">products selected</span>
          </div>

          <div className="bulk-actions">
            <button
              type="button"
              className="btn btn-sm btn-bulk-approve"
              onClick={handleExecuteBulkApprove}
              disabled={bulkApproving}
            >
              {bulkApproving ? (
                <>
                  <Loader2 size={13} className="spin-slow" />
                  <span>Approving {selectedIds.size} items...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 size={14} />
                  <span>Approve Selected ({selectedIds.size})</span>
                </>
              )}
            </button>

            <button
              type="button"
              className="btn btn-sm btn-secondary"
              onClick={handleExportSelectedCSV}
              title="Export selected rows to CSV file"
            >
              <Download size={13} />
              <span>Export CSV</span>
            </button>

            <button
              type="button"
              className="btn btn-sm btn-secondary"
              onClick={() => setSelectedIds(new Set())}
            >
              <X size={13} />
              <span>Clear Selection</span>
            </button>
          </div>
        </div>
      )}

      {/* Main Results Container (Table View vs Grid Card View) */}
      {viewMode === 'grid' ? (
        <div className="results-grid-container">
          {results.map((item, idx) => (
            <ResultCard
              key={item.id}
              item={item}
              isSelected={selectedIds.has(item.id)}
              onToggleSelect={() => handleToggleSelectRow(item.id)}
              isExpanded={expandedRowId === item.id}
              onToggleExpand={() => onToggleExpand(item.id)}
              onApprove={onApprove}
              onOpenLightbox={handleOpenLightbox}
            />
          ))}
        </div>
      ) : (
        <div className="table-container">
          <div className="table-responsive">
            <table className="results-table">
              <thead>
                <tr>
                  <th className="col-checkbox" style={{ width: '38px', textAlign: 'center' }}>
                    <input
                      type="checkbox"
                      aria-label="Select all products on page"
                      checked={allCurrentPageSelected}
                      onChange={handleToggleSelectAll}
                      disabled={unapprovedResults.length === 0}
                      className="table-checkbox"
                    />
                  </th>
                  <th className="col-expand" style={{ width: '36px' }}></th>
                  <th className="col-thumb" style={{ width: '52px' }}>Photo</th>
                  <th className="col-sku" style={{ width: '120px' }}>SKU</th>
                  <th className="col-title" style={{ width: '22%' }}>Product Name</th>
                  <th className="col-source" style={{ width: '18%' }}>Original Category</th>
                  <th className="col-prediction" style={{ width: '22%' }}>Suggested Category</th>
                  <th className="col-confidence" style={{ width: '110px' }}>Match Score</th>
                  <th className="col-status" style={{ width: '115px' }}>Status</th>
                  <th className="col-actions" style={{ width: '145px', textAlign: 'right' }}>
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {results.map((item, idx) => (
                  <ResultRow
                    key={item.id}
                    item={item}
                    isSelected={selectedIds.has(item.id)}
                    onToggleSelect={() => handleToggleSelectRow(item.id)}
                    isExpanded={expandedRowId === item.id}
                    onToggleExpand={() => onToggleExpand(item.id)}
                    onApprove={onApprove}
                    onOverrideCategory={onOverrideCategory}
                    onOpenLightbox={handleOpenLightbox}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Pagination Toolbar */}
      <div className="pagination-bar card-panel" style={{ marginTop: '16px' }}>
        <div className="pagination-info">
          <span>
            Showing page <strong className="font-mono">{currentPage}</strong> of{' '}
            <strong className="font-mono">{totalPages}</strong>
          </span>
          {onPageSizeChange && (
            <div className="page-size-selector">
              <span className="page-size-label">Per page:</span>
              <select
                className="page-size-select"
                value={pageSize}
                onChange={(e) => onPageSizeChange(parseInt(e.target.value, 10))}
              >
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
            </div>
          )}
        </div>

        <div className="pagination-controls">
          <button
            type="button"
            className="btn btn-sm btn-secondary"
            disabled={currentPage <= 1 || loading}
            onClick={() => onPageChange(currentPage - 1)}
          >
            <ChevronLeft size={14} />
            <span>Previous</span>
          </button>
          <span className="pagination-page-indicator font-mono">{currentPage}</span>
          <button
            type="button"
            className="btn btn-sm btn-secondary"
            disabled={currentPage >= totalPages || loading}
            onClick={() => onPageChange(currentPage + 1)}
          >
            <span>Next</span>
            <ChevronRight size={14} />
          </button>
        </div>
      </div>

      {/* Image Lightbox Modal */}
      <ImageLightbox
        isOpen={lightbox.isOpen}
        onClose={handleCloseLightbox}
        images={lightbox.images}
        currentIndex={lightbox.currentIndex}
        onIndexChange={(idx) => setLightbox((prev) => ({ ...prev, currentIndex: idx }))}
        productTitle={lightbox.productTitle}
        productSku={lightbox.productSku}
        categoryName={lightbox.categoryName}
      />
    </div>
  );
}
