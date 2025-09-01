#!/usr/bin/env python3
"""
Test runner script for the Gemini URL Search Tool.

This script provides different test execution modes:
- Unit tests only
- Integration tests only  
- End-to-end tests only
- All tests
- Coverage reporting
- Performance testing
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, capture_output=False):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    
    if capture_output:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    else:
        return subprocess.run(cmd).returncode


def install_test_dependencies():
    """Install test dependencies if not already installed."""
    print("Installing test dependencies...")
    
    dependencies = [
        "pytest>=7.4.0",
        "pytest-asyncio>=0.21.0", 
        "pytest-cov>=4.1.0",
        "pytest-mock>=3.11.0",
        "pytest-xdist>=3.3.0",  # For parallel test execution
        "pytest-html>=3.2.0",   # For HTML reports
        "psutil>=5.9.0"          # For performance monitoring
    ]
    
    for dep in dependencies:
        returncode = run_command([sys.executable, "-m", "pip", "install", dep])
        if returncode != 0:
            print(f"Failed to install {dep}")
            return False
    
    return True


def run_unit_tests(verbose=False, coverage=False):
    """Run unit tests only."""
    print("\n" + "="*50)
    print("RUNNING UNIT TESTS")
    print("="*50)
    
    cmd = [sys.executable, "-m", "pytest", "tests/", "-m", "unit"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])
    
    cmd.extend(["--tb=short", "--disable-warnings"])
    
    return run_command(cmd)


def run_integration_tests(verbose=False):
    """Run integration tests only."""
    print("\n" + "="*50)
    print("RUNNING INTEGRATION TESTS")
    print("="*50)
    
    cmd = [sys.executable, "-m", "pytest", "tests/", "-m", "integration"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend(["--tb=short", "--disable-warnings"])
    
    return run_command(cmd)


def run_e2e_tests(verbose=False):
    """Run end-to-end tests only."""
    print("\n" + "="*50)
    print("RUNNING END-TO-END TESTS")
    print("="*50)
    
    cmd = [sys.executable, "-m", "pytest", "tests/", "-m", "e2e"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend(["--tb=short", "--disable-warnings"])
    
    return run_command(cmd)


def run_all_tests(verbose=False, coverage=False, parallel=False):
    """Run all tests."""
    print("\n" + "="*50)
    print("RUNNING ALL TESTS")
    print("="*50)
    
    cmd = [sys.executable, "-m", "pytest", "tests/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term", "--cov-report=xml"])
    
    if parallel:
        cmd.extend(["-n", "auto"])  # Use all available CPUs
    
    cmd.extend(["--tb=short", "--disable-warnings"])
    
    return run_command(cmd)


def run_performance_tests(verbose=False):
    """Run performance tests only."""
    print("\n" + "="*50)
    print("RUNNING PERFORMANCE TESTS")
    print("="*50)
    
    cmd = [sys.executable, "-m", "pytest", "tests/", "-m", "slow"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend(["--tb=short", "--disable-warnings"])
    
    return run_command(cmd)


def run_specific_test(test_path, verbose=False):
    """Run a specific test file or test function."""
    print(f"\n" + "="*50)
    print(f"RUNNING SPECIFIC TEST: {test_path}")
    print("="*50)
    
    cmd = [sys.executable, "-m", "pytest", test_path]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend(["--tb=short", "--disable-warnings"])
    
    return run_command(cmd)


def generate_test_report():
    """Generate comprehensive test report."""
    print("\n" + "="*50)
    print("GENERATING TEST REPORT")
    print("="*50)
    
    cmd = [
        sys.executable, "-m", "pytest", "tests/",
        "--cov=src",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--cov-report=term",
        "--html=test_report.html",
        "--self-contained-html",
        "-v"
    ]
    
    return run_command(cmd)


def check_test_environment():
    """Check if the test environment is properly set up."""
    print("Checking test environment...")
    
    # Check if we're in the right directory
    if not Path("tests").exists():
        print("Error: tests directory not found. Please run from project root.")
        return False
    
    if not Path("src").exists():
        print("Error: src directory not found. Please run from project root.")
        return False
    
    # Check if pytest is installed
    try:
        import pytest
        print(f"✓ pytest {pytest.__version__} is installed")
    except ImportError:
        print("✗ pytest is not installed")
        return False
    
    # Check if pytest-asyncio is installed
    try:
        import pytest_asyncio
        print(f"✓ pytest-asyncio is installed")
    except ImportError:
        print("✗ pytest-asyncio is not installed")
        return False
    
    print("✓ Test environment is ready")
    return True


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Test runner for Gemini URL Search Tool")
    
    parser.add_argument(
        "test_type",
        choices=["unit", "integration", "e2e", "all", "performance", "report", "install", "check"],
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "-c", "--coverage",
        action="store_true", 
        help="Generate coverage report"
    )
    
    parser.add_argument(
        "-p", "--parallel",
        action="store_true",
        help="Run tests in parallel"
    )
    
    parser.add_argument(
        "-t", "--test",
        help="Run specific test file or function"
    )
    
    args = parser.parse_args()
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    if args.test_type == "install":
        success = install_test_dependencies()
        sys.exit(0 if success else 1)
    
    if args.test_type == "check":
        success = check_test_environment()
        sys.exit(0 if success else 1)
    
    # Check environment before running tests
    if not check_test_environment():
        print("\nTest environment check failed. Run with 'install' to install dependencies.")
        sys.exit(1)
    
    # Run tests based on type
    if args.test:
        returncode = run_specific_test(args.test, args.verbose)
    elif args.test_type == "unit":
        returncode = run_unit_tests(args.verbose, args.coverage)
    elif args.test_type == "integration":
        returncode = run_integration_tests(args.verbose)
    elif args.test_type == "e2e":
        returncode = run_e2e_tests(args.verbose)
    elif args.test_type == "all":
        returncode = run_all_tests(args.verbose, args.coverage, args.parallel)
    elif args.test_type == "performance":
        returncode = run_performance_tests(args.verbose)
    elif args.test_type == "report":
        returncode = generate_test_report()
    else:
        print(f"Unknown test type: {args.test_type}")
        sys.exit(1)
    
    # Print summary
    print("\n" + "="*50)
    if returncode == 0:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*50)
    
    sys.exit(returncode)


if __name__ == "__main__":
    main()