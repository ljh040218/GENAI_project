const pool = require('../config/database');

exports.getAllProducts = async (req, res) => {
  const client = await pool.connect();
  
  try {
    const { category, brand, finish, minPrice, maxPrice, page = 1, limit = 20 } = req.query;
    
    let query = 'SELECT * FROM products WHERE 1=1';
    const values = [];
    let paramCount = 1;

    if (category) {
      query += ` AND category = $${paramCount}`;
      values.push(category);
      paramCount++;
    }
    if (brand) {
      query += ` AND brand = $${paramCount}`;
      values.push(brand);
      paramCount++;
    }
    if (finish) {
      query += ` AND finish = $${paramCount}`;
      values.push(finish);
      paramCount++;
    }
    if (minPrice) {
      query += ` AND price >= $${paramCount}`;
      values.push(parseInt(minPrice));
      paramCount++;
    }
    if (maxPrice) {
      query += ` AND price <= $${paramCount}`;
      values.push(parseInt(maxPrice));
      paramCount++;
    }

    const offset = (page - 1) * limit;
    query += ` ORDER BY created_at DESC LIMIT $${paramCount} OFFSET $${paramCount + 1}`;
    values.push(parseInt(limit), offset);

    const result = await client.query(query, values);

    const countQuery = 'SELECT COUNT(*) FROM products WHERE 1=1';
    const countResult = await client.query(countQuery);
    const totalCount = parseInt(countResult.rows[0].count);

    res.json({
      success: true,
      products: result.rows,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total: totalCount,
        totalPages: Math.ceil(totalCount / limit)
      }
    });

  } catch (error) {
    console.error('Get products error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error'
    });
  } finally {
    client.release();
  }
};

exports.getProductById = async (req, res) => {
  const client = await pool.connect();
  
  try {
    const { id } = req.params;

    const result = await client.query(
      'SELECT * FROM products WHERE id = $1',
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: 'Product not found'
      });
    }

    res.json({
      success: true,
      product: result.rows[0]
    });

  } catch (error) {
    console.error('Get product error:', error);
    res.status(500).json({
      success: false,
      message: 'Server error'
    });
  } finally {
    client.release();
  }
};