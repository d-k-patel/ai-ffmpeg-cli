#!/usr/bin/env python3
"""Test runner script for ai-ffmpeg-cli.

This script provides convenient commands to run different test categories
with various options and configurations.
"""

import argparse
import subprocess
import sys


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'=' * 60}\n")

    try:
        subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} failed with exit code {e.returncode}")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Test runner for ai-ffmpeg-cli",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
          Examples:
            python run_tests.py unit                   # Run unit tests only
            python run_tests.py integration --cov      # Run integration tests with coverage
            python run_tests.py all --fast             # Run all fast tests
            python run_tests.py security --verbose     # Run security tests with verbose output
            python run_tests.py performance --slow     # Run performance tests (slow)
        """,
    )

    parser.add_argument(
        "category",
        choices=["unit", "integration", "e2e", "performance", "security", "all"],
        help="Test category to run",
    )

    parser.add_argument("--cov", action="store_true", help="Run with coverage reporting")

    parser.add_argument("--html", action="store_true", help="Generate HTML coverage report")

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    parser.add_argument("--fast", action="store_true", help="Run only fast tests")

    parser.add_argument("--slow", action="store_true", help="Run only slow tests")

    parser.add_argument(
        "--parallel",
        "-n",
        type=int,
        help="Run tests in parallel with specified number of workers",
    )

    parser.add_argument("--failed-first", action="store_true", help="Run failed tests first")

    parser.add_argument(
        "--tb",
        choices=["auto", "long", "short", "line", "no"],
        default="auto",
        help="Traceback style",
    )

    args = parser.parse_args()

    # Build pytest command
    cmd = ["python", "-m", "pytest"]

    # Add test path based on category
    if args.category == "all":
        cmd.append("tests/")
    else:
        cmd.append(f"tests/{args.category}/")

    # Add coverage options
    if args.cov:
        cmd.extend(["--cov=ai_ffmpeg_cli", "--cov-report=term-missing"])
        if args.html:
            cmd.append("--cov-report=html")

    # Add speed filters
    if args.fast:
        cmd.append("-m fast")
    elif args.slow:
        cmd.append("-m slow")

    # Add other options
    if args.verbose:
        cmd.append("-v")

    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])

    if args.failed_first:
        cmd.append("--ff")

    cmd.extend(["--tb", args.tb])

    # Run the command
    success = run_command(cmd, f"{args.category.title()} Tests")

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
