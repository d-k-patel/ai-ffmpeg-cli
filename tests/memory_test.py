#!/usr/bin/env python3
"""Memory testing script for ai-ffmpeg-cli.

This module provides comprehensive memory leak detection for the ai-ffmpeg-cli package.
It tests various scenarios including basic operations, large file lists, concurrent
operations, long-running processes, and error conditions.

Key assumptions:
- Memory increases >5MB indicate potential leaks (basic/concurrent/error tests)
- Memory increases >10MB indicate potential leaks (large file lists)
- psutil is available for memory monitoring
- Garbage collection is forced periodically to isolate memory issues
"""

import gc
import time

import psutil

from ai_ffmpeg_cli.intent_router import route_intent
from ai_ffmpeg_cli.nl_schema import Action
from ai_ffmpeg_cli.nl_schema import FfmpegIntent


def monitor_memory_usage():
    """Monitor current memory usage of the current process.

    Returns:
        dict: Memory usage statistics with keys:
            - rss_mb: Resident Set Size in MB (actual physical memory)
            - vms_mb: Virtual Memory Size in MB (total virtual memory)
            - percent: Memory usage as percentage of system total
    """
    process = psutil.Process()
    memory_info = process.memory_info()
    return {
        "rss_mb": memory_info.rss / 1024 / 1024,
        "vms_mb": memory_info.vms / 1024 / 1024,
        "percent": process.memory_percent(),
    }


def test_memory_leak_basic_operations():
    """Test for memory leaks in basic intent routing operations.

    Performs 100 consecutive intent routing operations with periodic garbage
    collection to detect memory leaks in the core routing logic.

    Returns:
        bool: True if memory increase is within acceptable limits (<5MB)

    Raises:
        AssertionError: If memory increase exceeds 5MB threshold
    """
    print("Testing memory usage in basic operations...")

    initial_memory = monitor_memory_usage()
    print(f"Initial memory: {initial_memory['rss_mb']:.2f} MB")

    # Perform multiple operations to stress test memory management
    for i in range(100):
        intent = FfmpegIntent(
            action=Action.convert, inputs=[f"video_{i}.mp4"], output=f"output_{i}.mp4"
        )

        route_intent(intent)

        # Force garbage collection every 10 operations to isolate memory issues
        # This helps distinguish between temporary allocations and actual leaks
        if i % 10 == 0:
            gc.collect()
            current_memory = monitor_memory_usage()
            print(f"Operation {i}: {current_memory['rss_mb']:.2f} MB")

    # Final garbage collection to measure true memory footprint
    gc.collect()
    final_memory = monitor_memory_usage()

    memory_increase = final_memory["rss_mb"] - initial_memory["rss_mb"]
    print(f"Final memory: {final_memory['rss_mb']:.2f} MB")
    print(f"Memory increase: {memory_increase:.2f} MB")

    # 5MB threshold accounts for Python's memory management overhead
    # and small object allocations that may persist between operations
    assert memory_increase < 5, f"Memory increase too high: {memory_increase} MB"

    return True


def test_memory_usage_large_files():
    """Test memory usage when processing large file lists.

    Creates a large list of 10,000 files and processes the first 100 to test
    memory efficiency when handling large input datasets.

    Returns:
        bool: True if memory increase is within acceptable limits (<10MB)

    Raises:
        AssertionError: If memory increase exceeds 10MB threshold
    """
    print("Testing memory usage with large file lists...")

    initial_memory = monitor_memory_usage()
    print(f"Initial memory: {initial_memory['rss_mb']:.2f} MB")

    # Create large file list to test memory efficiency with big datasets
    # Processing only first 100 files to keep test duration reasonable
    large_file_list = [f"video_{i}.mp4" for i in range(10000)]

    # Process the large list
    intent = FfmpegIntent(
        action=Action.convert,
        inputs=large_file_list[:100],  # Use first 100 files
        output="output.mp4",
    )

    route_intent(intent)

    gc.collect()
    final_memory = monitor_memory_usage()

    memory_increase = final_memory["rss_mb"] - initial_memory["rss_mb"]
    print(f"Final memory: {final_memory['rss_mb']:.2f} MB")
    print(f"Memory increase: {memory_increase:.2f} MB")

    # Higher threshold (10MB) for large file lists due to string storage overhead
    # and potential temporary data structures during processing
    assert memory_increase < 10, f"Memory increase too high: {memory_increase} MB"

    return True


def test_memory_usage_concurrent_operations():
    """Test memory usage under concurrent threading operations.

    Creates 10 concurrent threads, each performing intent routing operations
    to detect memory leaks in multi-threaded scenarios.

    Returns:
        bool: True if memory increase is within acceptable limits (<5MB)

    Raises:
        AssertionError: If memory increase exceeds 5MB threshold
    """
    import threading

    print("Testing memory usage under concurrent operations...")

    initial_memory = monitor_memory_usage()
    print(f"Initial memory: {initial_memory['rss_mb']:.2f} MB")

    # Shared results list to track thread outcomes
    results = []

    def worker(worker_id):
        """Worker function for concurrent testing.

        Args:
            worker_id: Unique identifier for this worker thread
        """
        try:
            intent = FfmpegIntent(
                action=Action.convert,
                inputs=[f"video_{worker_id}.mp4"],
                output=f"output_{worker_id}.mp4",
            )

            route_intent(intent)
            results.append(f"worker_{worker_id}_success")
        except Exception as e:
            results.append(f"worker_{worker_id}_error: {e}")

    # Create multiple threads to test concurrent memory usage
    # 10 threads provide good coverage without overwhelming the system
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]

    # Start all threads simultaneously
    for thread in threads:
        thread.start()

    # Wait for all threads to complete before measuring memory
    for thread in threads:
        thread.join()

    gc.collect()
    final_memory = monitor_memory_usage()

    memory_increase = final_memory["rss_mb"] - initial_memory["rss_mb"]
    print(f"Final memory: {final_memory['rss_mb']:.2f} MB")
    print(f"Memory increase: {memory_increase:.2f} MB")
    print(f"Successful operations: {len([r for r in results if 'success' in r])}")

    # 5MB threshold for concurrent operations accounts for thread overhead
    # and potential temporary allocations during parallel processing
    assert memory_increase < 5, f"Memory increase too high: {memory_increase} MB"

    return True


def test_memory_usage_long_running():
    """Test memory usage in long-running operations with time delays.

    Performs 1000 operations with small time delays to simulate real-world
    usage patterns and detect memory leaks that may occur over time.

    Returns:
        bool: True if memory increase is within acceptable limits (<5MB)

    Raises:
        AssertionError: If memory increase exceeds 5MB threshold
    """
    print("Testing memory usage in long-running operations...")

    initial_memory = monitor_memory_usage()
    print(f"Initial memory: {initial_memory['rss_mb']:.2f} MB")

    # Simulate long-running operations with realistic timing
    for i in range(1000):
        intent = FfmpegIntent(
            action=Action.convert, inputs=[f"video_{i}.mp4"], output=f"output_{i}.mp4"
        )

        route_intent(intent)

        # Simulate some processing time to test memory over extended periods
        # 1ms delay provides realistic timing without making test too slow
        time.sleep(0.001)

        # Check memory every 100 operations to monitor trends
        if i % 100 == 0:
            gc.collect()
            current_memory = monitor_memory_usage()
            print(f"Operation {i}: {current_memory['rss_mb']:.2f} MB")

    gc.collect()
    final_memory = monitor_memory_usage()

    memory_increase = final_memory["rss_mb"] - initial_memory["rss_mb"]
    print(f"Final memory: {final_memory['rss_mb']:.2f} MB")
    print(f"Memory increase: {memory_increase:.2f} MB")

    # 5MB threshold for long-running operations accounts for gradual
    # memory accumulation that may occur over extended periods
    assert memory_increase < 5, f"Memory increase too high: {memory_increase} MB"

    return True


def test_memory_usage_error_conditions():
    """Test memory usage under error conditions and exception handling.

    Performs 100 operations with simulated errors every 10th iteration
    to ensure memory is properly cleaned up after exceptions.

    Returns:
        bool: True if memory increase is within acceptable limits (<5MB)

    Raises:
        AssertionError: If memory increase exceeds 5MB threshold
    """
    print("Testing memory usage under error conditions...")

    initial_memory = monitor_memory_usage()
    print(f"Initial memory: {initial_memory['rss_mb']:.2f} MB")

    # Simulate operations that might fail to test exception handling
    for i in range(100):
        try:
            # Create an intent that might cause issues
            intent = FfmpegIntent(
                action=Action.convert,
                inputs=[f"video_{i}.mp4"],
                output=f"output_{i}.mp4",
            )

            route_intent(intent)

            # Simulate occasional errors to test memory cleanup in exception paths
            # Every 10th operation raises an error to test exception handling
            if i % 10 == 0:
                raise ValueError(f"Simulated error at iteration {i}")

        except ValueError:
            # Handle the error - this tests memory cleanup in exception handlers
            pass

        # Force garbage collection every 20 operations to isolate memory issues
        # More frequent GC helps detect leaks in error handling paths
        if i % 20 == 0:
            gc.collect()
            current_memory = monitor_memory_usage()
            print(f"Operation {i}: {current_memory['rss_mb']:.2f} MB")

    gc.collect()
    final_memory = monitor_memory_usage()

    memory_increase = final_memory["rss_mb"] - initial_memory["rss_mb"]
    print(f"Final memory: {final_memory['rss_mb']:.2f} MB")
    print(f"Memory increase: {memory_increase:.2f} MB")

    # 5MB threshold for error conditions ensures proper cleanup after exceptions
    # and prevents memory leaks in error handling code paths
    assert memory_increase < 5, f"Memory increase too high: {memory_increase} MB"

    return True


def main():
    """Run all memory tests and provide a comprehensive summary.

    Executes all memory test scenarios and reports pass/fail status
    for each test. Provides overall assessment of memory management.

    Returns:
        int: Exit code (0 for success, 1 for failures)
    """
    print("=== ai-ffmpeg-cli Memory Testing ===")

    # Define test suite with descriptive names and corresponding functions
    tests = [
        ("Basic Operations", test_memory_leak_basic_operations),
        ("Large File Lists", test_memory_usage_large_files),
        ("Concurrent Operations", test_memory_usage_concurrent_operations),
        ("Long Running", test_memory_usage_long_running),
        ("Error Conditions", test_memory_usage_error_conditions),
    ]

    results = {}

    # Execute each test and capture results
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            success = test_func()
            results[test_name] = "PASS" if success else "FAIL"
            print(f"Result: {results[test_name]}")
        except Exception as e:
            results[test_name] = f"ERROR: {e}"
            print(f"Result: {results[test_name]}")

    print("\n=== Memory Test Summary ===")
    for test_name, result in results.items():
        print(f"{test_name}: {result}")

    # Calculate overall test success rate
    passed_tests = sum(1 for result in results.values() if result == "PASS")
    total_tests = len(results)

    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("✅ All memory tests passed!")
        return 0
    else:
        print("⚠️  Some memory tests failed!")
        return 1


if __name__ == "__main__":
    exit(main())
