import React, { useState } from 'react';
import {
  UploadCloud,
  FileSpreadsheet,
  Play,
  CheckCircle2,
  AlertCircle,
  Loader2
} from 'lucide-react';

export default function ImportUploader({ onUpload, uploading, uploadStatus }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [sheet, setSheet] = useState('0');
  const [batchSize, setBatchSize] = useState('1000');
  const [dragActive, setDragActive] = useState(false);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = (autoClassify = true) => {
    if (!selectedFile) return;
    onUpload(selectedFile, sheet, batchSize, autoClassify);
  };

  return (
    <div className="import-card card-panel">
      <div
        className={`drop-zone ${dragActive ? 'drag-active' : ''} ${
          selectedFile ? 'file-selected' : ''
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <div className="drop-icon-box">
          {selectedFile ? (
            <FileSpreadsheet size={36} strokeWidth={1.8} />
          ) : (
            <UploadCloud size={36} strokeWidth={1.8} />
          )}
        </div>

        <div className="drop-text-content">
          {selectedFile ? (
            <div>
              <p className="selected-filename font-medium">{selectedFile.name}</p>
              <p className="selected-filesize font-mono text-muted">
                {(selectedFile.size / 1024).toFixed(1)} KB (Ready to upload)
              </p>
            </div>
          ) : (
            <div>
              <p className="drop-text-primary">Drag and drop spreadsheet here, or click to browse</p>
              <p className="drop-text-secondary">
                Supports Excel spreadsheets (.xlsx, .xls) and CSV files
              </p>
            </div>
          )}
        </div>

        <input
          type="file"
          id="catalog-file-input"
          accept=".xlsx,.xls,.xlsm,.csv"
          onChange={handleFileChange}
          className="file-input-hidden"
        />
        <label htmlFor="catalog-file-input" className="btn btn-secondary btn-browse">
          {selectedFile ? 'Change File' : 'Browse File'}
        </label>
      </div>

      {/* Options Row */}
      <div className="import-options-row">
        <div className="form-group">
          <label htmlFor="import-sheet-select" className="filter-label">
            Excel Sheet (optional):
          </label>
          <input
            id="import-sheet-select"
            type="text"
            className="form-control"
            value={sheet}
            onChange={(e) => setSheet(e.target.value)}
            placeholder="0 (first sheet) or Sheet Name"
          />
        </div>

        <div className="form-group">
          <label htmlFor="import-batch-size" className="filter-label">
            Batch Size:
          </label>
          <input
            id="import-batch-size"
            type="number"
            className="form-control"
            value={batchSize}
            onChange={(e) => setBatchSize(e.target.value)}
            min="100"
            max="5000"
            step="100"
          />
        </div>
      </div>

      {/* Actions Row */}
      <div className="import-actions-row">
        <button
          type="button"
          className="btn btn-primary btn-upload"
          disabled={!selectedFile || uploading}
          onClick={() => handleSubmit(true)}
        >
          {uploading ? (
            <>
              <Loader2 size={15} className="spinner-icon" />
              <span>Importing &amp; Categorizing...</span>
            </>
          ) : (
            <>
              <Play size={15} />
              <span>Upload &amp; Categorize Now</span>
            </>
          )}
        </button>

        <button
          type="button"
          className="btn btn-secondary"
          disabled={!selectedFile || uploading}
          onClick={() => handleSubmit(false)}
        >
          <span>Upload Only (Categorize Later)</span>
        </button>
      </div>

      {/* Status Alert */}
      {uploadStatus && (
        <div className={`status-alert alert-${uploadStatus.type}`}>
          <div className="alert-icon">
            {uploadStatus.type === 'success' ? (
              <CheckCircle2 size={18} />
            ) : (
              <AlertCircle size={18} />
            )}
          </div>
          <div className="alert-message font-medium">{uploadStatus.message}</div>
        </div>
      )}
    </div>
  );
}
