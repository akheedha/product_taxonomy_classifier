/**
 * ============================================================================
 * SUMMARY BAR (TOP KPI METRIC CARDS)
 * ============================================================================
 * Purpose:
 *   Displays high-level executive KPI metrics across the active classification run:
 *     - Total Processed: Overall volume and progress percentage.
 *     - Approved %: Products confirmed by curator or auto-approved.
 *     - Needing Review %: Ambiguous or low-confidence items requiring human review.
 *     - Errors / Failed: Exceptions or missing product metadata.
 */

import React from 'react';

export default function SummaryBar({
  job,             // Active ClassificationJob object (or null)
  resultsSummary,  // Aggregate metrics: {total, processed, approved, needsReview, failed}
}) {
  // Extract counts from active job or aggregate results
  const total = job?.total_products || resultsSummary.total || 0;
  const processed = job?.processed_count || resultsSummary.processed || 0;
  const failed = job?.failed_count || resultsSummary.failed || 0;
  const review = resultsSummary.needsReview || 0;
  const approved = resultsSummary.approved || 0;

  // Calculate percentages
  const approvedPct = processed > 0 ? ((approved / processed) * 100).toFixed(1) : '0.0';
  const reviewPct = processed > 0 ? ((review / processed) * 100).toFixed(1) : '0.0';
  const failedPct = total > 0 ? ((failed / total) * 100).toFixed(1) : '0.0';

  return (
    <div className="summary-grid">
      {/* Total Processed Metric Card */}
      <div className="summary-card card-total">
        <div className="summary-label">Total Processed</div>
        <div className="summary-value" style={{ color: '#3b82f6' }}>
          {processed.toLocaleString()} <span style={{ fontSize: '18px', color: '#94a3b8' }}>/ {total.toLocaleString()}</span>
        </div>
        <div className="summary-subtext">
          {job ? `Job #${job.id} [${job.status.toUpperCase()}] • ${job.progress_percentage}% completed` : 'All time statistics'}
        </div>
      </div>

      {/* Approved / Confirmed Metric Card */}
      <div className="summary-card card-approved">
        <div className="summary-label">Approved</div>
        <div className="summary-value" style={{ color: '#10b981' }}>
          {approvedPct}%
        </div>
        <div className="summary-subtext">
          {approved.toLocaleString()} items confirmed / verified
        </div>
      </div>

      {/* Needing Review Metric Card */}
      <div className="summary-card card-review">
        <div className="summary-label">Needing Review</div>
        <div className="summary-value" style={{ color: '#f59e0b' }}>
          {reviewPct}%
        </div>
        <div className="summary-subtext">
          {review.toLocaleString()} items requiring curator inspection
        </div>
      </div>

      {/* Errors / Failed Metric Card */}
      <div className="summary-card card-failed">
        <div className="summary-label">Errors / Failed</div>
        <div className="summary-value" style={{ color: '#ef4444' }}>
          {failedPct}%
        </div>
        <div className="summary-subtext">
          {failed.toLocaleString()} items with execution exceptions
        </div>
      </div>
    </div>
  );
}
