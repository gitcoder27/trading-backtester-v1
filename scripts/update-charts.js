#!/usr/bin/env node

/**
 * Update script for TradingView Lightweight Charts
 *
 * This script checks for the latest version of lightweight-charts on npm
 * and updates the local installation if a newer version is available.
 */

const https = require('https');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

async function getLatestVersion() {
    return new Promise((resolve, reject) => {
        console.log('🔍 Checking latest version on npm...');

        const options = {
            hostname: 'registry.npmjs.org',
            path: '/lightweight-charts',
            method: 'GET'
        };

        const req = https.request(options, (res) => {
            let data = '';

            res.on('data', (chunk) => {
                data += chunk;
            });

            res.on('end', () => {
                try {
                    const packageInfo = JSON.parse(data);
                    const latestVersion = packageInfo['dist-tags'].latest;
                    console.log(`📦 Latest version: ${latestVersion}`);
                    resolve(latestVersion);
                } catch (error) {
                    reject(new Error('Failed to parse npm response'));
                }
            });
        });

        req.on('error', (error) => {
            reject(error);
        });

        req.end();
    });
}

function getCurrentVersion() {
    try {
        const packageJson = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'package.json'), 'utf8'));
        const currentVersion = packageJson.dependencies['lightweight-charts'];
        // Remove ^ prefix if present
        return currentVersion.replace('^', '');
    } catch (error) {
        console.log('⚠️  Could not read current version from package.json');
        return null;
    }
}

function updatePackageJson(newVersion) {
    try {
        const packageJsonPath = path.join(__dirname, '..', 'package.json');
        const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));

        packageJson.dependencies['lightweight-charts'] = `^${newVersion}`;

        fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
        console.log(`📝 Updated package.json to version ^${newVersion}`);
    } catch (error) {
        console.error('❌ Failed to update package.json:', error.message);
    }
}

async function downloadLatestVersion(version) {
    const LIBRARY_URL = `https://unpkg.com/lightweight-charts@${version}/dist/lightweight-charts.standalone.production.js`;
    const OUTPUT_PATH = path.join(__dirname, '..', 'webapp', 'static', 'js', 'lightweight-charts.standalone.production.js');

    return new Promise((resolve, reject) => {
        console.log(`📦 Downloading version ${version}...`);

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
                console.log(`✅ Downloaded version ${version} to: ${OUTPUT_PATH}`);
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

function compareVersions(current, latest) {
    const currentParts = current.split('.').map(Number);
    const latestParts = latest.split('.').map(Number);

    for (let i = 0; i < Math.max(currentParts.length, latestParts.length); i++) {
        const currentPart = currentParts[i] || 0;
        const latestPart = latestParts[i] || 0;

        if (latestPart > currentPart) {
            return 'update';
        } else if (latestPart < currentPart) {
            return 'downgrade';
        }
    }

    return 'same';
}

async function main() {
    try {
        console.log('🚀 Checking for TradingView Lightweight Charts updates...');

        const latestVersion = await getLatestVersion();
        const currentVersion = getCurrentVersion();

        if (!currentVersion) {
            console.log('📦 No current version found, downloading latest...');
            await downloadLatestVersion(latestVersion);
            updatePackageJson(latestVersion);
            return;
        }

        console.log(`📊 Current version: ${currentVersion}`);
        console.log(`📊 Latest version: ${latestVersion}`);

        const comparison = compareVersions(currentVersion, latestVersion);

        switch (comparison) {
            case 'update':
                console.log(`🔄 Update available: ${currentVersion} → ${latestVersion}`);
                await downloadLatestVersion(latestVersion);
                updatePackageJson(latestVersion);
                console.log('✅ Update completed successfully!');
                break;

            case 'downgrade':
                console.log(`⚠️  Current version (${currentVersion}) is newer than latest (${latestVersion})`);
                console.log('🔄 Downgrading to match latest...');
                await downloadLatestVersion(latestVersion);
                updatePackageJson(latestVersion);
                break;

            case 'same':
                console.log(`✅ Already up to date (${currentVersion})`);
                // Still download to ensure we have the file
                await downloadLatestVersion(currentVersion);
                break;
        }

    } catch (error) {
        console.error('❌ Update failed:', error.message);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = { getLatestVersion, getCurrentVersion, compareVersions };
