import { request } from './api';

export async function uploadCatalog(file, sheet = 0, batchSize = 1000) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('sheet', sheet);
  formData.append('batch_size', batchSize);

  return request('/imports/upload/', {
    method: 'POST',
    body: formData,
  });
}

export async function getImportHistory() {
  return request('/imports/');
}
