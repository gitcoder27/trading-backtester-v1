---

### **The Development Strategy: Foundation First, Vertical Slices**

We will build the application in distinct phases. We'll start by setting up the "skeleton" of the back-end and front-end, making sure they can communicate with *mocked* data. Then, we will implement the real logic for one vertical slice of functionality at a time (e.g., getting datasets, then getting strategies, then running a backtest). This ensures that at the end of each phase, you have a testable, partially working application.

---

### **Phase 1: Back-End Foundation & API Contract**

**Goal:** Create a runnable FastAPI server that defines the "language" our front-end and back-end will use to communicate, but with no real logic yet.

* **Task 1.1: Setup the FastAPI Project**
    * **Prompt for AI:** "Create a new Python project for our back-end. Set up a virtual environment. Install `fastapi`, `uvicorn`, `pydantic`, and `python-dotenv`. Create a basic directory structure (`/api`, `/core`, `/tests`). Create a `main.py` file that initializes a FastAPI app and has a single root endpoint `/` that returns `{"message": "Hello, World!"}`."

* **Task 1.2: Define the Core API Models**
    * **Prompt for AI:** "Based on our PRD, create a `models.py` file. Inside, use Pydantic to define all the necessary data models for our API. This includes models for `DataSet`, `Strategy`, `StrategyParameter`, `BacktestRequest`, `BacktestJob`, and `BacktestResults` (including sub-models for metrics, trades, and equity curve points)."

* **Task 1.3: Create Mocked API Endpoints**
    * **Prompt for AI:** "Now, create the API endpoints specified in the PRD. Use the Pydantic models we just defined. For now, the logic should be mocked. For example, the `/strategies` endpoint should return a hardcoded list of `Strategy` objects. The `/backtest` endpoint should accept a `BacktestRequest` but just return a fake `BacktestJob` with a UUID. The `/backtest/results/{job_id}` endpoint should return a hardcoded `BacktestResults` object."

---

### **Phase 2: Front-End Skeleton & Mocked Data Integration**

**Goal:** Create a runnable React application that can successfully call the mocked back-end endpoints and display the fake data.

* **Task 2.1: Setup the React Project**
    * **Prompt for AI:** "Initialize a new React project using `create-react-app` with the TypeScript template. Install `axios` for API calls and `material-ui` for UI components. Set up a basic project structure with folders for `/components`, `/services`, and `/pages`."

* **Task 2.2: Build the Static UI Layout**
    * **Prompt for AI:** "Create the main layout components based on the PRD wireframes. This includes a `Navbar`, a `ConfigurationPanel` (sidebar), and a `Dashboard` view. For now, these should be static components with no functionality, just displaying placeholder text and buttons."

* **Task 2.3: Connect to the Mocked API**
    * **Prompt for AI:** "Create an API service file (`/services/api.ts`). Add functions to call our mocked back-end endpoints (`getStrategies`, `getDatasets`). Now, modify the `ConfigurationPanel` component to call these functions in a `useEffect` hook and populate the dropdowns with the hardcoded data from the back-end."

---

### **Phase 3: Implementing the Back-End Logic**

**Goal:** Replace the mocked back-end logic with the real, high-performance backtesting engine.

* **Task 3.1: Implement Data and Strategy Endpoints**
    * **Prompt for AI:** "Let's implement the real logic for the `/datasets` and `/strategies` endpoints. Read the existing Python code from the `backtester` and `strategies` directories to dynamically discover and list the available CSV files and trading strategies."

* **Task 3.2: Implement the Asynchronous Backtesting Job**
    * **Prompt for AI:** "This is a critical step. Modify the `/backtest` endpoint. Instead of mocked data, it should now:
        1.  Take the `BacktestRequest`.
        2.  Create a background job using **Celery** and **Redis**.
        3.  The job should execute the core backtesting logic from the existing `engine.py`.
        4.  Immediately return a `job_id` to the front-end."

* **Task 3.3: Implement Job Status and Results Endpoints**
    * **Prompt for AI:** "Implement the logic for the `/backtest/status/{job_id}` and `/backtest/results/{job_id}` endpoints. These should query Celery/Redis to get the status of the job and, if completed, retrieve the full `BacktestResults` and return them."

---

### **Phase 4: Making the Front-End Fully Interactive**

**Goal:** Connect the fully functional back-end to the front-end, creating a complete end-to-end user experience.

* **Task 4.1: Implement the Backtest Submission Flow**
    * **Prompt for AI:** "In the `ConfigurationPanel`, make the 'Run Backtest' button functional. When clicked, it should gather all the selected parameters, call the `/backtest` API endpoint, and store the returned `job_id` in the application's state."

* **Task 4.2: Implement Results Polling and Display**
    * **Prompt for AI:** "After a backtest job is submitted, the front-end needs to poll for the results. Start a polling mechanism that calls the `/backtest/status/{job_id}` endpoint every 2 seconds. While polling, display a loading indicator. Once the status is 'completed', call the `/backtest/results/{job_id}` endpoint and store the results in the global state."

* **Task 4.3: Build the Results Dashboard**
    * **Prompt for AI:** "Now, build the components to display the results. Create a `MetricsGrid` component, a `TradeLog` table, and a basic `EquityCurve` chart. These components should read the data from the global state and render it."

* **Task 4.4: Integrate the High-Performance Candlestick Chart**
    * **Prompt for AI:** "This is a major feature. Create a new `CandlestickChart` component. Use the **Lightweight Charts™ by TradingView** library. It should display the price data from the backtest results and render markers on the chart for each trade (buy/sell)."

---

### **Phase 5: Testing, Polish, and Finalization**

**Goal:** Ensure the application is robust, bug-free, and professional.

* **Task 5.1: Implement Comprehensive Error Handling**
    * **Prompt for AI:** "Add robust error handling. On the back-end, use FastAPI exception handlers to catch errors and return proper HTTP status codes. On the front-end, wrap all API calls in try/catch blocks and display user-friendly error messages (e.g., using Material-UI snackbars) if something goes wrong."

* **Task 5.2: Write Unit and Integration Tests**
    * **Prompt for AI:** "Let's ensure our code is reliable. Write unit tests using `pytest` for the most critical back-end logic (e.g., metrics calculations). Then, write tests for the front-end components using `Jest` and `React Testing Library` to ensure they render correctly with given props."
