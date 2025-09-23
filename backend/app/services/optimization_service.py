"""Optimization service that orchestrates backtest parameter sweeps."""

import concurrent.futures
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import traceback

from backend.app.services.backtest_service import BacktestService
from backend.app.services.datasets import DatasetRepository, DatasetStorage
from backend.app.services.optimization import ParameterGridError, generate_parameter_grid
from backend.app.tasks import JobStatus, get_job_runner

SUPPORTED_METRICS = {
    "total_return",
    "total_return_pct",
    "sharpe_ratio",
    "final_equity",
    "max_drawdown",
    "max_drawdown_pct",
    "total_trades",
    "win_rate",
    "profit_factor",
    "largest_winning_trade",
    "largest_losing_trade",
    "max_consecutive_wins",
    "max_consecutive_losses",
    "average_holding_time",
    "trading_sessions_days",
    "data_points",
}


class OptimizationService:
    """Service for running parameter optimization on trading strategies."""

    def __init__(
        self,
        *,
        backtest_service: Optional[BacktestService] = None,
        job_runner=None,
        dataset_repository: Optional[DatasetRepository] = None,
        storage: Optional[DatasetStorage] = None,
    ) -> None:
        self.backtest_service = backtest_service or BacktestService()
        self.job_runner = job_runner or get_job_runner()
        self.repository = dataset_repository or DatasetRepository()
        self.storage = storage or DatasetStorage()
    
    def start_optimization_job(
        self,
        strategy_path: str,
        dataset_id: int,
        param_ranges: Dict[str, Union[List, Dict]],
        optimization_metric: str = 'sharpe_ratio',
        engine_options: Optional[Dict[str, Any]] = None,
        max_workers: int = 2,
        validation_split: float = 0.3
    ) -> Dict[str, Any]:
        """Start a parameter optimization job"""
        dataset = self.repository.get(dataset_id)
        if not dataset:
            return {'success': False, 'error': 'Dataset not found'}

        try:
            param_combinations = generate_parameter_grid(param_ranges)
        except ParameterGridError as exc:
            return {'success': False, 'error': str(exc)}

        if not param_combinations:
            return {'success': False, 'error': 'No parameter combinations generated'}

        if len(param_combinations) > 1000:
            return {
                'success': False,
                'error': f'Too many combinations ({len(param_combinations)}). Maximum allowed is 1000.',
            }

        if optimization_metric not in SUPPORTED_METRICS:
            return {
                'success': False,
                'error': f"Unsupported optimization metric '{optimization_metric}'",
            }

        job_data = {
            'strategy_path': strategy_path,
            'dataset_id': dataset_id,
            'param_ranges': param_ranges,
            'param_combinations': param_combinations,
            'optimization_metric': optimization_metric,
            'engine_options': engine_options or {},
            'max_workers': max_workers,
            'validation_split': validation_split,
            'total_combinations': len(param_combinations)
        }

        job_id = self.job_runner.submit_job(
            job_type='optimization',
            job_data=job_data,
            progress_callback=self._optimization_progress_callback
        )

        total = len(param_combinations)
        return {
            'success': True,
            'job_id': job_id,
            'total_combinations': total,
            'estimated_time_minutes': self._estimate_optimization_time(total)
        }
    
    def run_optimization(self, job_data: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
        """Run the actual optimization process"""
        try:
            strategy_path = job_data['strategy_path']
            dataset_id = job_data['dataset_id']
            param_combinations = job_data['param_combinations']
            optimization_metric = job_data['optimization_metric']
            engine_options = job_data.get('engine_options') or {}
            max_workers = max(1, int(job_data.get('max_workers', 1)))
            validation_split = job_data.get('validation_split', 0.0)
            
            dataset = self.repository.get(dataset_id)
            if not dataset:
                raise ValueError('Dataset not found')

            self.repository.touch_last_accessed(dataset)
            data = self.storage.load_dataframe(dataset.file_path)
            train_data, validation_data = self._split_data(data, validation_split)
            
            # Track results
            results = []
            best_result = None
            completed = 0
            
            # Run optimization with parallel processing
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all jobs
                future_to_params = {}
                for i, params in enumerate(param_combinations):
                    future = executor.submit(
                        self._run_single_backtest,
                        strategy_path,
                        train_data,
                        params,
                        engine_options,
                    )
                    future_to_params[future] = params
                
                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_params):
                    params = future_to_params[future]
                    completed += 1
                    
                    try:
                        backtest_result = future.result()
                        if backtest_result['success']:
                            metrics = backtest_result['result']['metrics']
                            metric_value = metrics.get(optimization_metric, 0)
                            
                            result_entry = {
                                'parameters': params,
                                'metrics': metrics,
                                'optimization_score': float(metric_value),
                                'status': 'completed'
                            }
                            
                            results.append(result_entry)
                            
                            # Track best result
                            if best_result is None or metric_value > best_result['optimization_score']:
                                best_result = result_entry.copy()
                        else:
                            results.append({
                                'parameters': params,
                                'metrics': {},
                                'optimization_score': -float('inf'),
                                'status': 'failed',
                                'error': backtest_result.get('error', 'Unknown error')
                            })
                    
                    except Exception as e:
                        results.append({
                            'parameters': params,
                            'metrics': {},
                            'optimization_score': -float('inf'),
                            'status': 'error',
                            'error': str(e)
                        })
                    
                    # Update progress
                    if progress_callback:
                        progress_callback(completed, len(param_combinations))
            
            # Validate best parameters on out-of-sample data
            validation_result = None
            if best_result and not validation_data.empty:
                validation_backtest = self._run_single_backtest(
                    strategy_path,
                    validation_data,
                    best_result['parameters'],
                    engine_options,
                )
                
                if validation_backtest['success']:
                    validation_result = validation_backtest['result']['metrics']
            
            # Sort results by optimization score
            results.sort(key=lambda x: x['optimization_score'], reverse=True)
            
            # Generate optimization analysis
            analysis = self._analyze_optimization_results(results, optimization_metric)
            
            return {
                'success': True,
                'optimization_metric': optimization_metric,
                'total_combinations': len(param_combinations),
                'successful_runs': len([r for r in results if r['status'] == 'completed']),
                'failed_runs': len([r for r in results if r['status'] != 'completed']),
                'best_parameters': best_result['parameters'] if best_result else None,
                'best_score': best_result['optimization_score'] if best_result else None,
                'best_metrics': best_result['metrics'] if best_result else None,
                'validation_metrics': validation_result,
                'all_results': results[:50],  # Limit to top 50 results
                'analysis': analysis,
                'parameter_sensitivity': self._analyze_parameter_sensitivity(results)
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    def get_optimization_results(self, job_id: str) -> Dict[str, Any]:
        """Get optimization results for a job"""
        job = self.job_runner.get_job_status(job_id)
        if not job:
            return {'success': False, 'error': 'Job not found'}

        if job['status'] != JobStatus.COMPLETED:
            return {
                'success': False,
                'error': f"Job not completed. Current status: {job['status'].value}",
                'status': job['status'].value,
                'progress': job.get('progress')
            }

        results = self.job_runner.get_job_results(job_id)
        return {
            'success': True,
            'job_id': job_id,
            'results': results
        }

    # Backwards compatibility for existing tests/utilities
    def _generate_parameter_combinations(self, param_ranges: Dict[str, Union[List, Dict]]) -> List[Dict[str, Any]]:
        return generate_parameter_grid(param_ranges)
    
    def _split_data(self, data: pd.DataFrame, validation_split: float) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Split data into training and validation sets"""
        if validation_split <= 0 or validation_split >= 1:
            return data, pd.DataFrame()
        
        split_index = int(len(data) * (1 - validation_split))
        train_data = data.iloc[:split_index].copy()
        validation_data = data.iloc[split_index:].copy()
        
        return train_data, validation_data
    
    def _run_single_backtest(
        self,
        strategy_path: str,
        data: pd.DataFrame,
        params: Dict[str, Any],
        engine_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run a single backtest with given parameters"""
        try:
            return self.backtest_service.run_backtest(
                data=data,
                strategy=strategy_path,
                strategy_params=params,
                engine_options=engine_options,
            )
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    def _analyze_optimization_results(self, results: List[Dict], optimization_metric: str) -> Dict[str, Any]:
        """Analyze optimization results to extract insights"""
        successful_results = [r for r in results if r['status'] == 'completed']
        
        if len(successful_results) == 0:
            return {'error': 'No successful optimization runs'}
        
        scores = [r['optimization_score'] for r in successful_results]
        
        analysis = {
            'score_statistics': {
                'mean': float(np.mean(scores)),
                'std': float(np.std(scores)),
                'min': float(np.min(scores)),
                'max': float(np.max(scores)),
                'median': float(np.median(scores)),
                'q25': float(np.percentile(scores, 25)),
                'q75': float(np.percentile(scores, 75))
            },
            'top_10_results': successful_results[:10],
            'performance_distribution': self._create_performance_distribution(scores)
        }
        
        return analysis
    
    def _analyze_parameter_sensitivity(self, results: List[Dict]) -> Dict[str, Any]:
        """Analyze how sensitive the optimization metric is to each parameter"""
        successful_results = [r for r in results if r['status'] == 'completed']
        
        if len(successful_results) < 2:
            return {}
        
        # Convert to DataFrame for easier analysis
        data_rows = []
        for result in successful_results:
            row = result['parameters'].copy()
            row['score'] = result['optimization_score']
            data_rows.append(row)
        
        df = pd.DataFrame(data_rows)
        
        sensitivity = {}
        
        for param in df.columns:
            if param == 'score':
                continue
            
            try:
                # Calculate correlation between parameter and score
                correlation = df[param].corr(df['score'])
                
                # Calculate score variance by parameter value
                param_scores = df.groupby(param)['score'].agg(['mean', 'std', 'count'])
                
                sensitivity[param] = {
                    'correlation': float(correlation) if not pd.isna(correlation) else 0.0,
                    'score_by_value': param_scores.to_dict('index'),
                    'unique_values': len(df[param].unique()),
                    'value_range': {
                        'min': float(df[param].min()),
                        'max': float(df[param].max())
                    }
                }
            except Exception as e:
                sensitivity[param] = {'error': str(e)}
        
        return sensitivity
    
    def _create_performance_distribution(self, scores: List[float]) -> Dict[str, List]:
        """Create histogram data for performance distribution"""
        try:
            hist, bin_edges = np.histogram(scores, bins=20)
            bin_centers = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in range(len(bin_edges)-1)]
            
            return {
                'bin_centers': [float(x) for x in bin_centers],
                'counts': [int(x) for x in hist]
            }
        except Exception:
            return {'bin_centers': [], 'counts': []}
    
    def _estimate_optimization_time(self, num_combinations: int) -> float:
        """Estimate optimization time in minutes"""
        # Rough estimate: 5 seconds per backtest, with some parallelization
        base_time_per_test = 5  # seconds
        parallelization_factor = 0.6  # 40% reduction due to parallel processing
        
        total_time_seconds = num_combinations * base_time_per_test * parallelization_factor
        return total_time_seconds / 60  # Convert to minutes
    
    def _optimization_progress_callback(self, completed: int, total: int):
        """Progress callback for optimization jobs"""
        progress_pct = (completed / total) * 100 if total > 0 else 0
        return {
            'completed': completed,
            'total': total,
            'progress_percentage': progress_pct,
            'status': f"Completed {completed}/{total} backtests ({progress_pct:.1f}%)"
        }


# Optimization helper functions
def create_parameter_range(param_type: str, **kwargs) -> Dict[str, Any]:
    """Helper function to create parameter range specifications"""
    if param_type == 'range':
        return {
            'type': 'range',
            'start': kwargs.get('start'),
            'stop': kwargs.get('stop'),
            'step': kwargs.get('step', 1)
        }
    elif param_type == 'choice':
        return {
            'type': 'choice',
            'values': kwargs.get('values', [])
        }
    else:
        raise ValueError(f"Unknown parameter type: {param_type}")


def create_optimization_config(
    strategy_path: str,
    dataset_id: int,
    param_ranges: Dict[str, Dict],
    optimization_metric: str = 'sharpe_ratio',
    validation_split: float = 0.3,
    max_workers: int = 2
) -> Dict[str, Any]:
    """Helper function to create optimization configuration"""
    return {
        'strategy_path': strategy_path,
        'dataset_id': dataset_id,
        'param_ranges': param_ranges,
        'optimization_metric': optimization_metric,
        'validation_split': validation_split,
        'max_workers': max_workers
    }
