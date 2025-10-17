"""
Event Type Definitions for LiMOS Event Classification Layer
==========================================================

This module defines all event types, categories, and data models used
by the event classification system.
"""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


# Event Type Enums
# ================

class MoneyEventType(str, Enum):
    """Money/Financial event types"""
    PURCHASE = "purchase"
    RETURN = "return"
    TRANSFER = "transfer"
    AP_PAYMENT = "ap_payment"        # Accounts Payable payment
    AP_INVOICE = "ap_invoice"        # Accounts Payable invoice received
    DEPOSIT = "deposit"
    ACH = "ach"
    SALES = "sales"


class FleetEventType(str, Enum):
    """Fleet/Vehicle event types"""
    PUMP = "pump_event"              # Refueling
    REPAIR = "repair_event"          # Vehicle repair
    MAINT = "maint_event"            # Maintenance
    TRAVEL = "travel_event"          # Trip/mileage tracking


class HealthEventType(str, Enum):
    """Health/Wellness event types"""
    MEAL = "meal_event"
    EXERCISE = "exercise_event"
    HIKE = "hike_event"


class InventoryEventType(str, Enum):
    """Inventory event types"""
    STOCK = "stock_event"            # Adding items to inventory
    USE_FOOD = "use_food_event"      # Consuming inventory items
    FOOD_EXPIRY_CHECK = "food_expiry_check"  # Query for expiring items


class CalendarEventType(str, Enum):
    """Calendar event types"""
    APPOINTMENT = "appointment_event"
    REMINDER = "reminder_event"
    TASK = "task_event"


# Event Category Enum
# ===================

class EventCategory(str, Enum):
    """High-level event categories"""
    MONEY = "money"
    FLEET = "fleet"
    HEALTH = "health"
    INVENTORY = "inventory"
    CALENDAR = "calendar"


# Event Models
# ============

class ClassifiedEvent(BaseModel):
    """
    A classified event ready for module routing.

    Represents a single event that has been identified from a user command,
    with all necessary routing and data information.
    """
    event_type: str = Field(
        ...,
        description="Specific event type (e.g., 'purchase', 'pump_event')"
    )
    category: EventCategory = Field(
        ...,
        description="High-level category (money, fleet, health, etc.)"
    )
    module: str = Field(
        ...,
        description="Target module to handle this event (e.g., 'accounting', 'fleet')"
    )
    action: str = Field(
        ...,
        description="Action to perform (create, read, update, delete)"
    )
    extracted_data: Dict[str, Any] = Field(
        ...,
        description="Parsed and validated data for this event"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score 0.0-1.0"
    )
    is_primary: bool = Field(
        default=True,
        description="Whether this is the primary event in a multi-event command"
    )
    triggers_secondary: Optional[List[str]] = Field(
        default=None,
        description="List of secondary event types this event triggers"
    )

    class Config:
        schema_extra = {
            "example": {
                "event_type": "pump_event",
                "category": "fleet",
                "module": "fleet",
                "action": "create",
                "extracted_data": {
                    "price": 3.75,
                    "quantity": 12.0,
                    "unit_of_measure": "gallons",
                    "cost": 45.00,
                    "fuel_type": "regular",
                    "odometer": 45000
                },
                "confidence": 0.98,
                "is_primary": True,
                "triggers_secondary": ["purchase"]
            }
        }


class EventClassificationResult(BaseModel):
    """
    Complete result of event classification for a user command.

    Contains the primary event and any secondary events that should
    be triggered as part of handling the command.
    """
    primary_event: ClassifiedEvent = Field(
        ...,
        description="The main event identified in the command"
    )
    secondary_events: Optional[List[ClassifiedEvent]] = Field(
        default=None,
        description="Additional events triggered by the primary event"
    )
    intent: str = Field(
        ...,
        description="Human-readable description of what the user wants to do"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence score for the classification"
    )
    clarification_needed: Optional[str] = Field(
        default=None,
        description="Question to ask user if classification is ambiguous"
    )

    class Config:
        schema_extra = {
            "example": {
                "primary_event": {
                    "event_type": "pump_event",
                    "category": "fleet",
                    "module": "fleet",
                    "action": "create",
                    "extracted_data": {
                        "price": 3.75,
                        "quantity": 12.0,
                        "unit_of_measure": "gallons",
                        "cost": 45.00,
                        "fuel_type": "regular",
                        "odometer": 45000
                    },
                    "confidence": 0.98,
                    "is_primary": True,
                    "triggers_secondary": ["purchase"]
                },
                "secondary_events": [
                    {
                        "event_type": "purchase",
                        "category": "money",
                        "module": "accounting",
                        "action": "create",
                        "extracted_data": {
                            "amount": 45.00,
                            "description": "Fuel purchase",
                            "category": "gas"
                        },
                        "confidence": 0.98,
                        "is_primary": False,
                        "triggers_secondary": None
                    }
                ],
                "intent": "Log vehicle refueling and expense",
                "confidence": 0.98,
                "clarification_needed": None
            }
        }


# Event Type Mappings
# ===================

# Map event type strings to their enum values
EVENT_TYPE_MAP = {
    # Money Events
    "purchase": MoneyEventType.PURCHASE,
    "return": MoneyEventType.RETURN,
    "transfer": MoneyEventType.TRANSFER,
    "ap_payment": MoneyEventType.AP_PAYMENT,
    "ap_invoice": MoneyEventType.AP_INVOICE,
    "deposit": MoneyEventType.DEPOSIT,
    "ach": MoneyEventType.ACH,
    "sales": MoneyEventType.SALES,

    # Fleet Events
    "pump_event": FleetEventType.PUMP,
    "repair_event": FleetEventType.REPAIR,
    "maint_event": FleetEventType.MAINT,
    "travel_event": FleetEventType.TRAVEL,

    # Health Events
    "meal_event": HealthEventType.MEAL,
    "exercise_event": HealthEventType.EXERCISE,
    "hike_event": HealthEventType.HIKE,

    # Inventory Events
    "stock_event": InventoryEventType.STOCK,
    "use_food_event": InventoryEventType.USE_FOOD,
    "food_expiry_check": InventoryEventType.FOOD_EXPIRY_CHECK,

    # Calendar Events
    "appointment_event": CalendarEventType.APPOINTMENT,
    "reminder_event": CalendarEventType.REMINDER,
    "task_event": CalendarEventType.TASK,
}

# Map event types to their categories
EVENT_CATEGORY_MAP = {
    MoneyEventType.PURCHASE: EventCategory.MONEY,
    MoneyEventType.RETURN: EventCategory.MONEY,
    MoneyEventType.TRANSFER: EventCategory.MONEY,
    MoneyEventType.AP_PAYMENT: EventCategory.MONEY,
    MoneyEventType.AP_INVOICE: EventCategory.MONEY,
    MoneyEventType.DEPOSIT: EventCategory.MONEY,
    MoneyEventType.ACH: EventCategory.MONEY,
    MoneyEventType.SALES: EventCategory.MONEY,

    FleetEventType.PUMP: EventCategory.FLEET,
    FleetEventType.REPAIR: EventCategory.FLEET,
    FleetEventType.MAINT: EventCategory.FLEET,
    FleetEventType.TRAVEL: EventCategory.FLEET,

    HealthEventType.MEAL: EventCategory.HEALTH,
    HealthEventType.EXERCISE: EventCategory.HEALTH,
    HealthEventType.HIKE: EventCategory.HEALTH,

    InventoryEventType.STOCK: EventCategory.INVENTORY,
    InventoryEventType.USE_FOOD: EventCategory.INVENTORY,
    InventoryEventType.FOOD_EXPIRY_CHECK: EventCategory.INVENTORY,

    CalendarEventType.APPOINTMENT: EventCategory.CALENDAR,
    CalendarEventType.REMINDER: EventCategory.CALENDAR,
    CalendarEventType.TASK: EventCategory.CALENDAR,
}

# Map categories to modules
CATEGORY_MODULE_MAP = {
    EventCategory.MONEY: "accounting",
    EventCategory.FLEET: "fleet",
    EventCategory.HEALTH: "health",
    EventCategory.INVENTORY: "inventory",
    EventCategory.CALENDAR: "calendar",
}


# Helper Functions
# ================

def get_event_category(event_type: str) -> EventCategory:
    """Get the category for a given event type string."""
    enum_value = EVENT_TYPE_MAP.get(event_type)
    if not enum_value:
        raise ValueError(f"Unknown event type: {event_type}")
    return EVENT_CATEGORY_MAP[enum_value]


def get_event_module(event_type: str) -> str:
    """Get the module name for a given event type string."""
    category = get_event_category(event_type)
    return CATEGORY_MODULE_MAP[category]


def is_valid_event_type(event_type: str) -> bool:
    """Check if an event type string is valid."""
    return event_type in EVENT_TYPE_MAP
