import api from './api';

const productService = {
  async getProducts(params = {}) {
    const response = await api.get('/products', { params });
    return response.data;
  },

  async getProduct(id) {
    const response = await api.get(`/products/${id}`);
    return response.data;
  },

  async createProduct(productData) {
    const response = await api.post('/products', productData);
    return response.data;
  },

  async updateProduct(id, productData) {
    const response = await api.put(`/products/${id}`, productData);
    return response.data;
  },

  async deleteProduct(id) {
    const response = await api.delete(`/products/${id}`);
    return response.data;
  },

  async getProductsByCategory(category) {
    const response = await api.get(`/products/category/${category}`);
    return response.data;
  },

  async getUserProducts(userId) {
    const response = await api.get(`/products/user/${userId}`);
    return response.data;
  },
};

export default productService;
