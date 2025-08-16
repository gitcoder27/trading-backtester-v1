import sys
import os

# Disable numba JIT so coverage can track decorated functions
os.environ["NUMBA_DISABLE_JIT"] = "1"

# Ensure workspace root is in sys.path for test imports
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)
