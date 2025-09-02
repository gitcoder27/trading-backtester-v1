"""
Strategy Loader
Handles strategy discovery, loading, and validation with proper error handling
"""

import os
import importlib.util
import logging
from typing import Dict, Any, Type, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class StrategyLoaderError(Exception):
    """Custom exception for strategy loading errors"""
    pass


class StrategyLoader:
    """
    Handles strategy loading and validation with clean architecture principles.
    
    This class encapsulates all strategy-related operations including:
    - Strategy discovery from filesystem
    - Dynamic module loading
    - Strategy class instantiation
    - Parameter validation
    - Error handling and logging
    """
    
    def __init__(self, strategies_dir: str = "strategies"):
        """
        Initialize strategy loader.
        
        Args:
            strategies_dir: Directory containing strategy modules
        """
        self.strategies_dir = strategies_dir
        self._strategy_cache = {}  # Cache loaded strategy classes
    
    def load_strategy_class(self, strategy_path: str) -> Type:
        """
        Load strategy class from module.class path with validation.
        
        Args:
            strategy_path: Strategy path in format "module.submodule.ClassName"
            
        Returns:
            Type: Strategy class ready for instantiation
            
        Raises:
            StrategyLoaderError: If strategy cannot be loaded
        """
        # Check cache first
        if strategy_path in self._strategy_cache:
            logger.debug(f"Returning cached strategy: {strategy_path}")
            return self._strategy_cache[strategy_path]
        
        try:
            strategy_class = self._load_from_path(strategy_path)
            
            # Validate strategy class
            self._validate_strategy_class(strategy_class, strategy_path)
            
            # Cache the loaded strategy
            self._strategy_cache[strategy_path] = strategy_class
            
            logger.info(f"Successfully loaded strategy: {strategy_path}")
            return strategy_class
            
        except Exception as e:
            error_msg = f"Failed to load strategy '{strategy_path}': {str(e)}"
            logger.error(error_msg)
            raise StrategyLoaderError(error_msg) from e
    
    def _load_from_path(self, strategy_path: str) -> Type:
        """Load strategy class from dotted path"""
        if '.' not in strategy_path:
            raise StrategyLoaderError(f"Invalid strategy path format: {strategy_path}")
        
        # Parse module.class format
        parts = strategy_path.split('.')
        class_name = parts[-1]
        module_path = '.'.join(parts[:-1])
        
        # Try direct import first (for installed packages)
        try:
            module = importlib.import_module(module_path)
            logger.debug(f"Loaded module via import: {module_path}")
        except ImportError:
            # Try loading from file system
            module = self._load_module_from_file(module_path)
        
        # Get strategy class from module
        if not hasattr(module, class_name):
            available_classes = [name for name in dir(module) 
                               if not name.startswith('_') and callable(getattr(module, name))]
            raise StrategyLoaderError(
                f"Class '{class_name}' not found in module '{module_path}'. "
                f"Available classes: {available_classes}"
            )
        
        strategy_class = getattr(module, class_name)
        return strategy_class
    
    def _load_module_from_file(self, module_path: str):
        """Load module from file system"""
        # Convert module path to file path
        file_parts = module_path.split('.')
        
        # Try multiple possible file locations
        possible_paths = [
            Path(self.strategies_dir) / '/'.join(file_parts) / '__init__.py',
            Path(self.strategies_dir) / f"{'/'.join(file_parts)}.py",
            Path('.') / module_path.replace('.', '/') / '__init__.py',
            Path('.') / f"{module_path.replace('.', '/')}.py"
        ]
        
        for file_path in possible_paths:
            if file_path.exists():
                logger.debug(f"Loading module from file: {file_path}")
                spec = importlib.util.spec_from_file_location(module_path, file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    return module
        
        raise StrategyLoaderError(
            f"Module file not found for '{module_path}'. "
            f"Searched paths: {[str(p) for p in possible_paths]}"
        )
    
    def _validate_strategy_class(self, strategy_class: Type, strategy_path: str):
        """Validate that the loaded class is a proper strategy"""
        if not isinstance(strategy_class, type):
            raise StrategyLoaderError(
                f"'{strategy_path}' is not a class (got {type(strategy_class)})"
            )
        
        # Check for required methods (basic validation)
        required_methods = ['next']  # Most strategy frameworks require a 'next' method
        missing_methods = []
        
        for method in required_methods:
            if not hasattr(strategy_class, method):
                missing_methods.append(method)
        
        if missing_methods:
            logger.warning(
                f"Strategy '{strategy_path}' missing recommended methods: {missing_methods}"
            )
    
    def create_strategy_instance(
        self, 
        strategy_path: str, 
        strategy_params: Optional[Dict[str, Any]] = None
    ):
        """
        Create strategy instance with parameters.
        
        Args:
            strategy_path: Strategy path in format "module.submodule.ClassName"
            strategy_params: Optional parameters for strategy initialization
            
        Returns:
            Strategy instance ready for backtesting
            
        Raises:
            StrategyLoaderError: If strategy cannot be instantiated
        """
        try:
            strategy_class = self.load_strategy_class(strategy_path)
            
            # Create instance with or without parameters
            if strategy_params:
                logger.debug(f"Creating strategy instance with params: {strategy_params}")
                # Try different parameter patterns
                instance = self._create_instance_with_params(strategy_class, strategy_params)
            else:
                logger.debug("Creating strategy instance without parameters")
                instance = strategy_class()
            
            logger.info(f"Successfully created strategy instance: {strategy_path}")
            return instance
            
        except Exception as e:
            error_msg = f"Failed to create strategy instance '{strategy_path}': {str(e)}"
            logger.error(error_msg)
            raise StrategyLoaderError(error_msg) from e
    
    def _create_instance_with_params(self, strategy_class: Type, params: Dict[str, Any]):
        """Create strategy instance with parameters using different patterns"""
        # Try common parameter patterns
        creation_patterns = [
            lambda: strategy_class(params=params),  # params kwarg
            lambda: strategy_class(**params),       # direct kwargs
            lambda: strategy_class(params),         # params as positional
        ]
        
        last_error = None
        for pattern in creation_patterns:
            try:
                return pattern()
            except Exception as e:
                last_error = e
                continue
        
        # If all patterns fail, raise the last error
        raise StrategyLoaderError(
            f"Could not create strategy instance with parameters. "
            f"Tried multiple patterns. Last error: {last_error}"
        )
    
    def discover_strategies(self, pattern: str = "*.py") -> Dict[str, str]:
        """
        Discover available strategies in the strategies directory.
        
        Args:
            pattern: File pattern to match (default: "*.py")
            
        Returns:
            Dict mapping strategy names to their full paths
        """
        strategies = {}
        
        try:
            strategies_path = Path(self.strategies_dir)
            if not strategies_path.exists():
                logger.warning(f"Strategies directory not found: {strategies_path}")
                return strategies
            
            # Recursively find Python files
            for py_file in strategies_path.rglob(pattern):
                if py_file.name.startswith('_'):
                    continue  # Skip private files
                
                # Convert file path to module path
                relative_path = py_file.relative_to(strategies_path)
                module_parts = list(relative_path.with_suffix('').parts)
                
                # Skip __init__ files unless they're the only file in directory
                if module_parts[-1] == '__init__':
                    module_parts = module_parts[:-1]
                
                if module_parts:  # Skip empty paths
                    module_path = '.'.join([self.strategies_dir] + module_parts)
                    strategy_name = module_parts[-1]
                    strategies[strategy_name] = module_path
            
            logger.info(f"Discovered {len(strategies)} strategies")
            return strategies
            
        except Exception as e:
            logger.error(f"Error discovering strategies: {e}")
            return strategies
    
    def validate_strategy_parameters(
        self, 
        strategy_path: str, 
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate strategy parameters against strategy requirements.
        
        Args:
            strategy_path: Strategy to validate against
            params: Parameters to validate
            
        Returns:
            Dict with validation results and cleaned parameters
        """
        try:
            strategy_class = self.load_strategy_class(strategy_path)
            
            # Basic validation - check if strategy can be created with params
            test_instance = self.create_strategy_instance(strategy_path, params)
            
            return {
                'valid': True,
                'cleaned_params': params,
                'message': 'Parameters validated successfully'
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'message': f'Parameter validation failed: {str(e)}'
            }
    
    def clear_cache(self):
        """Clear the strategy class cache"""
        self._strategy_cache.clear()
        logger.info("Strategy cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cached strategies"""
        return {
            'cached_strategies': list(self._strategy_cache.keys()),
            'cache_size': len(self._strategy_cache)
        }
