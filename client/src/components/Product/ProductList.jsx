import { PencilIcon, PlusIcon, TrashIcon } from '@heroicons/react/24/outline';
import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { useSelector } from 'react-redux';
import productService from '../../services/product.service';
import { selectUser } from '../../store/authSlice';
import ProductForm from './ProductForm';

const ProductList = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [filters, setFilters] = useState({
    category: '',
    search: '',
    page: 1,
    limit: 10,
  });
  const [pagination, setPagination] = useState({});
  const user = useSelector(selectUser);

  const categories = ['electronics', 'clothing', 'food', 'books', 'toys', 'other'];

  useEffect(() => {
    fetchProducts();
  }, [filters]);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const response = await productService.getProducts(filters);
      setProducts(response.data.products);
      setPagination(response.data.pagination);
    } catch (error) {
      toast.error('Failed to fetch products');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this product?')) return;

    try {
      await productService.deleteProduct(id);
      toast.success('Product deleted successfully');
      fetchProducts();
    } catch (error) {
      toast.error(error.response?.data?.message || 'Failed to delete product');
    }
  };

  const handleEdit = (product) => {
    setSelectedProduct(product);
    setShowForm(true);
  };

  const handleCreate = () => {
    setSelectedProduct(null);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setSelectedProduct(null);
    fetchProducts();
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setFilters({ ...filters, page: 1 });
  };

  if (loading && products.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex flex-col sm:flex-row gap-4 flex-1">
          <select
            value={filters.category}
            onChange={(e) => setFilters({ ...filters, category: e.target.value, page: 1 })}
            className="input"
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
              </option>
            ))}
          </select>

          <form onSubmit={handleSearch} className="flex gap-2 flex-1">
            <input
              type="text"
              placeholder="Search products..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              className="input flex-1"
            />
            <button type="submit" className="btn-primary">
              Search
            </button>
          </form>
        </div>

        {user && (
          <button onClick={handleCreate} className="btn-primary flex items-center gap-2">
            <PlusIcon className="h-5 w-5" />
            Add Product
          </button>
        )}
      </div>

      {/* Products Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {products.map((product) => (
          <div key={product._id} className="card">
            <div className="card-body">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold text-gray-900">{product.name}</h3>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${product.inStock
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                  }`}>
                  {product.inStock ? 'In Stock' : 'Out of Stock'}
                </span>
              </div>

              <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                {product.description || 'No description available'}
              </p>

              <div className="flex justify-between items-center mb-4">
                <span className="text-2xl font-bold text-primary-600">
                  ${product.price.toFixed(2)}
                </span>
                <span className="text-sm text-gray-500">
                  {product.category}
                </span>
              </div>

              <div className="text-xs text-gray-500 mb-4">
                By {product.owner?.name || 'Unknown'}
              </div>

              {user && (user._id === product.owner?._id || user.role === 'admin') && (
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEdit(product)}
                    className="btn-secondary flex-1 flex items-center justify-center gap-1"
                  >
                    <PencilIcon className="h-4 w-4" />
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(product._id)}
                    className="btn-danger flex-1 flex items-center justify-center gap-1"
                  >
                    <TrashIcon className="h-4 w-4" />
                    Delete
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {(pagination.prev || pagination.next) && (
        <div className="flex justify-center gap-2">
          <button
            onClick={() => setFilters({ ...filters, page: filters.page - 1 })}
            disabled={!pagination.prev}
            className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <span className="flex items-center px-4">
            Page {filters.page}
          </span>
          <button
            onClick={() => setFilters({ ...filters, page: filters.page + 1 })}
            disabled={!pagination.next}
            className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      )}

      {/* Product Form Modal */}
      {showForm && (
        <ProductForm
          product={selectedProduct}
          onClose={handleFormClose}
        />
      )}
    </div>
  );
};

export default ProductList;
