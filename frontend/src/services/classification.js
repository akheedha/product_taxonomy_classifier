import { request } from './api';

export async function getJobs() {
  return request('/jobs/');
}

export async function getJob(jobId) {
  return request(`/jobs/${jobId}/`);
}

export async function createJob(limit = 0, sync = false) {
  return request('/jobs/', {
    method: 'POST',
    body: JSON.stringify({ limit, sync }),
  });
}

export async function resumeJob(jobId, sync = false) {
  return request(`/jobs/${jobId}/resume/`, {
    method: 'POST',
    body: JSON.stringify({ sync }),
  });
}

export async function getResults(params = {}) {
  const query = new URLSearchParams(params).toString();
  return request(`/results/${query ? `?${query}` : ''}`);
}

export async function getResultSummary(jobId = null) {
  const query = jobId ? `?job=${jobId}` : '';
  return request(`/results/summary/${query}`);
}

export async function getResultDetail(resultId) {
  return request(`/results/${resultId}/`);
}

export async function updateResultReview(resultId, data) {
  return request(`/results/${resultId}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}
