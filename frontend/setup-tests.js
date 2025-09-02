#!/usr/bin/env node

/**
 * Test Setup and Installation Script
 * 
 * This script sets up the complete testing environment for the Trading Backtester frontend.
 * It installs dependencies, configures testing tools, and validates the setup.
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

class TestSetup {
  constructor() {
    this.projectRoot = __dirname;
    this.hasErrors = false;
  }

  async setupTestingEnvironment() {
    console.log('🚀 Setting up Frontend Testing Environment\n');
    
    try {
      await this.checkNodeVersion();
      await this.installTestDependencies();
      await this.configureTestingTools();
      await this.validateTestSetup();
      await this.generateTestExamples();
      
      if (!this.hasErrors) {
        console.log('✅ Testing environment setup complete!');
        console.log('\nNext steps:');
        console.log('  npm run test          # Run all tests');
        console.log('  npm run test:coverage # Run with coverage');
        console.log('  npm run test:watch    # Run in watch mode');
        console.log('  npm run test:ui       # Open test UI');
      }
    } catch (error) {
      console.error('❌ Setup failed:', error.message);
      this.hasErrors = true;
    }
  }

  async checkNodeVersion() {
    console.log('📋 Checking Node.js version...');
    
    const nodeVersion = process.version;
    const majorVersion = parseInt(nodeVersion.slice(1).split('.')[0]);
    
    if (majorVersion < 16) {
      throw new Error(`Node.js 16+ required, found ${nodeVersion}`);
    }
    
    console.log(`  ✅ Node.js ${nodeVersion} (compatible)\n`);
  }

  async installTestDependencies() {
    console.log('📦 Installing testing dependencies...');
    
    const testDependencies = [
      'vitest@^1.0.4',
      '@vitest/ui@^1.0.4',
      '@vitest/coverage-v8@^1.0.4',
      '@testing-library/react@^14.1.2',
      '@testing-library/jest-dom@^6.1.4',
      '@testing-library/user-event@^14.5.1',
      'jsdom@^23.0.1',
      'msw@^2.0.11'
    ];
    
    try {
      console.log('  Installing packages...');
      execSync(`npm install --save-dev ${testDependencies.join(' ')}`, {
        stdio: 'pipe',
        cwd: this.projectRoot
      });
      console.log('  ✅ Dependencies installed\n');
    } catch (error) {
      console.log('  ⚠️  Using existing package.json configuration\n');
    }
  }

  async configureTestingTools() {
    console.log('⚙️  Configuring testing tools...');
    
    // Update vitest config
    await this.updateVitestConfig();
    
    // Create test setup file
    await this.createTestSetup();
    
    // Update TypeScript config for tests
    await this.updateTsConfig();
    
    console.log('  ✅ Configuration complete\n');
  }

  async updateVitestConfig() {
    const vitestConfig = `/// <reference types="vitest" />
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{js,ts,jsx,tsx}'],
    exclude: ['node_modules', 'dist', 'build'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        'dist/',
        'coverage/',
        'public/',
        'src/main.tsx',
        'src/vite-env.d.ts',
        '**/*.stories.*',
        '**/*.story.*'
      ],
      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80
        },
        'src/services/': {
          branches: 90,
          functions: 90,
          lines: 90,
          statements: 90
        }
      }
    },
    testTimeout: 10000,
    hookTimeout: 10000
  }
});`;

    fs.writeFileSync(path.join(this.projectRoot, 'vitest.config.ts'), vitestConfig);
    console.log('    ✅ vitest.config.ts updated');
  }

  async createTestSetup() {
    const setupContent = `import '@testing-library/jest-dom';
import { beforeAll, afterEach, afterAll } from 'vitest';
import { cleanup } from '@testing-library/react';
import { server } from './mocks/server';

// Setup MSW server
beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' });
});

afterEach(() => {
  cleanup();
  server.resetHandlers();
});

afterAll(() => {
  server.close();
});

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock HTMLCanvasElement.getContext
HTMLCanvasElement.prototype.getContext = vi.fn();

// Mock Plotly
vi.mock('plotly.js', () => ({
  newPlot: vi.fn(),
  react: vi.fn(),
  purge: vi.fn(),
  redraw: vi.fn(),
  relayout: vi.fn(),
}));

vi.mock('react-plotly.js', () => ({
  __esModule: true,
  default: vi.fn(() => null),
}));`;

    const setupDir = path.join(this.projectRoot, 'src', 'test');
    if (!fs.existsSync(setupDir)) {
      fs.mkdirSync(setupDir, { recursive: true });
    }
    
    fs.writeFileSync(path.join(setupDir, 'setup.ts'), setupContent);
    console.log('    ✅ Test setup file created');
  }

  async updateTsConfig() {
    const tsconfigPath = path.join(this.projectRoot, 'tsconfig.json');
    
    if (fs.existsSync(tsconfigPath)) {
      const tsconfig = JSON.parse(fs.readFileSync(tsconfigPath, 'utf8'));
      
      // Add vitest types
      if (!tsconfig.compilerOptions.types) {
        tsconfig.compilerOptions.types = [];
      }
      
      if (!tsconfig.compilerOptions.types.includes('vitest/globals')) {
        tsconfig.compilerOptions.types.push('vitest/globals');
      }
      
      // Include test files
      if (!tsconfig.include) {
        tsconfig.include = [];
      }
      
      const testIncludes = ['src/**/*.test.*', 'src/**/*.spec.*'];
      testIncludes.forEach(include => {
        if (!tsconfig.include.includes(include)) {
          tsconfig.include.push(include);
        }
      });
      
      fs.writeFileSync(tsconfigPath, JSON.stringify(tsconfig, null, 2));
      console.log('    ✅ TypeScript config updated');
    }
  }

  async validateTestSetup() {
    console.log('🔍 Validating test setup...');
    
    const validations = [
      {
        name: 'vitest.config.ts exists',
        check: () => fs.existsSync(path.join(this.projectRoot, 'vitest.config.ts'))
      },
      {
        name: 'Test setup file exists',
        check: () => fs.existsSync(path.join(this.projectRoot, 'src', 'test', 'setup.ts'))
      },
      {
        name: 'MSW handlers exist',
        check: () => fs.existsSync(path.join(this.projectRoot, 'src', 'test', 'mocks', 'handlers.ts'))
      },
      {
        name: 'Test files exist',
        check: () => {
          const testFiles = [
            'src/services/__tests__/api.test.ts',
            'src/services/__tests__/backtest.test.ts',
            'src/services/__tests__/analytics.test.ts'
          ];
          return testFiles.some(file => fs.existsSync(path.join(this.projectRoot, file)));
        }
      }
    ];
    
    validations.forEach(validation => {
      const status = validation.check() ? '✅' : '❌';
      console.log(`  ${status} ${validation.name}`);
      
      if (!validation.check()) {
        this.hasErrors = true;
      }
    });
    
    console.log();
  }

  async generateTestExamples() {
    console.log('📝 Generating test examples...');
    
    // Create example integration test
    const integrationTestContent = `import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from '../App';

describe('Integration Tests', () => {
  const createWrapper = () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    return ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };

  it('should render main application', () => {
    render(<App />, { wrapper: createWrapper() });
    
    expect(screen.getByText(/trading backtester/i)).toBeInTheDocument();
  });

  it('should navigate through main sections', async () => {
    const user = userEvent.setup();
    render(<App />, { wrapper: createWrapper() });
    
    // Test navigation
    const dashboardLink = screen.getByRole('link', { name: /dashboard/i });
    await user.click(dashboardLink);
    
    await waitFor(() => {
      expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
    });
  });
});`;

    const integrationDir = path.join(this.projectRoot, 'src', '__tests__', 'integration');
    if (!fs.existsSync(integrationDir)) {
      fs.mkdirSync(integrationDir, { recursive: true });
    }
    
    fs.writeFileSync(
      path.join(integrationDir, 'app-integration.test.tsx'),
      integrationTestContent
    );
    
    console.log('  ✅ Integration test example created');
    
    // Create test utility functions
    const testUtilsContent = `import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactElement } from 'react';

// Custom render with providers
export const renderWithProviders = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );

  return render(ui, { wrapper: Wrapper, ...options });
};

// Mock data factories
export const createMockBacktest = (overrides = {}) => ({
  id: '1',
  status: 'completed',
  created_at: new Date().toISOString(),
  metrics: {
    total_return: 15.5,
    sharpe_ratio: 1.41,
    max_drawdown: -5.2,
  },
  ...overrides,
});

export const createMockStrategy = (overrides = {}) => ({
  id: '1',
  name: 'Test Strategy',
  description: 'A test strategy',
  parameters: {},
  ...overrides,
});

// Wait utilities
export const waitForNextTick = () => new Promise(resolve => setTimeout(resolve, 0));

export * from '@testing-library/react';`;

    fs.writeFileSync(
      path.join(this.projectRoot, 'src', 'test', 'testUtils.tsx'),
      testUtilsContent
    );
    
    console.log('  ✅ Test utilities created\n');
  }
}

// CLI execution
async function main() {
  const args = process.argv.slice(2);
  
  if (args.includes('--help')) {
    console.log(`
Frontend Test Setup

Usage:
  node setup-tests.js [options]

Options:
  --skip-install    Skip dependency installation
  --help           Show this help message

This script will:
  - Install testing dependencies
  - Configure Vitest and testing tools
  - Create test setup files
  - Generate example tests
  - Validate the setup
    `);
    return;
  }
  
  const setup = new TestSetup();
  await setup.setupTestingEnvironment();
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = { TestSetup };
