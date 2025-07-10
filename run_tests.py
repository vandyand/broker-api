#!/usr/bin/env python3
"""
Comprehensive Test Runner for Broker API
Runs unit, integration, and end-to-end tests
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))


class TestRunner:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.tests_dir = self.base_dir / "tests"
        self.venv_python = self.base_dir / "venv" / "bin" / "python"
        self.results = {
            "unit": {"passed": 0, "failed": 0, "errors": []},
            "integration": {"passed": 0, "failed": 0, "errors": []},
            "e2e": {"passed": 0, "failed": 0, "errors": []}
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def run_test_file(self, test_file: Path, test_type: str) -> bool:
        """Run a single test file"""
        try:
            self.log(f"Running {test_file.name}...")
            
            # Set up environment with correct Python path
            env = os.environ.copy()
            app_path = str(self.base_dir / "app")
            if "PYTHONPATH" in env:
                env["PYTHONPATH"] = f"{app_path}:{env['PYTHONPATH']}"
            else:
                env["PYTHONPATH"] = app_path
            
            # Use venv Python interpreter
            python_exec = str(self.venv_python) if self.venv_python.exists() else sys.executable
            
            # Run the test
            result = subprocess.run(
                [python_exec, test_file.name],
                capture_output=True,
                text=True,
                timeout=60,  # 60 second timeout
                cwd=test_file.parent,
                env=env
            )
            
            if result.returncode == 0:
                self.log(f"✓ {test_file.name} passed", "SUCCESS")
                self.results[test_type]["passed"] += 1
                return True
            else:
                self.log(f"✗ {test_file.name} failed", "ERROR")
                self.log(f"Error output: {result.stderr}", "ERROR")
                self.results[test_type]["failed"] += 1
                self.results[test_type]["errors"].append({
                    "file": test_file.name,
                    "error": result.stderr,
                    "output": result.stdout
                })
                return False
                
        except subprocess.TimeoutExpired:
            self.log(f"✗ {test_file.name} timed out", "ERROR")
            self.results[test_type]["failed"] += 1
            self.results[test_type]["errors"].append({
                "file": test_file.name,
                "error": "Test timed out after 60 seconds"
            })
            return False
        except Exception as e:
            self.log(f"✗ {test_file.name} error: {e}", "ERROR")
            self.results[test_type]["failed"] += 1
            self.results[test_type]["errors"].append({
                "file": test_file.name,
                "error": str(e)
            })
            return False
    
    def run_unit_tests(self) -> bool:
        """Run all unit tests"""
        self.log("Running Unit Tests", "HEADER")
        self.log("=" * 50, "HEADER")
        
        unit_tests_dir = self.tests_dir / "unit"
        if not unit_tests_dir.exists():
            self.log("No unit tests directory found", "WARNING")
            return True
        
        test_files = list(unit_tests_dir.glob("test_*.py"))
        if not test_files:
            self.log("No unit test files found", "WARNING")
            return True
        
        all_passed = True
        for test_file in test_files:
            if not self.run_test_file(test_file, "unit"):
                all_passed = False
        
        return all_passed
    
    def run_integration_tests(self) -> bool:
        """Run all integration tests"""
        self.log("Running Integration Tests", "HEADER")
        self.log("=" * 50, "HEADER")
        
        integration_tests_dir = self.tests_dir / "integration"
        if not integration_tests_dir.exists():
            self.log("No integration tests directory found", "WARNING")
            return True
        
        test_files = list(integration_tests_dir.glob("test_*.py"))
        if not test_files:
            self.log("No integration test files found", "WARNING")
            return True
        
        all_passed = True
        for test_file in test_files:
            if not self.run_test_file(test_file, "integration"):
                all_passed = False
        
        return all_passed
    
    def run_e2e_tests(self) -> bool:
        """Run all end-to-end tests"""
        self.log("Running End-to-End Tests", "HEADER")
        self.log("=" * 50, "HEADER")
        
        e2e_tests_dir = self.tests_dir / "e2e"
        if not e2e_tests_dir.exists():
            self.log("No e2e tests directory found", "WARNING")
            return True
        
        test_files = list(e2e_tests_dir.glob("test_*.py"))
        if not test_files:
            self.log("No e2e test files found", "WARNING")
            return True
        
        all_passed = True
        for test_file in test_files:
            if not self.run_test_file(test_file, "e2e"):
                all_passed = False
        
        return all_passed
    
    def print_summary(self):
        """Print test results summary"""
        self.log("Test Results Summary", "HEADER")
        self.log("=" * 50, "HEADER")
        
        total_passed = 0
        total_failed = 0
        
        for test_type, results in self.results.items():
            passed = results["passed"]
            failed = results["failed"]
            total_passed += passed
            total_failed += failed
            
            self.log(f"{test_type.upper()} Tests: {passed} passed, {failed} failed", 
                    "SUCCESS" if failed == 0 else "ERROR")
            
            if results["errors"]:
                self.log(f"  Errors in {test_type} tests:", "ERROR")
                for error in results["errors"]:
                    self.log(f"    - {error['file']}: {error['error'][:100]}...", "ERROR")
        
        self.log("=" * 50, "HEADER")
        self.log(f"TOTAL: {total_passed} passed, {total_failed} failed", 
                "SUCCESS" if total_failed == 0 else "ERROR")
        
        if total_failed == 0:
            self.log("🎉 All tests passed!", "SUCCESS")
        else:
            self.log(f"❌ {total_failed} test(s) failed", "ERROR")
    
    def run_all_tests(self):
        """Run all tests"""
        self.log("Starting Comprehensive Test Suite", "HEADER")
        self.log("=" * 60, "HEADER")
        
        # Check if API is running
        self.log("Checking if API is running...")
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                self.log("✓ API is running", "SUCCESS")
            else:
                self.log("⚠ API health check failed", "WARNING")
        except Exception as e:
            self.log("⚠ API not running or not accessible", "WARNING")
            self.log("Some tests may fail. Start the API with: docker-compose up --build", "INFO")
        
        # Run tests
        unit_success = self.run_unit_tests()
        integration_success = self.run_integration_tests()
        e2e_success = self.run_e2e_tests()
        
        # Print summary
        self.print_summary()
        
        return unit_success and integration_success and e2e_success


def main():
    """Main function"""
    runner = TestRunner()
    success = runner.run_all_tests()
    
    if success:
        print("\n🚀 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main() 