const fs = require('fs');
const path = require('path');

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error('Usage: node node_pdf2md_runner.js <configJsonPath>');
    process.exit(2);
  }
  const configPath = args[0];
  if (!fs.existsSync(configPath)) {
    console.error('Config file not found:', configPath);
    process.exit(2);
  }
  const raw = fs.readFileSync(configPath, 'utf8');
  let cfg = {};
  try {
    cfg = JSON.parse(raw);
  } catch (e) {
    console.error('Failed to parse config JSON:', e);
    process.exit(2);
  }
  const pdfPath = cfg.pdfPath;
  const outputDir = cfg.outputDir || path.dirname(pdfPath);
  const options = cfg.options || {};
  try {
    const { parsePdf } = require('pdf2md-js');
    await parsePdf(pdfPath, options);
    console.log('parsePdf completed');
    process.exit(0);
  } catch (err) {
    console.error('parsePdf failed:', err);
    process.exit(3);
  }
}

main();


