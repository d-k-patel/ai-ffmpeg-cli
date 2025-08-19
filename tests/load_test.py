#!/usr/bin/env python3
"""Load testing script for ai-ffmpeg-cli."""

import argparse
import concurrent.futures
import time

from ai_ffmpeg_cli.intent_router import route_intent
from ai_ffmpeg_cli.nl_schema import Action
from ai_ffmpeg_cli.nl_schema import FfmpegIntent


def simulate_user_operation(user_id: int, operation_type: str = "convert"):
    """Simulate a single user operation."""
    start_time = time.time()

    try:
        # Simulate different types of operations
        if operation_type == "convert":
            intent = FfmpegIntent(
                action=Action.convert,
                inputs=[f"video_{user_id}.mp4"],
                output=f"output_{user_id}.mp4",
                scale="720p",
            )
        elif operation_type == "compress":
            intent = FfmpegIntent(
                action=Action.compress,
                inputs=[f"video_{user_id}.mp4"],
                output=f"compressed_{user_id}.mp4",
                crf=28,
            )
        elif operation_type == "extract":
            intent = FfmpegIntent(
                action=Action.extract_audio,
                inputs=[f"video_{user_id}.mp4"],
                output=f"audio_{user_id}.mp3",
            )
        else:
            intent = FfmpegIntent(
                action=Action.convert,
                inputs=[f"video_{user_id}.mp4"],
                output=f"output_{user_id}.mp4",
            )

        # Route the intent (this is the main operation we're testing)
        route_intent(intent)

        end_time = time.time()
        duration = end_time - start_time

        return {
            "user_id": user_id,
            "operation": operation_type,
            "duration": duration,
            "success": True,
            "error": None,
        }

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time

        return {
            "user_id": user_id,
            "operation": operation_type,
            "duration": duration,
            "success": False,
            "error": str(e),
        }


def run_concurrent_load_test(num_users: int, duration: int, operation_type: str = "convert"):
    """Run a concurrent load test."""
    print(f"Starting load test with {num_users} concurrent users for {duration} seconds...")
    print(f"Operation type: {operation_type}")

    start_time = time.time()
    results = []

    # Create a thread pool for concurrent operations
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
        # Submit all tasks
        future_to_user = {
            executor.submit(simulate_user_operation, i, operation_type): i for i in range(num_users)
        }

        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_user):
            result = future.result()
            results.append(result)

    end_time = time.time()
    total_duration = end_time - start_time

    # Analyze results
    successful_operations = [r for r in results if r["success"]]
    failed_operations = [r for r in results if not r["success"]]

    if successful_operations:
        avg_duration = sum(r["duration"] for r in successful_operations) / len(
            successful_operations
        )
        min_duration = min(r["duration"] for r in successful_operations)
        max_duration = max(r["duration"] for r in successful_operations)
    else:
        avg_duration = min_duration = max_duration = 0

    # Print results
    print("\n=== Load Test Results ===")
    print(f"Total duration: {total_duration:.2f} seconds")
    print(f"Total operations: {len(results)}")
    print(f"Successful operations: {len(successful_operations)}")
    print(f"Failed operations: {len(failed_operations)}")
    print(f"Success rate: {len(successful_operations) / len(results) * 100:.1f}%")

    if successful_operations:
        print(f"Average operation duration: {avg_duration:.3f} seconds")
        print(f"Min operation duration: {min_duration:.3f} seconds")
        print(f"Max operation duration: {max_duration:.3f} seconds")
        print(f"Operations per second: {len(successful_operations) / total_duration:.2f}")

    if failed_operations:
        print("\nFailed operations:")
        for result in failed_operations:
            print(f"  User {result['user_id']}: {result['error']}")

    return {
        "total_operations": len(results),
        "successful_operations": len(successful_operations),
        "failed_operations": len(failed_operations),
        "success_rate": len(successful_operations) / len(results) if results else 0,
        "avg_duration": avg_duration,
        "total_duration": total_duration,
        "operations_per_second": (
            len(successful_operations) / total_duration if total_duration > 0 else 0
        ),
    }


def run_sustained_load_test(num_users: int, duration: int, operation_type: str = "convert"):
    """Run a sustained load test over time."""
    print(f"Starting sustained load test with {num_users} users for {duration} seconds...")

    start_time = time.time()
    all_results = []

    while time.time() - start_time < duration:
        batch_start = time.time()

        # Run a batch of concurrent operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [
                executor.submit(simulate_user_operation, i, operation_type)
                for i in range(num_users)
            ]

            batch_results = [future.result() for future in concurrent.futures.as_completed(futures)]
            all_results.extend(batch_results)

        batch_duration = time.time() - batch_start
        print(f"Batch completed in {batch_duration:.2f}s - Total operations: {len(all_results)}")

        # Small delay between batches
        time.sleep(0.1)

    total_duration = time.time() - start_time
    successful_operations = [r for r in all_results if r["success"]]

    print("\n=== Sustained Load Test Results ===")
    print(f"Total duration: {total_duration:.2f} seconds")
    print(f"Total operations: {len(all_results)}")
    print(f"Successful operations: {len(successful_operations)}")
    print(f"Operations per second: {len(successful_operations) / total_duration:.2f}")

    return {
        "total_operations": len(all_results),
        "successful_operations": len(successful_operations),
        "total_duration": total_duration,
        "operations_per_second": (
            len(successful_operations) / total_duration if total_duration > 0 else 0
        ),
    }


def run_memory_load_test(num_iterations: int = 1000):
    """Run a memory load test to detect memory leaks."""
    import gc

    import psutil

    process = psutil.Process()
    initial_memory = process.memory_info().rss

    print(f"Starting memory load test with {num_iterations} iterations...")
    print(f"Initial memory usage: {initial_memory / 1024 / 1024:.2f} MB")

    for i in range(num_iterations):
        # Simulate typical operations
        intent = FfmpegIntent(
            action=Action.convert, inputs=[f"video_{i}.mp4"], output=f"output_{i}.mp4"
        )

        route_intent(intent)

        # Force garbage collection every 100 iterations
        if i % 100 == 0:
            gc.collect()
            current_memory = process.memory_info().rss
            print(f"Iteration {i}: Memory usage: {current_memory / 1024 / 1024:.2f} MB")

    # Final garbage collection
    gc.collect()
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory

    print("\n=== Memory Load Test Results ===")
    print(f"Final memory usage: {final_memory / 1024 / 1024:.2f} MB")
    print(f"Memory increase: {memory_increase / 1024 / 1024:.2f} MB")
    print(f"Memory increase per iteration: {memory_increase / num_iterations / 1024:.2f} KB")

    if memory_increase > 10 * 1024 * 1024:  # 10MB threshold
        print("⚠️  WARNING: Potential memory leak detected!")
    else:
        print("✅ Memory usage is stable")

    return {
        "initial_memory_mb": initial_memory / 1024 / 1024,
        "final_memory_mb": final_memory / 1024 / 1024,
        "memory_increase_mb": memory_increase / 1024 / 1024,
        "memory_increase_per_iteration_kb": memory_increase / num_iterations / 1024,
    }


def main():
    """Main function for load testing."""
    parser = argparse.ArgumentParser(description="Load testing for ai-ffmpeg-cli")
    parser.add_argument("--concurrent", type=int, default=5, help="Number of concurrent users")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument(
        "--operation",
        choices=["convert", "compress", "extract"],
        default="convert",
        help="Operation type",
    )
    parser.add_argument(
        "--test-type",
        choices=["concurrent", "sustained", "memory"],
        default="concurrent",
        help="Type of load test",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1000,
        help="Number of iterations for memory test",
    )

    args = parser.parse_args()

    print("=== ai-ffmpeg-cli Load Testing ===")
    print(f"Test type: {args.test_type}")
    print(f"Concurrent users: {args.concurrent}")
    print(f"Duration: {args.duration} seconds")
    print(f"Operation: {args.operation}")

    if args.test_type == "concurrent":
        results = run_concurrent_load_test(args.concurrent, args.duration, args.operation)
    elif args.test_type == "sustained":
        results = run_sustained_load_test(args.concurrent, args.duration, args.operation)
    elif args.test_type == "memory":
        results = run_memory_load_test(args.iterations)

    print("\nTest completed successfully!")
    return results


if __name__ == "__main__":
    main()
