"""
API Models Package
==================

Contains Pydantic models for API requests, responses, and events.
"""

from .events import (
    MoneyEventType,
    FleetEventType,
    HealthEventType,
    InventoryEventType,
    CalendarEventType,
    EventCategory,
    ClassifiedEvent,
    EventClassificationResult,
    get_event_category,
    get_event_module,
    is_valid_event_type,
)

__all__ = [
    # Event Type Enums
    "MoneyEventType",
    "FleetEventType",
    "HealthEventType",
    "InventoryEventType",
    "CalendarEventType",
    "EventCategory",

    # Event Models
    "ClassifiedEvent",
    "EventClassificationResult",

    # Helper Functions
    "get_event_category",
    "get_event_module",
    "is_valid_event_type",
]
