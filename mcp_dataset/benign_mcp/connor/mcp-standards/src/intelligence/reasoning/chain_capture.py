"""
Reasoning Chain Capture System

Automatically captures reasoning processes from agent interactions,
including tool usage patterns, decision points, and outcomes.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ReasoningStep(Enum):
    """Types of reasoning steps we can capture."""
    PROBLEM_ANALYSIS = "problem_analysis"
    TOOL_SELECTION = "tool_selection"
    PARAMETER_CHOICE = "parameter_choice"
    RESULT_INTERPRETATION = "result_interpretation"
    ERROR_RECOVERY = "error_recovery"
    OPTIMIZATION = "optimization"
    DECISION_POINT = "decision_point"


@dataclass
class ReasoningNode:
    """A single node in a reasoning chain."""
    id: str
    step_type: ReasoningStep
    timestamp: datetime
    description: str
    context: Dict[str, Any]
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    confidence: float  # 0.0 to 1.0
    duration_ms: Optional[float] = None
    success: bool = True
    error_details: Optional[str] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['step_type'] = self.step_type.value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReasoningNode':
        """Create from dictionary."""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['step_type'] = ReasoningStep(data['step_type'])
        return cls(**data)


@dataclass
class ReasoningChain:
    """A complete reasoning chain with metadata."""
    id: str
    task_id: str
    agent_type: str
    start_time: datetime
    end_time: Optional[datetime]
    nodes: List[ReasoningNode]
    outcome: str  # success, failure, partial
    final_result: Any
    lessons_learned: List[str]
    complexity_score: float  # 0.0 to 1.0
    effectiveness_score: float  # 0.0 to 1.0
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        result = asdict(self)
        result['start_time'] = self.start_time.isoformat()
        result['end_time'] = self.end_time.isoformat() if self.end_time else None
        result['nodes'] = [node.to_dict() for node in self.nodes]
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReasoningChain':
        """Create from dictionary."""
        data = data.copy()
        data['start_time'] = datetime.fromisoformat(data['start_time'])
        if data['end_time']:
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        data['nodes'] = [ReasoningNode.from_dict(node) for node in data['nodes']]
        return cls(**data)

    def add_node(self, node: ReasoningNode):
        """Add a reasoning node to the chain."""
        self.nodes.append(node)

    def get_duration_ms(self) -> Optional[float]:
        """Get total duration of the reasoning chain."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None

    def get_tool_sequence(self) -> List[str]:
        """Extract the sequence of tools used."""
        tools = []
        for node in self.nodes:
            if node.step_type == ReasoningStep.TOOL_SELECTION:
                tool_name = node.outputs.get('tool_name')
                if tool_name:
                    tools.append(tool_name)
        return tools

    def get_decision_points(self) -> List[ReasoningNode]:
        """Get all decision points in the chain."""
        return [node for node in self.nodes
                if node.step_type == ReasoningStep.DECISION_POINT]

    def calculate_effectiveness(self) -> float:
        """Calculate effectiveness based on success rate and efficiency."""
        if not self.nodes:
            return 0.0

        success_rate = sum(1 for node in self.nodes if node.success) / len(self.nodes)
        avg_confidence = sum(node.confidence for node in self.nodes) / len(self.nodes)

        # Penalize for errors and long duration
        error_penalty = sum(1 for node in self.nodes if not node.success) * 0.1

        effectiveness = (success_rate * 0.6 + avg_confidence * 0.4) - error_penalty
        return max(0.0, min(1.0, effectiveness))


class ReasoningChainCapture:
    """
    Captures reasoning chains from agent interactions.

    Integrates with hooks to automatically track reasoning processes
    and store them for later analysis and replay.
    """

    def __init__(self, memory_system=None):
        """
        Initialize reasoning capture system.

        Args:
            memory_system: PersistentMemory instance for storage
        """
        self.memory = memory_system
        self.active_chains: Dict[str, ReasoningChain] = {}
        self.chain_counter = 0

    def start_chain(self,
                   task_id: str,
                   agent_type: str,
                   initial_context: Dict[str, Any] = None) -> str:
        """
        Start capturing a new reasoning chain.

        Args:
            task_id: Unique identifier for the task
            agent_type: Type of agent performing reasoning
            initial_context: Initial context information

        Returns:
            Chain ID for future reference
        """
        self.chain_counter += 1
        chain_id = f"chain_{task_id}_{self.chain_counter}_{int(datetime.now().timestamp())}"

        chain = ReasoningChain(
            id=chain_id,
            task_id=task_id,
            agent_type=agent_type,
            start_time=datetime.now(),
            end_time=None,
            nodes=[],
            outcome="in_progress",
            final_result=None,
            lessons_learned=[],
            complexity_score=0.0,
            effectiveness_score=0.0,
            metadata=initial_context or {}
        )

        self.active_chains[chain_id] = chain
        logger.debug(f"Started reasoning chain: {chain_id}")

        return chain_id

    def add_reasoning_step(self,
                          chain_id: str,
                          step_type: ReasoningStep,
                          description: str,
                          context: Dict[str, Any] = None,
                          inputs: Dict[str, Any] = None,
                          outputs: Dict[str, Any] = None,
                          confidence: float = 1.0,
                          success: bool = True,
                          error_details: str = None) -> bool:
        """
        Add a reasoning step to an active chain.

        Args:
            chain_id: ID of the chain to add to
            step_type: Type of reasoning step
            description: Human-readable description
            context: Contextual information
            inputs: Input parameters/data
            outputs: Output results/data
            confidence: Confidence level (0.0-1.0)
            success: Whether the step succeeded
            error_details: Error information if failed

        Returns:
            True if step was added successfully
        """
        if chain_id not in self.active_chains:
            logger.warning(f"Chain {chain_id} not found")
            return False

        chain = self.active_chains[chain_id]
        node_id = f"{chain_id}_node_{len(chain.nodes)}"

        node = ReasoningNode(
            id=node_id,
            step_type=step_type,
            timestamp=datetime.now(),
            description=description,
            context=context or {},
            inputs=inputs or {},
            outputs=outputs or {},
            confidence=confidence,
            success=success,
            error_details=error_details
        )

        chain.add_node(node)
        logger.debug(f"Added reasoning step to {chain_id}: {step_type.value}")

        return True

    def capture_tool_usage(self,
                          chain_id: str,
                          tool_name: str,
                          parameters: Dict[str, Any],
                          result: Any,
                          duration_ms: float,
                          success: bool = True,
                          error_details: str = None) -> bool:
        """
        Capture a tool usage step.

        Args:
            chain_id: Chain ID
            tool_name: Name of the tool used
            parameters: Tool parameters
            result: Tool result
            duration_ms: Execution duration
            success: Whether tool succeeded
            error_details: Error details if failed

        Returns:
            True if captured successfully
        """
        return self.add_reasoning_step(
            chain_id=chain_id,
            step_type=ReasoningStep.TOOL_SELECTION,
            description=f"Used tool: {tool_name}",
            inputs={"tool_name": tool_name, "parameters": parameters},
            outputs={"result": result, "duration_ms": duration_ms},
            confidence=0.9 if success else 0.3,
            success=success,
            error_details=error_details
        )

    def capture_decision_point(self,
                              chain_id: str,
                              decision_description: str,
                              options: List[str],
                              chosen_option: str,
                              reasoning: str,
                              confidence: float) -> bool:
        """
        Capture a decision point in reasoning.

        Args:
            chain_id: Chain ID
            decision_description: What decision was being made
            options: Available options
            chosen_option: Selected option
            reasoning: Why this option was chosen
            confidence: Confidence in the decision

        Returns:
            True if captured successfully
        """
        return self.add_reasoning_step(
            chain_id=chain_id,
            step_type=ReasoningStep.DECISION_POINT,
            description=decision_description,
            inputs={"options": options, "reasoning": reasoning},
            outputs={"chosen_option": chosen_option},
            confidence=confidence
        )

    def finish_chain(self,
                    chain_id: str,
                    outcome: str,
                    final_result: Any = None,
                    lessons_learned: List[str] = None) -> bool:
        """
        Finish and store a reasoning chain.

        Args:
            chain_id: Chain ID to finish
            outcome: Final outcome (success/failure/partial)
            final_result: Final result of the reasoning
            lessons_learned: Extracted lessons

        Returns:
            True if stored successfully
        """
        if chain_id not in self.active_chains:
            logger.warning(f"Chain {chain_id} not found")
            return False

        chain = self.active_chains[chain_id]
        chain.end_time = datetime.now()
        chain.outcome = outcome
        chain.final_result = final_result
        chain.lessons_learned = lessons_learned or []

        # Calculate scores
        chain.effectiveness_score = chain.calculate_effectiveness()
        chain.complexity_score = min(1.0, len(chain.nodes) / 20.0)  # Normalize by expected max

        # Store in memory system
        success = self._store_chain(chain)

        if success:
            # Remove from active chains
            del self.active_chains[chain_id]
            logger.info(f"Finished and stored reasoning chain: {chain_id}")

        return success

    async def _store_chain(self, chain: ReasoningChain) -> bool:
        """Store a completed reasoning chain."""
        if not self.memory:
            logger.warning("No memory system configured for chain storage")
            return False

        try:
            key = f"reasoning_chain_{chain.id}"
            await self.memory.store(
                key=key,
                value=chain.to_dict(),
                namespace="reasoning",
                metadata={
                    "agent_type": chain.agent_type,
                    "task_id": chain.task_id,
                    "outcome": chain.outcome,
                    "effectiveness": chain.effectiveness_score,
                    "complexity": chain.complexity_score,
                    "duration_ms": chain.get_duration_ms(),
                    "tool_count": len(chain.get_tool_sequence())
                }
            )
            return True

        except Exception as e:
            logger.error(f"Failed to store reasoning chain: {e}")
            return False

    async def get_similar_chains(self,
                               current_context: str,
                               agent_type: str = None,
                               min_effectiveness: float = 0.7,
                               limit: int = 5) -> List[ReasoningChain]:
        """
        Find similar reasoning chains for guidance.

        Args:
            current_context: Description of current situation
            agent_type: Filter by agent type
            min_effectiveness: Minimum effectiveness score
            limit: Maximum number of results

        Returns:
            List of similar reasoning chains
        """
        if not self.memory:
            return []

        try:
            # Search for similar chains
            results = await self.memory.search(
                query=current_context,
                namespace="reasoning",
                top_k=limit * 2,  # Get extra for filtering
                include_metadata=True
            )

            chains = []
            for result in results:
                try:
                    chain_data = result['value']
                    metadata = result.get('metadata', {})

                    # Apply filters
                    if min_effectiveness and metadata.get('effectiveness', 0) < min_effectiveness:
                        continue

                    if agent_type and metadata.get('agent_type') != agent_type:
                        continue

                    chain = ReasoningChain.from_dict(chain_data)
                    chains.append(chain)

                    if len(chains) >= limit:
                        break

                except Exception as e:
                    logger.warning(f"Failed to deserialize chain: {e}")
                    continue

            return chains

        except Exception as e:
            logger.error(f"Failed to search for similar chains: {e}")
            return []

    def get_active_chains(self) -> Dict[str, ReasoningChain]:
        """Get all currently active reasoning chains."""
        return self.active_chains.copy()

    def abort_chain(self, chain_id: str) -> bool:
        """Abort an active reasoning chain without storing."""
        if chain_id in self.active_chains:
            del self.active_chains[chain_id]
            logger.info(f"Aborted reasoning chain: {chain_id}")
            return True
        return False