"""
Skills Registry System

Manages agent skills and capabilities with persistent storage and semantic search.
Provides intelligent skill-based routing and capability matching.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class AgentSkill:
    """Represents a skill that an agent can perform."""
    id: str
    name: str
    description: str
    categories: List[str]
    tools: List[str]
    capabilities: List[str]
    success_patterns: List[str]
    learned_optimizations: List[str]
    usage_count: int = 0
    success_rate: float = 1.0
    avg_duration_ms: float = 0.0
    last_used: Optional[datetime] = None
    confidence_score: float = 1.0
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        result = asdict(self)
        result['last_used'] = self.last_used.isoformat() if self.last_used else None
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentSkill':
        """Create from dictionary."""
        data = data.copy()
        if data.get('last_used'):
            data['last_used'] = datetime.fromisoformat(data['last_used'])
        return cls(**data)

    def update_usage_stats(self, duration_ms: float, success: bool):
        """Update usage statistics."""
        self.usage_count += 1
        self.last_used = datetime.now()

        # Update success rate (exponential moving average)
        alpha = 0.1  # Learning rate
        new_success = 1.0 if success else 0.0
        self.success_rate = (1 - alpha) * self.success_rate + alpha * new_success

        # Update average duration
        self.avg_duration_ms = (
            (self.avg_duration_ms * (self.usage_count - 1) + duration_ms) /
            self.usage_count
        )

        # Update confidence based on usage and success
        usage_factor = min(1.0, self.usage_count / 10.0)  # Confidence increases with usage
        self.confidence_score = self.success_rate * usage_factor


@dataclass
class AgentProfile:
    """Profile of an agent's capabilities and performance."""
    agent_id: str
    agent_type: str
    skills: List[AgentSkill]
    specializations: List[str]
    performance_metrics: Dict[str, float]
    learning_rate: float = 0.1
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        result = asdict(self)
        result['skills'] = [skill.to_dict() for skill in self.skills]
        result['created_at'] = self.created_at.isoformat()
        result['updated_at'] = self.updated_at.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentProfile':
        """Create from dictionary."""
        data = data.copy()
        data['skills'] = [AgentSkill.from_dict(skill) for skill in data['skills']]
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)

    def get_skill_by_id(self, skill_id: str) -> Optional[AgentSkill]:
        """Get a skill by ID."""
        for skill in self.skills:
            if skill.id == skill_id:
                return skill
        return None

    def add_skill(self, skill: AgentSkill):
        """Add a new skill to the agent."""
        existing = self.get_skill_by_id(skill.id)
        if existing:
            # Update existing skill
            existing.description = skill.description
            existing.capabilities.extend(skill.capabilities)
            existing.tools.extend(skill.tools)
            # Remove duplicates
            existing.capabilities = list(set(existing.capabilities))
            existing.tools = list(set(existing.tools))
        else:
            self.skills.append(skill)

        self.updated_at = datetime.now()

    def get_capabilities(self) -> Set[str]:
        """Get all capabilities across all skills."""
        capabilities = set()
        for skill in self.skills:
            capabilities.update(skill.capabilities)
        return capabilities

    def get_tools(self) -> Set[str]:
        """Get all tools across all skills."""
        tools = set()
        for skill in self.skills:
            tools.update(skill.tools)
        return tools

    def calculate_expertise_score(self, required_capabilities: List[str]) -> float:
        """Calculate expertise score for required capabilities."""
        if not required_capabilities:
            return 0.0

        agent_capabilities = self.get_capabilities()
        matching_skills = []

        for capability in required_capabilities:
            for skill in self.skills:
                if capability in skill.capabilities:
                    matching_skills.append(skill)
                    break

        if not matching_skills:
            return 0.0

        # Calculate weighted score based on skill confidence and success rate
        total_score = 0.0
        for skill in matching_skills:
            skill_score = skill.confidence_score * skill.success_rate
            total_score += skill_score

        # Normalize by number of required capabilities
        coverage = len(matching_skills) / len(required_capabilities)
        avg_skill_score = total_score / len(matching_skills) if matching_skills else 0.0

        return coverage * avg_skill_score


class SkillRegistry:
    """
    Central registry for agent skills and capabilities.

    Provides skill-based routing, capability matching, and performance tracking.
    Integrates with persistent memory for long-term learning.
    """

    def __init__(self, memory_system=None):
        """
        Initialize the skill registry.

        Args:
            memory_system: PersistentMemory instance for storage
        """
        self.memory = memory_system
        self.agent_profiles: Dict[str, AgentProfile] = {}
        self.skill_categories: Dict[str, List[str]] = {}

        # Load existing profiles
        if self.memory:
            self._load_profiles()

    async def _load_profiles(self):
        """Load agent profiles from memory."""
        try:
            if not self.memory:
                return

            # Search for all agent profiles
            results = await self.memory.search(
                query="agent_profile",
                namespace="skills",
                top_k=100,
                include_metadata=True
            )

            for result in results:
                try:
                    profile_data = result['value']
                    profile = AgentProfile.from_dict(profile_data)
                    self.agent_profiles[profile.agent_id] = profile
                    logger.debug(f"Loaded profile for agent: {profile.agent_id}")
                except Exception as e:
                    logger.warning(f"Failed to load agent profile: {e}")

            logger.info(f"Loaded {len(self.agent_profiles)} agent profiles")

        except Exception as e:
            logger.error(f"Failed to load agent profiles: {e}")

    async def register_agent(self,
                           agent_id: str,
                           agent_type: str,
                           skills: List[AgentSkill],
                           specializations: List[str] = None) -> bool:
        """
        Register a new agent with its skills.

        Args:
            agent_id: Unique agent identifier
            agent_type: Type/class of agent
            skills: List of agent skills
            specializations: Areas of specialization

        Returns:
            True if registered successfully
        """
        try:
            profile = AgentProfile(
                agent_id=agent_id,
                agent_type=agent_type,
                skills=skills,
                specializations=specializations or [],
                performance_metrics={}
            )

            self.agent_profiles[agent_id] = profile

            # Store in memory
            if self.memory:
                await self.memory.store(
                    key=f"agent_profile_{agent_id}",
                    value=profile.to_dict(),
                    namespace="skills",
                    metadata={
                        "agent_type": agent_type,
                        "skill_count": len(skills),
                        "capabilities": list(profile.get_capabilities()),
                        "tools": list(profile.get_tools())
                    }
                )

            logger.info(f"Registered agent: {agent_id} ({agent_type}) with {len(skills)} skills")
            return True

        except Exception as e:
            logger.error(f"Failed to register agent {agent_id}: {e}")
            return False

    async def update_skill_usage(self,
                               agent_id: str,
                               skill_id: str,
                               duration_ms: float,
                               success: bool) -> bool:
        """
        Update skill usage statistics.

        Args:
            agent_id: Agent identifier
            skill_id: Skill identifier
            duration_ms: Execution duration
            success: Whether execution succeeded

        Returns:
            True if updated successfully
        """
        try:
            profile = self.agent_profiles.get(agent_id)
            if not profile:
                logger.warning(f"Agent profile not found: {agent_id}")
                return False

            skill = profile.get_skill_by_id(skill_id)
            if not skill:
                logger.warning(f"Skill not found: {skill_id} for agent {agent_id}")
                return False

            skill.update_usage_stats(duration_ms, success)
            profile.updated_at = datetime.now()

            # Update in memory
            if self.memory:
                await self.memory.store(
                    key=f"agent_profile_{agent_id}",
                    value=profile.to_dict(),
                    namespace="skills",
                    metadata={
                        "agent_type": profile.agent_type,
                        "skill_count": len(profile.skills),
                        "capabilities": list(profile.get_capabilities()),
                        "tools": list(profile.get_tools()),
                        "last_updated": profile.updated_at.isoformat()
                    }
                )

            logger.debug(f"Updated skill usage: {agent_id}.{skill_id} "
                        f"(success: {success}, duration: {duration_ms}ms)")
            return True

        except Exception as e:
            logger.error(f"Failed to update skill usage: {e}")
            return False

    def find_capable_agents(self,
                           required_capabilities: List[str],
                           required_tools: List[str] = None,
                           min_confidence: float = 0.5,
                           limit: int = 5) -> List[tuple]:
        """
        Find agents capable of handling required capabilities.

        Args:
            required_capabilities: List of required capabilities
            required_tools: List of required tools (optional)
            min_confidence: Minimum confidence threshold
            limit: Maximum number of agents to return

        Returns:
            List of (agent_id, expertise_score, profile) tuples sorted by score
        """
        candidates = []

        for agent_id, profile in self.agent_profiles.items():
            # Check capabilities
            agent_capabilities = profile.get_capabilities()
            capability_match = all(cap in agent_capabilities for cap in required_capabilities)

            if not capability_match:
                continue

            # Check tools if specified
            if required_tools:
                agent_tools = profile.get_tools()
                tool_match = all(tool in agent_tools for tool in required_tools)
                if not tool_match:
                    continue

            # Calculate expertise score
            expertise_score = profile.calculate_expertise_score(required_capabilities)

            if expertise_score >= min_confidence:
                candidates.append((agent_id, expertise_score, profile))

        # Sort by expertise score (descending)
        candidates.sort(key=lambda x: x[1], reverse=True)

        return candidates[:limit]

    def get_agent_skills(self, agent_id: str) -> Optional[List[AgentSkill]]:
        """Get all skills for an agent."""
        profile = self.agent_profiles.get(agent_id)
        return profile.skills if profile else None

    def get_skill_statistics(self) -> Dict[str, Any]:
        """Get overall skill registry statistics."""
        total_agents = len(self.agent_profiles)
        total_skills = sum(len(profile.skills) for profile in self.agent_profiles.values())

        # Capability distribution
        capability_count = {}
        tool_count = {}

        for profile in self.agent_profiles.values():
            for capability in profile.get_capabilities():
                capability_count[capability] = capability_count.get(capability, 0) + 1
            for tool in profile.get_tools():
                tool_count[tool] = tool_count.get(tool, 0) + 1

        # Performance metrics
        avg_success_rates = []
        for profile in self.agent_profiles.values():
            for skill in profile.skills:
                avg_success_rates.append(skill.success_rate)

        avg_success_rate = sum(avg_success_rates) / len(avg_success_rates) if avg_success_rates else 0.0

        return {
            "total_agents": total_agents,
            "total_skills": total_skills,
            "avg_skills_per_agent": total_skills / total_agents if total_agents > 0 else 0,
            "unique_capabilities": len(capability_count),
            "unique_tools": len(tool_count),
            "avg_success_rate": avg_success_rate,
            "most_common_capabilities": sorted(capability_count.items(),
                                             key=lambda x: x[1], reverse=True)[:10],
            "most_common_tools": sorted(tool_count.items(),
                                      key=lambda x: x[1], reverse=True)[:10]
        }

    async def learn_from_interaction(self,
                                   agent_id: str,
                                   task_description: str,
                                   tools_used: List[str],
                                   outcome: str,
                                   lessons_learned: List[str]) -> bool:
        """
        Learn from agent interactions to improve skill definitions.

        Args:
            agent_id: Agent identifier
            task_description: Description of the task performed
            tools_used: Tools that were used
            outcome: Task outcome (success/failure/partial)
            lessons_learned: Extracted lessons

        Returns:
            True if learning was applied successfully
        """
        try:
            profile = self.agent_profiles.get(agent_id)
            if not profile:
                return False

            # Update relevant skills based on tools used
            for tool in tools_used:
                for skill in profile.skills:
                    if tool in skill.tools:
                        # Add lessons learned to optimizations
                        for lesson in lessons_learned:
                            if lesson not in skill.learned_optimizations:
                                skill.learned_optimizations.append(lesson)

                        # Update success patterns if successful
                        if outcome == "success" and task_description not in skill.success_patterns:
                            skill.success_patterns.append(task_description)

            profile.updated_at = datetime.now()

            # Store updated profile
            if self.memory:
                await self.memory.store(
                    key=f"agent_profile_{agent_id}",
                    value=profile.to_dict(),
                    namespace="skills"
                )

            logger.info(f"Applied learning for agent {agent_id} from task: {task_description}")
            return True

        except Exception as e:
            logger.error(f"Failed to apply learning: {e}")
            return False