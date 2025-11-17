const fetch = require('node-fetch');
const FormData = require('form-data');

const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';

exports.analyzeImage = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: 'No image file uploaded'
      });
    }

    const formData = new FormData();
    formData.append('file', req.file.buffer, {
      filename: req.file.originalname,
      contentType: req.file.mimetype
    });

    const response = await fetch(`${PYTHON_API_URL}/api/analyze/image`, {
      method: 'POST',
      body: formData,
      headers: formData.getHeaders()
    });

    const data = await response.json();

    res.json({
      success: true,
      analysis: data
    });

  } catch (error) {
    console.error('Image analysis error:', error);
    res.status(500).json({
      success: false,
      message: 'Analysis failed'
    });
  }
};