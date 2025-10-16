# Event Classification Layer Specification

## Overview

The Event Classification Layer is a new architectural component that sits between the natural language parser (Claude API) and the module routing logic in the LiMOS Orchestrator. Its purpose is to identify and classify the type of event(s) described in user commands before routing them to specific modules for processing.

## Architecture

### Current Flow (Before Event Classification)
```
User Command → Claude Parser → Module Router → Module Handler → Response
                    ↓
              [module, action, extracted_data]
```

### New Flow (With Event Classification)
```
User Command → Claude Parser → Event Classifier → Module Router → Module Handler → Response
                    ↓               ↓
              [intent, data]   [event_types, modules, routing_plan]
```

## Event Type Taxonomy

### Core Event Categories

Events are organized hierarchically. A single user command may trigger multiple events.

#### 1. Money Events
Money events involve financial transactions and always route to the `accounting` module.

**Event Types:**
- **Purchase**: Buying goods or services for cash/credit
  - Example: "I bought $50 of groceries at Safeway"
  - Creates: Expense increase, Asset decrease (cash/credit card)

- **Return**: Returning goods for refund
  - Example: "I returned the shirt to Target for $29.99"
  - Creates: Expense decrease, Asset increase

- **Transfer**: Moving money between accounts
  - Example: "Transfer $500 from checking to savings"
  - Creates: One asset decrease, one asset increase

- **AP_Payment**: Accounts Payable payment (paying a bill)
  - Example: "Paid the electric bill of $85"
  - Creates: Liability decrease, Asset decrease

- **AP_Invoice**: Accounts Payable invoice (receiving a bill)
  - Example: "Received electric bill for $85"
  - Creates: Expense increase, Liability increase

- **Deposit**: Money coming in (income/revenue)
  - Example: "Received paycheck deposit of $3,200"
  - Creates: Asset increase, Income increase

- **ACH**: Automated Clearing House transaction
  - Example: "ACH payment to credit card of $1,500"
  - Creates: Liability decrease, Asset decrease

- **Sales**: Selling goods or services
  - Example: "Sold old laptop for $400"
  - Creates: Asset increase (cash), Asset decrease (laptop) or Revenue increase

#### 2. Fleet Events
Fleet events involve vehicles and route to the `fleet` module. May also trigger Money Events.

**Event Types:**
- **PumpEvent** (Refuel): Refueling a vehicle
  - Example: "Filled up gas, 12 gallons, $45, odometer 45000"
  - Data: gallons, cost, odometer, fuel_type, location
  - Triggers: Money Event (Purchase)

- **RepairEvent**: Vehicle repair or service
  - Example: "Oil change at Jiffy Lube, $59.99, odometer 45500"
  - Data: service_type, cost, odometer, vendor, description
  - Triggers: Money Event (Purchase)

- **MaintEvent** (Maintenance): Scheduled maintenance
  - Example: "Replaced air filter, $25, DIY"
  - Data: maintenance_type, cost, odometer, parts, labor
  - Triggers: Money Event (Purchase if cost > 0)

- **TravelEvent**: Trip logging for mileage tracking
  - Example: "Drove to San Francisco, 240 miles"
  - Data: start_location, end_location, distance, purpose
  - May Trigger: Money Event (if business mileage reimbursement)

#### 3. Health Events
Health events involve nutrition, exercise, and wellness activities. Route to `health` module.

**Event Types:**
- **MealEvent**: Recording meals and nutrition
  - Example: "Had oatmeal with blueberries for breakfast, 350 calories"
  - Data: meal_type, items, calories, macros, time

- **ExerciseEvent**: Physical activity tracking
  - Example: "Ran 5 miles in 42 minutes"
  - Data: activity_type, duration, distance, calories_burned

- **HikeEvent**: Hiking activity (specialized ExerciseEvent)
  - Example: "Hiked Mt. Tam, 8 miles, 2000ft elevation gain"
  - Data: trail_name, distance, elevation_gain, duration, difficulty

#### 4. Inventory Events
Inventory events track household items. Route to `inventory` module.

**Event Types:**
- **StockEvent**: Adding items to inventory
  - Example: "Bought 2 gallons of milk, expires 10/20"
  - Data: item_name, quantity, location, expiration_date
  - May Trigger: Money Event (Purchase)

- **UseEvent**: Consuming or using inventory items
  - Example: "Used 1 can of tomato sauce"
  - Data: item_name, quantity_used

- **ExpiryCheck**: Checking for expired items
  - Example: "What's about to expire in the fridge?"
  - Data: location, days_threshold

#### 5. Calendar Events
Calendar events involve scheduling and time management. Route to `calendar` module.

**Event Types:**
- **AppointmentEvent**: Scheduled appointments
  - Example: "Doctor appointment Tuesday at 2pm"
  - Data: title, date, time, duration, location, attendees

- **ReminderEvent**: One-time or recurring reminders
  - Example: "Remind me to call mom tomorrow at 9am"
  - Data: title, reminder_time, recurrence_rule

- **TaskEvent**: To-do items and task tracking
  - Example: "Add task: clean garage, due Friday"
  - Data: title, description, due_date, priority, status

## Event Classification Logic

### Classification Rules

The Event Classifier uses a rule-based system combined with AI parsing to determine event types.

#### Primary Indicators

**Money Keywords:**
- `bought`, `purchased`, `spent`, `paid`, `cost`, `$`, `dollars`
- `returned`, `refund`
- `deposit`, `income`, `paycheck`, `revenue`
- `bill`, `invoice`
- `transfer`, `moved money`

**Fleet Keywords:**
- `gas`, `fuel`, `gallons`, `filled up`, `refuel`, `pump`
- `oil change`, `repair`, `mechanic`, `service`
- `maintenance`, `replaced`, `fixed`
- `drove`, `miles`, `odometer`, `mileage`

**Health Keywords:**
- `ate`, `meal`, `breakfast`, `lunch`, `dinner`, `snack`, `calories`
- `ran`, `walked`, `exercise`, `workout`, `gym`
- `hiked`, `trail`, `elevation`

**Inventory Keywords:**
- `bought` + `expires`, `stock`, `inventory`
- `used`, `consumed`, `ran out of`
- `expiring`, `expired`, `check expiration`

**Calendar Keywords:**
- `appointment`, `meeting`, `schedule`
- `remind me`, `reminder`, `don't forget`
- `task`, `todo`, `due`, `deadline`

#### Multi-Event Detection

Some commands trigger multiple events:

**Example 1: Refueling**
- Input: "Filled up gas, 12 gallons, $45, odometer 45000"
- Events:
  1. `PumpEvent` (Fleet) - Primary event
  2. `Purchase` (Money) - Secondary event
- Routing: Fleet module handles PumpEvent and creates Money Event for accounting

**Example 2: Grocery Shopping with Expiring Items**
- Input: "Bought 2 gallons of milk for $7.50, expires 10/20"
- Events:
  1. `Purchase` (Money) - Primary event
  2. `StockEvent` (Inventory) - Secondary event
- Routing: Accounting module handles Purchase, then routes to Inventory for StockEvent

### Confidence Scoring

Each event classification receives a confidence score:

- **High (0.85-1.0)**: Clear indicators present, unambiguous
- **Medium (0.70-0.84)**: Some ambiguity, may need clarification
- **Low (<0.70)**: Unclear intent, requires user clarification

## Implementation Plan

### Phase 1: Core Event Classification

**Files to Create:**
1. `/projects/api/routers/event_classifier.py` - Core classification logic
2. `/projects/api/models/events.py` - Event type definitions (Enums, Pydantic models)
3. `/projects/api/routers/event_rules.md` - Human-readable classification rules

**Files to Modify:**
1. `/projects/api/routers/orchestrator.py` - Add event classification step

### Phase 2: Enhanced Claude Prompt

Update the Claude system prompt to include event type identification in its response:

```json
{
  "module": "fleet",
  "action": "create",
  "intent": "Log vehicle refueling event",
  "event_types": ["PumpEvent", "Purchase"],  // NEW
  "primary_event": "PumpEvent",              // NEW
  "extracted_data": { ... },
  "confidence": 0.98
}
```

### Phase 3: Module Integration

Update module handlers to be event-aware:
- `route_to_fleet()` - Handle PumpEvent, RepairEvent, MaintEvent, TravelEvent
- `route_to_accounting()` - Handle Money Events with proper transaction types
- `route_to_health()` - Handle MealEvent, ExerciseEvent, HikeEvent
- `route_to_inventory()` - Handle StockEvent, UseEvent, ExpiryCheck
- `route_to_calendar()` - Handle AppointmentEvent, ReminderEvent, TaskEvent

### Phase 4: Cross-Module Event Propagation

Implement event chaining for multi-event commands:

```python
def process_multi_event_command(primary_event, secondary_events):
    """
    Process a command that triggers multiple events across modules.

    Example: PumpEvent → also creates Purchase money event
    """
    results = {}

    # Process primary event
    primary_result = route_to_module(primary_event.module, primary_event.action, primary_event.data)
    results['primary'] = primary_result

    # Process secondary events
    for event in secondary_events:
        secondary_result = route_to_module(event.module, event.action, event.data)
        results[event.event_type] = secondary_result

    return results
```

## Data Models

### EventType Enum

```python
from enum import Enum

class MoneyEventType(str, Enum):
    PURCHASE = "purchase"
    RETURN = "return"
    TRANSFER = "transfer"
    AP_PAYMENT = "ap_payment"
    AP_INVOICE = "ap_invoice"
    DEPOSIT = "deposit"
    ACH = "ach"
    SALES = "sales"

class FleetEventType(str, Enum):
    PUMP = "pump_event"
    REPAIR = "repair_event"
    MAINT = "maint_event"
    TRAVEL = "travel_event"

class HealthEventType(str, Enum):
    MEAL = "meal_event"
    EXERCISE = "exercise_event"
    HIKE = "hike_event"

class InventoryEventType(str, Enum):
    STOCK = "stock_event"
    USE = "use_event"
    EXPIRY_CHECK = "expiry_check"

class CalendarEventType(str, Enum):
    APPOINTMENT = "appointment_event"
    REMINDER = "reminder_event"
    TASK = "task_event"
```

### ClassifiedEvent Model

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class ClassifiedEvent(BaseModel):
    """A classified event ready for module routing."""
    event_type: str = Field(..., description="Type of event (e.g., 'purchase', 'pump_event')")
    category: str = Field(..., description="Event category (e.g., 'money', 'fleet')")
    module: str = Field(..., description="Target module (e.g., 'accounting', 'fleet')")
    action: str = Field(..., description="Action to perform (e.g., 'create', 'read')")
    extracted_data: Dict[str, Any] = Field(..., description="Parsed data for this event")
    confidence: float = Field(..., description="Confidence score 0.0-1.0")
    is_primary: bool = Field(default=True, description="Whether this is the primary event")
    triggers_secondary: Optional[List[str]] = Field(default=None, description="Secondary event types this triggers")

class EventClassificationResult(BaseModel):
    """Result of event classification."""
    primary_event: ClassifiedEvent
    secondary_events: Optional[List[ClassifiedEvent]] = None
    intent: str = Field(..., description="Human-readable description of intent")
    confidence: float = Field(..., description="Overall confidence score")
    clarification_needed: Optional[str] = None
```

## Example Classifications

### Example 1: Simple Purchase

**Input:** "I bought $50 of groceries at Safeway"

**Classification Result:**
```json
{
  "primary_event": {
    "event_type": "purchase",
    "category": "money",
    "module": "accounting",
    "action": "create",
    "extracted_data": {
      "amount": 50.00,
      "description": "Groceries at Safeway",
      "category": "groceries",
      "merchant": "Safeway"
    },
    "confidence": 0.95,
    "is_primary": true,
    "triggers_secondary": null
  },
  "secondary_events": null,
  "intent": "Record grocery purchase expense",
  "confidence": 0.95
}
```

### Example 2: Refueling (Multi-Event)

**Input:** "Filled up gas, 12 gallons, $45, odometer 45000"

**Classification Result:**
```json
{
  "primary_event": {
    "event_type": "pump_event",
    "category": "fleet",
    "module": "fleet",
    "action": "create",
    "extracted_data": {
      "gallons": 12.0,
      "cost": 45.00,
      "odometer": 45000,
      "fuel_type": "regular"
    },
    "confidence": 0.98,
    "is_primary": true,
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
        "category": "gas",
        "merchant": "Gas Station"
      },
      "confidence": 0.98,
      "is_primary": false,
      "triggers_secondary": null
    }
  ],
  "intent": "Log vehicle refueling and expense",
  "confidence": 0.98
}
```

### Example 3: Query (Read Operation)

**Input:** "How much did I spend on food this month?"

**Classification Result:**
```json
{
  "primary_event": {
    "event_type": "query",
    "category": "money",
    "module": "accounting",
    "action": "read",
    "extracted_data": {
      "category": "food",
      "time_period": "current_month",
      "query_type": "sum"
    },
    "confidence": 0.90,
    "is_primary": true,
    "triggers_secondary": null
  },
  "secondary_events": null,
  "intent": "Query spending by category for current month",
  "confidence": 0.90
}
```

## Benefits

### 1. Clear Separation of Concerns
- Parsing (Claude AI) focuses on understanding natural language
- Classification focuses on categorizing the business event
- Routing focuses on directing to the correct module
- Handling focuses on executing the business logic

### 2. Extensibility
- New event types can be added without modifying the parser
- Rules are defined in Markdown for easy human editing
- Event taxonomy grows with the system

### 3. Multi-Event Support
- Commands can naturally trigger multiple related events
- Cross-module coordination becomes explicit
- Better auditability and logging

### 4. Improved Accuracy
- Specialized classification logic per event category
- Confidence scoring helps identify ambiguous commands
- Clear fallback paths for uncertain classifications

### 5. Better User Experience
- More accurate routing to appropriate modules
- Better handling of complex commands
- Clearer error messages when intent is ambiguous

## Future Enhancements

### 1. Machine Learning Classification
- Train a classification model on historical commands
- Use ML to suggest new event types based on patterns
- Improve confidence scoring with learned patterns

### 2. Event Relationship Mapping
- Define explicit relationships between event types
- Automatic secondary event generation based on rules
- Event composition for complex business flows

### 3. Context-Aware Classification
- Use historical context to improve classification
- Learn user-specific patterns and preferences
- Time-of-day, location-based classification hints

### 4. Event Validation Rules
- Define validation rules per event type
- Check required fields before routing
- Suggest missing data to user

### 5. Event Analytics
- Track most common event types
- Identify misclassifications for improvement
- Generate insights from event patterns

## Migration Path

### Step 1: Add Event Classification (Non-Breaking)
- Implement event classifier alongside existing routing
- Run both in parallel, log differences
- Validate classification accuracy

### Step 2: Update Module Handlers (Gradual)
- Start with one module (e.g., fleet)
- Update handlers to be event-aware
- Test thoroughly before moving to next module

### Step 3: Enable Multi-Event Support
- Implement event chaining logic
- Update orchestrator to handle multiple results
- Test cross-module scenarios

### Step 4: Full Cutover
- Switch orchestrator to use event classification
- Remove old routing logic
- Monitor and refine

## Testing Strategy

### Unit Tests
- Test individual event classifiers
- Test confidence scoring
- Test multi-event detection

### Integration Tests
- Test end-to-end classification and routing
- Test multi-event scenarios
- Test edge cases and ambiguous commands

### User Acceptance Tests
- Test with real user commands
- Measure classification accuracy
- Gather feedback on clarification messages

## Success Metrics

- **Classification Accuracy**: >95% correct event type identification
- **Confidence Score Accuracy**: Correlation between confidence and correctness
- **Multi-Event Detection**: >90% correct identification of secondary events
- **Clarification Rate**: <10% of commands require clarification
- **Response Time**: <200ms added latency for classification

---

## Status

**Current Status**: Planning / Specification Complete

**Next Steps**:
1. Review and approve this specification
2. Create event type enums and models
3. Implement core event classifier
4. Update Claude system prompt
5. Test with sample commands
6. Integrate with orchestrator

**Owner**: To be assigned

**Last Updated**: 2025-10-16
