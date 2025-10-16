# Event Classification Layer - Documentation Index

This directory contains comprehensive planning and specification documents for the Event Classification Layer in the LiMOS Orchestrator.

## Quick Start

**New to this project?** Start here:
1. Read the [Implementation Plan](#implementation-plan) for an executive summary
2. Review the [Layer Specification](#layer-specification) for architecture details
3. Consult the [Classification Rules](#classification-rules) when implementing

---

## Document Overview

### 1. Implementation Plan
**File:** `EVENT_CLASSIFICATION_IMPLEMENTATION_PLAN.md`

**Purpose:** Executive summary and step-by-step implementation guide

**Contents:**
- Problem statement and proposed solution
- 6-phase implementation plan with timelines
- Code structure and key changes
- Testing strategy
- Risk assessment and success metrics

**When to use:**
- Starting the implementation
- Planning sprints and tasks
- Understanding project scope and timeline

---

### 2. Layer Specification
**File:** `EVENT_CLASSIFICATION_LAYER_SPEC.md`

**Purpose:** Complete architectural and technical specification

**Contents:**
- Architecture diagrams (current vs new flow)
- Event type taxonomy (25+ event types across 5 categories)
- Data models (Pydantic schemas)
- Classification logic and algorithms
- Multi-event support design
- Detailed examples with JSON

**When to use:**
- Implementing the core classification logic
- Understanding event relationships
- Designing new event types
- Technical architecture decisions

---

### 3. Classification Rules
**File:** `routers/EVENT_CLASSIFICATION_RULES.md`

**Purpose:** Human-readable rules for classifying user commands

**Contents:**
- Rule format: IF [conditions] THEN [event type]
- Keywords for each event type
- Confidence scoring guidelines
- Multi-event detection rules
- Special cases and edge cases
- Conflict resolution strategies

**When to use:**
- Implementing keyword-based classifier
- Writing Claude AI prompts
- Testing classification logic
- Adding new event types
- Debugging misclassifications

---

## Event Type Reference

### Money Events (Accounting Module)
- **Purchase** - Buying goods/services
- **Return** - Returning goods for refund
- **Transfer** - Moving money between accounts
- **AP Payment** - Paying a bill
- **AP Invoice** - Receiving a bill
- **Deposit** - Income/revenue received
- **ACH** - Automated payment
- **Sales** - Selling goods/services

### Fleet Events (Fleet Module)
- **PumpEvent** - Vehicle refueling
- **RepairEvent** - Vehicle repair by vendor
- **MaintEvent** - Scheduled/DIY maintenance
- **TravelEvent** - Trip for mileage tracking

### Health Events (Health Module)
- **MealEvent** - Meal logging
- **ExerciseEvent** - Physical activity
- **HikeEvent** - Hiking activity

### Inventory Events (Inventory Module)
- **StockEvent** - Adding items to inventory
- **UseEvent** - Consuming inventory items
- **ExpiryCheck** - Querying for expiring items

### Calendar Events (Calendar Module)
- **AppointmentEvent** - Scheduled appointments
- **ReminderEvent** - One-time or recurring reminders
- **TaskEvent** - To-do items

---

## Architecture at a Glance

### Current Flow
```
User Command → Claude Parser → Module Router → Module Handler → Response
```

### New Flow (With Event Classification)
```
User Command → Claude Parser → Event Classifier → Module Router → Module Handler(s) → Response
                    ↓               ↓                    ↓
              [intent, data]  [event types]      [primary + secondary]
```

### Key Benefits
1. **Clear separation of concerns** - Parsing, classification, routing, handling
2. **Better transaction handling** - Accounting knows whether it's Purchase, Return, Transfer
3. **Multi-event support** - Single command triggers multiple related events
4. **Extensibility** - New event types added via configuration
5. **Better logging** - Know exactly what events were processed

---

## Quick Examples

### Simple Purchase
**Input:** "I bought $50 of groceries at Safeway"
**Classification:**
- Primary: Purchase (Money Event)
- Secondary: None
**Routing:** accounting module
**Result:** Creates expense transaction

### Multi-Event (Refueling)
**Input:** "Filled up gas, 12 gallons, $45, odometer 45000"
**Classification:**
- Primary: PumpEvent (Fleet Event)
- Secondary: Purchase (Money Event)
**Routing:** fleet module (primary) + accounting module (secondary)
**Result:** Creates fleet refuel record AND expense transaction

### Query
**Input:** "How much did I spend on food this month?"
**Classification:**
- Primary: Query (Money Event)
- Secondary: None
**Routing:** accounting module
**Result:** Returns spending summary

---

## Implementation Status

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 1: Core Infrastructure | Planning Complete | 0% |
| Phase 2: Claude Integration | Not Started | 0% |
| Phase 3: Module Handlers | Not Started | 0% |
| Phase 4: Multi-Event Support | Not Started | 0% |
| Phase 5: Testing & Refinement | Not Started | 0% |
| Phase 6: Deployment | Not Started | 0% |

**Overall Status:** Planning Complete - Ready for Implementation

---

## File Structure

```
/Users/ksd/Projects/LiMOS/projects/api/
├── models/
│   └── events.py                          # NEW: Event type definitions (TO BE CREATED)
├── routers/
│   ├── orchestrator.py                    # MODIFIED: Add classification step
│   ├── event_classifier.py                # NEW: Classification logic (TO BE CREATED)
│   └── EVENT_CLASSIFICATION_RULES.md      # ✅ CREATED: Rules documentation
├── EVENT_CLASSIFICATION_LAYER_SPEC.md     # ✅ CREATED: Architecture spec
├── EVENT_CLASSIFICATION_IMPLEMENTATION_PLAN.md  # ✅ CREATED: Implementation guide
└── EVENT_CLASSIFICATION_README.md         # ✅ THIS FILE
```

---

## Development Workflow

### Adding a New Event Type

1. **Update Taxonomy**: Add event type to `EVENT_CLASSIFICATION_LAYER_SPEC.md`
2. **Add Rules**: Define classification rules in `routers/EVENT_CLASSIFICATION_RULES.md`
3. **Update Enum**: Add to appropriate enum in `models/events.py`
4. **Add Classifier Logic**: Update `routers/event_classifier.py`
5. **Update Module Handler**: Add handling logic to appropriate module
6. **Write Tests**: Add test cases for the new event type
7. **Update Documentation**: Document examples and usage

### Testing Classification

1. **Unit Test**: Test keyword matching for specific event type
2. **Integration Test**: Test end-to-end flow with real command
3. **Confidence Test**: Verify confidence score correlates with correctness
4. **Multi-Event Test**: If applicable, verify secondary events trigger correctly

---

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| Use Enum-based event types | Type safety and IDE support |
| Markdown rules for humans | Easy to edit by non-developers |
| Claude + keyword fallback | Balance AI power with reliability |
| Multi-event support from start | Core requirement, harder to add later |
| Rule-based classification | Predictable, debuggable, explainable |

---

## Success Metrics

### Technical
- Classification Accuracy: >95%
- Multi-Event Detection: >90%
- Added Latency: <200ms
- Test Coverage: >80%

### User Experience
- Clarification Rate: <10%
- User Satisfaction: >90%
- Support Tickets: <5/week

---

## Next Steps

1. ✅ Review and approve specification documents
2. Create Phase 1 tasks in project management
3. Set up development branch: `feature/event-classification`
4. Begin implementation of event models
5. Implement basic classifier with keyword matching
6. Update Claude system prompt
7. Test with sample commands

---

## Questions?

For technical questions or clarifications, refer to:
- **Architecture questions** → `EVENT_CLASSIFICATION_LAYER_SPEC.md`
- **Implementation questions** → `EVENT_CLASSIFICATION_IMPLEMENTATION_PLAN.md`
- **Classification logic questions** → `routers/EVENT_CLASSIFICATION_RULES.md`

---

**Status:** Planning Complete
**Last Updated:** 2025-10-16
**Owner:** TBD
