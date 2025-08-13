import { XMarkIcon } from '@heroicons/react/24/outline';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';
import productService from '../../services/product.service';

const ProductForm = ({ product, onClose }) => {
  const [loading, setLoading] = useState(false);
  const isEdit = !!product;

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm({
    defaultValues: product || {
      name: '',
      description: '',
      price: '',
      category: 'other',
      quantity: 0,
    },
  });

  useEffect(() => {
    if (product) {
      reset(product);
    }
  }, [product, reset]);

  const onSubmit = async (data) => {
    setLoading(true);
    try {
      if (isEdit) {
        await productService.updateProduct(product._id, data);
        toast.success('Product updated successfully');
      } else {
        await productService.createProduct(data);
        toast.success('Product created successfully');
      }
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.message || 'Operation failed');
    } finally {
      setLoading(false);
    }
  };

  const categories = ['electronics', 'clothing', 'food', 'books', 'toys', 'other'];

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-xl font-semibold">
            {isEdit ? 'Edit Product' : 'Create New Product'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
          <div>
            <label htmlFor="name" className="label">
              Product Name
            </label>
            <input
              {...register('name', {
                required: 'Product name is required',
                minLength: {
                  value: 2,
                  message: 'Name must be at least 2 characters',
                },
                maxLength: {
                  value: 100,
                  message: 'Name cannot exceed 100 characters',
                },
              })}
              type="text"
              className="input"
              placeholder="Enter product name"
            />
            {errors.name && (
              <p className="error-text">{errors.name.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="description" className="label">
              Description
            </label>
            <textarea
              {...register('description', {
                maxLength: {
                  value: 500,
                  message: 'Description cannot exceed 500 characters',
                },
              })}
              rows={3}
              className="input"
              placeholder="Enter product description"
            />
            {errors.description && (
              <p className="error-text">{errors.description.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="price" className="label">
              Price
            </label>
            <input
              {...register('price', {
                required: 'Price is required',
                min: {
                  value: 0,
                  message: 'Price cannot be negative',
                },
                valueAsNumber: true,
              })}
              type="number"
              step="0.01"
              className="input"
              placeholder="0.00"
            />
            {errors.price && (
              <p className="error-text">{errors.price.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="category" className="label">
              Category
            </label>
            <select
              {...register('category', {
                required: 'Category is required',
              })}
              className="input"
            >
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat.charAt(0).toUpperCase() + cat.slice(1)}
                </option>
              ))}
            </select>
            {errors.category && (
              <p className="error-text">{errors.category.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="quantity" className="label">
              Quantity
            </label>
            <input
              {...register('quantity', {
                min: {
                  value: 0,
                  message: 'Quantity cannot be negative',
                },
                valueAsNumber: true,
              })}
              type="number"
              className="input"
              placeholder="0"
            />
            {errors.quantity && (
              <p className="error-text">{errors.quantity.message}</p>
            )}
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary flex-1"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary flex-1"
            >
              {loading ? (
                <span className="loading-spinner" />
              ) : isEdit ? (
                'Update Product'
              ) : (
                'Create Product'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProductForm;
