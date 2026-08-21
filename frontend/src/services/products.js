import { request } from './api';

export async function getProducts(params = {}) {
  const query = new URLSearchParams(params).toString();
  return request(`/products/${query ? `?${query}` : ''}`);
}

export async function getProductById(id) {
  return request(`/products/${id}/`);
}
