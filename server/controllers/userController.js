import User from '../models/User.js';
import logger from '../utils/logger.js';

// @desc    Get user profile
// @route   GET /api/users/profile
// @access  Private
export const getUserProfile = async (req, res, next) => {
  try {
    const user = await User.findById(req.user.id);

    res.status(200).json({
      success: true,
      data: { user },
      message: 'User profile fetched successfully'
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Update user profile
// @route   PUT /api/users/profile
// @access  Private
export const updateUserProfile = async (req, res, next) => {
  try {
    const fieldsToUpdate = {
      name: req.body.name,
      email: req.body.email
    };

    // Remove undefined fields
    Object.keys(fieldsToUpdate).forEach(key =>
      fieldsToUpdate[key] === undefined && delete fieldsToUpdate[key]
    );

    const user = await User.findByIdAndUpdate(
      req.user.id,
      fieldsToUpdate,
      {
        new: true,
        runValidators: true
      }
    );

    logger.info(`User profile updated: ${user.email}`);

    res.status(200).json({
      success: true,
      data: { user },
      message: 'Profile updated successfully'
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Delete user account
// @route   DELETE /api/users/profile
// @access  Private
export const deleteUserAccount = async (req, res, next) => {
  try {
    await User.findByIdAndDelete(req.user.id);

    logger.info(`User account deleted: ${req.user.email}`);

    res.status(200).json({
      success: true,
      data: {},
      message: 'Account deleted successfully'
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Get user stats
// @route   GET /api/users/stats
// @access  Private
export const getUserStats = async (req, res, next) => {
  try {
    const stats = await User.aggregate([
      { $match: { _id: req.user._id } },
      {
        $lookup: {
          from: 'products',
          localField: '_id',
          foreignField: 'owner',
          as: 'products'
        }
      },
      {
        $project: {
          totalProducts: { $size: '$products' },
          productsByCategory: {
            $arrayToObject: {
              $map: {
                input: { $setUnion: ['$products.category'] },
                as: 'category',
                in: {
                  k: '$$category',
                  v: {
                    $size: {
                      $filter: {
                        input: '$products',
                        cond: { $eq: ['$$this.category', '$$category'] }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    ]);

    res.status(200).json({
      success: true,
      data: { stats: stats[0] || { totalProducts: 0, productsByCategory: {} } },
      message: 'User stats fetched successfully'
    });
  } catch (error) {
    next(error);
  }
};
