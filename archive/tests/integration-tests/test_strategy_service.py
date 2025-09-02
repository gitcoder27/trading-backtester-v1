#!/usr/bin/env python3
"""Test strategy service"""

import sys
import os
sys.path.append(os.path.abspath('.'))

from backend.app.services.strategy_service import StrategyService

def test_strategy_service():
    print("🧪 Testing Strategy Service...")
    
    service = StrategyService()
    strategies = service.get_strategies()
    
    print(f"📋 Found {len(strategies)} strategies:")
    for i, strategy in enumerate(strategies, 1):
        print(f"  {i}. {strategy}")
        
    if strategies:
        strategy_1 = strategies[0]
        print(f"\n🎯 Strategy 1 details:")
        print(f"  Type: {type(strategy_1)}")
        print(f"  Keys: {strategy_1.keys() if isinstance(strategy_1, dict) else 'Not a dict'}")
        
        if 'module_path' in strategy_1:
            print(f"  Module Path: {strategy_1['module_path']}")
        else:
            print(f"  Available keys: {list(strategy_1.keys())}")

if __name__ == "__main__":
    test_strategy_service()
