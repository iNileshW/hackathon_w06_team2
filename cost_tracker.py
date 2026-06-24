"""Cost tracking for LLM API calls.

Logs each call with model, token counts, and estimated cost.
Prints a summary at the end of a run.
"""

# Approximate costs per 1000 tokens (USD) as of 2025.
# Update these if using different models.
MODEL_COSTS = {
    "gpt-4o": {"prompt": 0.0025, "completion": 0.01},
    "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
}


class CostTracker:
    """Tracks token usage and estimated cost across multiple LLM calls."""

    def __init__(self):
        self.calls = []

    def log_call(self, agent_name: str, model: str, usage) -> dict:
        """Log a single API call.

        Args:
            agent_name: Which agent made the call (e.g., "triage", "compliance").
            model: The model ID used (e.g., "gpt-4o-mini").
            usage: The usage object from the OpenAI response (response.usage).

        Returns:
            A dictionary with the logged call details.
        """
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0

        # TODO: Calculate the estimated cost using MODEL_COSTS.
        # Look up the model in MODEL_COSTS. If the model is not listed,
        # use 0.0 for both prompt and completion cost rates.
        # Cost = (prompt_tokens / 1000) * prompt_rate + (completion_tokens / 1000) * completion_rate
        estimated_cost = 0.0

        entry = {
            "agent": agent_name,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "estimated_cost_usd": estimated_cost,
        }
        self.calls.append(entry)
        return entry

    def summary(self) -> dict:
        """Return a summary of all tracked calls.

        Returns:
            A dictionary with total tokens, total cost, and per-agent breakdown.
        """
        total_prompt = sum(c["prompt_tokens"] for c in self.calls)
        total_completion = sum(c["completion_tokens"] for c in self.calls)
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
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_tokens": total_prompt + total_completion,
            "total_cost_usd": total_cost,
            "by_agent": by_agent,
        }

    def print_summary(self):
        """Print a formatted cost summary to stdout."""
        s = self.summary()
        print("\n--- Cost Summary ---")
        print(f"Total calls: {s['total_calls']}")
        print(f"Total tokens: {s['total_tokens']} (prompt: {s['total_prompt_tokens']}, completion: {s['total_completion_tokens']})")
        print(f"Estimated cost: ${s['total_cost_usd']:.4f}")
        if s["by_agent"]:
            print("\nBy agent:")
            for agent, data in s["by_agent"].items():
                print(f"  {agent}: {data['calls']} calls, {data['tokens']} tokens, ${data['cost_usd']:.4f}")
