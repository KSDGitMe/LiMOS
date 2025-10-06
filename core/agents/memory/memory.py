"""
Agent Memory Management System

This module provides memory management capabilities for agents,
including short-term memory, long-term storage, context management,
and memory persistence.
"""

import json
import pickle
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class MemoryEntry(BaseModel):
    """A single memory entry."""
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}

    class Config:
        arbitrary_types_allowed = True

    def is_expired(self) -> bool:
        """Check if memory entry has expired."""
        if self.ttl_seconds is None:
            return False
        return datetime.utcnow() > self.created_at + timedelta(seconds=self.ttl_seconds)

    def touch(self) -> None:
        """Update access timestamp and increment access count."""
        self.accessed_at = datetime.utcnow()
        self.access_count += 1


class MemoryBackend(ABC):
    """Abstract base class for memory storage backends."""

    @abstractmethod
    async def get(self, key: str) -> Optional[MemoryEntry]:
        """Get a memory entry by key."""
        pass

    @abstractmethod
    async def set(self, entry: MemoryEntry) -> None:
        """Store a memory entry."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a memory entry."""
        pass

    @abstractmethod
    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """List memory keys, optionally filtered by pattern."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all memory entries."""
        pass

    @abstractmethod
    async def size(self) -> int:
        """Get the number of memory entries."""
        pass


class InMemoryBackend(MemoryBackend):
    """In-memory storage backend (non-persistent)."""

    def __init__(self):
        self._storage: Dict[str, MemoryEntry] = {}

    async def get(self, key: str) -> Optional[MemoryEntry]:
        """Get a memory entry by key."""
        entry = self._storage.get(key)
        if entry and entry.is_expired():
            await self.delete(key)
            return None
        if entry:
            entry.touch()
        return entry

    async def set(self, entry: MemoryEntry) -> None:
        """Store a memory entry."""
        self._storage[entry.key] = entry

    async def delete(self, key: str) -> bool:
        """Delete a memory entry."""
        if key in self._storage:
            del self._storage[key]
            return True
        return False

    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """List memory keys, optionally filtered by pattern."""
        all_keys = list(self._storage.keys())
        if pattern is None:
            return all_keys

        import fnmatch
        return [key for key in all_keys if fnmatch.fnmatch(key, pattern)]

    async def clear(self) -> None:
        """Clear all memory entries."""
        self._storage.clear()

    async def size(self) -> int:
        """Get the number of memory entries."""
        return len(self._storage)


class FileBackend(MemoryBackend):
    """File-based storage backend for persistent memory."""

    def __init__(self, storage_path: Union[str, Path]):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, key: str) -> Path:
        """Get file path for a memory key."""
        # Create a safe filename from the key
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.storage_path / f"{safe_key}.json"

    async def get(self, key: str) -> Optional[MemoryEntry]:
        """Get a memory entry by key."""
        file_path = self._get_file_path(key)
        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Reconstruct MemoryEntry
            entry = MemoryEntry(
                key=data['key'],
                value=data['value'],
                created_at=datetime.fromisoformat(data['created_at']),
                accessed_at=datetime.fromisoformat(data['accessed_at']),
                access_count=data['access_count'],
                ttl_seconds=data.get('ttl_seconds'),
                tags=data.get('tags', []),
                metadata=data.get('metadata', {})
            )

            if entry.is_expired():
                await self.delete(key)
                return None

            entry.touch()
            await self.set(entry)  # Update access info
            return entry

        except (json.JSONDecodeError, KeyError, ValueError):
            # Corrupted file, remove it
            file_path.unlink(missing_ok=True)
            return None

    async def set(self, entry: MemoryEntry) -> None:
        """Store a memory entry."""
        file_path = self._get_file_path(entry.key)

        data = {
            'key': entry.key,
            'value': entry.value,
            'created_at': entry.created_at.isoformat(),
            'accessed_at': entry.accessed_at.isoformat(),
            'access_count': entry.access_count,
            'ttl_seconds': entry.ttl_seconds,
            'tags': entry.tags,
            'metadata': entry.metadata
        }

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    async def delete(self, key: str) -> bool:
        """Delete a memory entry."""
        file_path = self._get_file_path(key)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """List memory keys, optionally filtered by pattern."""
        json_files = list(self.storage_path.glob("*.json"))
        keys = [f.stem for f in json_files]

        if pattern is None:
            return keys

        import fnmatch
        return [key for key in keys if fnmatch.fnmatch(key, pattern)]

    async def clear(self) -> None:
        """Clear all memory entries."""
        for file_path in self.storage_path.glob("*.json"):
            file_path.unlink()

    async def size(self) -> int:
        """Get the number of memory entries."""
        return len(list(self.storage_path.glob("*.json")))


class AgentMemory:
    """
    Agent memory management system.

    Provides high-level memory operations for agents, including
    short-term and long-term memory, TTL management, and querying.
    """

    def __init__(self, agent_id: str, backend: Optional[MemoryBackend] = None):
        """
        Initialize agent memory.

        Args:
            agent_id: Unique agent identifier
            backend: Memory storage backend (defaults to in-memory)
        """
        self.agent_id = agent_id
        self.backend = backend or InMemoryBackend()
        self._namespace = f"agent:{agent_id}"

    def _make_key(self, key: str) -> str:
        """Create namespaced key for the agent."""
        return f"{self._namespace}:{key}"

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store a value in memory.

        Args:
            key: Memory key
            value: Value to store
            ttl_seconds: Time to live in seconds
            tags: Optional tags for categorization
            metadata: Optional metadata
        """
        namespaced_key = self._make_key(key)
        now = datetime.utcnow()

        entry = MemoryEntry(
            key=namespaced_key,
            value=value,
            created_at=now,
            accessed_at=now,
            ttl_seconds=ttl_seconds,
            tags=tags or [],
            metadata=metadata or {}
        )

        await self.backend.set(entry)

    async def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value from memory.

        Args:
            key: Memory key
            default: Default value if key not found

        Returns:
            Stored value or default
        """
        namespaced_key = self._make_key(key)
        entry = await self.backend.get(namespaced_key)
        return entry.value if entry else default

    async def delete(self, key: str) -> bool:
        """
        Delete a memory entry.

        Args:
            key: Memory key

        Returns:
            True if deleted, False if not found
        """
        namespaced_key = self._make_key(key)
        return await self.backend.delete(namespaced_key)

    async def exists(self, key: str) -> bool:
        """
        Check if a memory key exists.

        Args:
            key: Memory key

        Returns:
            True if key exists and is not expired
        """
        namespaced_key = self._make_key(key)
        entry = await self.backend.get(namespaced_key)
        return entry is not None

    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """
        List memory keys for this agent.

        Args:
            pattern: Optional pattern to filter keys

        Returns:
            List of memory keys (without namespace prefix)
        """
        namespace_pattern = f"{self._namespace}:*"
        if pattern:
            namespace_pattern = f"{self._namespace}:{pattern}"

        namespaced_keys = await self.backend.keys(namespace_pattern)
        prefix_len = len(self._namespace) + 1
        return [key[prefix_len:] for key in namespaced_keys]

    async def find_by_tags(self, tags: List[str]) -> Dict[str, Any]:
        """
        Find memory entries by tags.

        Args:
            tags: List of tags to search for

        Returns:
            Dictionary of key-value pairs for matching entries
        """
        results = {}
        all_keys = await self.keys()

        for key in all_keys:
            namespaced_key = self._make_key(key)
            entry = await self.backend.get(namespaced_key)
            if entry and any(tag in entry.tags for tag in tags):
                results[key] = entry.value

        return results

    async def update_ttl(self, key: str, ttl_seconds: int) -> bool:
        """
        Update TTL for a memory entry.

        Args:
            key: Memory key
            ttl_seconds: New TTL in seconds

        Returns:
            True if updated, False if key not found
        """
        namespaced_key = self._make_key(key)
        entry = await self.backend.get(namespaced_key)
        if entry:
            entry.ttl_seconds = ttl_seconds
            await self.backend.set(entry)
            return True
        return False

    async def get_info(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a memory entry.

        Args:
            key: Memory key

        Returns:
            Dictionary with entry information or None
        """
        namespaced_key = self._make_key(key)
        entry = await self.backend.get(namespaced_key)
        if entry:
            return {
                "key": key,
                "created_at": entry.created_at,
                "accessed_at": entry.accessed_at,
                "access_count": entry.access_count,
                "ttl_seconds": entry.ttl_seconds,
                "tags": entry.tags,
                "metadata": entry.metadata,
                "is_expired": entry.is_expired()
            }
        return None

    async def clear(self) -> None:
        """Clear all memory entries for this agent."""
        keys = await self.keys()
        for key in keys:
            await self.delete(key)

    async def cleanup_expired(self) -> int:
        """
        Remove expired memory entries.

        Returns:
            Number of entries removed
        """
        keys = await self.keys()
        removed_count = 0

        for key in keys:
            namespaced_key = self._make_key(key)
            entry = await self.backend.get(namespaced_key)
            if entry and entry.is_expired():
                await self.backend.delete(namespaced_key)
                removed_count += 1

        return removed_count

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics for this agent.

        Returns:
            Dictionary with memory statistics
        """
        keys = await self.keys()
        total_entries = len(keys)
        expired_count = 0
        tag_counts = {}
        access_stats = {"min": float('inf'), "max": 0, "total": 0}

        for key in keys:
            namespaced_key = self._make_key(key)
            entry = await self.backend.get(namespaced_key)
            if entry:
                if entry.is_expired():
                    expired_count += 1

                # Count tags
                for tag in entry.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

                # Access statistics
                access_stats["min"] = min(access_stats["min"], entry.access_count)
                access_stats["max"] = max(access_stats["max"], entry.access_count)
                access_stats["total"] += entry.access_count

        if total_entries > 0:
            access_stats["average"] = access_stats["total"] / total_entries
        else:
            access_stats = {"min": 0, "max": 0, "total": 0, "average": 0}

        return {
            "agent_id": self.agent_id,
            "total_entries": total_entries,
            "expired_entries": expired_count,
            "active_entries": total_entries - expired_count,
            "tag_distribution": tag_counts,
            "access_statistics": access_stats
        }