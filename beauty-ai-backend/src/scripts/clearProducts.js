const { Pool } = require('pg');
require('dotenv').config();

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

async function clearProducts() {
  const client = await pool.connect();
  
  try {
    console.log('Clearing products table...');
    
    const result = await client.query('DELETE FROM products');
    
    console.log(`Deleted ${result.rowCount} products`);
    
  } catch (error) {
    console.error('Failed:', error);
    throw error;
  } finally {
    client.release();
    await pool.end();
  }
}

clearProducts().catch(console.error);