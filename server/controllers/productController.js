import Product from '../models/Product.js';
import cacheService from '../services/cache.service.js';
import logger from '../utils/logger.js';

// Helper function to invalidate product caches
const invalidateProductCaches = async (productId, userId, category) => {
  const promises = [];

  // Invalidate specific product cache
  if (productId) {
    promises.push(cacheService.del(`product:${productId}`));
  }

  // Invalidate user products cache
  if (userId) {
    promises.push(cacheService.del(`products:user:${userId}`));
  }

  // Invalidate category cache
  if (category) {
    promises.push(cacheService.del(`products:category:${category}`));
  }

  // Invalidate all products cache (clear all variations)
  const productKeys = await cacheService.memoryCache.keys();
  productKeys.forEach(key => {
    if (key.startsWith('products:')) {
      promises.push(cacheService.del(key));
    }
  });

  await Promise.all(promises);
};

// @desc    Get all products
// @route   GET /api/products
// @access  Public
export const getProducts = async (req, res, next) => {
  try {
    const {
      page = 1,
      limit = 10,
      sort = '-createdAt',
      fields,
      category,
      minPrice,
      maxPrice,
      inStock,
      search
    } = req.query;

    // Build query
    const queryObj = {};

    if (category) queryObj.category = category;
    if (inStock !== undefined) queryObj.inStock = inStock === 'true';

    if (minPrice || maxPrice) {
      queryObj.price = {};
      if (minPrice) queryObj.price.$gte = Number(minPrice);
      if (maxPrice) queryObj.price.$lte = Number(maxPrice);
    }

    if (search) {
      queryObj.$or = [
        { name: { $regex: search, $options: 'i' } },
        { description: { $regex: search, $options: 'i' } }
      ];
    }

    // Execute query
    const query = Product.find(queryObj).populate('owner', 'name email');

    // Select fields
    if (fields) {
      const fieldsList = fields.split(',').join(' ');
      query.select(fieldsList);
    }

    // Sort
    query.sort(sort);

    // Pagination
    const pageNum = parseInt(page, 10);
    const limitNum = parseInt(limit, 10);
    const startIndex = (pageNum - 1) * limitNum;
    const endIndex = pageNum * limitNum;
    const total = await Product.countDocuments(queryObj);

    query.skip(startIndex).limit(limitNum);

    const products = await query;

    // Pagination result
    const pagination = {};

    if (endIndex < total) {
      pagination.next = {
        page: pageNum + 1,
        limit: limitNum
      };
    }

    if (startIndex > 0) {
      pagination.prev = {
        page: pageNum - 1,
        limit: limitNum
      };
    }

    res.status(200).json({
      success: true,
      data: {
        products,
        pagination,
        total
      },
      message: 'Products fetched successfully'
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Get single product
// @route   GET /api/products/:id
// @access  Public
export const getProduct = async (req, res, next) => {
  try {
    const product = await Product.findById(req.params.id).populate('owner', 'name email');

    if (!product) {
      return res.status(404).json({
        success: false,
        data: null,
        message: 'Product not found'
      });
    }

    res.status(200).json({
      success: true,
      data: { product },
      message: 'Product fetched successfully'
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Create new product
// @route   POST /api/products
// @access  Private
export const createProduct = async (req, res, next) => {
  try {
    req.body.owner = req.user.id;

    const product = await Product.create(req.body);

    // Invalidate relevant caches
    await invalidateProductCaches(null, req.user.id, product.category);

    logger.info(`New product created: ${product.name} by user ${req.user.email}`);

    res.status(201).json({
      success: true,
      data: { product },
      message: 'Product created successfully'
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Update product
// @route   PUT /api/products/:id
// @access  Private (Owner only)
export const updateProduct = async (req, res, next) => {
  try {
    let product = await Product.findById(req.params.id);

    if (!product) {
      return res.status(404).json({
        success: false,
        data: null,
        message: 'Product not found'
      });
    }

    // Make sure user is product owner
    if (product.owner.toString() !== req.user.id && req.user.role !== 'admin') {
      return res.status(403).json({
        success: false,
        data: null,
        message: 'Not authorized to update this product'
      });
    }

    const oldCategory = product.category;

    product = await Product.findByIdAndUpdate(req.params.id, req.body, {
      new: true,
      runValidators: true
    });

    // Invalidate relevant caches
    await invalidateProductCaches(
      product._id.toString(),
      product.owner.toString(),
      product.category
    );

    // If category changed, also invalidate old category
    if (oldCategory !== product.category) {
      await cacheService.del(`products:category:${oldCategory}`);
    }

    logger.info(`Product updated: ${product.name} by user ${req.user.email}`);

    res.status(200).json({
      success: true,
      data: { product },
      message: 'Product updated successfully'
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Delete product
// @route   DELETE /api/products/:id
// @access  Private (Owner only)
export const deleteProduct = async (req, res, next) => {
  try {
    const product = await Product.findById(req.params.id);

    if (!product) {
      return res.status(404).json({
        success: false,
        data: null,
        message: 'Product not found'
      });
    }

    // Make sure user is product owner
    if (product.owner.toString() !== req.user.id && req.user.role !== 'admin') {
      return res.status(403).json({
        success: false,
        data: null,
        message: 'Not authorized to delete this product'
      });
    }

    await product.deleteOne();

    // Invalidate relevant caches
    await invalidateProductCaches(
      product._id.toString(),
      product.owner.toString(),
      product.category
    );

    logger.info(`Product deleted: ${product.name} by user ${req.user.email}`);

    res.status(200).json({
      success: true,
      data: {},
      message: 'Product deleted successfully'
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Get products by category
// @route   GET /api/products/category/:category
// @access  Public
export const getProductsByCategory = async (req, res, next) => {
  try {
    const products = await Product.findByCategory(req.params.category)
      .populate('owner', 'name email');

    res.status(200).json({
      success: true,
      data: {
        products,
        count: products.length
      },
      message: 'Products fetched successfully'
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Get user products
// @route   GET /api/products/user/:userId
// @access  Public
export const getUserProducts = async (req, res, next) => {
  try {
    const products = await Product.find({ owner: req.params.userId })
      .populate('owner', 'name email')
      .sort('-createdAt');

    res.status(200).json({
      success: true,
      data: {
        products,
        count: products.length
      },
      message: 'User products fetched successfully'
    });
  } catch (error) {
    next(error);
  }
};
