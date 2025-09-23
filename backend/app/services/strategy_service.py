"""
Strategy registry and validation service
Discovers strategies from the strategies/ directory and provides metadata
"""

import os
import importlib
import inspect
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Type
import traceback
import tempfile
import shutil
from datetime import datetime
import pandas as pd
import numpy as np

from backend.app.database.models import get_session_factory, Strategy
from backtester.strategy_base import StrategyBase


class StrategyRegistry:
    """Service for discovering, registering, and validating trading strategies"""
    
    def __init__(self, strategies_dir: str = "strategies"):
        self.strategies_dir = Path(strategies_dir)
        self.SessionLocal = get_session_factory()
        self._strategy_cache = {}

    # ------------------------------------------------------------------
    # File helpers
    # ------------------------------------------------------------------

    def _resolve_module_to_path(self, module_path: str) -> Path:
        """Return absolute path to module inside the strategies directory."""
        if not module_path:
            raise ValueError("Module path is required")

        module_parts = module_path.split('.')
        # Trim leading package reference (commonly 'strategies')
        if module_parts and module_parts[0] == self.strategies_dir.name:
            module_parts = module_parts[1:]

        if not module_parts:
            raise ValueError(f"Invalid module path: {module_path}")

        relative_path = Path(*module_parts).with_suffix('.py')
        return self._ensure_within_strategies_dir(self.strategies_dir / relative_path)

    def _ensure_within_strategies_dir(self, path: Path) -> Path:
        """Ensure target path stays within the strategies directory."""
        strategies_root = self.strategies_dir.resolve()
        target = path.resolve()
        try:
            target.relative_to(strategies_root)
        except ValueError as exc:
            raise ValueError("Path must be inside strategies directory") from exc
        return target

    def _invalidate_module_cache(self, module_path: str) -> None:
        """Invalidate Python import cache for a strategy module."""
        importlib.invalidate_caches()
        if module_path in sys.modules:
            del sys.modules[module_path]

    def _resolve_strategy_id(self, strategy_id: int) -> Strategy:
        db = self.SessionLocal()
        try:
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                raise ValueError(f"Strategy {strategy_id} not found")
            return strategy
        finally:
            db.close()

    def _relative_to_strategies(self, path: Path) -> str:
        """Return strategy file path relative to strategies directory."""
        try:
            return str(path.resolve().relative_to(self.strategies_dir.resolve()))
        except ValueError:
            return str(path)

    def _get_archive_dir(self) -> Path:
        """Return directory where deleted strategy files are archived."""
        archive_root = Path("archive/strategies")
        archive_root.mkdir(parents=True, exist_ok=True)
        return archive_root

    # ------------------------------------------------------------------
    # File accessors
    # ------------------------------------------------------------------

    def get_strategy_source(self, strategy_id: int) -> Dict[str, Any]:
        """Load strategy source file content for editing."""
        strategy = self._resolve_strategy_id(strategy_id)
        file_path = self._resolve_module_to_path(strategy.module_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Strategy file not found at {file_path}")

        content = file_path.read_text(encoding='utf-8')
        return {
            'strategy_id': strategy.id,
            'module_path': strategy.module_path,
            'class_name': strategy.class_name,
            'file_path': self._relative_to_strategies(file_path),
            'content': content,
        }

    def update_strategy_source(self, strategy_id: int, content: str) -> Dict[str, Any]:
        """Persist new content to an existing strategy source file."""
        if content is None:
            raise ValueError("Content is required to update strategy source")

        strategy = self._resolve_strategy_id(strategy_id)
        file_path = self._resolve_module_to_path(strategy.module_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Strategy file not found at {file_path}")

        file_path.write_text(content, encoding='utf-8')
        self._invalidate_module_cache(strategy.module_path)

        registration: Optional[Dict[str, Any]] = None
        try:
            strategy_id_str = f"{strategy.module_path}.{strategy.class_name}"
            registration = self.register_strategies(strategy_ids=[strategy_id_str])
        except Exception as exc:  # pragma: no cover - defensive
            registration = {
                'success': False,
                'error': str(exc),
                'registered': 0,
                'updated': 0,
                'errors': [str(exc)]
            }

        return {
            'strategy_id': strategy.id,
            'file_path': self._relative_to_strategies(file_path),
            'module_path': strategy.module_path,
            'registration': registration,
        }

    def create_strategy_source(self, file_name: str, content: str, overwrite: bool = False) -> Dict[str, Any]:
        """Create a new strategy Python file inside the strategies directory."""
        if not file_name:
            raise ValueError("File name is required")
        if content is None:
            raise ValueError("Content is required")

        sanitized = file_name.strip()
        if not sanitized:
            raise ValueError("File name cannot be empty")

        # Disallow path traversal
        if any(sep in sanitized for sep in ('/', '\\')):
            raise ValueError("File name must not include directories")

        if not sanitized.endswith('.py'):
            sanitized = f"{sanitized}.py"

        target_path = self._ensure_within_strategies_dir(self.strategies_dir / sanitized)
        self.strategies_dir.mkdir(parents=True, exist_ok=True)

        if target_path.exists() and not overwrite:
            raise FileExistsError(f"Strategy file {sanitized} already exists")

        target_path.write_text(content, encoding='utf-8')

        module_path = f"{self.strategies_dir.name}.{Path(sanitized).stem}"
        self._invalidate_module_cache(module_path)

        registration: Optional[Dict[str, Any]] = None
        registered_ids: List[str] = []

        try:
            analyzed = self._analyze_strategy_file(target_path)
            candidate_ids = [info['id'] for info in analyzed if info.get('is_valid')]
            if candidate_ids:
                registration = self.register_strategies(strategy_ids=candidate_ids)
                if registration.get('success'):
                    registered_ids = candidate_ids
        except Exception as exc:  # pragma: no cover - defensive
            registration = {
                'success': False,
                'error': str(exc),
                'registered': 0,
                'updated': 0,
                'errors': [str(exc)]
            }

        return {
            'file_path': self._relative_to_strategies(target_path),
            'module_path': module_path,
            'created': True,
            'registration': registration,
            'registered_ids': registered_ids,
        }

    def delete_strategy(self, strategy_id: int) -> Dict[str, Any]:
        """Delete a registered strategy, archive its file, and remove metadata."""
        db = self.SessionLocal()
        archive_path: Optional[Path] = None
        file_removed = False
        try:
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                raise ValueError(f"Strategy {strategy_id} not found")

            module_path = strategy.module_path
            file_path: Optional[Path] = None
            try:
                file_path = self._resolve_module_to_path(module_path)
            except ValueError:
                file_path = None

            shared_count = db.query(Strategy).filter(
                Strategy.module_path == module_path,
                Strategy.id != strategy_id
            ).count()

            if file_path and file_path.exists() and shared_count == 0:
                archive_dir = self._get_archive_dir()
                timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
                archive_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
                archive_path = archive_dir / archive_name
                shutil.move(str(file_path), archive_path)
                file_removed = True
            elif file_path and file_path.exists():
                archive_path = None
                file_removed = False

            self._invalidate_module_cache(module_path)

            db.delete(strategy)
            db.commit()

            return {
                'success': True,
                'strategy_id': strategy_id,
                'file_removed': file_removed,
                'archive_path': str(archive_path) if archive_path else None,
                'module_path': module_path,
                'class_name': strategy.class_name,
                'shared_module': shared_count > 0
            }
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    
    def discover_strategies(self) -> List[Dict[str, Any]]:
        """
        Discover all strategies in the strategies directory
        Returns list of strategy metadata
        """
        strategies = []
        
        if not self.strategies_dir.exists():
            return strategies
        
        # Add strategies directory to Python path if not already there
        strategies_path = str(self.strategies_dir.absolute().parent)
        if strategies_path not in sys.path:
            sys.path.insert(0, strategies_path)
        
        # Scan all Python files in strategies directory
        for py_file in self.strategies_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            try:
                strategy_info = self._analyze_strategy_file(py_file)
                if strategy_info:
                    relative = self._relative_to_strategies(py_file)
                    for info in strategy_info:
                        info.setdefault('file_path', relative)
                    strategies.extend(strategy_info)
            except Exception as e:
                print(f"Error analyzing {py_file}: {e}")
                continue

        return strategies
    
    def register_strategies(self, strategy_ids: List[str] = None) -> Dict[str, Any]:
        """
        Register discovered strategies in the database
        Args:
            strategy_ids: Optional list of strategy IDs to register. If None, registers all discovered strategies.
        Returns:
            Summary of registration process
        """
        discovered = self.discover_strategies()
        
        # Filter strategies if specific IDs provided
        if strategy_ids:
            discovered = [s for s in discovered if s.get('id') in strategy_ids]
        
        db = self.SessionLocal()
        try:
            registered = 0
            updated = 0
            errors = []
            
            for strategy_info in discovered:
                try:
                    # Check if strategy already exists
                    existing = db.query(Strategy).filter(
                        Strategy.module_path == strategy_info['module_path'],
                        Strategy.class_name == strategy_info['class_name']
                    ).first()
                    
                    if existing:
                        # Update existing strategy
                        existing.name = strategy_info['name']
                        existing.description = strategy_info['description']
                        existing.parameters_schema = strategy_info['parameters_schema']
                        existing.default_parameters = strategy_info['default_parameters']
                        existing.last_used = None  # Reset last used
                        updated += 1
                    else:
                        # Create new strategy
                        strategy = Strategy(
                            name=strategy_info['name'],
                            module_path=strategy_info['module_path'],
                            class_name=strategy_info['class_name'],
                            description=strategy_info['description'],
                            parameters_schema=strategy_info['parameters_schema'],
                            default_parameters=strategy_info['default_parameters']
                        )
                        db.add(strategy)
                        registered += 1
                    
                except Exception as e:
                    errors.append(f"Failed to register {strategy_info['name']}: {str(e)}")
            
            db.commit()
            
            return {
                'success': True,
                'discovered': len(discovered),
                'registered': registered,
                'updated': updated,
                'errors': errors
            }
            
        except Exception as e:
            db.rollback()
            return {
                'success': False,
                'error': str(e),
                'discovered': len(discovered),
                'registered': 0,
                'updated': 0
            }
        finally:
            db.close()
    
    def get_strategy_metadata(self, strategy_id: int) -> Dict[str, Any]:
        """Get detailed metadata for a specific strategy"""
        db = self.SessionLocal()
        try:
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                raise ValueError(f"Strategy {strategy_id} not found")
            
            return self._strategy_to_dict(strategy)
            
        finally:
            db.close()
    
    def list_strategies(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """List all registered strategies"""
        db = self.SessionLocal()
        try:
            query = db.query(Strategy)
            if active_only:
                query = query.filter(Strategy.is_active == True)
            
            strategies = query.order_by(Strategy.name).all()
            return [self._strategy_to_dict(strategy, include_schema=False) for strategy in strategies]
            
        finally:
            db.close()
    
    def validate_strategy(
        self,
        strategy_id: int,
        sample_data: Optional[bytes] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate a strategy by attempting to instantiate and run it
        
        Args:
            strategy_id: Strategy ID from database
            sample_data: Optional CSV data for testing (if None, uses generated sample)
            parameters: Strategy parameters to test with
            
        Returns:
            Validation results with any errors or warnings
        """
        db = self.SessionLocal()
        try:
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                raise ValueError(f"Strategy {strategy_id} not found")
            
            return self._validate_strategy_implementation(
                strategy.module_path,
                strategy.class_name,
                sample_data,
                parameters or strategy.default_parameters or {}
            )
            
        finally:
            db.close()
    
    def validate_strategy_by_path(
        self,
        module_path: str,
        class_name: str,
        sample_data: Optional[bytes] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Validate a strategy by module path and class name"""
        return self._validate_strategy_implementation(
            module_path, class_name, sample_data, parameters or {}
        )
    
    def _analyze_strategy_file(self, py_file: Path) -> List[Dict[str, Any]]:
        """Analyze a Python file for strategy classes"""
        strategies = []
        
        # Get module name
        module_name = f"strategies.{py_file.stem}"
        
        try:
            # Import the module
            module = importlib.import_module(module_name)
            
            # Find all classes that inherit from StrategyBase
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (obj != StrategyBase and 
                    issubclass(obj, StrategyBase) and 
                    obj.__module__ == module_name):
                    
                    strategy_info = self._extract_strategy_metadata(obj, module_name, name)
                    strategies.append(strategy_info)
        
        except Exception as e:
            # If module import fails, still try to extract basic info
            print(f"Failed to import {module_name}: {e}")
            strategies.append({
                'id': f"{module_name}.Unknown",  # Unique ID for failed strategies
                'name': py_file.stem,
                'module_path': module_name,
                'class_name': 'Unknown',
                'description': f'Failed to analyze: {str(e)}',
                'parameters_schema': {},
                'default_parameters': {},
                'is_valid': False,
                'error': str(e),
                'file_path': self._relative_to_strategies(py_file)
            })

        return strategies
    
    def _extract_strategy_metadata(self, strategy_class: Type, module_path: str, class_name: str) -> Dict[str, Any]:
        """Extract metadata from a strategy class"""
        try:
            # Get basic info
            name = getattr(strategy_class, 'NAME', class_name)
            description = strategy_class.__doc__ or "No description available"
            
            # Try to get parameter schema if method exists
            parameters_schema = {}
            default_parameters = {}
            
            try:
                # Check if strategy has get_params_config method
                if hasattr(strategy_class, 'get_params_config'):
                    config = strategy_class.get_params_config()
                    if isinstance(config, list):
                        # Convert list format (Streamlit style) to dict format
                        for param_config in config:
                            param_name = param_config.get('param_key', param_config.get('name', ''))
                            if param_name:
                                parameters_schema[param_name] = {
                                    'type': param_config.get('type', 'number_input'),
                                    'default': param_config.get('default'),
                                    'min': param_config.get('min'),
                                    'max': param_config.get('max'),
                                    'step': param_config.get('step'),
                                    'label': param_config.get('label', param_name),
                                    'description': param_config.get('description', f'Parameter {param_name}')
                                }
                                default_parameters[param_name] = param_config.get('default')
                    elif isinstance(config, dict):
                        parameters_schema = config
                
                # Try to extract default parameters from __init__
                init_signature = inspect.signature(strategy_class.__init__)
                for param_name, param in init_signature.parameters.items():
                    if param_name != 'self' and param.default != inspect.Parameter.empty:
                        default_parameters[param_name] = param.default
                        
                        # Add to schema if not already present
                        if param_name not in parameters_schema:
                            param_type = type(param.default).__name__ if param.default is not None else 'any'
                            parameters_schema[param_name] = {
                                'type': param_type,
                                'default': param.default,
                                'description': f'Parameter {param_name}'
                            }
            
            except Exception as e:
                print(f"Failed to extract parameters for {class_name}: {e}")
            
            return {
                'id': f"{module_path}.{class_name}",  # Unique ID
                'name': name,
                'module_path': module_path,
                'class_name': class_name,
                'description': description.strip(),
                'parameters_schema': parameters_schema,
                'default_parameters': default_parameters,
                'is_valid': True
            }
            
        except Exception as e:
            return {
                'id': f"{module_path}.Unknown",  # Unique ID even for failed strategies
                'name': class_name,
                'module_path': module_path,
                'class_name': class_name,
                'description': f'Error analyzing strategy: {str(e)}',
                'parameters_schema': {},
                'default_parameters': {},
                'is_valid': False,
                'error': str(e)
            }
    
    def _validate_strategy_implementation(
        self,
        module_path: str,
        class_name: str,
        sample_data: Optional[bytes] = None,
        parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Validate strategy implementation by trying to run it"""
        validation_results = {
            'is_valid': False,
            'errors': [],
            'warnings': [],
            'tests_passed': [],
            'tests_failed': []
        }
        
        try:
            # Import the strategy
            module = importlib.import_module(module_path)
            strategy_class = getattr(module, class_name)
            
            validation_results['tests_passed'].append('Module import successful')
            
            # Test instantiation
            try:
                if parameters:
                    strategy = strategy_class(**parameters)
                else:
                    strategy = strategy_class()
                validation_results['tests_passed'].append('Strategy instantiation successful')
            except Exception as e:
                validation_results['errors'].append(f'Instantiation failed: {str(e)}')
                validation_results['tests_failed'].append('Strategy instantiation')
                return validation_results
            
            # Create sample data if not provided
            if sample_data is None:
                sample_df = self._create_sample_data()
            else:
                try:
                    import io
                    sample_df = pd.read_csv(io.BytesIO(sample_data))
                    # Convert timestamp column if exists
                    if 'timestamp' in sample_df.columns:
                        sample_df['timestamp'] = pd.to_datetime(sample_df['timestamp'])
                        sample_df.set_index('timestamp', inplace=True)
                    elif sample_df.index.name == 'timestamp':
                        sample_df.index = pd.to_datetime(sample_df.index)
                except Exception as e:
                    validation_results['warnings'].append(f'Failed to parse sample data: {str(e)}')
                    sample_df = self._create_sample_data()
            
            validation_results['tests_passed'].append('Sample data preparation successful')
            
            # Test required methods
            required_methods = ['generate_signals']
            for method_name in required_methods:
                if hasattr(strategy, method_name):
                    validation_results['tests_passed'].append(f'Method {method_name} exists')
                else:
                    validation_results['errors'].append(f'Required method {method_name} not found')
                    validation_results['tests_failed'].append(f'Method {method_name}')
            
            # Test signal generation
            try:
                signals = strategy.generate_signals(sample_df)
                if signals is not None and hasattr(signals, '__len__'):
                    validation_results['tests_passed'].append('Signal generation successful')
                    
                    # Check signal format
                    if hasattr(signals, 'index') and len(signals) > 0:
                        validation_results['tests_passed'].append('Signals have proper format')
                    else:
                        validation_results['warnings'].append('Signals appear to be empty or malformed')
                else:
                    validation_results['warnings'].append('Signal generation returned None or invalid data')
                    
            except Exception as e:
                validation_results['errors'].append(f'Signal generation failed: {str(e)}')
                validation_results['tests_failed'].append('Signal generation')
            
            # Test strategy properties
            try:
                if hasattr(strategy, 'NAME'):
                    validation_results['tests_passed'].append('Strategy has NAME property')
                else:
                    validation_results['warnings'].append('Strategy missing NAME property')
                
                if hasattr(strategy, '__doc__') and strategy.__doc__:
                    validation_results['tests_passed'].append('Strategy has documentation')
                else:
                    validation_results['warnings'].append('Strategy missing documentation')
                    
            except Exception as e:
                validation_results['warnings'].append(f'Error checking strategy properties: {str(e)}')
            
            # Overall validation result
            validation_results['is_valid'] = len(validation_results['errors']) == 0
            
        except ImportError as e:
            validation_results['errors'].append(f'Import error: {str(e)}')
            validation_results['tests_failed'].append('Module import')
        except AttributeError as e:
            validation_results['errors'].append(f'Strategy class not found: {str(e)}')
            validation_results['tests_failed'].append('Class discovery')
        except Exception as e:
            validation_results['errors'].append(f'Unexpected error: {str(e)}')
            validation_results['tests_failed'].append('General validation')
        
        return validation_results
    
    def _create_sample_data(self) -> pd.DataFrame:
        """Create sample OHLCV data for testing"""
        dates = pd.date_range('2024-01-01 09:15:00', periods=100, freq='1min')
        
        # Generate realistic price data
        np.random.seed(42)  # For reproducible test data
        prices = []
        current_price = 100.0
        
        for _ in range(100):
            change = np.random.normal(0, 0.5)
            current_price += change
            
            # Generate OHLC from current price
            high = current_price + abs(np.random.normal(0, 0.3))
            low = current_price - abs(np.random.normal(0, 0.3))
            open_price = np.random.uniform(low, high)
            close = np.random.uniform(low, high)
            volume = np.random.randint(1000, 10000)
            
            prices.append({
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        df = pd.DataFrame(prices, index=dates)
        df.index.name = 'timestamp'
        
        return df
    
    def _strategy_to_dict(self, strategy: Strategy, include_schema: bool = True) -> Dict[str, Any]:
        """Convert strategy model to dictionary"""
        result = {
            'id': strategy.id,
            'name': strategy.name,
            'module_path': strategy.module_path,
            'class_name': strategy.class_name,
            'file_path': self._relative_to_strategies(self._resolve_module_to_path(strategy.module_path)),
            'description': strategy.description,
            'total_backtests': strategy.total_backtests,
            'avg_performance': strategy.avg_performance,
            'is_active': strategy.is_active,
            'created_at': strategy.created_at.isoformat() if strategy.created_at else None,
            'last_used': strategy.last_used.isoformat() if strategy.last_used else None
        }
        
        if include_schema:
            result['parameters_schema'] = strategy.parameters_schema or {}
            result['default_parameters'] = strategy.default_parameters or {}
        
        return result

# Backward-compatible alias expected by tests and docs
class StrategyService(StrategyRegistry):
    """Compatibility wrapper.
    Historically this service was named StrategyService; keep alias to avoid
    breaking imports in tests and external integrations.
    """
    pass
