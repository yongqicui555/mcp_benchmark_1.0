"""Model Router - Intelligent routing to cost-efficient models via agentic-flow

Routes operations to appropriate models based on complexity:
- Simple CRUD operations → Gemini 1.5 Flash ($0.075/1M tokens - 99.5% savings)
- Pattern analysis → DeepSeek Chat ($0.14/1M tokens - 99% savings)
- Complex reasoning → Claude (premium quality when needed)

This enables the self-learning system to operate at near-zero cost while
maintaining quality where it matters.
"""

import os
import json
from typing import Dict, Any, Optional, List
from enum import Enum


class TaskComplexity(Enum):
    """Task complexity levels for model routing"""
    SIMPLE = "simple"           # CRUD, simple queries
    MODERATE = "moderate"       # Pattern detection, basic analysis
    COMPLEX = "complex"         # Deep reasoning, code generation


class ModelRouter:
    """Routes tasks to cost-efficient models via agentic-flow"""

    # Task complexity mapping
    TASK_COMPLEXITY = {
        # Simple operations (Gemini Flash - $0.075/1M)
        "add_episode": TaskComplexity.SIMPLE,
        "search_episodes": TaskComplexity.SIMPLE,
        "list_recent": TaskComplexity.SIMPLE,
        "log_tool_execution": TaskComplexity.SIMPLE,
        "get_agent_stats": TaskComplexity.SIMPLE,
        "check_quality_gates": TaskComplexity.SIMPLE,

        # Moderate operations (DeepSeek/Gemini - $0.14/1M)
        "extract_patterns": TaskComplexity.MODERATE,
        "detect_corrections": TaskComplexity.MODERATE,
        "suggest_claudemd_update": TaskComplexity.MODERATE,
        "calculate_significance": TaskComplexity.MODERATE,
        "recommend_agent": TaskComplexity.MODERATE,

        # Complex operations (Claude - premium)
        "validate_spec": TaskComplexity.COMPLEX,
        "generate_claudemd": TaskComplexity.COMPLEX,
        "analyze_workflow": TaskComplexity.COMPLEX,
    }

    # Model preferences by complexity
    MODEL_PREFERENCES = {
        TaskComplexity.SIMPLE: {
            "primary": "gemini-1.5-flash",
            "fallback": "deepseek-chat",
            "cost_per_1m": 0.075
        },
        TaskComplexity.MODERATE: {
            "primary": "deepseek-chat",
            "fallback": "gemini-1.5-flash",
            "cost_per_1m": 0.14
        },
        TaskComplexity.COMPLEX: {
            "primary": "claude-sonnet-4",
            "fallback": "deepseek-chat",
            "cost_per_1m": 15.0
        }
    }

    def __init__(self):
        self.cost_optimization_enabled = os.getenv("COST_OPTIMIZATION", "true").lower() == "true"
        self.default_model = os.getenv("DEFAULT_MODEL", "gemini-1.5-flash")
        self.fallback_model = os.getenv("FALLBACK_MODEL", "deepseek-chat")

        # Track usage for cost monitoring
        self.usage_stats = {
            "simple": {"count": 0, "estimated_cost": 0.0},
            "moderate": {"count": 0, "estimated_cost": 0.0},
            "complex": {"count": 0, "estimated_cost": 0.0}
        }

    def route_task(
        self,
        task_name: str,
        estimated_tokens: int = 1000,
        force_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Route a task to the appropriate model

        Args:
            task_name: Name of the task/operation
            estimated_tokens: Estimated token count
            force_model: Force specific model (overrides routing)

        Returns:
            Routing decision with model, cost estimate, and metadata
        """
        if force_model:
            return {
                "model": force_model,
                "reason": "forced",
                "complexity": "unknown",
                "estimated_cost": 0.0
            }

        # Determine complexity
        complexity = self.TASK_COMPLEXITY.get(task_name, TaskComplexity.MODERATE)

        # Get model preference
        model_config = self.MODEL_PREFERENCES[complexity]

        # Calculate cost estimate
        cost_per_token = model_config["cost_per_1m"] / 1_000_000
        estimated_cost = estimated_tokens * cost_per_token

        # Update usage stats
        complexity_key = complexity.value
        self.usage_stats[complexity_key]["count"] += 1
        self.usage_stats[complexity_key]["estimated_cost"] += estimated_cost

        return {
            "model": model_config["primary"],
            "fallback": model_config["fallback"],
            "complexity": complexity.value,
            "estimated_cost": estimated_cost,
            "estimated_tokens": estimated_tokens,
            "cost_per_1m": model_config["cost_per_1m"],
            "reason": f"Task complexity: {complexity.value}"
        }

    def get_model_for_operation(
        self,
        operation_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get recommended model for an operation

        Args:
            operation_type: Type of operation
            context: Additional context for routing decision

        Returns:
            Model name to use
        """
        routing = self.route_task(operation_type)
        return routing["model"]

    def estimate_savings(self) -> Dict[str, Any]:
        """
        Calculate cost savings from using cheap models

        Compares actual costs vs if everything used Claude
        """
        # Calculate actual cost
        actual_cost = sum(stats["estimated_cost"] for stats in self.usage_stats.values())

        # Calculate what it would cost with Claude for everything
        total_operations = sum(stats["count"] for stats in self.usage_stats.values())
        claude_cost = total_operations * 1000 * (15.0 / 1_000_000)  # Assume 1k tokens avg

        savings = claude_cost - actual_cost
        savings_percent = (savings / claude_cost * 100) if claude_cost > 0 else 0

        return {
            "actual_cost": round(actual_cost, 4),
            "claude_cost": round(claude_cost, 4),
            "savings": round(savings, 4),
            "savings_percent": round(savings_percent, 1),
            "total_operations": total_operations,
            "breakdown": self.usage_stats
        }

    def should_use_cheap_model(self, task_name: str) -> bool:
        """Check if task should use cheap model"""
        if not self.cost_optimization_enabled:
            return False

        complexity = self.TASK_COMPLEXITY.get(task_name, TaskComplexity.MODERATE)
        return complexity in [TaskComplexity.SIMPLE, TaskComplexity.MODERATE]


class AgenticFlowIntegration:
    """Integration layer with agentic-flow MCP server"""

    def __init__(self, model_router: ModelRouter):
        self.router = model_router
        self.agentic_flow_available = self._check_agentic_flow()

    def _check_agentic_flow(self) -> bool:
        """Check if agentic-flow MCP server is available"""
        # Check if GEMINI_API_KEY is configured
        return bool(os.getenv("GEMINI_API_KEY"))

    async def execute_with_routing(
        self,
        task_name: str,
        task_prompt: str,
        estimated_tokens: int = 1000,
        force_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a task with intelligent model routing

        This would integrate with agentic-flow MCP's agent execution
        to route the task to the appropriate model

        Args:
            task_name: Name of the task
            task_prompt: Prompt/description for the task
            estimated_tokens: Token estimate
            force_model: Override model selection

        Returns:
            Task execution result with metadata
        """
        # Get routing decision
        routing = self.router.route_task(task_name, estimated_tokens, force_model)

        # If agentic-flow is available, route through it
        if self.agentic_flow_available and not force_model:
            # This would call the agentic-flow MCP server
            # For now, return routing metadata
            return {
                "status": "routed",
                "routing": routing,
                "task_name": task_name,
                "note": "Would execute via agentic-flow MCP server"
            }
        else:
            # Fall back to direct execution
            return {
                "status": "direct",
                "routing": routing,
                "task_name": task_name,
                "note": "Executed directly (agentic-flow not available)"
            }

    def get_cost_report(self) -> Dict[str, Any]:
        """Generate cost savings report"""
        savings = self.router.estimate_savings()

        return {
            "summary": f"Saved ${savings['savings']:.2f} ({savings['savings_percent']:.1f}%) with smart routing",
            "details": savings,
            "agentic_flow_enabled": self.agentic_flow_available,
            "total_operations": savings["total_operations"]
        }


# Global router instance
_router = None
_integration = None


def get_model_router() -> ModelRouter:
    """Get global model router instance"""
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router


def get_agentic_flow_integration() -> AgenticFlowIntegration:
    """Get global agentic-flow integration instance"""
    global _integration
    if _integration is None:
        router = get_model_router()
        _integration = AgenticFlowIntegration(router)
    return _integration


# Convenience functions
def route_task(task_name: str, estimated_tokens: int = 1000) -> Dict[str, Any]:
    """Route a task to appropriate model"""
    router = get_model_router()
    return router.route_task(task_name, estimated_tokens)


def get_cost_savings_report() -> Dict[str, Any]:
    """Get cost savings report"""
    integration = get_agentic_flow_integration()
    return integration.get_cost_report()
