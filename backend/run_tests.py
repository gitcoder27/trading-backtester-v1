"""
Test Runner Script for Backend Module
Runs comprehensive tests with coverage analysis
"""

import subprocess
import sys
import os
from pathlib import Path


def run_tests():
    """Run all tests with coverage"""
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    print("=" * 70)
    print("BACKEND MODULE - COMPREHENSIVE TESTING")
    print("=" * 70)
    
    # Test commands to run
    test_commands = [
        # Run comprehensive tests
        ["python", "-m", "pytest", "tests/test_comprehensive_backend.py", 
         "--cov=app", "--cov=database", "--cov=services", 
         "--cov-report=term-missing", "--cov-report=html", "--cov-report=xml",
         "-v", "--tb=short"],
        
        # Run existing tests as well
        ["python", "-m", "pytest", "tests/", 
         "--cov=app", "--cov-append",
         "--cov-report=term-missing", "--cov-report=html", "--cov-report=xml",
         "-v", "--tb=short", "--maxfail=10"],
    ]
    
    all_passed = True
    
    for i, cmd in enumerate(test_commands, 1):
        print(f"\n--- Running Test Suite {i} ---")
        print(" ".join(cmd))
        print("-" * 50)
        
        try:
            result = subprocess.run(cmd, check=False, capture_output=False)
            if result.returncode != 0:
                print(f"Warning: Test suite {i} had failures or errors")
                all_passed = False
        except Exception as e:
            print(f"Error running test suite {i}: {e}")
            all_passed = False
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    if all_passed:
        print("✅ All test suites completed successfully!")
    else:
        print("⚠️  Some tests failed or had errors. Check output above.")
    
    # Check if coverage report was generated
    html_report = backend_dir / "htmlcov" / "index.html"
    if html_report.exists():
        print(f"📊 HTML Coverage report generated: {html_report}")
        print("📊 Open in browser to view detailed coverage")
    
    xml_report = backend_dir / "coverage.xml"
    if xml_report.exists():
        print(f"📊 XML Coverage report generated: {xml_report}")
    
    print("\n" + "=" * 70)


def check_dependencies():
    """Check if required testing dependencies are installed"""
    required_packages = [
        'pytest', 'pytest-cov', 'pytest-asyncio', 'httpx', 'fastapi'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstall them with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True


def main():
    """Main function"""
    print("Backend Testing Suite")
    print("Checking dependencies...")
    
    if not check_dependencies():
        print("❌ Missing dependencies. Install them first.")
        return 1
    
    print("✅ All dependencies found.")
    
    try:
        run_tests()
        return 0
    except KeyboardInterrupt:
        print("\n❌ Testing interrupted by user.")
        return 1
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
