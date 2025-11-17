const express = require('express');
const router = express.Router();
const multer = require('multer');
const { analyzeImage } = require('../controllers/imageAnalysisController');
const authMiddleware = require('../middleware/authMiddleware');

const upload = multer({ storage: multer.memoryStorage() });

router.post('/analyze', authMiddleware, upload.single('image'), analyzeImage);

module.exports = router;