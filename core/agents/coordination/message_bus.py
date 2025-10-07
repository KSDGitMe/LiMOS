"""
Message Bus for Inter-Agent Communication

Provides event-driven communication between agents using publish-subscribe pattern.
Enables loose coupling and scalable agent coordination.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


class EventPriority(str, Enum):
    """Event priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Event:
    """
    Event data structure for message bus.

    Events are published by agents and delivered to subscribed agents.
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    source_agent: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "source_agent": self.source_agent,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata
        }


@dataclass
class Subscription:
    """Agent subscription to event types."""
    subscriber_id: str
    event_types: Set[str]
    callback: Callable
    filter_func: Optional[Callable] = None
    priority: EventPriority = EventPriority.NORMAL


class MessageBus:
    """
    Central event bus for inter-agent communication.

    Features:
    - Publish-subscribe pattern
    - Event filtering
    - Priority-based delivery
    - Event history
    - Dead letter queue for failed deliveries

    Usage:
        bus = MessageBus()

        # Subscribe to events
        bus.subscribe(
            agent_id="budget_agent",
            event_types=["transaction.created", "transaction.updated"],
            callback=handle_transaction_event
        )

        # Publish events
        await bus.publish(
            event_type="transaction.created",
            payload={"transaction_id": "123", "amount": 50.00},
            source_agent="transaction_agent"
        )
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize message bus.

        Args:
            max_history: Maximum number of events to keep in history
        """
        self._subscriptions: Dict[str, List[Subscription]] = defaultdict(list)
        self._event_history: List[Event] = []
        self._max_history = max_history
        self._dead_letter_queue: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
        self._stats = {
            "total_published": 0,
            "total_delivered": 0,
            "total_failed": 0
        }
        logger.info("MessageBus initialized")

    async def publish(
        self,
        event_type: str,
        payload: Dict[str, Any],
        source_agent: str,
        priority: EventPriority = EventPriority.NORMAL,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Event:
        """
        Publish an event to the message bus.

        Args:
            event_type: Type of event (e.g., "transaction.created")
            payload: Event data
            source_agent: ID of agent publishing the event
            priority: Event priority level
            correlation_id: Optional ID to correlate related events
            metadata: Optional metadata dictionary

        Returns:
            The published Event object
        """
        event = Event(
            event_type=event_type,
            payload=payload,
            source_agent=source_agent,
            priority=priority,
            correlation_id=correlation_id,
            metadata=metadata or {}
        )

        async with self._lock:
            # Add to history
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)

            self._stats["total_published"] += 1

        logger.info(
            f"Event published: {event_type} from {source_agent} "
            f"(id: {event.event_id}, priority: {priority.value})"
        )

        # Deliver to subscribers asynchronously
        await self._deliver_event(event)

        return event

    async def _deliver_event(self, event: Event):
        """
        Deliver event to all subscribed agents.

        Args:
            event: Event to deliver
        """
        subscriptions = self._subscriptions.get(event.event_type, [])

        if not subscriptions:
            logger.debug(f"No subscribers for event type: {event.event_type}")
            return

        # Sort by priority
        priority_order = {
            EventPriority.CRITICAL: 0,
            EventPriority.HIGH: 1,
            EventPriority.NORMAL: 2,
            EventPriority.LOW: 3
        }
        sorted_subs = sorted(
            subscriptions,
            key=lambda s: priority_order.get(s.priority, 2)
        )

        # Deliver to each subscriber
        delivery_tasks = []
        for subscription in sorted_subs:
            # Apply filter if present
            if subscription.filter_func:
                try:
                    if not subscription.filter_func(event):
                        continue
                except Exception as e:
                    logger.error(f"Error in filter function: {e}")
                    continue

            # Create delivery task
            task = self._deliver_to_subscriber(event, subscription)
            delivery_tasks.append(task)

        # Execute deliveries concurrently
        if delivery_tasks:
            results = await asyncio.gather(*delivery_tasks, return_exceptions=True)

            # Track stats
            for result in results:
                if isinstance(result, Exception):
                    self._stats["total_failed"] += 1
                else:
                    self._stats["total_delivered"] += 1

    async def _deliver_to_subscriber(self, event: Event, subscription: Subscription):
        """
        Deliver event to a single subscriber.

        Args:
            event: Event to deliver
            subscription: Subscription details
        """
        try:
            logger.debug(
                f"Delivering {event.event_type} to {subscription.subscriber_id}"
            )

            # Call the subscriber's callback
            if asyncio.iscoroutinefunction(subscription.callback):
                await subscription.callback(event)
            else:
                subscription.callback(event)

        except Exception as e:
            logger.error(
                f"Failed to deliver event {event.event_id} to "
                f"{subscription.subscriber_id}: {e}"
            )

            # Add to dead letter queue
            self._dead_letter_queue.append({
                "event": event.to_dict(),
                "subscriber_id": subscription.subscriber_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })

            raise

    def subscribe(
        self,
        agent_id: str,
        event_types: List[str],
        callback: Callable,
        filter_func: Optional[Callable] = None,
        priority: EventPriority = EventPriority.NORMAL
    ) -> str:
        """
        Subscribe an agent to specific event types.

        Args:
            agent_id: Unique identifier for subscribing agent
            event_types: List of event types to subscribe to
            callback: Function to call when event received
            filter_func: Optional function to filter events
            priority: Subscription priority

        Returns:
            Subscription ID
        """
        subscription = Subscription(
            subscriber_id=agent_id,
            event_types=set(event_types),
            callback=callback,
            filter_func=filter_func,
            priority=priority
        )

        # Add subscription for each event type
        for event_type in event_types:
            self._subscriptions[event_type].append(subscription)

        logger.info(
            f"Agent {agent_id} subscribed to: {', '.join(event_types)}"
        )

        return agent_id

    def unsubscribe(self, agent_id: str, event_types: Optional[List[str]] = None):
        """
        Unsubscribe an agent from event types.

        Args:
            agent_id: Agent to unsubscribe
            event_types: Specific event types to unsubscribe from (None = all)
        """
        if event_types is None:
            # Unsubscribe from all
            for event_type in list(self._subscriptions.keys()):
                self._subscriptions[event_type] = [
                    sub for sub in self._subscriptions[event_type]
                    if sub.subscriber_id != agent_id
                ]
            logger.info(f"Agent {agent_id} unsubscribed from all events")
        else:
            # Unsubscribe from specific types
            for event_type in event_types:
                if event_type in self._subscriptions:
                    self._subscriptions[event_type] = [
                        sub for sub in self._subscriptions[event_type]
                        if sub.subscriber_id != agent_id
                    ]
            logger.info(
                f"Agent {agent_id} unsubscribed from: {', '.join(event_types)}"
            )

    def get_event_history(
        self,
        event_type: Optional[str] = None,
        source_agent: Optional[str] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        Get event history with optional filtering.

        Args:
            event_type: Filter by event type
            source_agent: Filter by source agent
            limit: Maximum number of events to return

        Returns:
            List of historical events
        """
        events = self._event_history

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if source_agent:
            events = [e for e in events if e.source_agent == source_agent]

        return events[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get message bus statistics."""
        return {
            **self._stats,
            "active_subscriptions": sum(
                len(subs) for subs in self._subscriptions.values()
            ),
            "event_history_size": len(self._event_history),
            "dead_letter_queue_size": len(self._dead_letter_queue)
        }

    def get_dead_letter_queue(self) -> List[Dict[str, Any]]:
        """Get failed event deliveries."""
        return self._dead_letter_queue.copy()

    def clear_dead_letter_queue(self):
        """Clear the dead letter queue."""
        self._dead_letter_queue.clear()
        logger.info("Dead letter queue cleared")


# Global message bus instance
_global_bus: Optional[MessageBus] = None


def get_message_bus() -> MessageBus:
    """
    Get the global message bus instance.

    Returns:
        Global MessageBus instance
    """
    global _global_bus
    if _global_bus is None:
        _global_bus = MessageBus()
    return _global_bus
