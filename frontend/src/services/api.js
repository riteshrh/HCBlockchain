import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Auth API
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
};

// Records API
export const recordsAPI = {
  upload: (data) => api.post('/records/upload', data),
  getMyRecords: () => api.get('/records/my-records'),
  getRecord: (id) => api.get(`/records/${id}`),
  getRecordContent: (id) => api.get(`/records/${id}/content`),
};

// Consent API
export const consentAPI = {
  grant: (data) => api.post('/consent/grant', data),
  revoke: (data) => api.post('/consent/revoke', data),
  getMyConsents: () => api.get('/consent/my-consents'),
  checkConsent: (providerId, recordId) => api.get(`/consent/check/${providerId}/${recordId}`),
};

// Blockchain API
export const blockchainAPI = {
  getInfo: () => api.get('/blockchain/info'),
  getBlocks: (limit) => api.get('/blockchain/blocks', { params: { limit } }),
  getBlock: (index) => api.get(`/blockchain/blocks/${index}`),
  getTransactions: (type, limit) => api.get('/blockchain/transactions', { params: { transaction_type: type, limit } }),
  getTransaction: (txId) => api.get(`/blockchain/transactions/${txId}`),
  getTransactionsByType: (type) => api.get(`/blockchain/transactions/type/${type}`),
  validate: () => api.get('/blockchain/validate'),
};

// Admin API
export const adminAPI = {
  getProviders: () => api.get('/admin/providers'),
  approveProvider: (providerId) => api.post(`/admin/providers/${providerId}/approve`),
  rejectProvider: (providerId) => api.post(`/admin/providers/${providerId}/reject`),
};

export default api;

