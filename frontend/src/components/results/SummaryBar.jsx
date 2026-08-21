import React from 'react';
import { Package, CheckCircle2, AlertCircle, XCircle, Sparkles, BarChart3 } from 'lucide-react';

export default function SummaryBar({ summary, loading, onFilterNeedsReview, onFilterAll }) {
  if (loading && !summary) {
    return (
      <div className="skeleton-container">
        {[1, 2, 3, 4].map((n) => (
          <div key={n} className="skeleton"></div>
        ))}
      </div>
    );
  }

  const total = summary?.total_results || 0;
  const approved = summary?.approved_count || 0;
  const needsReview = summary?.needs_review_count || 0;
  const failed = summary?.failed_count || 0;
  const unclassified = Math.max(0, total - (approved + needsReview + failed));

  const approvedPercent = total > 0 ? ((approved / total) * 100).toFixed(1) : '0.0';
  const reviewPercent = total > 0 ? ((needsReview / total) * 100).toFixed(1) : '0.0';
  const errorPercent = total > 0 ? ((failed / total) * 100).toFixed(1) : '0.0';
  const unclassifiedPercent = total > 0 ? ((unclassified / total) * 100).toFixed(1) : '0.0';

  return (
    <div>
      {/* 4 KPI Metric Cards */}
      <div className="summary-grid">
        <div
          className="metric-card card-total clickable"
          onClick={onFilterAll}
          title="Click to view all products"
          role="button"
          tabIndex={0}
        >
          <div className="metric-header">
            <div className="metric-label-group">
              <div className="metric-icon-box icon-total">
                <Package size={17} strokeWidth={2.2} />
              </div>
              <span className="metric-label">Total Catalog</span>
            </div>
            <span className="metric-badge">All</span>
          </div>
          <div className="metric-value font-mono">{total.toLocaleString()}</div>
          <div className="metric-subtext">All products in catalog</div>
        </div>

        <div className="metric-card card-approved">
          <div className="metric-header">
            <div className="metric-label-group">
              <div className="metric-icon-box icon-approved">
                <CheckCircle2 size={17} strokeWidth={2.2} />
              </div>
              <span className="metric-label">Auto-Matched</span>
            </div>
            <span className="metric-badge badge-success font-mono">{approvedPercent}%</span>
          </div>
          <div className="metric-value font-mono">{approved.toLocaleString()}</div>
          <div className="metric-subtext">High match score (≥70%) or approved</div>
        </div>

        <div
          className="metric-card card-review clickable"
          onClick={onFilterNeedsReview}
          title="Click to view products needing review"
          role="button"
          tabIndex={0}
        >
          <div className="metric-header">
            <div className="metric-label-group">
              <div className="metric-icon-box icon-review">
                <AlertCircle size={17} strokeWidth={2.2} />
              </div>
              <span className="metric-label">Needs Review</span>
            </div>
            <span className="metric-badge badge-warning font-mono">{reviewPercent}%</span>
          </div>
          <div className="metric-value font-mono">{needsReview.toLocaleString()}</div>
          <div className="metric-subtext">Low match score or uncertain</div>
        </div>

        <div className="metric-card card-errors">
          <div className="metric-header">
            <div className="metric-label-group">
              <div className="metric-icon-box icon-errors">
                <XCircle size={17} strokeWidth={2.2} />
              </div>
              <span className="metric-label">Issues</span>
            </div>
            <span className="metric-badge badge-danger font-mono">{errorPercent}%</span>
          </div>
          <div className="metric-value font-mono">{failed.toLocaleString()}</div>
          <div className="metric-subtext">Unassigned or failed errors</div>
        </div>
      </div>

      {/* Catalog Categorization Coverage & Breakdown */}
      {total > 0 && (
        <div className="card-panel coverage-meter-card">
          <div className="coverage-header">
            <div className="coverage-title">
              <BarChart3 size={15} className="text-primary" />
              <span>Catalog Categorization Coverage</span>
            </div>
            <span className="font-mono text-sm font-medium">
              {(( (approved + needsReview) / total) * 100).toFixed(1)}% Categorized
            </span>
          </div>

          <div className="multi-segment-bar" title="Catalog Coverage Distribution">
            <div
              className="segment-fill segment-approved"
              style={{ width: `${approvedPercent}%` }}
              title={`Approved / High Match: ${approved.toLocaleString()} (${approvedPercent}%)`}
            ></div>
            <div
              className="segment-fill segment-review"
              style={{ width: `${reviewPercent}%` }}
              title={`Needs Review: ${needsReview.toLocaleString()} (${reviewPercent}%)`}
            ></div>
            <div
              className="segment-fill segment-unclassified"
              style={{ width: `${unclassifiedPercent}%` }}
              title={`Unclassified: ${unclassified.toLocaleString()} (${unclassifiedPercent}%)`}
            ></div>
          </div>

          <div className="coverage-legend">
            <div className="legend-item">
              <span className="legend-dot" style={{ background: 'var(--success)' }}></span>
              <span>Approved / Confident ({approved.toLocaleString()})</span>
            </div>
            <div className="legend-item">
              <span className="legend-dot" style={{ background: 'var(--warning)' }}></span>
              <span>Needs Review ({needsReview.toLocaleString()})</span>
            </div>
            {unclassified > 0 && (
              <div className="legend-item">
                <span className="legend-dot" style={{ background: 'var(--border-strong)' }}></span>
                <span>Unclassified ({unclassified.toLocaleString()})</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
