import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Play,
  CheckSquare,
  UploadCloud,
  FolderTree,
  ArrowRight,
  Activity,
  Clock,
  Sparkles,
  Zap,
  Layers
} from 'lucide-react';
import SummaryBar from '../components/results/SummaryBar';

export default function DashboardPage({
  summary,
  jobs = [],
  activeJob = null,
  loading = false,
  onLaunchJob,
}) {
  const navigate = useNavigate();

  const handleFilterNeedsReview = () => {
    navigate('/review?needs_review=true');
  };

  const handleFilterAll = () => {
    navigate('/review');
  };

  return (
    <div className="page-dashboard">
      <div className="page-header">
        <div>
          <h2>Product Classification Hub</h2>
          <p className="text-muted">
            Real-time catalog taxonomy metrics, active AI categorization batches, and quick curation tools.
          </p>
        </div>
        <div className="page-header-actions">
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => onLaunchJob(0)}
            disabled={activeJob !== null}
          >
            {activeJob ? (
              <>
                <Activity size={15} className="spin-slow" />
                <span>Categorizing Catalog...</span>
              </>
            ) : (
              <>
                <Play size={15} />
                <span>Categorize Catalog</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* KPI Metrics & Coverage Meter */}
      <SummaryBar
        summary={summary}
        loading={loading}
        onFilterNeedsReview={handleFilterNeedsReview}
        onFilterAll={handleFilterAll}
      />

      {/* Active Job Live Progress Banner */}
      {activeJob && (
        <div className="active-job-banner">
          <div className="banner-header">
            <div className="banner-title">
              <span className="pulse-indicator"></span>
              <strong>Categorization in Progress (Batch #{activeJob.id})</strong>
              <span className="status-pill status-running">Running</span>
            </div>
            <div className="banner-stats">
              {activeJob.processed_count?.toLocaleString()} / {activeJob.total_products?.toLocaleString()} products (
              {activeJob.progress_percentage || 0}%)
            </div>
          </div>
          <div className="progress-bar-container">
            <div
              className="progress-bar-fill"
              style={{ width: `${Math.min(100, Math.max(2, activeJob.progress_percentage || 0))}%` }}
            ></div>
          </div>
          <div className="banner-footer">
            <span>Errors: {activeJob.failed_count || 0}</span>
            <Link to={`/review?job=${activeJob.id}`} className="link-action">
              <span>View Active Batch in Review Queue</span>
              <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      )}

      {/* Quick Action Navigation Grid */}
      <div className="quick-actions-grid">
        <Link to="/review?needs_review=true" className="action-card">
          <div className="action-card-top">
            <div className="action-icon-box">
              <CheckSquare size={20} strokeWidth={2.2} />
            </div>
            <div className="action-card-header">
              <h3>Review Queue</h3>
              <p>Review {summary?.needs_review_count?.toLocaleString() || 0} products that need curation or category changes.</p>
            </div>
          </div>
          <div className="action-link">
            <span>Open Review Queue</span>
            <ArrowRight size={14} />
          </div>
        </Link>

        <Link to="/import" className="action-card">
          <div className="action-card-top">
            <div className="action-icon-box">
              <UploadCloud size={20} strokeWidth={2.2} />
            </div>
            <div className="action-card-header">
              <h3>Import Products</h3>
              <p>Upload product spreadsheets (.xlsx, .csv). Columns and images are organized automatically.</p>
            </div>
          </div>
          <div className="action-link">
            <span>Upload Spreadsheet</span>
            <ArrowRight size={14} />
          </div>
        </Link>

        <Link to="/taxonomy" className="action-card">
          <div className="action-card-top">
            <div className="action-icon-box">
              <FolderTree size={20} strokeWidth={2.2} />
            </div>
            <div className="action-card-header">
              <h3>Category Directory</h3>
              <p>Explore all 5,000+ official Shopify categories and browse supported attributes.</p>
            </div>
          </div>
          <div className="action-link">
            <span>Browse Categories</span>
            <ArrowRight size={14} />
          </div>
        </Link>
      </div>

      {/* Historical Batch Runs Table */}
      <div className="historical-jobs-section card-panel">
        <div className="section-header">
          <div className="section-title-group">
            <Clock size={16} className="text-primary" />
            <h3>Recent Imports &amp; Batches</h3>
          </div>
        </div>

        {jobs.length === 0 ? (
          <div className="empty-state-simple">
            <p className="text-muted">No product batches yet. Click 'Categorize Catalog' above to start.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="jobs-table">
              <thead>
                <tr>
                  <th>Batch ID</th>
                  <th>Status</th>
                  <th>Progress</th>
                  <th>Processed / Total</th>
                  <th>Errors</th>
                  <th>Started</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => (
                  <tr key={job.id}>
                    <td className="font-mono font-medium">#{job.id}</td>
                    <td>
                      <span className={`status-pill status-${job.status}`}>
                        <span className="status-dot"></span>
                        {job.status.toUpperCase()}
                      </span>
                    </td>
                    <td>
                      <div className="table-progress-wrapper">
                        <div className="table-progress-bar">
                          <div
                            className="table-progress-fill"
                            style={{ width: `${job.progress_percentage || 0}%` }}
                          ></div>
                        </div>
                        <span className="table-progress-text font-mono">{job.progress_percentage || 0}%</span>
                      </div>
                    </td>
                    <td className="font-mono text-sm">
                      {job.processed_count?.toLocaleString()} / {job.total_products?.toLocaleString()}
                    </td>
                    <td>
                      {job.failed_count > 0 ? (
                        <span className="text-danger font-medium">{job.failed_count}</span>
                      ) : (
                        <span className="text-muted">0</span>
                      )}
                    </td>
                    <td className="text-muted text-sm">
                      {job.created_at ? new Date(job.created_at).toLocaleString() : 'N/A'}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <Link to={`/review?job=${job.id}`} className="btn btn-sm btn-secondary">
                        <span>View Products</span>
                        <ArrowRight size={12} />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
