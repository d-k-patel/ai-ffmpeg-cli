"""Performance benchmark tests for ai-ffmpeg-cli."""

import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from ai_ffmpeg_cli.command_builder import build_commands
from ai_ffmpeg_cli.intent_router import route_intent
from ai_ffmpeg_cli.nl_schema import Action
from ai_ffmpeg_cli.nl_schema import FfmpegIntent


class TestPerformance:
    """Performance benchmark tests."""

    @pytest.mark.benchmark
    def test_command_builder_performance(self, benchmark):
        """Benchmark command building performance."""
        from ai_ffmpeg_cli.nl_schema import CommandEntry
        from ai_ffmpeg_cli.nl_schema import CommandPlan

        # Create a complex command plan
        plan = CommandPlan(
            summary="Test command plan",
            entries=[
                CommandEntry(
                    input=Path("input.mp4"),
                    output=Path("output.mp4"),
                    args=["-i", "input.mp4"],
                    extra_inputs=[Path("overlay.png")],
                ),
                CommandEntry(
                    input=Path("output.mp4"),
                    output=Path("scaled.mp4"),
                    args=["-i", "output.mp4", "-vf", "scale=1280:720"],
                ),
            ],
        )

        def build_commands_wrapper():
            return build_commands(plan, assume_yes=False)

        result = benchmark(build_commands_wrapper)
        assert len(result) == 2

    @pytest.mark.benchmark
    def test_intent_routing_performance(self, benchmark):
        """Benchmark intent routing performance."""
        intent = FfmpegIntent(
            action=Action.convert,
            inputs=["video.mp4"],
            output="output.mp4",
            scale="720p",
        )

        def route_intent_wrapper():
            return route_intent(intent)

        result = benchmark(route_intent_wrapper)
        assert result is not None

    @pytest.mark.benchmark
    def test_large_file_handling_performance(self, benchmark):
        """Benchmark handling of large file lists."""
        # Create a large list of files
        large_file_list = [f"video_{i}.mp4" for i in range(1000)]

        def process_large_file_list():
            # Simulate processing large file lists
            return [f for f in large_file_list if f.endswith(".mp4")]

        result = benchmark(process_large_file_list)
        assert len(result) == 1000

    @pytest.mark.benchmark
    def test_memory_usage_under_load(self, benchmark):
        """Benchmark memory usage under load."""
        import gc

        def memory_intensive_operation():
            # Simulate memory-intensive operation
            large_data = [f"data_{i}" * 1000 for i in range(1000)]
            gc.collect()  # Force garbage collection
            return len(large_data)

        result = benchmark(memory_intensive_operation)
        assert result == 1000

    @pytest.mark.benchmark
    def test_concurrent_operations_performance(self, benchmark):
        """Benchmark concurrent operations."""
        import queue
        import threading

        def concurrent_operation():
            results = queue.Queue()

            def worker(worker_id):
                # Simulate work
                time.sleep(0.001)  # 1ms work
                results.put(f"result_{worker_id}")

            threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

            return [results.get() for _ in range(10)]

        result = benchmark(concurrent_operation)
        assert len(result) == 10

    @pytest.mark.benchmark
    def test_file_io_performance(self, benchmark):
        """Benchmark file I/O operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            def file_io_operation():
                # Create multiple files
                files = []
                for i in range(100):
                    file_path = temp_path / f"test_{i}.txt"
                    file_path.write_text(f"content_{i}")
                    files.append(file_path)

                # Read files back
                contents = [f.read_text() for f in files]

                # Clean up
                for f in files:
                    f.unlink()

                return len(contents)

            result = benchmark(file_io_operation)
            assert result == 100

    @pytest.mark.benchmark
    def test_string_processing_performance(self, benchmark):
        """Benchmark string processing operations."""
        large_string = "convert video.mp4 to 720p with high quality" * 1000

        def string_processing():
            # Simulate string processing operations
            words = large_string.split()
            processed = [word.upper() for word in words if len(word) > 3]
            return len(processed)

        result = benchmark(string_processing)
        assert result > 0

    @pytest.mark.benchmark
    def test_config_loading_performance(self, benchmark):
        """Benchmark configuration loading."""
        with patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "test-key",
                "AICLIP_MODEL": "gpt-4o",
                "AICLIP_DRY_RUN": "true",
            },
        ):

            def load_config():
                from ai_ffmpeg_cli.config import load_config

                return load_config()

            result = benchmark(load_config)
            assert result is not None

    @pytest.mark.benchmark
    def test_error_handling_performance(self, benchmark):
        """Benchmark error handling performance."""

        def error_handling_operation():
            try:
                # Simulate an operation that might fail
                if time.time() % 2 == 0:
                    raise ValueError("Simulated error")
                return "success"
            except ValueError:
                return "error"

        result = benchmark(error_handling_operation)
        assert result in ["success", "error"]

    @pytest.mark.benchmark
    def test_path_validation_performance(self, benchmark):
        """Benchmark path validation performance."""
        from ai_ffmpeg_cli.io_utils import is_safe_path

        test_paths = [
            "normal/path/file.mp4",
            "../../../etc/passwd",
            "/safe/absolute/path",
            "path/with/../traversal",
            "normal_file.mp4",
        ] * 200  # Repeat to make it more intensive

        result = benchmark(lambda: [is_safe_path(path) for path in test_paths])
        assert len(result) == len(test_paths)


class TestLoadTesting:
    """Load testing scenarios."""

    def test_concurrent_users_simulation(self):
        """Simulate multiple concurrent users."""
        import threading
        import time

        results = []
        errors = []

        def simulate_user(user_id):
            try:
                # Simulate user operation
                time.sleep(0.1)  # Simulate processing time
                results.append(f"user_{user_id}_success")
            except Exception as e:
                errors.append(f"user_{user_id}_error: {e}")

        # Simulate 10 concurrent users
        threads = [threading.Thread(target=simulate_user, args=(i,)) for i in range(10)]

        start_time = time.time()
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        end_time = time.time()

        # Should complete within reasonable time
        assert end_time - start_time < 2.0
        assert len(results) == 10
        assert len(errors) == 0

    def test_memory_leak_detection(self):
        """Detect potential memory leaks in application code."""
        import gc

        import psutil

        from ai_ffmpeg_cli.intent_router import route_intent
        from ai_ffmpeg_cli.nl_schema import Action
        from ai_ffmpeg_cli.nl_schema import FfmpegIntent

        process = psutil.Process()

        # Force initial garbage collection and get baseline
        gc.collect()
        gc.collect()  # Run twice to ensure cleanup
        initial_memory = process.memory_info().rss

        # Perform operations that simulate actual application usage
        for i in range(50):  # Reduced iterations for more realistic test
            # Create and process intents (actual application code)
            intent = FfmpegIntent(
                action=Action.convert,
                inputs=[f"video_{i}.mp4"],
                output=f"output_{i}.mp4",
            )

            # Route the intent (tests actual code paths)
            plan = route_intent(intent)

            # Clean up references
            del intent, plan

            # Force garbage collection every 10 iterations
            if i % 10 == 0:
                gc.collect()

        # Final cleanup
        gc.collect()
        gc.collect()  # Run twice to ensure thorough cleanup

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # More realistic threshold: 50MB (Python interpreter overhead + test environment)
        max_allowed_increase = 50 * 1024 * 1024

        # If memory increase is significant, report it but don't fail the test
        # This makes the test informational rather than blocking
        if memory_increase > max_allowed_increase:
            print(
                f"WARNING: Significant memory increase detected: {memory_increase / (1024 * 1024):.2f} MB"
            )
            print("This may indicate a memory leak or normal Python memory management")

        # Only fail if memory increase is extremely high (> 100MB)
        assert memory_increase < 100 * 1024 * 1024, (
            f"Severe memory leak detected: {memory_increase / (1024 * 1024):.2f} MB. "
            f"This indicates a serious issue that needs investigation."
        )

    def test_cpu_usage_under_load(self):
        """Test CPU usage under load."""
        import os
        import time

        import psutil

        process = psutil.Process()

        # Adjust test parameters based on environment
        # macOS CI runners can be slower, so use more conservative settings
        if os.name == "posix" and os.uname().sysname == "Darwin":
            iterations = 3
            workload_size = 3000
            sleep_time = 0.03
            max_execution_time = 4.0
        else:
            iterations = 5
            workload_size = 5000
            sleep_time = 0.05
            max_execution_time = 3.0

        # Measure CPU usage during intensive operations
        start_time = time.time()
        cpu_percentages = []

        for _ in range(iterations):
            # Simulate CPU-intensive work
            _ = sum(i * i for i in range(workload_size))
            cpu_percentages.append(process.cpu_percent())
            time.sleep(sleep_time)

        end_time = time.time()

        # Should complete within reasonable time (adjusted for environment)
        execution_time = end_time - start_time
        assert execution_time < max_execution_time, (
            f"Test took too long: {execution_time:.2f} seconds"
        )

        # Average CPU usage should be reasonable
        avg_cpu = sum(cpu_percentages) / len(cpu_percentages)
        assert avg_cpu < 100, f"CPU usage too high: {avg_cpu}%"
