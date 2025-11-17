const { Pool } = require('pg');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const pool = new Pool({
  connectionString: process.env.VECTOR_DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

async function runVectorMigration() {
  const client = await pool.connect();
  
  try {
    console.log('🚀 Starting vector database migration...');
    
    const migrationPath = path.join(__dirname, '../migrations/002_create_vector_tables.sql');
    const sql = fs.readFileSync(migrationPath, 'utf8');
    
    await client.query(sql);
    
    console.log('✅ Vector migration completed successfully!');
    console.log('📊 Created tables:');
    console.log('  - feedback_embeddings (with pgvector support)');
    console.log('  - Vector index for similarity search');
    
  } catch (error) {
    console.error('❌ Vector migration failed:', error);
    throw error;
  } finally {
    client.release();
    await pool.end();
  }
}

runVectorMigration().catch(console.error);