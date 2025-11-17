const { Pool } = require('pg');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

async function runMigration() {
  const client = await pool.connect();
  
  try {
    console.log('🚀 Starting database migration...');
    
    const migrationPath = path.join(__dirname, '../migrations/001_create_beauty_tables.sql');
    const sql = fs.readFileSync(migrationPath, 'utf8');
    
    await client.query(sql);
    
    console.log('✅ Migration completed successfully!');
    console.log('📊 Created tables:');
    console.log('  - beauty_profiles');
    console.log('  - products');
    console.log('  - recommendations');
    console.log('  - feedbacks');
    console.log('  - chat_sessions');
    console.log('  - chat_messages');
    console.log('  - feedback_embeddings');
    
  } catch (error) {
    console.error('❌ Migration failed:', error);
    throw error;
  } finally {
    client.release();
    await pool.end();
  }
}

runMigration().catch(console.error);