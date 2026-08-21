import { request } from './api';

export async function searchCategories(query = '', level = null, parent = null) {
  const params = new URLSearchParams();
  if (query) params.append('q', query);
  if (level !== null && level !== undefined) params.append('level', level);
  if (parent) params.append('parent', parent);

  const queryString = params.toString();
  return request(`/taxonomy/categories/${queryString ? `?${queryString}` : ''}`);
}

export async function getCategoryDetail(categoryId) {
  return request(`/taxonomy/categories/${encodeURIComponent(categoryId)}/`);
}

export async function getAttributesForCategory(categoryId) {
  return request(`/taxonomy/attributes/?category=${encodeURIComponent(categoryId)}`);
}
