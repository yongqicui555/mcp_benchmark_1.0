"""
Skills Management System

Dynamic skill registry and capability matching for intelligent agent routing.
Migrates and enhances existing .claude/skills/ functionality.
"""

from .skill_registry import SkillRegistry
from .skill_migrator import SkillMigrator
from .capability_matcher import CapabilityMatcher

__all__ = ["SkillRegistry", "SkillMigrator", "CapabilityMatcher"]