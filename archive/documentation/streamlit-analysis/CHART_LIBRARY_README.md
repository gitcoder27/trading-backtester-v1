# TradingView Lightweight Charts Integration

This document explains how the TradingView Lightweight Charts library is managed and integrated into the Streamlit trading backtester application.

## Overview

The application uses TradingView Lightweight Charts v5.0+ for displaying interactive financial charts. The library is managed through an npm-based workflow that ensures you always have the latest version.

## Architecture

### Why npm + Local Files (Not CDN)?

1. **Version Control**: npm allows precise version management and dependency tracking
2. **Offline Capability**: Local files work without internet connection
3. **Security**: No external script loading dependencies
4. **Reproducibility**: Exact library versions are tracked in package.json
5. **Automatic Updates**: Easy update process with version checking

### File Structure

```
trading-backtester-v1/
├── package.json                    # npm dependencies and scripts
├── scripts/
│   ├── build-charts.js            # Download specific versions (fallback/advanced)
│   └── update-charts.js           # Auto-update to latest version (recommended)
└── webapp/static/js/
    └── lightweight-charts.standalone.production.js  # Local library file
```

## Usage

### Installing Dependencies

```bash
# Install Node.js dependencies (only needed once)
npm install

# Download the latest version automatically
npm run update-charts
```

### Updating to Latest Version

```bash
# Check for and download latest version automatically (recommended)
npm run update-charts
```

### Checking for Updates (Without Downloading)

```bash
# Just check what updates are available
npm run check-updates
```

### Building Specific Versions (Advanced)

```bash
# Build specific version (for testing, CI/CD, or rollback)
npm run build-version 5.0.0

# Build default version (5.0.0) - for fallback or testing
npm run build
```

**Note**: `build-charts.js` is kept for flexibility and serves as a fallback option. For regular use, `update-charts` is recommended as it automatically finds and downloads the latest version.

## Technical Details

### How It Works

1. **npm Management**: The `lightweight-charts` package is managed via npm
2. **Version Checking**: Scripts query npm registry for latest versions
3. **Automated Download**: Latest version is downloaded from unpkg.com
4. **Local Storage**: Library stored in `webapp/static/js/`
5. **Streamlit Integration**: HTML embeds the local JavaScript file directly

### Version Tracking

- Current version is tracked in `package.json`
- Update scripts compare local vs. npm versions
- Automatic updates when newer versions are available

### File Size

- Current: ~180KB (v5.0.8)
- Standalone IIFE build variant used for browser compatibility
- Minified and optimized for production use

## Benefits Over CDN Approach

| Feature | CDN | npm + Local |
|---------|-----|-------------|
| Version Control | Manual | Automatic |
| Offline Support | ❌ | ✅ |
| Security | External dependency | Local control |
| Updates | Manual downloads | Automated scripts |
| Dependency Tracking | None | package.json |

## Integration with Python Code

The Python code remains unchanged - it still reads the local JavaScript file:

```python
# In TVLwRenderer.__init__()
self._load_chart_library()  # Loads from local file
```

## Troubleshooting

### Common Issues

1. **Library file not found**: Run `npm run update-charts` to download the latest library
2. **Outdated version**: Run `npm run update-charts` to get the latest version
3. **Permission errors**: Ensure write access to `webapp/static/js/`
4. **Need specific version**: Use `npm run build-version X.Y.Z` for version rollback/testing

### Manual Download

If automated scripts fail, you can manually download:

```bash
curl -L -o webapp/static/js/lightweight-charts.standalone.production.js \
  https://unpkg.com/lightweight-charts@5.0.0/dist/lightweight-charts.standalone.production.js
```

## Development

### Adding New Scripts

1. Add scripts to `scripts/` directory
2. Update `package.json` scripts section
3. Test with `node scripts/your-script.js`

### Version Management

- Use semantic versioning in package.json
- Test updates in development before production
- Keep backup of working versions

## Future Enhancements

- [ ] Add version rollback capability
- [ ] Implement library integrity checks
- [ ] Add automated testing for chart functionality
- [ ] Support for development builds with source maps

---

**Note**: This setup provides the best of both worlds - npm's version management and dependency tracking combined with local file storage for maximum compatibility with Streamlit's component system.
