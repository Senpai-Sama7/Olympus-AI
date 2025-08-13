import api from './api';

const REFRESH_TOKEN_KEY = 'refreshToken';

const authService = {
  async register(userData) {
    const response = await api.post('/auth/register', userData);
    if (response.data.data.refreshToken) {
      localStorage.setItem(REFRESH_TOKEN_KEY, response.data.data.refreshToken);
    }
    return response.data;
  },

  async login(credentials) {
    const response = await api.post('/auth/login', credentials);
    if (response.data.data.refreshToken) {
      localStorage.setItem(REFRESH_TOKEN_KEY, response.data.data.refreshToken);
    }
    return response.data;
  },

  async refreshToken() {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await api.post('/auth/refresh', { refreshToken });
    if (response.data.data.refreshToken) {
      localStorage.setItem(REFRESH_TOKEN_KEY, response.data.data.refreshToken);
    }
    return response.data;
  },

  async getMe() {
    const response = await api.get('/auth/me');
    return response.data;
  },

  async updatePassword(passwordData) {
    const response = await api.put('/auth/updatepassword', passwordData);
    return response.data;
  },

  async logout() {
    try {
      const response = await api.post('/auth/logout');
      return response.data;
    } finally {
      // Always clear tokens on logout
      localStorage.removeItem('token');
      localStorage.removeItem(REFRESH_TOKEN_KEY);
    }
  },

  clearTokens() {
    localStorage.removeItem('token');
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },

  getRefreshToken() {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  }
};

export default authService;
