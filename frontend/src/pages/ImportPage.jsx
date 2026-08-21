import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, CheckCircle2, HelpCircle, FileCheck, Info, Sparkles } from 'lucide-react';
import ImportUploader from '../components/imports/ImportUploader';
import { uploadCatalog } from '../services/imports';
import { createJob } from '../services/classification';

export default function ImportPage({ onRefreshJobs }) {
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const navigate = useNavigate();

  const handleUpload = async (file, sheet, batchSize, autoClassify) => {
    setUploading(true);
    setUploadStatus(null);

    try {
      const data = await uploadCatalog(file, sheet, batchSize);
      const importedCount = data.result?.imported_count || 0;

      if (autoClassify) {
        setUploadStatus({
          type: 'success',
          message: `Successfully imported ${importedCount.toLocaleString()} products. Launching categorization batch...`,
        });

        // Trigger batch classification job
        const job = await createJob(0, false);
        if (onRefreshJobs) onRefreshJobs();

        setTimeout(() => {
          navigate(`/review?job=${job.id}`);
        }, 1200);
      } else {
        setUploadStatus({
          type: 'success',
          message: `Successfully ingested ${importedCount.toLocaleString()} catalog products into the database.`,
        });
        if (onRefreshJobs) onRefreshJobs();
      }
    } catch (err) {
      setUploadStatus({
        type: 'danger',
        message: err.message || 'Upload failed. Check spreadsheet format and required columns.',
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="page-import">
      <div className="page-header">
        <div>
          <h2>Import Product Catalog</h2>
          <p className="text-muted">
            Upload product spreadsheets (.xlsx, .xls, or .csv). Images, descriptions, and categories are parsed and mapped automatically.
          </p>
        </div>
      </div>

      <div className="import-layout-grid">
        <ImportUploader
          onUpload={handleUpload}
          uploading={uploading}
          uploadStatus={uploadStatus}
        />

        {/* Guidelines / Documentation Card */}
        <div className="card-panel import-guidelines">
          <div className="guidelines-header">
            <FileCheck size={18} className="text-primary" />
            <h3>Supported Columns &amp; Header Mapping</h3>
          </div>
          <p className="text-muted text-sm" style={{ marginBottom: '14px' }}>
            The parser automatically detects and normalizes the following standard headers:
          </p>
          <ul className="guideline-list">
            <li>
              <strong>SKU / Product Number:</strong> Unique identifier (e.g. <code>SKU</code>, <code>Item #</code>, <code>Product Number</code>).
            </li>
            <li>
              <strong>Product Title / Name:</strong> Product title (e.g. <code>Title</code>, <code>Product Name</code>, <code>Item</code>).
            </li>
            <li>
              <strong>Original Category &amp; Sub-Category:</strong> Source taxonomies.
            </li>
            <li>
              <strong>Brand / Vendor:</strong> Manufacturer or brand name.
            </li>
            <li>
              <strong>Description &amp; Bullet Points:</strong> Feature details and body text.
            </li>
            <li>
              <strong>Materials, Colors, Dimensions:</strong> Physical attributes used for AI matching.
            </li>
            <li>
              <strong>Primary Image / Image 1...20:</strong> Public photo URLs for visual review.
            </li>
          </ul>

          <div className="callout-box">
            <Info size={16} className="callout-icon" />
            <div>
              <strong>Smart Auto-Mapping:</strong> You do not need to rename spreadsheet headers. Column aliases are matched intelligently without manual configuration.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
