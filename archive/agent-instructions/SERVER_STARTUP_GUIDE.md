# 🚀 Server Startup Guide

## Backend Server (FastAPI)

**Important:** Always run the backend server from the **project root directory**, not from the `backend` subdirectory.

### ✅ Correct Way (from project root):
```powershell
# Navigate to project root
cd D:\Programming\trading\trading-backtester-v1

# Start backend server
D:\Programming\trading\trading-backtester-v1\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

```text
D:/Programming/trading/trading-backtester-v1/.venv/Scripts/python.exe -m uvicorn backend.app.main:app --reload --port 8000
```

### ❌ Incorrect Way (causes ModuleNotFoundError):
```powershell
# DON'T do this - causes import errors
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend Server (React + Vite)

```powershell
# Navigate to frontend directory
cd D:\Programming\trading\trading-backtester-v1\frontend

# Start frontend development server
npm run dev
```

## URLs

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **API Alternative Docs**: http://localhost:8000/redoc

## Troubleshooting

### Backend Import Errors
If you see `ModuleNotFoundError: No module named 'backend.app'`:
1. Make sure you're running the server from the project root directory
2. Use the full module path: `backend.app.main:app`
3. Check that the virtual environment is activated

### Frontend Issues
- Make sure `npm install` has been run in the frontend directory
- Check that Node.js and npm are properly installed
- Verify the React dev server is running on port 5173

### API Connection Issues
- Ensure both frontend and backend are running
- Check that the backend is running on port 8000
- Verify CORS is properly configured (should be automatic)

## Development Workflow

1. **Start Backend** (from project root):
   ```powershell
   D:\Programming\trading\trading-backtester-v1\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start Frontend** (from frontend directory):
   ```powershell
   cd frontend
   npm run dev
   ```

3. **Open Application**:
   - Visit http://localhost:5173 for the React frontend
   - Visit http://localhost:8000/docs for API documentation

Both servers support hot reload, so changes will be automatically reflected.
