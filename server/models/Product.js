import mongoose from 'mongoose';

const productSchema = new mongoose.Schema({
  name: {
    type: String,
    required: [true, 'Product name is required'],
    trim: true,
    minlength: [2, 'Product name must be at least 2 characters'],
    maxlength: [100, 'Product name cannot exceed 100 characters']
  },
  description: {
    type: String,
    trim: true,
    maxlength: [500, 'Description cannot exceed 500 characters']
  },
  price: {
    type: Number,
    required: [true, 'Price is required'],
    min: [0, 'Price cannot be negative'],
    validate: {
      validator: function (value) {
        return value >= 0 && Number.isFinite(value);
      },
      message: 'Price must be a valid positive number'
    }
  },
  category: {
    type: String,
    required: [true, 'Category is required'],
    trim: true,
    enum: {
      values: ['electronics', 'clothing', 'food', 'books', 'toys', 'other'],
      message: '{VALUE} is not a valid category'
    }
  },
  inStock: {
    type: Boolean,
    default: true
  },
  quantity: {
    type: Number,
    default: 0,
    min: [0, 'Quantity cannot be negative']
  },
  images: [{
    type: String,
    validate: {
      validator: function (v) {
        return /^https?:\/\/.+/.test(v);
      },
      message: 'Image URL must be a valid HTTP(S) URL'
    }
  }],
  owner: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: [true, 'Product must have an owner']
  },
  tags: [{
    type: String,
    trim: true
  }],
  ratings: {
    average: {
      type: Number,
      min: 0,
      max: 5,
      default: 0
    },
    count: {
      type: Number,
      default: 0
    }
  }
}, {
  timestamps: true,
  toJSON: {
    transform: function (doc, ret) {
      delete ret.__v;
      return ret;
    }
  }
});

// Compound index for efficient searching by name and category
productSchema.index({ name: 1, category: 1 });

// Index for owner lookup
productSchema.index({ owner: 1 });

// Text index for full-text search
productSchema.index({ name: 'text', description: 'text' });

// Virtual for formatted price
productSchema.virtual('formattedPrice').get(function () {
  return `$${this.price.toFixed(2)}`;
});

// Method to check if product is low in stock
productSchema.methods.isLowStock = function (threshold = 10) {
  return this.quantity < threshold;
};

// Static method to find products by category
productSchema.statics.findByCategory = function (category) {
  return this.find({ category });
};

// Pre-save hook to update inStock based on quantity
productSchema.pre('save', function (next) {
  this.inStock = this.quantity > 0;
  next();
});

const Product = mongoose.model('Product', productSchema);

export default Product;
