#!/usr/bin/env python3
"""
Test runner for the Campus Event Management System.
Runs unit tests, integration tests, and generates a coverage report.
"""
import os
import sys
import subprocess
import webbrowser
from pathlib import Path

def run_tests():
    """Run all tests with coverage reporting."""
    print("🚀 Starting test suite...")
    
    # Ensure we're in the project root
    os.chdir(Path(__file__).parent)
    
    # Run tests with coverage
    cmd = [
        "pytest",
        "tests/",
        "-v",
        "--cov=.",
        "--cov-report=html",
        "--cov-report=term"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ All tests passed!")
        
        # Open coverage report in browser
        report_path = Path("htmlcov/index.html").absolute()
        if report_path.exists():
            print(f"📊 Opening coverage report: {report_path}")
            webbrowser.open(f"file://{report_path}")
        
        return 0
    except subprocess.CalledProcessError:
        print("\n❌ Some tests failed!")
        return 1

def run_application():
    """Run the FastAPI application for manual testing."""
    print("\n🚀 Starting FastAPI application...")
    print("   Press Ctrl+C to stop the server")
    print("   Visit http://localhost:8000/api/v1/docs for API documentation")
    print("   Visit http://localhost:8000/dashboard for the admin dashboard\n")
    
    try:
        subprocess.run(["uvicorn", "main_clean:app", "--reload"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        return 1
    return 0

def main():
    """Main entry point for the test runner."""
    print("\n" + "="*60)
    print("🏫 Campus Event Management System - Test Runner")
    print("="*60)
    
    # Run tests
    test_result = run_tests()
    
    if test_result != 0:
        print("\n⚠️  Some tests failed. Fix the issues before proceeding.")
        return test_result
    
    # Ask if user wants to run the application
    print("\n" + "-"*60)
    run_app = input("\nWould you like to start the application? (y/n): ").strip().lower()
    if run_app == 'y':
        return run_application()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
