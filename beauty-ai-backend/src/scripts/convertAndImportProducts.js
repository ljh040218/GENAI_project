const { Pool } = require('pg');
const fs = require('fs');
const path = require('path');
const csv = require('csv-parser');
require('dotenv').config();

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

const FINISH_MAP = {
  '글로시': 'glossy',
  '매트': 'matte',
  '새틴': 'satin',
  '벨벳': 'velvet',
  '데우': 'dewy',
  '데이': 'dewy',
  '세미매트': 'satin',
  '시머': 'glossy',
  '쉬머': 'glossy',
  '펄': 'glossy',
  '크림': 'satin',
  '리퀴드': 'dewy',
  '파우더': 'matte',
  '쉬어': 'satin',
  '젤리': 'dewy',
  '': 'satin'
};

function parsePrice(priceStr) {
  if (!priceStr) return 0;
  return parseInt(priceStr.replace(/[^0-9]/g, ''));
}

function labToRGB(L, a, b) {
  let y = (L + 16) / 116;
  let x = a / 500 + y;
  let z = y - b / 200;

  x = 0.95047 * ((x * x * x > 0.008856) ? x * x * x : (x - 16/116) / 7.787);
  y = 1.00000 * ((y * y * y > 0.008856) ? y * y * y : (y - 16/116) / 7.787);
  z = 1.08883 * ((z * z * z > 0.008856) ? z * z * z : (z - 16/116) / 7.787);

  let r = x *  3.2406 + y * -1.5372 + z * -0.4986;
  let g = x * -0.9689 + y *  1.8758 + z *  0.0415;
  let bl = x *  0.0557 + y * -0.2040 + z *  1.0570;

  r = (r > 0.0031308) ? (1.055 * Math.pow(r, 1/2.4) - 0.055) : 12.92 * r;
  g = (g > 0.0031308) ? (1.055 * Math.pow(g, 1/2.4) - 0.055) : 12.92 * g;
  bl = (bl > 0.0031308) ? (1.055 * Math.pow(bl, 1/2.4) - 0.055) : 12.92 * bl;

  return [
    Math.max(0, Math.min(1, r)) * 255,
    Math.max(0, Math.min(1, g)) * 255,
    Math.max(0, Math.min(1, bl)) * 255
  ].map(Math.round);
}

function rgbToHex(rgb) {
  return '#' + rgb.map(x => {
    const hex = x.toString(16);
    return hex.length === 1 ? '0' + hex : hex;
  }).join('');
}

function sanitize(str) {
  if (!str) return '';
  return str.toString().trim().replace(/\r/g, '').replace(/\uFEFF/g, '');
}

async function readCSV(filePath) {
  return new Promise((resolve, reject) => {
    const results = [];
    fs.createReadStream(filePath)
      .pipe(csv())
      .on('data', (data) => {
        const cleanData = {};
        for (const [key, value] of Object.entries(data)) {
          const cleanKey = sanitize(key);
          cleanData[cleanKey] = sanitize(value);
        }
        results.push(cleanData);
      })
      .on('end', () => resolve(results))
      .on('error', reject);
  });
}

async function importProducts() {
  const client = await pool.connect();
  
  try {
    console.log('Starting product import from CSV files...\n');

    const categories = ['lip', 'cheek', 'eye'];
    const categoryMap = {
    'lip': 'lips',
    'cheek': 'cheeks', 
    'eye': 'eyes'};
    const allProducts = [];

    for (const category of categories) {
      const filePath = `/home/jeongmin/genai/data/product/${category}.csv`;

      if (!fs.existsSync(filePath)) {
        console.log(`${category}.csv not found, skipping...`);
        continue;
      }

      console.log(`Reading ${category}.csv...`);
      const rows = await readCSV(filePath);
      
      let validRows = 0;
      let skippedRows = 0;

      for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        
        if (!row.brand || !row.product_name || !row.shade_name) {
          skippedRows++;
          continue;
        }

        try {
          const lab_L = parseFloat(row.lab_L);
          const lab_a = parseFloat(row.lab_a);
          const lab_b = parseFloat(row.lab_b);

          if (isNaN(lab_L) || isNaN(lab_a) || isNaN(lab_b)) {
            console.log(`  Skipping row ${i + 1}: Invalid LAB values`);
            skippedRows++;
            continue;
          }

          const rgb = labToRGB(lab_L, lab_a, lab_b);
          const hex = row.color_hex || rgbToHex(rgb);

          const safeBrand = row.brand.replace(/[^a-zA-Z0-9가-힣]/g, '_');
          const safeShadeName = row.shade_name.replace(/[^a-zA-Z0-9가-힣]/g, '_');
          const timestamp = Date.now() + validRows;

          const product = {
            id: `${category}_${safeBrand}_${safeShadeName}_${timestamp}`,
            brand: row.brand,
            name: `${row.product_name} - ${row.shade_name}`,
            category: categoryMap[category],
            price: parsePrice(row.price),
            finish: (() => {
            const finishValue = row.finish ? row.finish.trim() : '';
            const mapped = FINISH_MAP[finishValue];
            if (mapped) return mapped;
            // 영문 그대로 있으면 소문자로
            const lower = finishValue.toLowerCase();
            if (['matte', 'glossy', 'satin', 'velvet', 'dewy'].includes(lower)) {
                return lower;
            }
            console.log(`Unknown finish: "${finishValue}", using default "satin"`);
            return 'satin';
            })(),
            color_rgb: rgb,
            color_lab: [lab_L, lab_a, lab_b],
            color_hex: hex,
            image_url: row.image_url || row.swatch_url || '',
            description: `${row.product_name} ${row.shade_name}`,
            purchase_links: {
              olive: 'https://www.oliveyoung.co.kr'
            },
            swatch_url: row.swatch_url || row.image_url
          };

          allProducts.push(product);
          validRows++;

        } catch (err) {
          console.log(`  Error processing row ${i + 1}:`, err.message);
          skippedRows++;
        }
      }

      console.log(`Loaded ${validRows} valid products from ${category}.csv (skipped ${skippedRows})`);
    }

    console.log(`\nTotal products to import: ${allProducts.length}\n`);

    if (allProducts.length === 0) {
      console.log('No products to import');
      return;
    }

    let imported = 0;
    let skipped = 0;
    let failed = 0;

    for (const product of allProducts) {
      try {
        await client.query(
          `INSERT INTO products (
            id, brand, name, category, price, finish,
            color_rgb, color_lab, color_hex, image_url,
            description, purchase_links
          ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
          ON CONFLICT (id) DO NOTHING`,
          [
            product.id,
            product.brand,
            product.name,
            product.category,
            product.price,
            product.finish,
            product.color_rgb,
            product.color_lab,
            product.color_hex,
            product.image_url,
            product.description,
            JSON.stringify(product.purchase_links)
          ]
        );
        imported++;
        
        if (imported % 100 === 0) {
          console.log(`  Imported ${imported}/${allProducts.length} products...`);
        }
      } catch (err) {
        if (err.code === '23505') {
          skipped++;
        } else {
          console.error(`  Failed to import ${product.name}:`, err.message);
          failed++;
        }
      }
    }

    console.log(`\nImport completed!`);
    console.log(`Statistics:`);
    console.log(`   - Total products: ${allProducts.length}`);
    console.log(`   - Successfully imported: ${imported}`);
    console.log(`   - Skipped (duplicates): ${skipped}`);
    console.log(`   - Failed: ${failed}`);

    const countResult = await client.query('SELECT COUNT(*) FROM products');
    console.log(`   - Total in database: ${countResult.rows[0].count}\n`);

  } catch (error) {
    console.error('Import failed:', error);
    throw error;
  } finally {
    client.release();
    await pool.end();
  }
}

importProducts().catch(console.error);