"""Token tracking module for ai-ffmpeg-cli.

This module provides functionality to track token usage using tiktoken
and display usage statistics to users.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime

import tiktoken
from rich.console import Console
from rich.table import Table
from rich.text import Text

# Initialize console for Rich output
console = Console()


@dataclass
class TokenUsage:
    """Represents token usage for a single operation."""

    operation: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    timestamp: datetime = field(default_factory=datetime.now)
    cost_estimate: float | None = None

    @property
    def total_cost_estimate(self) -> float | None:
        """Calculate total cost estimate if available."""
        if self.cost_estimate:
            return self.cost_estimate
        return None


@dataclass
class SessionTokenTracker:
    """Tracks token usage for a CLI session."""

    session_id: str
    start_time: datetime = field(default_factory=datetime.now)
    operations: list[TokenUsage] = field(default_factory=list)
    model: str = "gpt-4o"

    def add_operation(self, operation: TokenUsage) -> None:
        """Add a token usage operation to the session."""
        self.operations.append(operation)

    @property
    def total_input_tokens(self) -> int:
        """Get total input tokens for the session."""
        return sum(op.input_tokens for op in self.operations)

    @property
    def total_output_tokens(self) -> int:
        """Get total output tokens for the session."""
        return sum(op.output_tokens for op in self.operations)

    @property
    def total_tokens(self) -> int:
        """Get total tokens for the session."""
        return sum(op.total_tokens for op in self.operations)

    @property
    def total_cost_estimate(self) -> float | None:
        """Get total cost estimate for the session."""
        costs = [op.total_cost_estimate for op in self.operations if op.total_cost_estimate]
        return sum(costs) if costs else None

    @property
    def session_duration(self) -> float:
        """Get session duration in seconds."""
        return (datetime.now() - self.start_time).total_seconds()


class TokenTracker:
    """Main token tracking class."""

    def __init__(self) -> None:
        self.current_session: SessionTokenTracker | None = None
        self.encoding_cache: dict[str, tiktoken.Encoding] = {}

    def start_session(self, session_id: str, model: str = "gpt-4o") -> None:
        """Start a new token tracking session."""
        self.current_session = SessionTokenTracker(session_id=session_id, model=model)

    def get_encoding(self, model: str) -> tiktoken.Encoding:
        """Get tiktoken encoding for a model, with caching."""
        if model not in self.encoding_cache:
            try:
                # Map common model names to their encoding
                if "gpt-4" in model or "gpt-3.5" in model:
                    encoding_name = "cl100k_base"  # GPT-4 and GPT-3.5-turbo
                elif "gpt-3" in model:
                    encoding_name = "r50k_base"  # GPT-3
                else:
                    encoding_name = "cl100k_base"  # Default to GPT-4 encoding

                self.encoding_cache[model] = tiktoken.get_encoding(encoding_name)
            except Exception:
                # Fallback to GPT-4 encoding if model-specific encoding fails
                self.encoding_cache[model] = tiktoken.get_encoding("cl100k_base")

        return self.encoding_cache[model]

    def count_tokens(self, text: str, model: str) -> int:
        """Count tokens in text for a specific model."""
        if not text:
            return 0

        encoding = self.get_encoding(model)
        return len(encoding.encode(text))

    def track_operation(
        self,
        operation: str,
        model: str,
        input_text: str,
        output_text: str,
        cost_estimate: float | None = None,
    ) -> TokenUsage:
        """Track token usage for an operation."""
        if not self.current_session:
            # Create a default session if none exists
            self.start_session("default", model)

        input_tokens = self.count_tokens(input_text, model)
        output_tokens = self.count_tokens(output_text, model)
        total_tokens = input_tokens + output_tokens

        usage = TokenUsage(
            operation=operation,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_estimate=cost_estimate,
        )

        if self.current_session:
            self.current_session.add_operation(usage)
        return usage

    def display_session_summary(self) -> None:
        """Display a summary of token usage for the current session."""
        if not self.current_session or not self.current_session.operations:
            return

        session = self.current_session

        # Create summary table
        summary_table = Table(
            title="[bold cyan]Token Usage Summary[/bold cyan]",
            show_header=True,
            header_style="bold blue",
        )
        summary_table.add_column("Metric", style="bold cyan")
        summary_table.add_column("Value", style="white", justify="right")
        summary_table.add_column("Details", style="dim")

        # Session info
        summary_table.add_row(
            "Session ID",
            session.session_id,
            f"Started at {session.start_time.strftime('%H:%M:%S')}",
        )

        summary_table.add_row("Duration", f"{session.session_duration:.1f}s", "Session duration")

        summary_table.add_row(
            "Operations", str(len(session.operations)), "Total operations performed"
        )

        # Token counts
        summary_table.add_row(
            "Input Tokens", f"{session.total_input_tokens:,}", "Total tokens sent to AI"
        )

        summary_table.add_row(
            "Output Tokens",
            f"{session.total_output_tokens:,}",
            "Total tokens received from AI",
        )

        summary_table.add_row(
            "Total Tokens", f"{session.total_tokens:,}", "Combined input + output"
        )

        # Cost estimate if available
        if session.total_cost_estimate:
            summary_table.add_row(
                "Estimated Cost",
                f"${session.total_cost_estimate:.4f}",
                "Based on OpenAI pricing",
            )

        console.print(summary_table)
        console.print()

    def display_detailed_usage(self) -> None:
        """Display detailed token usage for each operation."""
        if not self.current_session or not self.current_session.operations:
            return

        # Create detailed operations table
        operations_table = Table(
            title="[bold green]Detailed Token Usage[/bold green]",
            show_header=True,
            header_style="bold blue",
        )
        operations_table.add_column("#", style="bold cyan", justify="center")
        operations_table.add_column("Operation", style="bold white")
        operations_table.add_column("Model", style="cyan")
        operations_table.add_column("Input", style="green", justify="right")
        operations_table.add_column("Output", style="yellow", justify="right")
        operations_table.add_column("Total", style="bold", justify="right")
        operations_table.add_column("Time", style="dim")

        for i, operation in enumerate(self.current_session.operations, 1):
            operations_table.add_row(
                str(i),
                operation.operation,
                operation.model,
                f"{operation.input_tokens:,}",
                f"{operation.output_tokens:,}",
                f"{operation.total_tokens:,}",
                operation.timestamp.strftime("%H:%M:%S"),
            )

        console.print(operations_table)
        console.print()

    def get_cost_estimate(self, model: str, input_tokens: int, output_tokens: int) -> float | None:
        """Get cost estimate for token usage based on OpenAI pricing."""
        # OpenAI pricing (as of 2024, approximate)
        pricing = {
            "gpt-4o": {"input": 0.0025, "output": 0.01},  # per 1K tokens
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        }

        # Find the closest model match
        model_key = None
        for key in pricing:
            if key in model.lower():
                model_key = key
                break

        if not model_key:
            return None

        input_cost = (input_tokens / 1000) * pricing[model_key]["input"]
        output_cost = (output_tokens / 1000) * pricing[model_key]["output"]

        return input_cost + output_cost

    def display_realtime_usage(self, operation: TokenUsage) -> None:
        """Display real-time token usage for an operation."""
        usage_text = Text()
        usage_text.append("📊 ", style="bold cyan")
        usage_text.append(f"{operation.operation}: ", style="bold white")
        usage_text.append(f"{operation.input_tokens:,} → {operation.output_tokens:,} ", style="dim")
        usage_text.append(f"({operation.total_tokens:,} total)", style="green")

        if operation.total_cost_estimate:
            usage_text.append(f" | ${operation.total_cost_estimate:.4f}", style="yellow")

        console.print(usage_text)
