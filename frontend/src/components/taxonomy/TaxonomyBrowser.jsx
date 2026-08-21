import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Search,
  FolderTree,
  Layers,
  Tag,
  ChevronRight,
  Loader2,
  X,
  ExternalLink,
  Copy,
  CheckCheck,
  Filter
} from 'lucide-react';

export default function TaxonomyBrowser({
  categories = [],
  selectedCategory = null,
  attributes = [],
  onSelectCategory,
  onSearch,
  searchQuery = '',
  loading = false,
}) {
  const [query, setQuery] = useState(searchQuery);
  const [levelFilter, setLevelFilter] = useState(null);
  const [attrSearch, setAttrSearch] = useState('');
  const [copiedGid, setCopiedGid] = useState(false);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    onSearch(query, levelFilter);
  };

  const handleClearSearch = () => {
    setQuery('');
    onSearch('', levelFilter);
  };

  const handleLevelFilterClick = (lvl) => {
    const nextLvl = levelFilter === lvl ? null : lvl;
    setLevelFilter(nextLvl);
    onSearch(query, nextLvl);
  };

  const handleCopyGid = (gid) => {
    navigator.clipboard.writeText(gid);
    setCopiedGid(true);
    setTimeout(() => setCopiedGid(false), 2000);
  };

  const filteredAttributes = attributes.filter((attr) => {
    if (!attrSearch) return true;
    const q = attrSearch.toLowerCase();
    return (
      attr.name?.toLowerCase().includes(q) ||
      attr.values?.some((v) => v.value?.toLowerCase().includes(q))
    );
  });

  return (
    <div className="taxonomy-explorer-grid">
      {/* Left Column: Search & Category Tree */}
      <div className="taxonomy-col-left card-panel">
        <form onSubmit={handleSearchSubmit} className="taxonomy-search-form">
          <div className="search-wrapper">
            <Search size={14} className="search-icon" />
            <input
              type="text"
              className="search-input"
              placeholder="Search categories (e.g. Sofa, Shirt, Lamp)..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            {query && (
              <button
                type="button"
                className="search-clear-btn"
                onClick={handleClearSearch}
                title="Clear search"
              >
                <X size={13} />
              </button>
            )}
            <button type="submit" className="btn btn-primary btn-sm search-submit-btn">
              Search
            </button>
          </div>
        </form>

        {/* Level Filters */}
        <div style={{ display: 'flex', gap: '6px', marginBottom: '14px', flexWrap: 'wrap' }}>
          <button
            type="button"
            className={`preset-pill ${levelFilter === null ? 'active' : ''}`}
            onClick={() => handleLevelFilterClick(null)}
          >
            All Levels
          </button>
          <button
            type="button"
            className={`preset-pill ${levelFilter === 1 ? 'active' : ''}`}
            onClick={() => handleLevelFilterClick(1)}
          >
            L1 (Root)
          </button>
          <button
            type="button"
            className={`preset-pill ${levelFilter === 2 ? 'active' : ''}`}
            onClick={() => handleLevelFilterClick(2)}
          >
            L2 (Dept)
          </button>
          <button
            type="button"
            className={`preset-pill ${levelFilter === 3 ? 'active' : ''}`}
            onClick={() => handleLevelFilterClick(3)}
          >
            L3 (Type)
          </button>
        </div>

        {/* Category List */}
        <div className="category-list-scroll">
          {loading ? (
            <div className="loading-spinner-container">
              <Loader2 size={24} className="spinner-icon" />
              <p>Searching official Shopify categories...</p>
            </div>
          ) : categories.length === 0 ? (
            <div className="empty-state-simple">
              <p className="text-muted">No categories found matching "{query}".</p>
            </div>
          ) : (
            <ul className="category-tree-list">
              {categories.map((cat) => (
                <li
                  key={cat.id}
                  className={`category-item ${selectedCategory?.id === cat.id ? 'selected' : ''}`}
                  onClick={() => onSelectCategory(cat)}
                  role="button"
                  tabIndex={0}
                >
                  <div className="cat-item-main">
                    <span className="cat-name">{cat.name}</span>
                    <span className="cat-level-badge font-mono">L{cat.level}</span>
                  </div>
                  <div className="cat-full-path">{cat.full_name}</div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Right Column: Selected Category Details & Attributes */}
      <div className="taxonomy-col-right card-panel">
        {selectedCategory ? (
          <div className="selected-category-details">
            <div className="details-header">
              <div className="details-header-top">
                <span className="cat-gid font-mono">
                  {selectedCategory.id}
                  <button
                    type="button"
                    className="btn-copy-sku"
                    onClick={() => handleCopyGid(selectedCategory.id)}
                    title="Copy Category GID"
                    style={{ marginLeft: '4px' }}
                  >
                    {copiedGid ? <CheckCheck size={11} className="text-success" /> : <Copy size={11} />}
                  </button>
                </span>
                <span className="cat-level-pill font-mono">Level {selectedCategory.level}</span>

                <Link
                  to={`/review?search=${encodeURIComponent(selectedCategory.name)}`}
                  className="btn btn-sm btn-secondary"
                  style={{ marginLeft: 'auto' }}
                  title="Find products categorized under this category in Review Queue"
                >
                  <ExternalLink size={12} />
                  <span>View Products</span>
                </Link>
              </div>

              <h3>{selectedCategory.name}</h3>
              <div className="breadcrumb-trail">
                <FolderTree size={14} className="text-primary" />
                <span>{selectedCategory.full_name}</span>
              </div>
            </div>

            {/* Attributes Section */}
            <div className="details-attributes-section">
              <div className="attributes-section-title">
                <Layers size={16} className="text-primary" />
                <h4>Supported Shopify Attributes</h4>
                <span className="attributes-count-badge font-mono">{attributes?.length || 0}</span>

                {attributes.length > 3 && (
                  <div style={{ marginLeft: 'auto', width: '200px' }}>
                    <input
                      type="text"
                      className="search-input"
                      style={{ padding: '4px 8px', fontSize: '12px' }}
                      placeholder="Filter attributes..."
                      value={attrSearch}
                      onChange={(e) => setAttrSearch(e.target.value)}
                    />
                  </div>
                )}
              </div>

              {filteredAttributes.length > 0 ? (
                <div className="attributes-grid">
                  {filteredAttributes.map((attr) => (
                    <div key={attr.id} className="attribute-card">
                      <div className="attr-header">
                        <span className="attr-title">{attr.name}</span>
                        <span className="attr-count font-mono">{attr.values?.length || 0} options</span>
                      </div>
                      {attr.values && attr.values.length > 0 && (
                        <div className="attr-values-preview">
                          {attr.values.slice(0, 10).map((v) => (
                            <span key={v.id} className="val-tag">
                              {v.value}
                            </span>
                          ))}
                          {attr.values.length > 10 && (
                            <span className="val-tag-more font-mono">
                              +{attr.values.length - 10} more
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state-simple">
                  <p className="text-muted">
                    {attributes.length === 0
                      ? 'No specific attributes defined for this category.'
                      : `No attributes matching "${attrSearch}".`}
                  </p>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="empty-state">
            <div className="empty-icon-box">
              <FolderTree size={32} strokeWidth={1.5} />
            </div>
            <h3>Select a Category</h3>
            <p>Click any category on the left to inspect its path, taxonomy level, and supported Shopify attributes.</p>
          </div>
        )}
      </div>
    </div>
  );
}
