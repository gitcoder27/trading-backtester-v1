#!/usr/bin/env node

/**
 * Build script for TradingView Lightweight Charts
 *
 * This script downloads the latest version of the lightweight-charts library
 * from npm and prepares it for use in the Streamlit application.
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

// Default version - can be overridden via command line argument
const DEFAULT_VERSION = '5.0.0';
const version = process.argv[2] || DEFAULT_VERSION;
const LIBRARY_URL = `https://unpkg.com/lightweight-charts@${version}/dist/lightweight-charts.standalone.production.js`;
const OUTPUT_PATH = path.join(__dirname, '..', 'webapp', 'static', 'js', 'lightweight-charts.standalone.production.js');

async function downloadChartLibrary() {
    return new Promise((resolve, reject) => {
        console.log(`📦 Downloading TradingView Lightweight Charts v${version}...`);

        // Ensure output directory exists
        const outputDir = path.dirname(OUTPUT_PATH);
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }

        const file = fs.createWriteStream(OUTPUT_PATH);

        const request = https.get(LIBRARY_URL, (response) => {
            if (response.statusCode !== 200) {
                reject(new Error(`Failed to download: ${response.statusCode}`));
                return;
            }

            response.pipe(file);

            file.on('finish', () => {
                file.close();
                console.log(`✅ Downloaded TradingView Lightweight Charts v${version}`);
                console.log(`📁 Saved to: ${OUTPUT_PATH}`);
                console.log(`📊 File size: ${fs.statSync(OUTPUT_PATH).size} bytes`);
                resolve();
            });
        });

        request.on('error', (err) => {
            fs.unlink(OUTPUT_PATH, () => {}); // Delete the file on error
            reject(err);
        });

        file.on('error', (err) => {
            fs.unlink(OUTPUT_PATH, () => {}); // Delete the file on error
            reject(err);
        });
    });
}

async function checkVersion() {
    try {
        const packageJson = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'package.json'), 'utf8'));
        const version = packageJson.dependencies['lightweight-charts'];
        console.log(`🎯 Target version: ${version}`);
    } catch (error) {
        console.log('⚠️  Could not read package.json version');
    }
}

async function main() {
    try {
        console.log('🚀 Building TradingView Lightweight Charts...');

        await checkVersion();
        await downloadChartLibrary();

        console.log('🎉 Build completed successfully!');
        console.log(`📁 Library ready at: ${OUTPUT_PATH}`);

    } catch (error) {
        console.error('❌ Build failed:', error.message);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = { downloadChartLibrary, checkVersion };
