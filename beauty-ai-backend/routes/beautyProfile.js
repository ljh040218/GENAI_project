const express = require('express');
const router = express.Router();
const { body } = require('express-validator');
const {
  createBeautyProfile,
  getBeautyProfile,
  updateBeautyProfile
} = require('../controllers/beautyProfileController');
const authMiddleware = require('../middleware/authMiddleware');

const personalColorTypes = [
  'bright_spring', 'true_spring', 'light_spring',
  'light_summer', 'true_summer', 'soft_summer',
  'soft_autumn', 'true_autumn', 'deep_autumn',
  'deep_winter', 'true_winter', 'bright_winter'
];

router.post(
  '/beauty',
  authMiddleware,
  [
    body('personalColor')
      .isIn(personalColorTypes)
      .withMessage('Invalid personal color type'),
    body('skinUndertone')
      .isIn(['warm', 'cool', 'neutral'])
      .withMessage('Skin undertone must be warm, cool, or neutral'),
    body('skinType')
      .optional({ checkFalsy: true })
      .isIn(['oily', 'dry', 'combination', 'sensitive'])
      .withMessage('Invalid skin type'),
    body('contrastLevel')
      .optional({ checkFalsy: true })
      .isIn(['high', 'medium', 'low'])
      .withMessage('Contrast level must be high, medium, or low'),
    body('preferredFinish')
      .optional({ checkFalsy: true })
      .isIn(['matte', 'glossy', 'satin', 'velvet', 'dewy'])
      .withMessage('Invalid preferred finish'),
    body('preferredStore')
      .optional({ checkFalsy: true })
      .isIn(['roadshop', 'department', 'online', 'luxury'])
      .withMessage('Invalid preferred store'),
    body('priceRangeMin')
      .optional({ checkFalsy: true })
      .isInt({ min: 0 })
      .withMessage('Price range min must be a positive number'),
    body('priceRangeMax')
      .optional({ checkFalsy: true })
      .isInt({ min: 0 })
      .withMessage('Price range max must be a positive number')
  ],
  createBeautyProfile
);

router.get('/beauty', authMiddleware, getBeautyProfile);

router.put(
  '/beauty', 
  authMiddleware,
  [
    body('personalColor')
      .optional()
      .isIn(personalColorTypes),
    body('skinUndertone')
      .optional()
      .isIn(['warm', 'cool', 'neutral']),
    body('skinType')
      .optional({ checkFalsy: true })
      .isIn(['oily', 'dry', 'combination', 'sensitive']),
    body('contrastLevel')
      .optional({ checkFalsy: true })
      .isIn(['high', 'medium', 'low']),
    body('preferredFinish')
      .optional({ checkFalsy: true })
      .isIn(['matte', 'glossy', 'satin', 'velvet', 'dewy']),
    body('preferredStore')
      .optional({ checkFalsy: true })
      .isIn(['roadshop', 'department', 'online', 'luxury']),
    body('priceRangeMin')
      .optional({ checkFalsy: true })
      .isInt({ min: 0 })
      .withMessage('Price range min must be a positive number'),
    body('priceRangeMax')
      .optional({ checkFalsy: true })
      .isInt({ min: 0 })
      .withMessage('Price range max must be a positive number')
  ],
  updateBeautyProfile
);

module.exports = router;