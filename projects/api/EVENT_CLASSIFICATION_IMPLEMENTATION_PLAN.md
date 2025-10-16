# Event Classification Layer - Implementation Plan

## Executive Summary

This document outlines the implementation plan for adding an Event Classification Layer to the LiMOS Orchestrator. This new architectural component will parse user commands, identify event types based on rules, and intelligently route to appropriate modules.

## Related Documents

- **[EVENT_CLASSIFICATION_LAYER_SPEC.md](./EVENT_CLASSIFICATION_LAYER_SPEC.md)** - Complete architectural specification
- **[routers/EVENT_CLASSIFICATION_RULES.md](./routers/EVENT_CLASSIFICATION_RULES.md)** - Human-readable classification rules

## Problem Statement

Currently, the orchestrator uses Claude AI to parse commands and directly route to modules. This approach has limitations:

1. **No explicit event type identification** - We jump from parsing to module routing
2. **Limited multi-event support** - Difficult to handle commands that trigger multiple events
3. **Unclear transaction types** - Accounting module doesn't know if it's a Purchase, Return, Transfer, etc.
4. **Hard to extend** - Adding new event types requires modifying multiple parts of the code

## Proposed Solution

Add an Event Classification Layer that:
1. Takes parsed command data from Claude
2. Classifies the command into one or more event types (Purchase, PumpEvent, etc.)
3. Determines primary and secondary events
4. Routes events to appropriate modules with full context

### Benefits

- **Clear separation of concerns**: Parsing → Classification → Routing → Handling
- **Better transaction handling**: Accounting knows whether it's a Purchase, Return, Transfer
- **Multi-event support**: Single command can trigger multiple events (e.g., refuel → PumpEvent + Purchase)
- **Extensibility**: New event types added via configuration
- **Better logging**: Know exactly what events were processed

## Architecture

### Current Flow
```
User Command → Claude Parser → Module Router → Module Handler → Response
```

### New Flow
```
User Command → Claude Parser → Event Classifier → Module Router → Module Handler(s) → Response
                    ↓               ↓                    ↓
              [intent, data]  [event types]      [primary + secondary]
```

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)

**Goal:** Create event type definitions and core classification logic

**Tasks:**
1. ✅ Create specification documents (COMPLETE)
2. Create `/projects/api/models/events.py`:
   - Event type enums (MoneyEventType, FleetEventType, etc.)
   - ClassifiedEvent model
   - EventClassificationResult model
3. Create `/projects/api/routers/event_classifier.py`:
   - `classify_event()` function
   - Keyword matching logic
   - Confidence scoring
   - Multi-event detection

**Deliverables:**
- Event type enums defined
- Basic classifier that can identify single events
- Unit tests for classification logic

**Success Criteria:**
- Can correctly classify 10 test commands with >90% accuracy
- Confidence scores correlate with actual correctness

---

### Phase 2: Claude Integration (Week 1-2)

**Goal:** Update Claude prompts to include event type identification

**Tasks:**
1. Update `ORCHESTRATOR_SYSTEM_PROMPT` in `orchestrator.py`:
   - Add event type taxonomy to prompt
   - Request `event_types` and `primary_event` in response
   - Provide examples of event classification
2. Update `parse_command_with_claude()`:
   - Parse new `event_types` field
   - Validate event types against known types
3. Add fallback logic:
   - If Claude doesn't provide event types, use keyword-based classifier

**Deliverables:**
- Updated Claude prompt with event awareness
- Parser handles new response format
- Fallback to rule-based classification

**Success Criteria:**
- Claude correctly identifies event types in 95% of test cases
- Fallback classifier works when Claude response is incomplete

---

### Phase 3: Update Module Handlers (Week 2)

**Goal:** Make module handlers event-aware

**Tasks:**
1. Update `route_to_accounting()`:
   - Accept `event_type` parameter
   - Handle different money event types:
     - `purchase` → Expense increase, Asset decrease
     - `return` → Expense decrease (negative), Asset increase
     - `transfer` → Asset decrease + Asset increase
     - `deposit` → Asset increase, Income increase
     - `ap_payment` → Liability decrease, Asset decrease
     - `ap_invoice` → Expense increase, Liability increase
   - Remove hardcoded "expense" logic

2. Update `route_to_fleet()`:
   - Accept `event_type` parameter
   - Handle fleet events:
     - `pump_event` → Log refueling data
     - `repair_event` → Log repair with service details
     - `maint_event` → Log maintenance
     - `travel_event` → Log trip for mileage
   - Remove mock responses

3. Create stubs for other modules:
   - `route_to_health()` - Handle meal, exercise, hike events
   - `route_to_inventory()` - Handle stock, use, expiry events
   - `route_to_calendar()` - Handle appointment, reminder, task events

**Deliverables:**
- Accounting module handles all Money Event types
- Fleet module handles all Fleet Event types
- Stub handlers for health, inventory, calendar

**Success Criteria:**
- Can create different transaction types in accounting based on event type
- Fleet events are logged with proper categorization
- No regressions in existing functionality

---

### Phase 4: Multi-Event Support (Week 3)

**Goal:** Enable commands to trigger multiple events across modules

**Tasks:**
1. Create `process_multi_event_command()` in `orchestrator.py`:
   - Process primary event first
   - Chain secondary events
   - Aggregate results
   - Handle cross-module transactions

2. Implement secondary event triggers:
   - `PumpEvent` → also creates `Purchase` in accounting
   - `RepairEvent` → also creates `Purchase` in accounting
   - `MaintEvent` → also creates `Purchase` if cost > 0
   - `StockEvent` → also creates `Purchase` if cost mentioned
   - `MealEvent` → also creates `Purchase` if eating out

3. Update response generation:
   - Include info from all events
   - Summarize multi-event actions
   - Provide IDs for both primary and secondary events

**Deliverables:**
- Multi-event processing pipeline
- Cross-module event propagation
- Comprehensive response messages

**Success Criteria:**
- "Filled up gas, $45" creates both fleet event and accounting transaction
- Response message mentions both actions
- Both records linked/traceable

---

### Phase 5: Testing & Refinement (Week 3-4)

**Goal:** Validate the system with comprehensive testing

**Tasks:**
1. Create test suite:
   - Unit tests for each event type classifier
   - Integration tests for end-to-end flows
   - Multi-event scenario tests
   - Edge case tests (ambiguous commands, missing data)

2. Test with real commands:
   - 50+ real user commands from various categories
   - Measure classification accuracy
   - Measure confidence score accuracy
   - Identify misclassifications

3. Refine classification rules:
   - Adjust keywords based on test results
   - Tune confidence scoring thresholds
   - Add missing event types or variants

4. Documentation:
   - API documentation for new endpoints
   - User guide for supported event types
   - Developer guide for adding new event types

**Deliverables:**
- Comprehensive test suite with 50+ test cases
- Classification accuracy report
- Refined rules and thresholds
- Complete documentation

**Success Criteria:**
- >95% classification accuracy on test set
- <5% false positive rate for multi-event detection
- <10% clarification request rate
- Zero regressions in existing functionality

---

### Phase 6: Deployment & Monitoring (Week 4)

**Goal:** Deploy to production and monitor performance

**Tasks:**
1. Gradual rollout:
   - Deploy to staging environment
   - Run A/B test: old routing vs new classification
   - Monitor error rates and latency

2. Add telemetry:
   - Log all classifications with confidence scores
   - Track event type frequencies
   - Monitor misclassification rates
   - Alert on low confidence trends

3. User feedback loop:
   - Collect user feedback on incorrect classifications
   - Build correction mechanism
   - Periodically review and refine rules

**Deliverables:**
- Deployed to production
- Telemetry and monitoring in place
- Feedback collection mechanism

**Success Criteria:**
- <200ms added latency
- >95% user satisfaction with classifications
- Clear visibility into system performance

---

## Implementation Details

### File Structure

```
/Users/ksd/Projects/LiMOS/projects/api/
├── models/
│   └── events.py                          # NEW: Event type definitions
├── routers/
│   ├── orchestrator.py                    # MODIFIED: Add classification step
│   ├── event_classifier.py                # NEW: Classification logic
│   └── EVENT_CLASSIFICATION_RULES.md      # CREATED: Rules documentation
├── EVENT_CLASSIFICATION_LAYER_SPEC.md     # CREATED: Architecture spec
└── EVENT_CLASSIFICATION_IMPLEMENTATION_PLAN.md  # THIS FILE
```

### Key Code Changes

#### 1. New Event Models (`models/events.py`)

```python
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

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

# ... more event type enums

class ClassifiedEvent(BaseModel):
    event_type: str
    category: str
    module: str
    action: str
    extracted_data: Dict[str, Any]
    confidence: float
    is_primary: bool = True
    triggers_secondary: Optional[List[str]] = None

class EventClassificationResult(BaseModel):
    primary_event: ClassifiedEvent
    secondary_events: Optional[List[ClassifiedEvent]] = None
    intent: str
    confidence: float
    clarification_needed: Optional[str] = None
```

#### 2. Event Classifier (`routers/event_classifier.py`)

```python
from projects.api.models.events import (
    MoneyEventType,
    FleetEventType,
    ClassifiedEvent,
    EventClassificationResult
)
from typing import Dict, Any, List, Optional

def classify_event(
    command: str,
    parsed_data: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> EventClassificationResult:
    """
    Classify a parsed command into one or more event types.

    Args:
        command: Original user command
        parsed_data: Data extracted by Claude parser
        context: Optional context (location, time, etc.)

    Returns:
        EventClassificationResult with primary and optional secondary events
    """
    # Check if Claude already provided event types
    if "event_types" in parsed_data:
        return classify_from_claude_response(parsed_data)

    # Fallback to keyword-based classification
    return classify_from_keywords(command, parsed_data)

def classify_from_keywords(
    command: str,
    parsed_data: Dict[str, Any]
) -> EventClassificationResult:
    """Keyword-based classification using rules from EVENT_CLASSIFICATION_RULES.md"""
    command_lower = command.lower()

    # Check for money events
    if any(kw in command_lower for kw in ["bought", "purchased", "spent", "paid", "$"]):
        return classify_money_event(command_lower, parsed_data)

    # Check for fleet events
    if any(kw in command_lower for kw in ["gas", "fuel", "gallons", "odometer"]):
        return classify_fleet_event(command_lower, parsed_data)

    # ... more classification logic

def classify_money_event(command: str, data: Dict[str, Any]) -> EventClassificationResult:
    """Classify money event subtypes"""
    if "return" in command or "refund" in command:
        event_type = MoneyEventType.RETURN
        confidence = 0.90
    elif "transfer" in command:
        event_type = MoneyEventType.TRANSFER
        confidence = 0.92
    else:
        event_type = MoneyEventType.PURCHASE
        confidence = 0.85

    # ... create and return EventClassificationResult
```

#### 3. Updated Orchestrator (`routers/orchestrator.py`)

```python
from projects.api.routers.event_classifier import classify_event

@router.post("/command", response_model=OrchestratorResponse)
async def process_command(raw_request: Request):
    # ... existing request parsing ...

    try:
        # Step 1: Parse command with Claude
        parsed = parse_command_with_claude(request.command, request.context)

        # Step 2: Classify events (NEW)
        classification = classify_event(
            command=request.command,
            parsed_data=parsed,
            context=request.context
        )

        # Step 3: Process primary event
        primary_result = process_event(classification.primary_event)

        # Step 4: Process secondary events if any
        secondary_results = []
        if classification.secondary_events:
            for event in classification.secondary_events:
                result = process_event(event)
                secondary_results.append(result)

        # Step 5: Generate comprehensive response
        message = generate_multi_event_response(
            classification,
            primary_result,
            secondary_results
        )

        return OrchestratorResponse(
            success=True,
            message=message,
            module=classification.primary_event.module,
            action=classification.primary_event.action,
            data={
                "primary": primary_result,
                "secondary": secondary_results
            }
        )
```

#### 4. Updated Accounting Handler

```python
def route_to_accounting(
    action: str,
    extracted_data: Dict[str, Any],
    event_type: Optional[str] = None  # NEW parameter
) -> Dict[str, Any]:
    """
    Route to accounting module with event type awareness.
    """
    if action == "create":
        event_type = event_type or MoneyEventType.PURCHASE  # Default to purchase

        if event_type == MoneyEventType.PURCHASE:
            return create_purchase_transaction(extracted_data)
        elif event_type == MoneyEventType.RETURN:
            return create_return_transaction(extracted_data)
        elif event_type == MoneyEventType.TRANSFER:
            return create_transfer_transaction(extracted_data)
        elif event_type == MoneyEventType.DEPOSIT:
            return create_deposit_transaction(extracted_data)
        # ... handle other event types
```

---

## Testing Strategy

### Unit Tests

**Event Classification Tests:**
```python
def test_classify_purchase():
    command = "I bought $50 of groceries at Safeway"
    parsed = {"amount": 50.00, "description": "Groceries at Safeway"}

    result = classify_event(command, parsed)

    assert result.primary_event.event_type == MoneyEventType.PURCHASE
    assert result.primary_event.module == "accounting"
    assert result.confidence >= 0.85
    assert result.secondary_events is None

def test_classify_refuel_multi_event():
    command = "Filled up gas, 12 gallons, $45, odometer 45000"
    parsed = {"gallons": 12.0, "cost": 45.00, "odometer": 45000}

    result = classify_event(command, parsed)

    assert result.primary_event.event_type == FleetEventType.PUMP
    assert result.primary_event.module == "fleet"
    assert len(result.secondary_events) == 1
    assert result.secondary_events[0].event_type == MoneyEventType.PURCHASE
```

### Integration Tests

**End-to-End Flow Tests:**
```python
@pytest.mark.asyncio
async def test_refuel_creates_both_events():
    client = TestClient(app)

    response = client.post("/api/orchestrator/command", json={
        "command": "Filled up gas, 12 gallons, $45, odometer 45000"
    })

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert data["success"] is True
    assert "primary" in data["data"]
    assert "secondary" in data["data"]

    # Verify fleet event was created
    assert data["data"]["primary"]["event_type"] == "pump_event"

    # Verify accounting transaction was created
    assert len(data["data"]["secondary"]) == 1
    assert data["data"]["secondary"][0]["amount"] == 45.00
```

### Test Data

Create 50+ test commands covering:
- All money event types (8 types × 3-5 variations = 32 tests)
- All fleet event types (4 types × 3 variations = 12 tests)
- Multi-event scenarios (10+ tests)
- Edge cases (ambiguous, missing data, etc.) (10+ tests)

---

## Risk Assessment

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Claude API doesn't support event types | High | Low | Use keyword-based fallback classifier |
| Classification accuracy < 90% | Medium | Medium | Extensive testing and rule refinement |
| Added latency > 200ms | Medium | Low | Optimize classifier, cache results |
| Breaking existing functionality | High | Low | Comprehensive regression testing |

### Business Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| User confusion with new event types | Low | Medium | Clear documentation and examples |
| Increased clarification requests | Medium | Low | Good confidence thresholds |
| Multi-event creates unexpected records | Medium | Medium | Clear logging and user notifications |

---

## Success Metrics

### Technical Metrics
- **Classification Accuracy**: >95% correct event type identification
- **Confidence Correlation**: Pearson correlation >0.85 between confidence and correctness
- **Multi-Event Detection**: >90% correct secondary event identification
- **Latency**: <200ms added processing time
- **Error Rate**: <1% server errors

### User Experience Metrics
- **Clarification Rate**: <10% of commands require clarification
- **User Satisfaction**: >90% of test users satisfied with classifications
- **Support Tickets**: <5 misclassification reports per week

### Business Metrics
- **Event Coverage**: Support for 25+ distinct event types
- **Module Coverage**: Full integration with 2+ modules (accounting, fleet)
- **Code Quality**: >80% test coverage

---

## Timeline Summary

| Phase | Duration | Key Deliverable |
|-------|----------|-----------------|
| Phase 1: Core Infrastructure | Week 1 | Event models and basic classifier |
| Phase 2: Claude Integration | Week 1-2 | Updated prompts and parser |
| Phase 3: Module Handlers | Week 2 | Event-aware accounting and fleet |
| Phase 4: Multi-Event Support | Week 3 | Cross-module event chaining |
| Phase 5: Testing & Refinement | Week 3-4 | 95% accuracy on test set |
| Phase 6: Deployment | Week 4 | Production deployment |

**Total Duration:** 4 weeks

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Create Phase 1 tasks** in project management tool
3. **Set up development branch**: `feature/event-classification`
4. **Begin implementation** of event models and basic classifier
5. **Schedule weekly check-ins** to review progress

---

## Questions to Resolve

1. **Event Type Granularity**: Are the current event types granular enough, or do we need more subtypes?
2. **Multi-Module Coordination**: Should we support rollback if a secondary event fails?
3. **Event Linking**: Do we need a formal linking system between primary and secondary events?
4. **Configuration**: Should event classification rules be in a database or config file instead of code?
5. **Analytics**: What telemetry/analytics do we need to track classification performance?

---

## Appendix A: Example Commands by Event Type

### Money Events
- Purchase: "I bought $50 of groceries at Safeway"
- Return: "I returned the shirt to Target for $29.99"
- Transfer: "Transfer $500 from checking to savings"
- AP Payment: "Paid the electric bill of $85"
- AP Invoice: "Received electric bill for $85"
- Deposit: "Received paycheck deposit of $3,200"
- ACH: "ACH payment to credit card of $1,500"
- Sales: "Sold old laptop for $400"

### Fleet Events
- PumpEvent: "Filled up gas, 12 gallons, $45, odometer 45000"
- RepairEvent: "Brake repair at Midas, $450, odometer 46000"
- MaintEvent: "Oil change at Jiffy Lube, $59.99, odometer 45500"
- TravelEvent: "Drove to San Francisco, 240 miles, business"

### Health Events
- MealEvent: "Had oatmeal with blueberries for breakfast, 350 calories"
- ExerciseEvent: "Ran 5 miles in 42 minutes"
- HikeEvent: "Hiked Mt. Tam, 8 miles, 2000ft elevation gain"

### Inventory Events
- StockEvent: "Bought 2 gallons of milk, expires 10/20"
- UseEvent: "Used 1 can of tomato sauce"
- ExpiryCheck: "What's about to expire in the fridge?"

### Calendar Events
- AppointmentEvent: "Doctor appointment Tuesday at 2pm"
- ReminderEvent: "Remind me to call mom tomorrow at 9am"
- TaskEvent: "Add task: clean garage, due Friday"

---

## Appendix B: Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-10-16 | Use enum-based event types | Type safety and IDE support |
| 2025-10-16 | Markdown rules for human readability | Easy to edit by non-developers |
| 2025-10-16 | Claude + keyword fallback | Balance AI power with reliability |
| 2025-10-16 | Multi-event support from start | Core requirement, harder to add later |

---

**Status:** Planning Complete - Ready for Implementation
**Owner:** TBD
**Last Updated:** 2025-10-16
