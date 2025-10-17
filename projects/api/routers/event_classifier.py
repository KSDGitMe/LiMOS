"""
Event Classifier
================

Classifies user commands into event types using keyword matching and
applies parsing conditionals to calculate missing data.

Based on rules defined in EVENT_CLASSIFICATION_RULES.md
"""

from typing import Dict, Any, List, Optional, Tuple
from projects.api.models.events import (
    ClassifiedEvent,
    EventClassificationResult,
    EventCategory,
    MoneyEventType,
    FleetEventType,
    HealthEventType,
    InventoryEventType,
    CalendarEventType,
    get_event_module,
)


# Keyword Definitions
# ===================

# Money Event Keywords
PURCHASE_KEYWORDS = ["bought", "purchased", "spent", "paid for", "cost", "$", "got", "picked up"]
RETURN_KEYWORDS = ["returned", "return", "refund", "took back", "sent back"]
TRANSFER_KEYWORDS = ["transfer", "moved", "transferred", "sent money"]
AP_PAYMENT_KEYWORDS = ["paid bill", "paid invoice", "payment for", "paid the", "bill payment"]
AP_INVOICE_KEYWORDS = ["received bill", "got invoice", "bill came", "was billed", "charged"]
DEPOSIT_KEYWORDS = ["deposit", "received", "got paid", "income", "paycheck", "earned", "revenue", "payment received"]
ACH_KEYWORDS = ["ACH", "automated payment", "auto-pay", "automatic deduction"]
SALES_KEYWORDS = ["sold", "sale", "sold for", "revenue from sale"]

# Fleet Event Keywords
PUMP_KEYWORDS = ["gas", "fuel", "filled up", "refuel", "pump", "gallons", "diesel", "premium", "additive", "DEF"]
REPAIR_KEYWORDS = ["repair", "fixed", "mechanic", "service", "shop", "repaired"]
MAINT_KEYWORDS = ["oil change", "maintenance", "replaced", "changed", "serviced", "tune-up", "filter", "fluids", "DIY"]
TRAVEL_KEYWORDS = ["drove", "trip to", "drive", "traveled", "miles", "mileage", "business trip", "started driving", "stopped for the day"]

# Health Event Keywords
MEAL_KEYWORDS = ["ate", "had", "meal", "breakfast", "lunch", "dinner", "snack", "food", "calories"]
EXERCISE_KEYWORDS = ["ran", "walked", "jogged", "workout", "exercise", "gym", "lifted", "swam", "biked", "cardio", "training"]
HIKE_KEYWORDS = ["hiked", "hike", "trail", "trekking", "mountain", "elevation gain"]

# Inventory Event Keywords
STOCK_KEYWORDS = ["bought", "stocked", "got", "purchased"]  # Must also have expiration
EXPIRATION_KEYWORDS = ["expires", "expiry", "best by", "use by"]
USE_FOOD_KEYWORDS = ["used", "consumed", "ate", "finished", "ran out of", "opened"]
FOOD_EXPIRY_CHECK_KEYWORDS = ["expiring", "expired", "about to expire", "check expiration", "what's expiring", "going bad"]

# Calendar Event Keywords
APPOINTMENT_KEYWORDS = ["appointment", "meeting", "scheduled", "book", "reserve", "doctor", "dentist", "call scheduled"]
REMINDER_KEYWORDS = ["remind me", "reminder", "don't forget", "alert me", "notification"]
TASK_KEYWORDS = ["task", "todo", "to-do", "need to", "must", "add task", "due"]


# Classifier Functions
# ====================

def classify_event(
    command: str,
    parsed_data: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> EventClassificationResult:
    """
    Classify a user command into one or more event types.

    Args:
        command: Original user command text
        parsed_data: Data extracted from command (e.g., by Claude)
        context: Optional context information

    Returns:
        EventClassificationResult with primary and optional secondary events
    """
    # Check if parsed_data already contains event types (from Claude)
    if "event_types" in parsed_data and "primary_event" in parsed_data:
        return classify_from_claude_response(parsed_data)

    # Fallback to keyword-based classification
    return classify_from_keywords(command, parsed_data, context)


def classify_from_claude_response(parsed_data: Dict[str, Any]) -> EventClassificationResult:
    """
    Build classification result from Claude's response.

    Claude should provide:
    - event_types: List of event type strings
    - primary_event: Which event is primary
    - extracted_data: Parsed data for the event
    """
    event_types = parsed_data.get("event_types", [])
    primary_event_type = parsed_data.get("primary_event")
    extracted_data = parsed_data.get("extracted_data", {})
    confidence = parsed_data.get("confidence", 0.0)
    intent = parsed_data.get("intent", "")

    # Apply parsing conditionals to extracted data
    extracted_data = apply_parsing_conditionals(primary_event_type, extracted_data)

    # Build primary event
    primary_event = ClassifiedEvent(
        event_type=primary_event_type,
        category=get_event_category_str(primary_event_type),
        module=get_event_module(primary_event_type),
        action=parsed_data.get("action", "create"),
        extracted_data=extracted_data,
        confidence=confidence,
        is_primary=True,
        triggers_secondary=event_types[1:] if len(event_types) > 1 else None
    )

    # Build secondary events
    secondary_events = []
    if len(event_types) > 1:
        for event_type in event_types[1:]:
            secondary_data = build_secondary_event_data(primary_event_type, event_type, extracted_data)
            if secondary_data:
                secondary_events.append(ClassifiedEvent(
                    event_type=event_type,
                    category=get_event_category_str(event_type),
                    module=get_event_module(event_type),
                    action="create",
                    extracted_data=secondary_data,
                    confidence=confidence,
                    is_primary=False,
                    triggers_secondary=None
                ))

    return EventClassificationResult(
        primary_event=primary_event,
        secondary_events=secondary_events if secondary_events else None,
        intent=intent,
        confidence=confidence,
        clarification_needed=parsed_data.get("clarification_needed")
    )


def classify_from_keywords(
    command: str,
    parsed_data: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> EventClassificationResult:
    """
    Keyword-based classification fallback.

    Analyzes command text for keywords and determines event type.
    """
    command_lower = command.lower()

    # Try to classify in priority order (most specific first)
    result = None

    # Fleet Events (high priority - specific keywords)
    if any(kw in command_lower for kw in PUMP_KEYWORDS):
        result = classify_pump_event(command_lower, parsed_data)
    elif any(kw in command_lower for kw in TRAVEL_KEYWORDS):
        result = classify_travel_event(command_lower, parsed_data)
    elif any(kw in command_lower for kw in REPAIR_KEYWORDS):
        result = classify_repair_event(command_lower, parsed_data)
    elif any(kw in command_lower for kw in MAINT_KEYWORDS):
        result = classify_maint_event(command_lower, parsed_data)

    # Inventory Events (check for expiration context)
    elif any(kw in command_lower for kw in FOOD_EXPIRY_CHECK_KEYWORDS):
        result = classify_food_expiry_check(command_lower, parsed_data)
    elif any(kw in command_lower for kw in USE_FOOD_KEYWORDS) and not any(kw in command_lower for kw in MEAL_KEYWORDS):
        result = classify_use_food_event(command_lower, parsed_data)
    elif any(kw in command_lower for kw in STOCK_KEYWORDS) and any(kw in command_lower for kw in EXPIRATION_KEYWORDS):
        result = classify_stock_event(command_lower, parsed_data)

    # Money Events
    elif any(kw in command_lower for kw in RETURN_KEYWORDS):
        result = classify_return_event(command_lower, parsed_data)
    elif any(kw in command_lower for kw in TRANSFER_KEYWORDS):
        result = classify_transfer_event(command_lower, parsed_data)
    elif any(kw in command_lower for kw in DEPOSIT_KEYWORDS):
        result = classify_deposit_event(command_lower, parsed_data)
    elif any(kw in command_lower for kw in AP_PAYMENT_KEYWORDS):
        result = classify_ap_payment_event(command_lower, parsed_data)
    elif any(kw in command_lower for kw in AP_INVOICE_KEYWORDS):
        result = classify_ap_invoice_event(command_lower, parsed_data)
    elif any(kw in command_lower for kw in SALES_KEYWORDS):
        result = classify_sales_event(command_lower, parsed_data)
    elif any(kw in command_lower for kw in ACH_KEYWORDS):
        result = classify_ach_event(command_lower, parsed_data)
    elif any(kw in command_lower for kw in PURCHASE_KEYWORDS):
        result = classify_purchase_event(command_lower, parsed_data)

    # Health Events
    elif any(kw in command_lower for kw in HIKE_KEYWORDS):
        result = classify_hike_event(command_lower, parsed_data)
    elif any(kw in command_lower for kw in EXERCISE_KEYWORDS):
        result = classify_exercise_event(command_lower, parsed_data)
    elif any(kw in command_lower for kw in MEAL_KEYWORDS):
        result = classify_meal_event(command_lower, parsed_data)

    # Calendar Events
    elif any(kw in command_lower for kw in REMINDER_KEYWORDS):
        result = classify_reminder_event(command_lower, parsed_data)
    elif any(kw in command_lower for kw in TASK_KEYWORDS):
        result = classify_task_event(command_lower, parsed_data)
    elif any(kw in command_lower for kw in APPOINTMENT_KEYWORDS):
        result = classify_appointment_event(command_lower, parsed_data)

    if result:
        return result

    # No clear classification - low confidence
    return EventClassificationResult(
        primary_event=ClassifiedEvent(
            event_type="unknown",
            category=EventCategory.MONEY,  # Default to money
            module="accounting",
            action="create",
            extracted_data=parsed_data,
            confidence=0.3,
            is_primary=True,
            triggers_secondary=None
        ),
        secondary_events=None,
        intent="Unable to classify command",
        confidence=0.3,
        clarification_needed="I'm not sure what type of event this is. Could you clarify?"
    )


# Event-Specific Classifiers
# ===========================

def classify_pump_event(command: str, data: Dict[str, Any]) -> EventClassificationResult:
    """Classify refueling event with conditional parsing."""
    # Apply PumpEvent parsing conditionals
    parsed_data = apply_pump_event_conditionals(data)

    # Calculate confidence
    confidence = 0.7
    if parsed_data.get("gallons") and parsed_data.get("cost"):
        confidence += 0.1
    if parsed_data.get("odometer"):
        confidence += 0.1
    if parsed_data.get("price"):
        confidence += 0.05

    confidence = min(confidence, 1.0)

    primary_event = ClassifiedEvent(
        event_type=FleetEventType.PUMP.value,
        category=EventCategory.FLEET,
        module="fleet",
        action="create",
        extracted_data=parsed_data,
        confidence=confidence,
        is_primary=True,
        triggers_secondary=["purchase"] if parsed_data.get("cost", 0) > 0 else None
    )

    # Create secondary Purchase event if cost > 0
    secondary_events = []
    if parsed_data.get("cost", 0) > 0:
        secondary_events.append(ClassifiedEvent(
            event_type=MoneyEventType.PURCHASE.value,
            category=EventCategory.MONEY,
            module="accounting",
            action="create",
            extracted_data={
                "amount": parsed_data.get("cost"),
                "description": "Fuel purchase",
                "category": "gas",
            },
            confidence=confidence,
            is_primary=False,
            triggers_secondary=None
        ))

    return EventClassificationResult(
        primary_event=primary_event,
        secondary_events=secondary_events if secondary_events else None,
        intent="Log vehicle refueling event" + (" and expense" if secondary_events else ""),
        confidence=confidence,
        clarification_needed=None
    )


def classify_purchase_event(command: str, data: Dict[str, Any]) -> EventClassificationResult:
    """Classify purchase event."""
    confidence = 0.85
    if data.get("amount") and data.get("description"):
        confidence = 0.90
    if data.get("merchant"):
        confidence += 0.05

    confidence = min(confidence, 1.0)

    primary_event = ClassifiedEvent(
        event_type=MoneyEventType.PURCHASE.value,
        category=EventCategory.MONEY,
        module="accounting",
        action="create",
        extracted_data=data,
        confidence=confidence,
        is_primary=True,
        triggers_secondary=None
    )

    return EventClassificationResult(
        primary_event=primary_event,
        secondary_events=None,
        intent="Record purchase expense",
        confidence=confidence,
        clarification_needed=None
    )


def classify_stock_event(command: str, data: Dict[str, Any]) -> EventClassificationResult:
    """Classify food inventory stock event."""
    confidence = 0.85
    if data.get("item_name") and data.get("quantity"):
        confidence = 0.90
    if data.get("expiration_date"):
        confidence += 0.05

    confidence = min(confidence, 1.0)

    primary_event = ClassifiedEvent(
        event_type=InventoryEventType.STOCK.value,
        category=EventCategory.INVENTORY,
        module="inventory",
        action="create",
        extracted_data=data,
        confidence=confidence,
        is_primary=True,
        triggers_secondary=["purchase"] if data.get("cost") else None
    )

    # Create secondary Purchase event if cost mentioned
    secondary_events = []
    if data.get("cost"):
        secondary_events.append(ClassifiedEvent(
            event_type=MoneyEventType.PURCHASE.value,
            category=EventCategory.MONEY,
            module="accounting",
            action="create",
            extracted_data={
                "amount": data.get("cost"),
                "description": f"Purchase: {data.get('item_name', 'grocery item')}",
                "category": "groceries",
            },
            confidence=confidence,
            is_primary=False,
            triggers_secondary=None
        ))

    return EventClassificationResult(
        primary_event=primary_event,
        secondary_events=secondary_events if secondary_events else None,
        intent="Add item to food inventory" + (" and record expense" if secondary_events else ""),
        confidence=confidence,
        clarification_needed=None
    )


# Stub classifiers for other event types (to be expanded)

def classify_return_event(command: str, data: Dict[str, Any]) -> EventClassificationResult:
    return create_simple_event_result(MoneyEventType.RETURN.value, EventCategory.MONEY, "accounting", data, 0.85, "Record product return")

def classify_transfer_event(command: str, data: Dict[str, Any]) -> EventClassificationResult:
    return create_simple_event_result(MoneyEventType.TRANSFER.value, EventCategory.MONEY, "accounting", data, 0.88, "Transfer money between accounts")

def classify_deposit_event(command: str, data: Dict[str, Any]) -> EventClassificationResult:
    return create_simple_event_result(MoneyEventType.DEPOSIT.value, EventCategory.MONEY, "accounting", data, 0.85, "Record deposit/income")

def classify_ap_payment_event(command: str, data: Dict[str, Any]) -> EventClassificationResult:
    return create_simple_event_result(MoneyEventType.AP_PAYMENT.value, EventCategory.MONEY, "accounting", data, 0.82, "Record bill payment")

def classify_ap_invoice_event(command: str, data: Dict[str, Any]) -> EventClassificationResult:
    return create_simple_event_result(MoneyEventType.AP_INVOICE.value, EventCategory.MONEY, "accounting", data, 0.80, "Record received bill/invoice")

def classify_sales_event(command: str, data: Dict[str, Any]) -> EventClassificationResult:
    return create_simple_event_result(MoneyEventType.SALES.value, EventCategory.MONEY, "accounting", data, 0.85, "Record sale of item")

def classify_ach_event(command: str, data: Dict[str, Any]) -> EventClassificationResult:
    return create_simple_event_result(MoneyEventType.ACH.value, EventCategory.MONEY, "accounting", data, 0.88, "Record ACH transaction")

def classify_travel_event(command: str, data: Dict[str, Any]) -> EventClassificationResult:
    return create_simple_event_result(FleetEventType.TRAVEL.value, EventCategory.FLEET, "fleet", data, 0.85, "Log trip for mileage tracking")

def classify_repair_event(command: str, data: Dict[str, Any]) -> EventClassificationResult:
    return create_simple_event_result(FleetEventType.REPAIR.value, EventCategory.FLEET, "fleet", data, 0.85, "Log vehicle repair")

def classify_maint_event(command: str, data: Dict[str, Any]) -> EventClassificationResult:
    return create_simple_event_result(FleetEventType.MAINT.value, EventCategory.FLEET, "fleet", data, 0.83, "Log vehicle maintenance")

def classify_meal_event(command: str, data: Dict[str, Any]) -> EventClassificationResult:
    return create_simple_event_result(HealthEventType.MEAL.value, EventCategory.HEALTH, "health", data, 0.80, "Log meal")

def classify_exercise_event(command: str, data: Dict[str, Any]) -> EventClassificationResult:
    return create_simple_event_result(HealthEventType.EXERCISE.value, EventCategory.HEALTH, "health", data, 0.85, "Log exercise activity")

def classify_hike_event(command: str, data: Dict[str, Any]) -> EventClassificationResult:
    return create_simple_event_result(HealthEventType.HIKE.value, EventCategory.HEALTH, "health", data, 0.88, "Log hiking activity")

def classify_use_food_event(command: str, data: Dict[str, Any]) -> EventClassificationResult:
    return create_simple_event_result(InventoryEventType.USE_FOOD.value, EventCategory.INVENTORY, "inventory", data, 0.80, "Record food item usage")

def classify_food_expiry_check(command: str, data: Dict[str, Any]) -> EventClassificationResult:
    return create_simple_event_result(InventoryEventType.FOOD_EXPIRY_CHECK.value, EventCategory.INVENTORY, "inventory", data, 0.90, "Check for expiring food items", action="read")

def classify_appointment_event(command: str, data: Dict[str, Any]) -> EventClassificationResult:
    return create_simple_event_result(CalendarEventType.APPOINTMENT.value, EventCategory.CALENDAR, "calendar", data, 0.85, "Schedule appointment")

def classify_reminder_event(command: str, data: Dict[str, Any]) -> EventClassificationResult:
    return create_simple_event_result(CalendarEventType.REMINDER.value, EventCategory.CALENDAR, "calendar", data, 0.88, "Set reminder")

def classify_task_event(command: str, data: Dict[str, Any]) -> EventClassificationResult:
    return create_simple_event_result(CalendarEventType.TASK.value, EventCategory.CALENDAR, "calendar", data, 0.82, "Create task/todo")


# Parsing Conditionals
# ====================

def apply_parsing_conditionals(event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply parsing conditionals based on event type to calculate missing fields.

    Implements the conditional rules from EVENT_CLASSIFICATION_RULES.md
    """
    if event_type == FleetEventType.PUMP.value or event_type == "pump_event":
        return apply_pump_event_conditionals(data)

    return data


def apply_pump_event_conditionals(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply PumpEvent parsing conditionals.

    Rules from EVENT_CLASSIFICATION_RULES.md:
    - IF Have(cost) AND Have(price) AND Missing(gallons) → calculate gallons
    - IF Have(gallons) AND Have(price) AND Missing(cost) → calculate cost
    """
    result = data.copy()

    cost = result.get("cost")
    price = result.get("price")
    gallons = result.get("gallons") or result.get("quantity")

    # Calculate gallons if missing
    if cost and price and not gallons:
        result["gallons"] = cost / price
        result["quantity"] = result["gallons"]
        result["unit_of_measure"] = "gallons"

    # Calculate cost if missing
    elif gallons and price and not cost:
        result["cost"] = gallons * price

    # Ensure we have quantity and unit_of_measure
    if gallons and not result.get("quantity"):
        result["quantity"] = gallons
        result["unit_of_measure"] = "gallons"

    return result


def build_secondary_event_data(
    primary_event_type: str,
    secondary_event_type: str,
    primary_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Build data for a secondary event based on the primary event.

    E.g., PumpEvent → Purchase (use cost from PumpEvent)
    """
    if secondary_event_type == "purchase" or secondary_event_type == MoneyEventType.PURCHASE.value:
        # Extract cost from primary event
        amount = primary_data.get("cost") or primary_data.get("amount")
        if not amount:
            return None

        return {
            "amount": amount,
            "description": f"{primary_event_type.replace('_', ' ').title()} expense",
            "category": get_category_for_event(primary_event_type),
        }

    return None


# Helper Functions
# ================

def create_simple_event_result(
    event_type: str,
    category: EventCategory,
    module: str,
    data: Dict[str, Any],
    confidence: float,
    intent: str,
    action: str = "create"
) -> EventClassificationResult:
    """Helper to create a simple single-event result."""
    primary_event = ClassifiedEvent(
        event_type=event_type,
        category=category,
        module=module,
        action=action,
        extracted_data=data,
        confidence=confidence,
        is_primary=True,
        triggers_secondary=None
    )

    return EventClassificationResult(
        primary_event=primary_event,
        secondary_events=None,
        intent=intent,
        confidence=confidence,
        clarification_needed=None
    )


def get_event_category_str(event_type: str) -> EventCategory:
    """Get EventCategory enum from event type string."""
    if event_type in [e.value for e in MoneyEventType]:
        return EventCategory.MONEY
    elif event_type in [e.value for e in FleetEventType]:
        return EventCategory.FLEET
    elif event_type in [e.value for e in HealthEventType]:
        return EventCategory.HEALTH
    elif event_type in [e.value for e in InventoryEventType]:
        return EventCategory.INVENTORY
    elif event_type in [e.value for e in CalendarEventType]:
        return EventCategory.CALENDAR
    return EventCategory.MONEY  # Default


def get_category_for_event(event_type: str) -> str:
    """Get accounting category for an event type."""
    category_map = {
        "pump_event": "gas",
        "repair_event": "auto_repair",
        "maint_event": "auto_maintenance",
        "stock_event": "groceries",
    }
    return category_map.get(event_type, "general")
