"""
Agent Registry System

This module provides a registry for managing and discovering agents
within the LiMOS system. It handles agent registration, discovery,
lifecycle management, and coordination between agents.
"""

import asyncio
import weakref
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Type, Union

from pydantic import BaseModel

from ..base.agent import BaseAgent, AgentConfig, AgentStatus


class AgentRegistration(BaseModel):
    """Agent registration information."""
    agent_id: str
    name: str
    agent_class: str
    config: AgentConfig
    status: AgentStatus
    registered_at: datetime
    last_activity: datetime
    tags: Set[str] = set()
    metadata: Dict[str, Any] = {}


class AgentRegistry:
    """
    Central registry for managing agents in the LiMOS system.

    The registry provides agent discovery, lifecycle management,
    and coordination capabilities. It maintains references to
    active agents and their metadata.
    """

    def __init__(self):
        """Initialize the agent registry."""
        self._agents: Dict[str, weakref.ReferenceType[BaseAgent]] = {}
        self._registrations: Dict[str, AgentRegistration] = {}
        self._agent_classes: Dict[str, Type[BaseAgent]] = {}
        self._tags: Dict[str, Set[str]] = {}  # tag -> set of agent_ids
        self._lock = asyncio.Lock()

    async def register_agent_class(
        self,
        agent_class: Type[BaseAgent],
        name: Optional[str] = None
    ) -> None:
        """
        Register an agent class for factory creation.

        Args:
            agent_class: Agent class to register
            name: Optional name override (defaults to class name)
        """
        async with self._lock:
            class_name = name or agent_class.__name__
            self._agent_classes[class_name] = agent_class

    async def register_agent(
        self,
        agent: BaseAgent,
        tags: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Register an agent instance with the registry.

        Args:
            agent: Agent instance to register
            tags: Optional tags for categorization
            metadata: Optional metadata

        Returns:
            Agent ID

        Raises:
            ValueError: If agent is already registered
        """
        async with self._lock:
            agent_id = agent.agent_id

            if agent_id in self._registrations:
                raise ValueError(f"Agent {agent_id} is already registered")

            # Create registration record
            registration = AgentRegistration(
                agent_id=agent_id,
                name=agent.name,
                agent_class=agent.__class__.__name__,
                config=agent.config,
                status=agent.status,
                registered_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                tags=tags or set(),
                metadata=metadata or {}
            )

            self._registrations[agent_id] = registration

            # Store weak reference to agent
            def cleanup_callback(ref):
                asyncio.create_task(self._cleanup_agent(agent_id))

            self._agents[agent_id] = weakref.ref(agent, cleanup_callback)

            # Update tag index
            for tag in registration.tags:
                if tag not in self._tags:
                    self._tags[tag] = set()
                self._tags[tag].add(agent_id)

            return agent_id

    async def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from the registry.

        Args:
            agent_id: Agent ID to unregister

        Returns:
            True if agent was unregistered, False if not found
        """
        async with self._lock:
            return await self._cleanup_agent(agent_id)

    async def _cleanup_agent(self, agent_id: str) -> bool:
        """Internal method to clean up agent registration."""
        if agent_id not in self._registrations:
            return False

        registration = self._registrations[agent_id]

        # Remove from tag index
        for tag in registration.tags:
            if tag in self._tags:
                self._tags[tag].discard(agent_id)
                if not self._tags[tag]:
                    del self._tags[tag]

        # Remove registration and weak reference
        del self._registrations[agent_id]
        self._agents.pop(agent_id, None)

        return True

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get an agent instance by ID.

        Args:
            agent_id: Agent ID

        Returns:
            Agent instance or None if not found/garbage collected
        """
        if agent_id in self._agents:
            agent_ref = self._agents[agent_id]
            return agent_ref()
        return None

    def get_registration(self, agent_id: str) -> Optional[AgentRegistration]:
        """
        Get agent registration information.

        Args:
            agent_id: Agent ID

        Returns:
            AgentRegistration or None if not found
        """
        return self._registrations.get(agent_id)

    def list_agents(
        self,
        status: Optional[AgentStatus] = None,
        tags: Optional[Set[str]] = None,
        capabilities: Optional[List[str]] = None
    ) -> List[AgentRegistration]:
        """
        List registered agents with optional filtering.

        Args:
            status: Filter by agent status
            tags: Filter by tags (agent must have ALL tags)
            capabilities: Filter by capabilities

        Returns:
            List of matching agent registrations
        """
        results = []

        for registration in self._registrations.values():
            # Status filter
            if status is not None and registration.status != status:
                continue

            # Tags filter (must have ALL specified tags)
            if tags is not None and not tags.issubset(registration.tags):
                continue

            # Capabilities filter
            if capabilities is not None:
                agent_capabilities = [cap.value for cap in registration.config.capabilities]
                if not all(cap in agent_capabilities for cap in capabilities):
                    continue

            results.append(registration)

        return results

    def find_agents_by_tag(self, tag: str) -> List[AgentRegistration]:
        """
        Find agents by a specific tag.

        Args:
            tag: Tag to search for

        Returns:
            List of agent registrations with the tag
        """
        if tag not in self._tags:
            return []

        agent_ids = self._tags[tag]
        return [self._registrations[aid] for aid in agent_ids if aid in self._registrations]

    async def create_agent(
        self,
        agent_class_name: str,
        config: AgentConfig,
        auto_register: bool = True,
        **kwargs
    ) -> BaseAgent:
        """
        Create an agent instance using registered agent class.

        Args:
            agent_class_name: Name of registered agent class
            config: Agent configuration
            auto_register: Whether to automatically register the agent
            **kwargs: Additional arguments for agent constructor

        Returns:
            Created agent instance

        Raises:
            ValueError: If agent class is not registered
        """
        if agent_class_name not in self._agent_classes:
            raise ValueError(f"Agent class '{agent_class_name}' is not registered")

        agent_class = self._agent_classes[agent_class_name]
        agent = agent_class(config, **kwargs)

        if auto_register:
            await self.register_agent(agent)

        return agent

    async def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """
        Update agent status in registry.

        Args:
            agent_id: Agent ID
            status: New status

        Returns:
            True if updated, False if agent not found
        """
        async with self._lock:
            if agent_id not in self._registrations:
                return False

            self._registrations[agent_id].status = status
            self._registrations[agent_id].last_activity = datetime.utcnow()
            return True

    async def update_agent_activity(self, agent_id: str) -> bool:
        """
        Update agent last activity timestamp.

        Args:
            agent_id: Agent ID

        Returns:
            True if updated, False if agent not found
        """
        async with self._lock:
            if agent_id not in self._registrations:
                return False

            self._registrations[agent_id].last_activity = datetime.utcnow()
            return True

    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dictionary with registry statistics
        """
        total_agents = len(self._registrations)
        status_counts = {}
        capabilities_counts = {}
        tags_counts = {}

        for registration in self._registrations.values():
            # Count by status
            status = registration.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

            # Count by capabilities
            for capability in registration.config.capabilities:
                cap_name = capability.value
                capabilities_counts[cap_name] = capabilities_counts.get(cap_name, 0) + 1

            # Count by tags
            for tag in registration.tags:
                tags_counts[tag] = tags_counts.get(tag, 0) + 1

        return {
            "total_agents": total_agents,
            "registered_classes": len(self._agent_classes),
            "status_distribution": status_counts,
            "capability_distribution": capabilities_counts,
            "tag_distribution": tags_counts,
            "active_references": len([ref for ref in self._agents.values() if ref() is not None])
        }

    async def cleanup_stale_agents(self, max_age_hours: int = 24) -> int:
        """
        Clean up agents that haven't been active recently.

        Args:
            max_age_hours: Maximum age in hours for last activity

        Returns:
            Number of agents cleaned up
        """
        from datetime import timedelta

        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        stale_agents = []

        for agent_id, registration in self._registrations.items():
            if registration.last_activity < cutoff_time:
                # Check if agent is still alive
                agent = self.get_agent(agent_id)
                if agent is None or agent.status == AgentStatus.STOPPED:
                    stale_agents.append(agent_id)

        for agent_id in stale_agents:
            await self.unregister_agent(agent_id)

        return len(stale_agents)


# Global registry instance
agent_registry = AgentRegistry()