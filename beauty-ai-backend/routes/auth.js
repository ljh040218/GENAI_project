const express = require('express');
const router = express.Router();
const AuthController = require('../controllers/authController');
const authMiddleware = require('../middleware/auth');
const { 
  validateRegistration, 
  validateLogin, 
  validateRefreshToken 
} = require('../middleware/validation');

router.post('/register', validateRegistration, AuthController.register);

router.post('/login', validateLogin, AuthController.login);

router.post('/refresh', validateRefreshToken, AuthController.refreshToken);

router.post('/logout', AuthController.logout);

router.get('/profile', authMiddleware, AuthController.getProfile);

module.exports = router;
