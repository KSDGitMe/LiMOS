"""
Event Dispatcher for Agent Coordination

Provides routing and filtering of events with pattern matching support.
"""

import asyncio
import logging
import re
from typing import Any, Callable, Dict, List, Optional, Pattern
from dataclasses import dataclass

from .message_bus import MessageBus, Event, EventPriority, get_message_bus

logger = logging.getLogger(__name__)


@dataclass
class EventRoute:
    """Event routing rule."""
    pattern: Pattern
    handler: Callable
    priority: EventPriority = EventPriority.NORMAL
    description: str = ""


class EventDispatcher:
    """
    Event dispatcher with pattern matching and routing.

    Provides more sophisticated event routing than basic pub/sub,
    including regex pattern matching and conditional routing.

    Usage:
        dispatcher = EventDispatcher()

        # Add route with pattern
        dispatcher.add_route(
            pattern=r"transaction\.(created|updated)",
            handler=handle_transaction,
            description="Handle transaction events"
        )

        # Dispatch event
        await dispatcher.dispatch(event)
    """

    def __init__(self, message_bus: Optional[MessageBus] = None):
        """
        Initialize event dispatcher.

        Args:
            message_bus: Optional MessageBus instance (uses global if None)
        """
        self.message_bus = message_bus or get_message_bus()
        self._routes: List[EventRoute] = []
        self._stats = {
            "total_dispatched": 0,
            "total_matched": 0,
            "total_unmatched": 0
        }
        logger.info("EventDispatcher initialized")

    def add_route(
        self,
        pattern: str,
        handler: Callable,
        priority: EventPriority = EventPriority.NORMAL,
        description: str = ""
    ):
        """
        Add an event routing rule.

        Args:
            pattern: Regex pattern for matching event types
            handler: Function to handle matched events
            priority: Route priority
            description: Human-readable description
        """
        compiled_pattern = re.compile(pattern)
        route = EventRoute(
            pattern=compiled_pattern,
            handler=handler,
            priority=priority,
            description=description
        )
        self._routes.append(route)

        # Sort by priority
        priority_order = {
            EventPriority.CRITICAL: 0,
            EventPriority.HIGH: 1,
            EventPriority.NORMAL: 2,
            EventPriority.LOW: 3
        }
        self._routes.sort(key=lambda r: priority_order.get(r.priority, 2))

        logger.info(f"Added route: {pattern} -> {handler.__name__}")

    async def dispatch(self, event: Event) -> List[Any]:
        """
        Dispatch an event through routing rules.

        Args:
            event: Event to dispatch

        Returns:
            List of results from matched handlers
        """
        self._stats["total_dispatched"] += 1
        matched_routes = []

        # Find matching routes
        for route in self._routes:
            if route.pattern.match(event.event_type):
                matched_routes.append(route)

        if not matched_routes:
            self._stats["total_unmatched"] += 1
            logger.debug(f"No routes matched for event: {event.event_type}")
            return []

        self._stats["total_matched"] += 1
        logger.debug(
            f"Event {event.event_type} matched {len(matched_routes)} route(s)"
        )

        # Execute handlers
        results = []
        for route in matched_routes:
            try:
                if asyncio.iscoroutinefunction(route.handler):
                    result = await route.handler(event)
                else:
                    result = route.handler(event)
                results.append(result)
            except Exception as e:
                logger.error(
                    f"Error executing handler {route.handler.__name__} "
                    f"for event {event.event_id}: {e}"
                )
                results.append({"error": str(e)})

        return results

    def remove_route(self, pattern: str):
        """
        Remove routing rule by pattern.

        Args:
            pattern: Pattern string to remove
        """
        self._routes = [
            r for r in self._routes if r.pattern.pattern != pattern
        ]
        logger.info(f"Removed route: {pattern}")

    def get_routes(self) -> List[Dict[str, Any]]:
        """Get all routing rules."""
        return [
            {
                "pattern": route.pattern.pattern,
                "handler": route.handler.__name__,
                "priority": route.priority.value,
                "description": route.description
            }
            for route in self._routes
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get dispatcher statistics."""
        return {
            **self._stats,
            "total_routes": len(self._routes)
        }
