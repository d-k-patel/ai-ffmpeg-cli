#!/usr/bin/env python3
"""Memory testing script for ai-ffmpeg-cli."""

import gc
import time

import psutil

from ai_ffmpeg_cli.intent_router import route_intent
from ai_ffmpeg_cli.nl_schema import Action
from ai_ffmpeg_cli.nl_schema import FfmpegIntent


def monitor_memory_usage():
    """Monitor current memory usage."""
    process = psutil.Process()
    memory_info = process.memory_info()
    return {
        "rss_mb": memory_info.rss / 1024 / 1024,
        "vms_mb": memory_info.vms / 1024 / 1024,
        "percent": process.memory_percent(),
    }


def test_memory_leak_basic_operations():
    """Test for memory leaks in basic operations."""
    print("Testing memory usage in basic operations...")

    initial_memory = monitor_memory_usage()
    print(f"Initial memory: {initial_memory['rss_mb']:.2f} MB")

    # Perform multiple operations
    for i in range(100):
        intent = FfmpegIntent(
            action=Action.convert, inputs=[f"video_{i}.mp4"], output=f"output_{i}.mp4"
        )

        route_intent(intent)

        # Force garbage collection every 10 operations
        if i % 10 == 0:
            gc.collect()
            current_memory = monitor_memory_usage()
            print(f"Operation {i}: {current_memory['rss_mb']:.2f} MB")

    # Final garbage collection
    gc.collect()
    final_memory = monitor_memory_usage()

    memory_increase = final_memory["rss_mb"] - initial_memory["rss_mb"]
    print(f"Final memory: {final_memory['rss_mb']:.2f} MB")
    print(f"Memory increase: {memory_increase:.2f} MB")

    assert memory_increase < 10, (
        f"Memory increase too high: {memory_increase} MB"
    )  # Should be less than 10MB


def test_memory_usage_large_files():
    """Test memory usage with large file lists."""
    print("Testing memory usage with large file lists...")

    initial_memory = monitor_memory_usage()
    print(f"Initial memory: {initial_memory['rss_mb']:.2f} MB")

    # Create large file lists
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

    assert memory_increase < 50, (
        f"Memory increase too high: {memory_increase} MB"
    )  # Should be less than 50MB for large lists


def test_memory_usage_concurrent_operations():
    """Test memory usage under concurrent operations."""
    import threading

    print("Testing memory usage under concurrent operations...")

    initial_memory = monitor_memory_usage()
    print(f"Initial memory: {initial_memory['rss_mb']:.2f} MB")

    results = []

    def worker(worker_id):
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

    # Create multiple threads
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    gc.collect()
    final_memory = monitor_memory_usage()

    memory_increase = final_memory["rss_mb"] - initial_memory["rss_mb"]
    print(f"Final memory: {final_memory['rss_mb']:.2f} MB")
    print(f"Memory increase: {memory_increase:.2f} MB")
    print(f"Successful operations: {len([r for r in results if 'success' in r])}")

    assert memory_increase < 20, (
        f"Memory increase too high: {memory_increase} MB"
    )  # Should be less than 20MB


def test_memory_usage_long_running():
    """Test memory usage in long-running operations."""
    print("Testing memory usage in long-running operations...")

    initial_memory = monitor_memory_usage()
    print(f"Initial memory: {initial_memory['rss_mb']:.2f} MB")

    # Simulate long-running operations
    for i in range(1000):
        intent = FfmpegIntent(
            action=Action.convert, inputs=[f"video_{i}.mp4"], output=f"output_{i}.mp4"
        )

        route_intent(intent)

        # Simulate some processing time
        time.sleep(0.001)

        # Check memory every 100 operations
        if i % 100 == 0:
            gc.collect()
            current_memory = monitor_memory_usage()
            print(f"Operation {i}: {current_memory['rss_mb']:.2f} MB")

    gc.collect()
    final_memory = monitor_memory_usage()

    memory_increase = final_memory["rss_mb"] - initial_memory["rss_mb"]
    print(f"Final memory: {final_memory['rss_mb']:.2f} MB")
    print(f"Memory increase: {memory_increase:.2f} MB")

    assert memory_increase < 30, (
        f"Memory increase too high: {memory_increase} MB"
    )  # Should be less than 30MB


def test_memory_usage_error_conditions():
    """Test memory usage under error conditions."""
    print("Testing memory usage under error conditions...")

    initial_memory = monitor_memory_usage()
    print(f"Initial memory: {initial_memory['rss_mb']:.2f} MB")

    # Simulate operations that might fail
    for i in range(100):
        try:
            # Create an intent that might cause issues
            intent = FfmpegIntent(
                action=Action.convert,
                inputs=[f"video_{i}.mp4"],
                output=f"output_{i}.mp4",
            )

            route_intent(intent)

            # Simulate occasional errors
            if i % 10 == 0:
                raise ValueError(f"Simulated error at iteration {i}")

        except ValueError:
            # Handle the error
            pass

        # Force garbage collection every 20 operations
        if i % 20 == 0:
            gc.collect()
            current_memory = monitor_memory_usage()
            print(f"Operation {i}: {current_memory['rss_mb']:.2f} MB")

    gc.collect()
    final_memory = monitor_memory_usage()

    memory_increase = final_memory["rss_mb"] - initial_memory["rss_mb"]
    print(f"Final memory: {final_memory['rss_mb']:.2f} MB")
    print(f"Memory increase: {memory_increase:.2f} MB")

    assert memory_increase < 15, (
        f"Memory increase too high: {memory_increase} MB"
    )  # Should be less than 15MB


def main():
    """Run all memory tests."""
    print("=== ai-ffmpeg-cli Memory Testing ===")

    tests = [
        ("Basic Operations", test_memory_leak_basic_operations),
        ("Large File Lists", test_memory_usage_large_files),
        ("Concurrent Operations", test_memory_usage_concurrent_operations),
        ("Long Running", test_memory_usage_long_running),
        ("Error Conditions", test_memory_usage_error_conditions),
    ]

    results = {}

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

    # Overall assessment
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
