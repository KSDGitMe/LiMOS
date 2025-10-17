# Event Classification Layer - Implementation Progress

## Status: Phase 3 Complete

Last Updated: 2025-10-16

---

## Completed

### Phase 1: Core Infrastructure ✅

**Files Created:**
- `/projects/api/models/events.py` - Event type enums and Pydantic models (375 lines)
- `/projects/api/models/__init__.py` - Package exports

**Event Types Defined:**
- **Money Events** (8 types): Purchase, Return, Transfer, AP_Payment, AP_Invoice, Deposit, ACH, Sales
- **Fleet Events** (4 types): PumpEvent, RepairEvent, MaintEvent, TravelEvent
- **Health Events** (3 types): MealEvent, ExerciseEvent, HikeEvent
- **Inventory Events** (3 types): StockEvent, UseFoodEvent, FoodExpiryCheck
- **Calendar Events** (3 types): AppointmentEvent, ReminderEvent, TaskEvent

**Data Models Created:**
- `ClassifiedEvent` - Represents a single classified event with routing info
- `EventClassificationResult` - Complete classification result with primary + secondary events
- Helper functions: `get_event_category()`, `get_event_module()`, `is_valid_event_type()`

**Key Features:**
- Type-safe event type enums
- Pydantic validation for all event data
- Automatic category and module mapping
- Support for confidence scoring
- Multi-event support (primary + secondary events)

### Phase 2: Event Classifier Implementation ✅

**Files Created:**
- `/projects/api/routers/event_classifier.py` - Core classification logic (650+ lines)

**Implemented Features:**
1. **Keyword-based classification** with all event type keywords from rules:
   - PUMP_KEYWORDS including "DEF", "additive" (user's additions)
   - TRAVEL_KEYWORDS including "started driving", "stopped for the day"
   - All Money, Fleet, Health, Inventory, and Calendar event keywords

2. **Confidence scoring** based on:
   - Keyword matches (base 0.7)
   - Data completeness (up to +0.3)
   - Required fields validation

3. **Multi-event detection**:
   - PumpEvent → Purchase (when cost > 0)
   - StockEvent → Purchase (when cost > 0)
   - Automatic secondary event generation

4. **Conditional parsing for PumpEvent** (user's requirement):
   ```python
   # IF Have(cost) AND Have(price) AND Missing(gallons) → calculate gallons
   if cost and price and not gallons:
       result["gallons"] = cost / price

   # IF Have(gallons) AND Have(price) AND Missing(cost) → calculate cost
   elif gallons and price and not cost:
       result["cost"] = gallons * price
   ```

5. **Complete event classifiers** for all event types:
   - `classify_pump_event()` - Full implementation with conditionals
   - `classify_travel_event()` - Stub classifier
   - `classify_purchase_event()` - Stub classifier
   - 20+ additional event type classifiers (stubs ready for expansion)

6. **Main entry points**:
   - `classify_event()` - Primary classification function
   - `classify_from_keywords()` - Keyword-based fallback
   - `classify_from_claude_response()` - Claude AI response parser

### Phase 3: Claude Integration ✅

**Files Modified:**
- `/projects/api/routers/orchestrator.py` - Integrated event classifier

**Implemented Features:**
1. **Updated ORCHESTRATOR_SYSTEM_PROMPT** to include:
   - Event types by category (Money, Fleet, Health, Inventory, Calendar)
   - Instructions for Claude to identify event_types and primary_event
   - Updated examples showing multi-event classification

2. **Integrated event classifier** into process_command() flow:
   - Added import: `from projects.api.routers.event_classifier import classify_event`
   - Classification runs after Claude parsing (Step 1.5)
   - Classification result added to parsed data for module handlers
   - Logging of classification results for debugging

3. **Enhanced Claude response format:**
   ```json
   {
     "module": "module_name",
     "action": "action_type",
     "intent": "description",
     "event_types": ["primary_event", "secondary_event"],
     "primary_event": "primary_event_type",
     "extracted_data": {...},
     "confidence": 0.0-1.0
   }
   ```

4. **Classification fallback logic:**
   - Classifier runs regardless of whether Claude provides event types
   - Can use Claude's event types as hint, or classify from scratch
   - Provides validation and backup classification

---

## Next Steps

### Phase 4: Module Handler Updates

**To Update:**
- `/projects/api/routers/orchestrator.py` - Add event classification step

**Must Implement:**
1. Update `ORCHESTRATOR_SYSTEM_PROMPT` to include event types in response
2. Update `parse_command_with_claude()` to extract event types
3. Add fallback to keyword-based classifier if Claude doesn't provide event types
4. Integrate classifier into `process_command()` flow

**New Claude Response Format:**
```json
{
  "module": "fleet",
  "action": "create",
  "intent": "Log vehicle refueling",
  "event_types": ["pump_event", "purchase"],
  "primary_event": "pump_event",
  "extracted_data": { ... },
  "confidence": 0.98
}
```

### Phase 4: Module Handler Updates

**To Update:**
- `route_to_accounting()` - Handle different Money Event types
- `route_to_fleet()` - Handle different Fleet Event types
- Stub handlers for health, inventory, calendar

**Must Implement:**
1. **Accounting Module** - Event-aware transaction creation:
   - Purchase → Expense increase, Asset decrease
   - Return → Expense decrease (negative), Asset increase
   - Transfer → Asset decrease + Asset increase
   - Deposit → Asset increase, Income increase
   - AP_Payment → Liability decrease, Asset decrease
   - AP_Invoice → Expense increase, Liability increase

2. **Fleet Module** - Event-aware fleet operations:
   - PumpEvent → Log refueling with price, quantity, cost calculations
   - RepairEvent → Log repair with service details
   - MaintEvent → Log maintenance
   - TravelEvent → Log trip for mileage tracking

### Phase 5: Multi-Event Support & Testing

**To Implement:**
1. `process_multi_event_command()` - Handle cross-module events
2. Event chaining logic (PumpEvent → Purchase)
3. Comprehensive test suite (50+ test cases)
4. Integration tests for end-to-end flows

---

## Updated Rules from User

The user has made important updates to `/projects/api/routers/EVENT_CLASSIFICATION_RULES.md`:

### Key Changes:

1. **Added Parsing Rules Section** (Line 3):
   - System now looks at received data and applies **Parsing Rules** to handle missing data
   - Once parsing conditionals are applied, validate that all **Required Data** are not null

2. **PumpEvent Enhanced** (Lines 210-237):
   - **Keywords**: Added `DEF`, `additive`
   - **Identifiable Data**: price, quantity, unit-of-measure, odometer, cost, date-time, fuel-gauge, payment-method, from-account, to-account, fuel-type, location, vehicle
   - **Conditionals**:
     - IF Have(cost) AND Have(price) AND Missing(gallons) → calculate gallons
     - IF Have(gallons) AND Have(price) AND Missing(cost) → calculate cost
   - **Required Data**: price, quantity, unit-of-measure, cost, date-time, from-account, to-account, fuel-type, location

3. **Food Inventory Renamed** (Line 377):
   - Changed from "Inventory Events" to "Food Inventory Events"
   - UseEvent → UseFoodEvent
   - ExpiryCheck → FoodExpiryCheck

4. **TravelEvent Enhanced** (Line 283):
   - Added keywords: `Started driving`, `stopped for the day`

5. **Conflict Resolution Updated** (Line 577):
   - "Explicit Keywords Win": Specifically mentions "A Fuel Event Keyword"

---

## Technical Decisions

### Why Pydantic Models?
- Type safety and validation
- Auto-generated API documentation
- Easy serialization/deserialization
- IDE autocomplete support

### Why String Enums?
- Can be used directly in FastAPI responses
- JSON-serializable
- Better error messages than int enums

### Why Helper Functions?
- Centralize category/module mapping logic
- Easy to test and maintain
- DRY principle

---

## Testing Strategy

### Unit Tests (To Create)
- Test each event type classifier
- Test confidence scoring
- Test multi-event detection
- Test data validation and parsing conditionals

### Integration Tests (To Create)
- Test end-to-end classification flow
- Test multi-event scenarios
- Test Claude + fallback classifier
- Test event routing to modules

### Test Commands (50+ examples needed)
```python
# Money Events
"I bought $50 of groceries at Safeway"  # Purchase
"I returned the shirt for $29.99"        # Return
"Transfer $500 to savings"               # Transfer

# Fleet Events
"Filled up gas, 12 gallons, $45, odometer 45000"  # PumpEvent + Purchase
"Got gas, $52 at $4.33/gallon"                    # PumpEvent (calc gallons)
"Oil change, $59.99, odometer 45500"              # MaintEvent + Purchase

# Inventory Events
"Bought 2 gallons of milk, expires 10/20"  # StockEvent + Purchase
"Used 1 can of tomato sauce"               # UseFoodEvent
"What's expiring in the fridge?"           # FoodExpiryCheck
```

---

## Performance Goals

- Classification time: <50ms
- Confidence accuracy: Pearson correlation >0.85
- Classification accuracy: >95% on test set
- Multi-event detection: >90% accuracy

---

## Next Session Tasks

1. Create `event_classifier.py` with keyword matching
2. Implement conditional parsing for PumpEvent
3. Update orchestrator to use classifier
4. Test with 10-20 sample commands
5. Iterate on confidence scoring

---

## Notes

- User's updated rules emphasize **conditional parsing** - system must calculate missing fields when possible
- PumpEvent is the most complex with price/quantity/cost calculations
- Food inventory events have specific naming (UseFoodEvent, FoodExpiryCheck)
- Multi-event support is critical for Fleet events (always trigger Purchase if cost > 0)
