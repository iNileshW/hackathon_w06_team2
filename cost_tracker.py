"""Cost tracking for LLM API calls.

Logs each call with model, token counts, and estimated cost.
Prints a summary at the end of a run.
"""

# Approximate costs per 1000 tokens (USD) as of 2025.
# Update these if using different models.
MODEL_COSTS = {
    "claude-sonnet-4-5": {"input": 0.003, "output": 0.015},
    "claude-haiku-4-5": {"input": 0.001, "output": 0.005},
}


class CostTracker:
    """Tracks token usage and estimated cost across multiple LLM calls."""

    def __init__(self):
        self.calls = []

    def log_call(self, agent_name: str, model: str, usage) -> dict:
        """Log a single API call.

        Args:
            agent_name: Which agent made the call (e.g., "triage", "compliance").
            model: The model ID used (e.g., "claude-sonnet-4-5").
            usage: The usage_metadata dict from a LangChain AIMessage response
                (response.usage_metadata), with "input_tokens" and
                "output_tokens" keys.

        Returns:
            A dictionary with the logged call details.
        """
        usage = usage or {}
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)

        # TODO: Calculate the estimated cost using MODEL_COSTS.
        # Look up the model in MODEL_COSTS. If the model is not listed,
        # use 0.0 for both input and output cost rates.
        # Cost = (input_tokens / 1000) * input_rate + (output_tokens / 1000) * output_rate
        estimated_cost = 0.0

        entry = {
            "agent": agent_name,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "estimated_cost_usd": estimated_cost,
        }
        self.calls.append(entry)
        return entry

    def summary(self) -> dict:
        """Return a summary of all tracked calls.

        Returns:
            A dictionary with total tokens, total cost, and per-agent breakdown.
        """
        total_input = sum(c["input_tokens"] for c in self.calls)
        total_output = sum(c["output_tokens"] for c in self.calls)
        total_cost = sum(c["estimated_cost_usd"] for c in self.calls)

        by_agent = {}
        for call in self.calls:
            agent = call["agent"]
            if agent not in by_agent:
                by_agent[agent] = {"calls": 0, "tokens": 0, "cost_usd": 0.0}
            by_agent[agent]["calls"] += 1
            by_agent[agent]["tokens"] += call["total_tokens"]
            by_agent[agent]["cost_usd"] += call["estimated_cost_usd"]

        return {
            "total_calls": len(self.calls),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "total_cost_usd": total_cost,
            "by_agent": by_agent,
        }

    def print_summary(self):
        """Print a formatted cost summary to stdout."""
        s = self.summary()
        print("\n--- Cost Summary ---")
        print(f"Total calls: {s['total_calls']}")
        print(
            f"Total tokens: {s['total_tokens']} (input: {s['total_input_tokens']}, output: {s['total_output_tokens']})"
        )
        print(f"Estimated cost: ${s['total_cost_usd']:.4f}")
        if s["by_agent"]:
            print("\nBy agent:")
            for agent, data in s["by_agent"].items():
                print(
                    f"  {agent}: {data['calls']} calls, {data['tokens']} tokens, ${data['cost_usd']:.4f}"
                )