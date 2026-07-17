"""
Skills Migration System

Migrates existing .claude/skills/ files to the new database-backed system.
Preserves all existing functionality while adding search and analytics.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
from datetime import datetime

from .skill_registry import SkillRegistry, AgentSkill, AgentProfile

logger = logging.getLogger(__name__)


class SkillMigrator:
    """
    Migrates existing Claude skills to the new registry system.

    Supports both the current SKILL.md format and creates enhanced
    database entries with semantic search capabilities.
    """

    def __init__(self, skill_registry: SkillRegistry):
        """
        Initialize the migrator.

        Args:
            skill_registry: Target skill registry for migration
        """
        self.registry = skill_registry
        self.migration_log = []

    def discover_skills(self, skills_directory: Path = None) -> Dict[str, List[Path]]:
        """
        Discover all skill files in the skills directory.

        Args:
            skills_directory: Path to .claude/skills directory

        Returns:
            Dictionary mapping agent types to lists of skill files
        """
        if skills_directory is None:
            skills_directory = Path.home() / ".claude" / "skills"

        discovered = {}

        try:
            if not skills_directory.exists():
                logger.warning(f"Skills directory not found: {skills_directory}")
                return discovered

            # Look for skill directories and files
            for skill_path in skills_directory.iterdir():
                if skill_path.is_dir():
                    # Directory-based skills (new format)
                    skill_file = skill_path / "SKILL.md"
                    if skill_file.exists():
                        agent_type = skill_path.name
                        if agent_type not in discovered:
                            discovered[agent_type] = []
                        discovered[agent_type].append(skill_file)

                elif skill_path.suffix == ".md" and skill_path.name.startswith("skill_"):
                    # Legacy file-based skills
                    agent_type = skill_path.stem.replace("skill_", "")
                    if agent_type not in discovered:
                        discovered[agent_type] = []
                    discovered[agent_type].append(skill_path)

            logger.info(f"Discovered {sum(len(files) for files in discovered.values())} "
                       f"skills across {len(discovered)} agent types")

        except Exception as e:
            logger.error(f"Failed to discover skills: {e}")

        return discovered

    def parse_skill_file(self, skill_file: Path) -> Optional[Dict[str, Any]]:
        """
        Parse a SKILL.md file into structured data.

        Args:
            skill_file: Path to skill file

        Returns:
            Parsed skill data or None if failed
        """
        try:
            content = skill_file.read_text(encoding='utf-8')

            # Try to extract YAML frontmatter
            frontmatter = {}
            description = content

            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    try:
                        frontmatter = yaml.safe_load(parts[1])
                        description = parts[2].strip()
                    except yaml.YAMLError as e:
                        logger.warning(f"Failed to parse YAML frontmatter in {skill_file}: {e}")

            # Extract metadata from frontmatter or content
            skill_data = {
                'file_path': str(skill_file),
                'name': frontmatter.get('name', skill_file.stem),
                'description': frontmatter.get('description', description[:500]),
                'categories': frontmatter.get('categories', ['general']),
                'tools': frontmatter.get('tools', []),
                'capabilities': frontmatter.get('capabilities', []),
                'examples': frontmatter.get('examples', []),
                'triggers': frontmatter.get('triggers', []),
                'success_patterns': frontmatter.get('success_patterns', []),
                'learned_optimizations': frontmatter.get('optimizations', []),
                'metadata': frontmatter
            }

            # Try to extract additional info from content
            if not skill_data['capabilities']:
                skill_data['capabilities'] = self._extract_capabilities_from_content(description)

            if not skill_data['tools']:
                skill_data['tools'] = self._extract_tools_from_content(description)

            return skill_data

        except Exception as e:
            logger.error(f"Failed to parse skill file {skill_file}: {e}")
            return None

    def _extract_capabilities_from_content(self, content: str) -> List[str]:
        """Extract capabilities from skill content using heuristics."""
        capabilities = []
        content_lower = content.lower()

        # Common capability patterns
        capability_patterns = [
            'can perform', 'able to', 'capable of', 'specializes in',
            'expertise in', 'skilled at', 'proficient in'
        ]

        # Tool-based capabilities
        tool_patterns = [
            'bash', 'python', 'javascript', 'sql', 'docker', 'git',
            'testing', 'debugging', 'analysis', 'optimization',
            'web search', 'file operations', 'data processing'
        ]

        for pattern in tool_patterns:
            if pattern in content_lower:
                capabilities.append(pattern.replace(' ', '_'))

        # Extract from bullet points and lists
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('- ') or line.startswith('* '):
                # Extract capability from bullet point
                capability = line[2:].strip().lower()
                if len(capability) > 5 and len(capability) < 50:
                    capabilities.append(capability.replace(' ', '_'))

        return list(set(capabilities))  # Remove duplicates

    def _extract_tools_from_content(self, content: str) -> List[str]:
        """Extract tools from skill content using heuristics."""
        tools = []
        content_lower = content.lower()

        # Common tool names
        common_tools = [
            'bash', 'read', 'write', 'edit', 'glob', 'grep', 'websearch',
            'webfetch', 'todowrite', 'python', 'javascript', 'sql',
            'docker', 'git', 'npm', 'pip', 'curl', 'jq'
        ]

        for tool in common_tools:
            if tool in content_lower:
                tools.append(tool)

        return list(set(tools))

    async def migrate_agent_skills(self,
                                 agent_type: str,
                                 skill_files: List[Path]) -> bool:
        """
        Migrate skills for a specific agent type.

        Args:
            agent_type: Type of agent
            skill_files: List of skill files to migrate

        Returns:
            True if migration succeeded
        """
        try:
            skills = []
            migration_errors = []

            for skill_file in skill_files:
                skill_data = self.parse_skill_file(skill_file)
                if skill_data:
                    # Create AgentSkill object
                    skill = AgentSkill(
                        id=f"{agent_type}_{skill_data['name']}",
                        name=skill_data['name'],
                        description=skill_data['description'],
                        categories=skill_data['categories'],
                        tools=skill_data['tools'],
                        capabilities=skill_data['capabilities'],
                        success_patterns=skill_data['success_patterns'],
                        learned_optimizations=skill_data['learned_optimizations'],
                        metadata=skill_data['metadata']
                    )
                    skills.append(skill)

                    self.migration_log.append({
                        'action': 'parsed_skill',
                        'agent_type': agent_type,
                        'skill_name': skill_data['name'],
                        'file_path': str(skill_file),
                        'timestamp': datetime.now().isoformat()
                    })

                else:
                    migration_errors.append(str(skill_file))

            if skills:
                # Register agent with skills
                success = await self.registry.register_agent(
                    agent_id=f"migrated_{agent_type}",
                    agent_type=agent_type,
                    skills=skills,
                    specializations=list(set(cat for skill in skills for cat in skill.categories))
                )

                if success:
                    self.migration_log.append({
                        'action': 'registered_agent',
                        'agent_type': agent_type,
                        'skill_count': len(skills),
                        'errors': migration_errors,
                        'timestamp': datetime.now().isoformat()
                    })

                    logger.info(f"Migrated {len(skills)} skills for agent type: {agent_type}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to migrate skills for {agent_type}: {e}")
            return False

    async def migrate_all_skills(self, skills_directory: Path = None) -> Dict[str, Any]:
        """
        Migrate all discovered skills to the registry.

        Args:
            skills_directory: Path to skills directory

        Returns:
            Migration summary
        """
        start_time = datetime.now()
        discovered_skills = self.discover_skills(skills_directory)

        migration_summary = {
            'start_time': start_time.isoformat(),
            'discovered_agents': len(discovered_skills),
            'total_skill_files': sum(len(files) for files in discovered_skills.values()),
            'successful_agents': 0,
            'failed_agents': 0,
            'total_skills_migrated': 0,
            'errors': []
        }

        for agent_type, skill_files in discovered_skills.items():
            try:
                success = await self.migrate_agent_skills(agent_type, skill_files)
                if success:
                    migration_summary['successful_agents'] += 1
                    migration_summary['total_skills_migrated'] += len(skill_files)
                else:
                    migration_summary['failed_agents'] += 1

            except Exception as e:
                migration_summary['failed_agents'] += 1
                migration_summary['errors'].append(f"{agent_type}: {str(e)}")
                logger.error(f"Migration failed for {agent_type}: {e}")

        end_time = datetime.now()
        migration_summary['end_time'] = end_time.isoformat()
        migration_summary['duration_seconds'] = (end_time - start_time).total_seconds()

        # Store migration log
        if self.registry.memory:
            await self.registry.memory.store(
                key=f"migration_log_{int(start_time.timestamp())}",
                value=self.migration_log,
                namespace="migration",
                metadata=migration_summary
            )

        logger.info(f"Migration completed: {migration_summary['successful_agents']} agents, "
                   f"{migration_summary['total_skills_migrated']} skills in "
                   f"{migration_summary['duration_seconds']:.2f} seconds")

        return migration_summary

    def create_index_json(self, skills_directory: Path = None) -> bool:
        """
        Create INDEX.json for fast skill discovery by Claude Code.

        Args:
            skills_directory: Path to skills directory

        Returns:
            True if index was created successfully
        """
        try:
            if skills_directory is None:
                skills_directory = Path.home() / ".claude" / "skills"

            discovered_skills = self.discover_skills(skills_directory)
            index_data = {
                'version': '2.0.0',
                'generated_at': datetime.now().isoformat(),
                'total_agents': len(discovered_skills),
                'total_skills': sum(len(files) for files in discovered_skills.values()),
                'agents': {}
            }

            for agent_type, skill_files in discovered_skills.items():
                agent_skills = []
                for skill_file in skill_files:
                    skill_data = self.parse_skill_file(skill_file)
                    if skill_data:
                        agent_skills.append({
                            'name': skill_data['name'],
                            'description': skill_data['description'][:200],
                            'categories': skill_data['categories'],
                            'capabilities': skill_data['capabilities'],
                            'tools': skill_data['tools'],
                            'file_path': str(skill_file.relative_to(skills_directory))
                        })

                index_data['agents'][agent_type] = {
                    'type': agent_type,
                    'skill_count': len(agent_skills),
                    'skills': agent_skills
                }

            # Write index file
            index_file = skills_directory / "INDEX.json"
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Created skills index: {index_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to create skills index: {e}")
            return False

    def get_migration_log(self) -> List[Dict[str, Any]]:
        """Get the migration log."""
        return self.migration_log.copy()

    async def validate_migration(self) -> Dict[str, Any]:
        """
        Validate that migration completed successfully.

        Returns:
            Validation results
        """
        try:
            stats = self.registry.get_skill_statistics()

            # Check if any agents were migrated
            migrated_agents = [aid for aid in self.registry.agent_profiles.keys()
                             if aid.startswith("migrated_")]

            validation_results = {
                'migrated_agents': len(migrated_agents),
                'total_skills': stats['total_skills'],
                'unique_capabilities': stats['unique_capabilities'],
                'unique_tools': stats['unique_tools'],
                'avg_success_rate': stats['avg_success_rate'],
                'validation_passed': len(migrated_agents) > 0 and stats['total_skills'] > 0
            }

            return validation_results

        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            return {'validation_passed': False, 'error': str(e)}


def create_sample_skill_file(skill_path: Path,
                           skill_name: str,
                           agent_type: str) -> bool:
    """
    Create a sample SKILL.md file for testing.

    Args:
        skill_path: Path where to create the skill file
        skill_name: Name of the skill
        agent_type: Type of agent

    Returns:
        True if created successfully
    """
    try:
        skill_content = f'''---
name: {skill_name}
description: Sample skill for {agent_type} agent
categories:
  - general
  - {agent_type}
capabilities:
  - {skill_name.replace('-', '_').lower()}
  - general_assistance
tools:
  - bash
  - read
  - write
success_patterns:
  - "Successfully completed {skill_name} task"
triggers:
  - "{skill_name}"
  - "{agent_type} help"
---

# {skill_name} Skill

This is a sample skill for demonstrating the migration system.

## Description

{skill_name} provides capabilities for {agent_type} agents to perform
specialized tasks with high efficiency and reliability.

## Examples

- Basic usage: `{skill_name.lower()} --help`
- Advanced usage: `{skill_name.lower()} --optimize`

## Performance

- Average execution time: 200ms
- Success rate: 95%
- Optimization level: High
'''

        skill_path.parent.mkdir(parents=True, exist_ok=True)
        skill_path.write_text(skill_content, encoding='utf-8')

        logger.info(f"Created sample skill file: {skill_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to create sample skill file: {e}")
        return False