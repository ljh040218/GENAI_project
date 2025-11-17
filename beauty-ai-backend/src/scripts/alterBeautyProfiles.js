const { Pool } = require('pg');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

async function alterBeautyProfiles() {
  const client = await pool.connect();
  
  try {
    console.log('🚀 Altering beauty_profiles table (keeping existing data)...');
    
    const migrationPath = path.join(__dirname, '../migrations/003_alter_beauty_profiles.sql');
    const sql = fs.readFileSync(migrationPath, 'utf8');
    
    await client.query(sql);
    
    console.log('✅ Beauty profiles table altered successfully!');
    console.log('📦 Existing data preserved.');
    
    console.log('\n📊 Required fields (2):');
    console.log('  ✅ Personal color (12 types)');
    console.log('  ✅ Skin undertone (warm/cool/neutral)');
    
    console.log('\n⭕ Optional fields (nullable):');
    console.log('  - Skin type');
    console.log('  - Contrast level');
    console.log('  - Preferred finish');
    console.log('  - Preferred store');
    console.log('  - Price range (min/max)');
    
    const countResult = await client.query('SELECT COUNT(*) FROM beauty_profiles');
    console.log(`\n💾 Total profiles in database: ${countResult.rows[0].count}`);
    
  } catch (error) {
    console.error('❌ Alter failed:', error);
    throw error;
  } finally {
    client.release();
    await pool.end();
  }
}

alterBeautyProfiles().catch(console.error);