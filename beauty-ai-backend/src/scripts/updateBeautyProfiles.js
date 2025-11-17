const { Pool } = require('pg');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

async function updateBeautyProfiles() {
  const client = await pool.connect();
  
  try {
    console.log('🚀 Updating beauty_profiles table...');
    
    const migrationPath = path.join(__dirname, '../migrations/003_update_beauty_profiles.sql');
    const sql = fs.readFileSync(migrationPath, 'utf8');
    
    await client.query(sql);
    
    console.log('✅ Beauty profiles table updated successfully!');
    console.log('📊 New features:');
    console.log('  - 12 personal color types (4 seasons × 3 variants)');
    console.log('  - Skin undertone: warm/cool/neutral');
    console.log('  - Skin type: oily/dry/combination/sensitive');
    console.log('  - Contrast level: high/medium/low');
    console.log('  - Preferred finish: matte/glossy/satin/velvet/dewy');
    console.log('  - Preferred store: roadshop/department/online/luxury');
    console.log('  - Price range preferences');
    
  } catch (error) {
    console.error('❌ Update failed:', error);
    throw error;
  } finally {
    client.release();
    await pool.end();
  }
}

updateBeautyProfiles().catch(console.error);