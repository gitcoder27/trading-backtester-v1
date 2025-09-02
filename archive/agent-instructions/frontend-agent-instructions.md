# Frontend Development Instructions (React + TypeScript)

Use this file as the exact instruction for the next AI agent you assign to implement the frontend described in the attached PRD. Work step-by-step and build a modern React application that consumes the existing FastAPI backend. The goal is to build a professional, fast, and intuitive trading backtester web application.

-----

## High-level rules (must follow)
- Do NOT perform any git operations (branching, commits, pushes, PRs). The human operator will handle all git actions.
- Do NOT modify or depend on the Streamlit UI. Any module that imports `streamlit` must be considered legacy and ignored. The new React frontend will completely replace the Streamlit interface.
- Do NOT modify the backend API. The FastAPI backend is complete and tested - consume the existing endpoints as documented.
- Ask clarifying questions only when absolutely necessary (missing API endpoint details, unclear UI requirements). Otherwise proceed and return results when a phase is complete.
- Follow modern React best practices: TypeScript, hooks, proper state management, component composition.
- Ensure mobile-responsive design and excellent performance on desktop browsers.
- Prefer component-based architecture with clear separation of concerns.

-----

## Backend API Integration (ready to consume)

The FastAPI backend is complete and running at `http://localhost:8000` with the following endpoints:

### **Core Backtesting Endpoints**
- `POST /api/v1/backtests` - Run backtests (synchronous for small datasets)
- `GET /api/v1/backtests/{id}/results` - Get backtest results
- `POST /api/v1/backtests/upload` - Upload CSV and run backtest

### **Background Jobs Endpoints**
- `POST /api/v1/jobs` - Submit background backtest jobs
- `GET /api/v1/jobs/{id}/status` - Get job status with real-time progress
- `GET /api/v1/jobs/{id}/results` - Get job results when completed
- `POST /api/v1/jobs/{id}/cancel` - Cancel running jobs
- `GET /api/v1/jobs` - List all jobs with pagination

### **Dataset Management Endpoints**
- `POST /api/v1/datasets/upload` - Upload market data CSV files
- `GET /api/v1/datasets` - List all datasets with metadata
- `GET /api/v1/datasets/{id}` - Get dataset details
- `GET /api/v1/datasets/{id}/preview` - Preview dataset (first N rows)
- `GET /api/v1/datasets/{id}/quality` - Data quality analysis
- `DELETE /api/v1/datasets/{id}` - Delete datasets

### **Strategy Management Endpoints**
- `GET /api/v1/strategies/discover` - Auto-discover strategies from filesystem
- `GET /api/v1/strategies` - List all registered strategies
- `POST /api/v1/strategies/{id}/validate` - Validate strategy code
- `GET /api/v1/strategies/{id}/schema` - Get strategy parameter schema

### **Analytics & Charts Endpoints**
- `GET /api/v1/analytics/performance/{id}` - Get comprehensive performance metrics
- `GET /api/v1/analytics/charts/{id}` - Get Plotly chart data (equity, drawdown, returns)
- `POST /api/v1/analytics/compare` - Compare multiple strategies
- `GET /api/v1/analytics/charts/{id}/equity` - Equity curve data
- `GET /api/v1/analytics/charts/{id}/drawdown` - Drawdown analysis

### **Optimization Endpoints**
- `POST /api/v1/optimize` - Run parameter optimization (background job)
- `GET /api/v1/optimize/{id}/status` - Optimization job status
- `GET /api/v1/optimize/{id}/results` - Optimization results with parameter rankings
- `POST /api/v1/optimize/{id}/cancel` - Cancel optimization jobs

**API Documentation**: Available at `http://localhost:8000/docs` (OpenAPI/Swagger)

-----

## Tech Stack & Dependencies

### **Required Frontend Stack**
- **React 18+** with TypeScript
- **Vite** for build tool and dev server
- **TanStack Query (React Query)** for server state management
- **Zustand** for client state management
- **React Router** for navigation
- **Tailwind CSS** for styling
- **React Hook Form** for form handling
- **Plotly.js** for chart visualization (backend provides Plotly JSON)
- **React Dropzone** for file uploads
- **Lucide React** for icons

### **Recommended Additional Libraries**
- **date-fns** for date manipulation
- **clsx** for conditional CSS classes
- **react-hot-toast** for notifications
- **framer-motion** for animations (optional)
- **@headlessui/react** for accessible UI components

-----

## Phased Development Plan (execute strictly in order)

### Phase 0 — Project Setup and Architecture (deliverable: working React app with routing)
1. Create React + TypeScript project using Vite in `frontend/` directory
2. Set up project structure with proper folder organization:
   ```
   frontend/
   ├── src/
   │   ├── components/          # Reusable UI components
   │   ├── pages/              # Main page components
   │   ├── hooks/              # Custom React hooks
   │   ├── services/           # API service layer
   │   ├── stores/             # Zustand stores
   │   ├── types/              # TypeScript type definitions
   │   ├── utils/              # Utility functions
   │   └── lib/                # Third-party library configurations
   ```
3. Install and configure all required dependencies
4. Set up Tailwind CSS with a professional color scheme
5. Create basic routing structure for main pages: Dashboard, Strategies, Data, Backtests, Analytics
6. Set up API service layer with proper TypeScript types for all backend endpoints
7. Configure TanStack Query for API state management
8. Create a basic layout with navigation and test that all routes work

### Phase 1 — Core Infrastructure and Design System (deliverable: design system and shared components)
1. Create a comprehensive design system with:
   - Color palette (primary, secondary, success, warning, error, neutral shades)
   - Typography scale and font configurations
   - Spacing and sizing scales
   - Component variants (buttons, inputs, cards, etc.)
2. Build essential UI components:
   - Button (with variants: primary, secondary, outline, ghost)
   - Input, Select, Textarea with validation states
   - Card, Modal, Dialog components
   - Loading spinners and skeletons
   - Table with sorting and filtering
   - Progress bars (for backtest progress)
   - File upload dropzone
   - Toast notifications
3. Create layout components:
   - Main layout with sidebar navigation
   - Page headers with breadcrumbs
   - Responsive grid system
4. Set up proper error handling and loading states
5. Implement dark/light theme support (optional but recommended)

### Phase 2 — Dashboard and Data Management (deliverable: working dashboard and dataset management)
1. **Dashboard Page**:
   - Recent backtests widget (last 10 with status indicators)
   - Quick statistics cards (total strategies, datasets, successful backtests)
   - Performance overview (best strategy, overall stats)
   - Quick action buttons (New Backtest, Upload Data, Create Strategy)
   - System health indicators
2. **Dataset Management Page**:
   - Dataset upload with drag-and-drop interface
   - Dataset library with grid/list view toggle
   - Dataset preview modal with data quality metrics
   - Dataset search and filtering
   - Delete/download functionality
   - Data quality visualization (missing data, gaps, etc.)
3. **Navigation and Layout**:
   - Responsive sidebar with page navigation
   - Breadcrumb navigation
   - User-friendly page transitions

### Phase 3 — Strategy Management and Validation (deliverable: strategy management interface)
1. **Strategy Library Page**:
   - Grid view of discovered strategies with cards showing:
     - Strategy name and description
     - Parameter schema preview
     - Recent performance (if available)
     - Last used date
   - Strategy search and filtering by name, parameters, performance
   - Strategy validation with real-time feedback
2. **Strategy Detail View**:
   - Strategy parameter schema display
   - Parameter input form with validation
   - Strategy validation results
   - Historical performance if backtested before
3. **Strategy Parameter Builder**:
   - Dynamic form generation based on strategy schema
   - Parameter validation and default values
   - Parameter range inputs for optimization
   - Save/load parameter presets

### Phase 4 — Backtesting Interface and Job Management (deliverable: complete backtesting workflow)
1. **Backtest Configuration Page**:
   - Strategy selection dropdown with search
   - Dataset selection with preview
   - Strategy parameter form (dynamic based on selected strategy)
   - Engine options configuration (initial cash, lots, fees, etc.)
   - Validation before submitting backtest
2. **Backtest Execution Interface**:
   - Real-time progress tracking for background jobs
   - Job status dashboard with all running/completed backtests
   - Job cancellation capability
   - Estimated time remaining and progress visualization
3. **Job Management**:
   - Jobs list with filtering (status, date, strategy)
   - Job details modal with progress and logs
   - Bulk operations (cancel multiple jobs)
   - Job history with search functionality

### Phase 5 — Results Analysis and Charts (deliverable: comprehensive analytics interface)
1. **Backtest Results Page**:
   - Performance metrics dashboard with key indicators:
     - Total return, Sharpe ratio, max drawdown
     - Win rate, profit factor, trade statistics
     - Risk metrics (VaR, volatility, etc.)
   - Interactive Plotly charts:
     - Equity curve with drawdown overlay
     - Trade markers on price chart
     - Returns distribution histogram
     - Monthly returns heatmap
2. **Trade Analysis Interface**:
   - Sortable and filterable trade log table
   - Trade detail modal with entry/exit analysis
   - Trade duration and P&L distribution charts
   - Trade statistics and patterns
3. **Advanced Analytics**:
   - Rolling performance metrics
   - Risk-adjusted returns analysis
   - Correlation analysis between strategies
   - Performance attribution and breakdown

### Phase 6 — Strategy Comparison and Optimization (deliverable: optimization and comparison tools)
1. **Strategy Comparison Interface**:
   - Multi-strategy comparison table
   - Side-by-side performance charts
   - Statistical significance tests
   - Correlation matrix visualization
2. **Parameter Optimization Interface**:
   - Optimization job configuration with parameter ranges
   - 3D parameter surface visualization
   - Optimization progress tracking
   - Results table with sortable parameters
   - Out-of-sample validation results
3. **Optimization Results Analysis**:
   - Parameter sensitivity analysis
   - Overfitting detection warnings
   - Best parameter selection with confidence intervals
   - Export optimization results

### Phase 7 — Advanced Features and Polish (deliverable: production-ready application)
1. **Advanced Data Management**:
   - Bulk dataset operations
   - Data synchronization indicators
   - Data export functionality
   - Advanced data quality reports
2. **Performance Optimizations**:
   - Virtual scrolling for large datasets
   - Chart performance optimization
   - Lazy loading for heavy components
   - API request optimization and caching
3. **User Experience Enhancements**:
   - Keyboard shortcuts for power users
   - Customizable dashboard widgets
   - Export functionality (PDF reports, CSV data)
   - Advanced filtering and search across all pages
4. **Error Handling and Edge Cases**:
   - Comprehensive error boundary implementation
   - Offline mode handling
   - Network error recovery
   - Data validation and sanitization

-----

## UI/UX Design Requirements

### **Design Principles**
- **Speed First**: Sub-second interactions, optimistic updates
- **Professional**: Clean, data-dense interface suitable for trading
- **Intuitive**: Minimal learning curve, discoverable features
- **Responsive**: Works perfectly on desktop, tablet, and mobile

### **Color Scheme and Visual Design**
```css
/* Professional Trading Theme */
:root {
  /* Primary Colors */
  --color-primary-50: #eff6ff;
  --color-primary-500: #3b82f6;
  --color-primary-600: #2563eb;
  --color-primary-900: #1e3a8a;
  
  /* Success/Profit Colors */
  --color-success-50: #f0fdf4;
  --color-success-500: #22c55e;
  --color-success-600: #16a34a;
  
  /* Error/Loss Colors */
  --color-error-50: #fef2f2;
  --color-error-500: #ef4444;
  --color-error-600: #dc2626;
  
  /* Neutral Colors */
  --color-gray-50: #f9fafb;
  --color-gray-100: #f3f4f6;
  --color-gray-500: #6b7280;
  --color-gray-900: #111827;
}
```

### **Typography Scale**
- **Headings**: Inter or Outfit font family
- **Body**: Inter font family
- **Monospace**: JetBrains Mono or Fira Code (for numbers, code)

### **Component Standards**
- **Cards**: Subtle shadows, rounded corners, clean borders
- **Forms**: Clear labels, validation states, helpful error messages
- **Tables**: Striped rows, sortable headers, sticky headers for long tables
- **Charts**: Professional color scheme, clear legends, interactive tooltips

-----

## API Integration Guidelines

### **Service Layer Architecture**
Create a service layer that abstracts API calls:

```typescript
// services/api.ts
export class BacktestService {
  static async runBacktest(config: BacktestConfig): Promise<BacktestResult> {
    // Handle API call with proper error handling
  }
  
  static async getJobStatus(jobId: string): Promise<JobStatus> {
    // Poll job status with proper loading states
  }
}
```

### **Error Handling Strategy**
- Network errors: Show retry mechanisms
- Validation errors: Display field-specific errors
- Server errors: User-friendly error messages
- Loading states: Skeleton screens and progress indicators

### **Real-time Updates**
- Use TanStack Query for automatic background refetching
- Implement polling for job status updates
- Show real-time progress for long-running operations

-----

## Performance Requirements

### **Loading Performance**
- Initial page load: < 2 seconds
- Route transitions: < 500ms
- Chart rendering: < 1 second for 10k+ data points
- Table operations: < 200ms for 1000+ rows

### **Memory Management**
- Efficient chart data handling
- Virtual scrolling for large datasets
- Proper cleanup of subscriptions and timers
- Optimized re-renders with React.memo and useMemo

### **User Experience**
- Optimistic updates for fast feedback
- Skeleton screens during loading
- Progressive data loading
- Responsive design for all screen sizes

-----

## Testing Strategy

### **Required Tests**
1. **Component Tests**: Key UI components with React Testing Library
2. **Integration Tests**: Critical user flows (run backtest, view results)
3. **API Integration**: Mock API responses for consistent testing
4. **Performance Tests**: Chart rendering and large dataset handling

### **Testing Tools**
- **Vitest** for unit testing
- **React Testing Library** for component testing
- **MSW (Mock Service Worker)** for API mocking
- **Playwright** for end-to-end testing (optional)

-----

## File Structure and Organization

```
frontend/
├── public/
│   ├── favicon.ico
│   └── manifest.json
├── src/
│   ├── components/           # Reusable UI components
│   │   ├── ui/              # Basic UI elements (Button, Input, etc.)
│   │   ├── charts/          # Chart components
│   │   ├── forms/           # Form components
│   │   └── layout/          # Layout components
│   ├── pages/               # Main page components
│   │   ├── Dashboard/
│   │   ├── Strategies/
│   │   ├── Datasets/
│   │   ├── Backtests/
│   │   └── Analytics/
│   ├── hooks/               # Custom React hooks
│   │   ├── useApi.ts
│   │   ├── usePolling.ts
│   │   └── useLocalStorage.ts
│   ├── services/            # API service layer
│   │   ├── api.ts
│   │   ├── backtest.ts
│   │   ├── dataset.ts
│   │   └── strategy.ts
│   ├── stores/              # Zustand stores
│   │   ├── authStore.ts
│   │   ├── uiStore.ts
│   │   └── settingsStore.ts
│   ├── types/               # TypeScript definitions
│   │   ├── api.ts
│   │   ├── backtest.ts
│   │   └── common.ts
│   ├── utils/               # Utility functions
│   │   ├── format.ts
│   │   ├── validation.ts
│   │   └── constants.ts
│   ├── lib/                 # Third-party configurations
│   │   ├── queryClient.ts
│   │   └── plotly.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── README.md
```

-----

## Acceptance Criteria / Quality Gates

### **Functional Requirements**
- All backend API endpoints successfully integrated
- Complete CRUD operations for datasets, strategies, and backtests
- Real-time job progress tracking working
- Interactive charts displaying properly
- Responsive design working on desktop and mobile
- File upload functionality working with proper validation

### **Performance Requirements**
- Page load times under targets specified above
- Smooth chart interactions with large datasets
- No memory leaks during extended usage
- Proper error handling and recovery

### **Code Quality**
- TypeScript with strict mode enabled
- Comprehensive component testing
- Consistent code formatting (Prettier + ESLint)
- Proper error boundaries and fallback UI
- Accessibility compliance (WCAG 2.1 AA)

-----

## Development Workflow

### **Environment Setup**
```bash
# Create React project with Vite
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install

# Install required dependencies
npm install @tanstack/react-query zustand react-router-dom react-hook-form
npm install tailwindcss @headlessui/react lucide-react plotly.js-react plotly.js
npm install react-dropzone date-fns clsx react-hot-toast

# Install dev dependencies
npm install -D @types/plotly.js eslint prettier @typescript-eslint/eslint-plugin
```

### **Development Server**
```bash
# Start frontend dev server (from frontend/ directory)
npm run dev

# Backend should be running at http://localhost:8000
# Frontend will be available at http://localhost:5173
```

### **Build and Deploy**
```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

-----

## Integration with Existing Backend

### **Backend Status**
The FastAPI backend is complete and provides:
- ✅ 35+ API endpoints covering all functionality
- ✅ Real-time job progress tracking
- ✅ File upload support
- ✅ Comprehensive error handling
- ✅ OpenAPI documentation at `/docs`

### **API Base URL**
- Development: `http://localhost:8000`
- All endpoints prefixed with `/api/v1/`

### **Authentication**
- No authentication required for initial version
- Add session management structure for future auth implementation

-----

## Minimal Deliverables per Phase

### **Phase 0**: 
- Working React + TypeScript + Vite setup
- Basic routing and navigation
- API service layer foundation
- Clean project structure

### **Phase 1**: 
- Complete design system and UI component library
- Responsive layout with navigation
- Error handling and loading states

### **Phase 2**: 
- Functional dashboard with real data
- Dataset upload and management interface
- Basic data visualization

### **Phase 3**: 
- Strategy management and validation
- Dynamic parameter forms
- Strategy discovery integration

### **Phase 4**: 
- Complete backtesting workflow
- Job management with real-time progress
- Background job handling

### **Phase 5**: 
- Results analysis with interactive charts
- Performance metrics dashboard
- Trade analysis interface

### **Phase 6**: 
- Strategy comparison tools
- Parameter optimization interface
- Advanced analytics

### **Phase 7**: 
- Production polish and optimizations
- Advanced features and export capabilities
- Comprehensive error handling

-----

## Success Metrics

### **User Experience**
- Page load time < 2 seconds
- Chart interactions < 500ms response time
- Zero loading states > 3 seconds
- Mobile responsive score > 95%

### **Code Quality**
- TypeScript strict mode with 0 errors
- Test coverage > 80% for critical components
- Lighthouse performance score > 90
- Accessibility score > 95

### **Feature Completeness**
- All API endpoints successfully consumed
- All PRD requirements implemented
- All user workflows functional end-to-end
- Production-ready deployment configuration

-----

## Final Notes to Frontend Agent

- **DO NOT modify the backend** - it is complete and tested
- **DO NOT reference Streamlit code** - ignore all existing UI implementations
- **Focus on performance** - this is a data-intensive application
- **Prioritize user experience** - traders need fast, reliable interfaces
- **Use modern React patterns** - hooks, composition, proper state management
- **Build incrementally** - ensure each phase is fully working before proceeding
- **Test thoroughly** - especially chart rendering and large dataset handling

When each phase is completed, provide:
- Screenshots or video of working functionality
- Performance metrics and loading times
- Any technical decisions or trade-offs made
- Instructions for running and testing the implementation

---

End of frontend development instructions.
