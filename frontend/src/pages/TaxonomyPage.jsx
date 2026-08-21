import React, { useState, useEffect } from 'react';
import TaxonomyBrowser from '../components/taxonomy/TaxonomyBrowser';
import { searchCategories, getCategoryDetail, getAttributesForCategory } from '../services/taxonomy';

export default function TaxonomyPage() {
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [attributes, setAttributes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchCategories = async (q = '', level = null) => {
    setLoading(true);
    try {
      const data = await searchCategories(q, level);
      const results = Array.isArray(data) ? data : data.results || [];
      setCategories(results);
      if (results.length > 0 && !selectedCategory) {
        handleSelectCategory(results[0]);
      }
    } catch (err) {
      console.error('Failed to search taxonomy categories:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectCategory = async (cat) => {
    setSelectedCategory(cat);
    try {
      const attrData = await getAttributesForCategory(cat.id);
      const attrList = Array.isArray(attrData) ? attrData : attrData.results || [];
      setAttributes(attrList);
    } catch (err) {
      console.error('Failed to load attributes for category:', err);
      setAttributes([]);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  const handleSearch = (q, level = null) => {
    setSearchQuery(q);
    fetchCategories(q, level);
  };

  return (
    <div className="page-taxonomy">
      <div className="page-header">
        <div>
          <h2>Shopify Taxonomy Explorer</h2>
          <p className="text-muted">
            Explore 5,000+ official Shopify categories, inspect hierarchy levels, and browse supported attributes like Color, Material, and Style.
          </p>
        </div>
      </div>

      <TaxonomyBrowser
        categories={categories}
        selectedCategory={selectedCategory}
        attributes={attributes}
        onSelectCategory={handleSelectCategory}
        onSearch={handleSearch}
        searchQuery={searchQuery}
        loading={loading}
      />
    </div>
  );
}
