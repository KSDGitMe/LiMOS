"""
LiMOS Orchestrator Router
=========================
Universal endpoint for processing natural language commands via Apple Shortcuts.
Uses Claude API to parse intent and route to appropriate modules.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
import anthropic
import os
from datetime import datetime
import json

# Import event classifier
from projects.api.routers.event_classifier import classify_event
from projects.api.models.events import EventClassificationResult

router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])

# Initialize Claude client
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("⚠️  WARNING: ANTHROPIC_API_KEY not set - orchestrator will not function")
    client = None
else:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# Request/Response Models
class OrchestratorRequest(BaseModel):
    """Request from Universal Shortcut"""
    command: str = Field(..., description="Natural language command from user")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context (location, time, etc.)")
    user_id: Optional[str] = Field(default=None, description="User identifier for multi-tenant support")


class OrchestratorResponse(BaseModel):
    """Response to Universal Shortcut"""
    success: bool
    message: str = Field(..., description="Human-readable response for Siri to speak")
    module: str = Field(..., description="Which module handled the request (accounting, fleet, etc.)")
    action: str = Field(..., description="Action performed (create, read, update, delete)")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Structured data about what was done")
    suggestions: Optional[List[str]] = Field(default=None, description="Follow-up action suggestions")


# System prompt for Claude
ORCHESTRATOR_SYSTEM_PROMPT = """You are the LiMOS Orchestrator, an intelligent routing system for a life management platform.

Your job is to analyze user commands and determine:
1. Which module should handle the request (accounting, fleet, health, inventory, calendar)
2. What action to perform (create, read, update, delete)
3. What specific event types are involved
4. Extract structured data from the natural language command

Available Modules:
- **accounting**: Financial transactions, expenses, income, budgets
- **fleet**: Vehicles, refueling, maintenance, mileage tracking
- **health**: Meals, nutrition, exercise, activities, hiking
- **inventory**: Household items, expiration tracking, storage locations
- **calendar**: Events, appointments, reminders, scheduling

Event Types by Category:
- **Money Events**: purchase, return, transfer, ap_payment, ap_invoice, deposit, ach, sales
- **Fleet Events**: pump_event, repair_event, maint_event, travel_event
- **Health Events**: meal_event, exercise_event, hike_event
- **Inventory Events**: stock_event, use_food_event, food_expiry_check
- **Calendar Events**: appointment_event, reminder_event, task_event

Respond with a JSON object containing:
{
  "module": "module_name",
  "action": "action_type",
  "intent": "detailed description of what user wants",
  "event_types": ["primary_event_type", "secondary_event_type"],
  "primary_event": "primary_event_type",
  "extracted_data": {
    // Structured data extracted from command
  },
  "confidence": 0.0-1.0,
  "clarification_needed": "optional question if ambiguous"
}

Examples:

User: "I bought $50 of groceries at Safeway"
Response: {
  "module": "accounting",
  "action": "create",
  "intent": "Record grocery purchase expense",
  "event_types": ["purchase"],
  "primary_event": "purchase",
  "extracted_data": {
    "amount": 50.00,
    "description": "Groceries at Safeway",
    "category": "groceries",
    "merchant": "Safeway",
    "account_type": "expense"
  },
  "confidence": 0.95
}

User: "Filled up gas, 12 gallons, $45, odometer 45000"
Response: {
  "module": "fleet",
  "action": "create",
  "intent": "Log vehicle refueling event and expense",
  "event_types": ["pump_event", "purchase"],
  "primary_event": "pump_event",
  "extracted_data": {
    "gallons": 12.0,
    "cost": 45.00,
    "odometer": 45000,
    "price": 3.75,
    "fuel_type": "regular"
  },
  "confidence": 0.98
}

User: "How much did I spend on food this month?"
Response: {
  "module": "accounting",
  "action": "read",
  "intent": "Query spending by category for current month",
  "event_types": [],
  "primary_event": null,
  "extracted_data": {
    "category": "food",
    "time_period": "current_month",
    "query_type": "sum"
  },
  "confidence": 0.90
}

Be precise in data extraction and always err on the side of asking for clarification if critical information is missing.
"""


def parse_command_with_claude(command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Use Claude to parse the natural language command and determine routing.

    Args:
        command: Natural language command from user
        context: Optional context (location, time, etc.)

    Returns:
        Dict with module, action, intent, and extracted_data
    """
    if not client:
        raise HTTPException(
            status_code=503,
            detail="Orchestrator unavailable: ANTHROPIC_API_KEY not configured"
        )

    # Build the user message with context if available
    user_message = f"Command: {command}"
    if context:
        user_message += f"\n\nContext:\n{context}"

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=ORCHESTRATOR_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        # Parse Claude's response
        import json
        import re
        response_text = message.content[0].text
        print(f"🤖 Claude raw response: {response_text}")

        # Try to extract JSON from the response
        # Claude might wrap it in markdown code blocks or add explanatory text
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            parsed = json.loads(json_str)
        else:
            # Fallback: try parsing the whole response
            parsed = json.loads(response_text)

        print(f"✅ Parsed Claude response: {parsed}")
        return parsed

    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {str(e)}")
        print(f"❌ Response text was: {response_text}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse Claude response: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Claude API error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error calling Claude API: {str(e)}"
        )


def route_to_accounting(action: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route to accounting module and create actual journal entries.
    """
    from projects.accounting.models.journal_entries import (
        JournalEntry,
        Distribution,
        JournalEntryStatus,
    )
    from projects.accounting.database import JournalEntryRepository, get_db
    from projects.accounting.services import account_mapper
    import uuid

    if action == "create":
        # Create a simple expense journal entry
        # This will need enhancement to handle different transaction types

        amount = extracted_data.get("amount", 0.0)
        description = extracted_data.get("description", "Expense")
        category = extracted_data.get("category", "general")
        merchant = extracted_data.get("merchant", "")
        confidence = extracted_data.get("confidence", 0.0)

        # Use description as-is (Claude already includes merchant in description)
        full_description = description

        # Determine confidence level for account mapping
        confidence_level = "high" if confidence and confidence >= 0.85 else "low"

        # Map to actual Notion account page IDs
        payment_account_id = account_mapper.get_payment_account()
        expense_account_id = account_mapper.get_expense_account(
            category=category,
            merchant=merchant,
            confidence=confidence_level
        )

        # Log the mapping results
        print(f"💳 Mapped payment account: {payment_account_id}")
        print(f"📊 Mapped expense account for '{category}' / '{merchant}': {expense_account_id}")

        # Import required enums
        from projects.accounting.models.journal_entries import (
            AccountType,
            FlowDirection,
            DebitCredit,
        )

        # Create journal entry with FROM (expense) and TO (credit card/cash) distributions
        # Example 4 from the docs: Record expense $100 (Expense increases, Cash decreases):
        #   - Cash (Asset): FROM, multiplier -1
        #   - Expense (Expense): TO, multiplier +1

        entry = JournalEntry(
            journal_entry_id=str(uuid.uuid4()),
            entry_date=datetime.now().strftime("%Y-%m-%d"),
            amount=amount,  # REQUIRED: Total transaction amount
            description=full_description,
            status=JournalEntryStatus.DRAFT,  # Start as draft
            distributions=[
                # Cash/Card going OUT (FROM) - Asset decreasing
                Distribution(
                    distribution_id=str(uuid.uuid4()),
                    account_id=payment_account_id or "unknown",  # Mapped account ID
                    account_type=AccountType.ASSET,
                    flow_direction=FlowDirection.FROM,
                    amount=amount,
                    multiplier=-1,  # Asset decreasing
                    debit_credit=DebitCredit.CREDIT,  # Asset decrease = Credit
                    description=f"Payment for: {full_description}"
                ),
                # Expense account receiving (TO) - Expense increasing
                Distribution(
                    distribution_id=str(uuid.uuid4()),
                    account_id=expense_account_id or "unknown",  # Mapped account ID
                    account_type=AccountType.EXPENSE,
                    flow_direction=FlowDirection.TO,
                    amount=amount,
                    multiplier=1,  # Expense increasing
                    debit_credit=DebitCredit.DEBIT,  # Expense increase = Debit
                    description=f"Expense: {full_description}"
                )
            ]
        )

        # Create the entry in the database
        try:
            # For Notion backend, pass None as db
            # For SQL backend, get a connection
            if os.getenv("ACCOUNTING_BACKEND") == "notion":
                created_entry = JournalEntryRepository.create(None, entry)
            else:
                db_gen = get_db()
                db = next(db_gen)
                try:
                    created_entry = JournalEntryRepository.create(db, entry)
                finally:
                    try:
                        next(db_gen)
                    except StopIteration:
                        pass

            return {
                "transaction_id": created_entry.journal_entry_id,
                "amount": amount,
                "description": full_description,
                "category": category,
                "status": created_entry.status.value,
                "created_at": created_entry.entry_date
            }
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"❌ Error creating journal entry: {e}")
            print(f"❌ Full traceback:\n{error_trace}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create transaction: {str(e)}"
            )

    elif action == "read":
        # Future: implement read/query functionality
        return {
            "message": "Query functionality not yet implemented",
            "note": "This will query journal entries and return summaries"
        }
    else:
        return {"message": f"Action '{action}' not yet implemented for accounting"}


def route_to_fleet(action: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route to fleet module.
    This will eventually call the fleet API endpoints.
    """
    if action == "create":
        event_type = extracted_data.get("event_type", "refuel")
        # In future: call POST /api/fleet/events
        return {
            "event_id": "mock-fleet-456",
            "event_type": event_type,
            "gallons": extracted_data.get("gallons"),
            "cost": extracted_data.get("cost"),
            "odometer": extracted_data.get("odometer"),
            "created_at": datetime.now().isoformat()
        }
    else:
        return {"message": f"Action '{action}' not yet implemented for fleet"}


def route_to_health(action: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """Route to health/nutrition module."""
    return {"message": "Health module not yet implemented"}


def route_to_inventory(action: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """Route to inventory module."""
    return {"message": "Inventory module not yet implemented"}


def route_to_calendar(action: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """Route to calendar module."""
    return {"message": "Calendar module not yet implemented"}


# Module router mapping
MODULE_HANDLERS = {
    "accounting": route_to_accounting,
    "fleet": route_to_fleet,
    "health": route_to_health,
    "inventory": route_to_inventory,
    "calendar": route_to_calendar,
}


@router.post("/command", response_model=OrchestratorResponse)
async def process_command(raw_request: Request):
    """
    Universal endpoint for processing natural language commands.

    This is the main entry point called by the Apple Shortcut.

    Flow:
    1. Receive natural language command
    2. Use Claude to parse intent and extract data
    3. Route to appropriate module (accounting, fleet, etc.)
    4. Execute action and return human-readable response
    """
    # Debug: Log raw request body
    try:
        body = await raw_request.body()
        print(f"📥 Raw request body: {body.decode('utf-8')}")
        body_json = json.loads(body.decode('utf-8'))
        print(f"📦 Parsed JSON: {body_json}")
    except Exception as e:
        print(f"❌ Error parsing request body: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid request body: {str(e)}")

    # Parse into Pydantic model
    try:
        request = OrchestratorRequest(**body_json)
        print(f"🎤 Received command: '{request.command}' (length: {len(request.command)})")
    except Exception as e:
        print(f"❌ Pydantic validation error: {e}")
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")

    try:
        # Step 1: Parse command with Claude
        parsed = parse_command_with_claude(request.command, request.context)

        module = parsed.get("module")
        action = parsed.get("action")
        intent = parsed.get("intent")
        extracted_data = parsed.get("extracted_data", {})
        confidence = parsed.get("confidence", 0.0)
        clarification = parsed.get("clarification_needed")

        # Check if clarification is needed
        if clarification:
            return OrchestratorResponse(
                success=False,
                message=clarification,
                module="orchestrator",
                action="clarify",
                data={"original_command": request.command, "parsed": parsed}
            )

        # Check confidence threshold
        if confidence < 0.7:
            return OrchestratorResponse(
                success=False,
                message=f"I'm not sure I understood that correctly. Did you want to {intent}?",
                module="orchestrator",
                action="confirm",
                data={"original_command": request.command, "parsed": parsed}
            )

        # Step 1.5: Classify event types
        # Use event classifier if Claude didn't provide event types or as validation
        print(f"🔍 Running event classification for: '{request.command}'")
        classification: EventClassificationResult = classify_event(
            command=request.command,
            parsed_data=parsed,
            context=request.context
        )

        # Log classification result
        print(f"✅ Event classification complete:")
        print(f"   Primary event: {classification.primary_event.event_type} (confidence: {classification.primary_event.confidence})")
        if classification.secondary_events:
            for sec_event in classification.secondary_events:
                print(f"   Secondary event: {sec_event.event_type}")

        # Add classification data to parsed result
        parsed["event_classification"] = {
            "primary_event": classification.primary_event.dict(),
            "secondary_events": [e.dict() for e in classification.secondary_events] if classification.secondary_events else None,
            "classification_confidence": classification.confidence
        }

        # Step 2: Route to appropriate module
        if module not in MODULE_HANDLERS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown module: {module}"
            )

        handler = MODULE_HANDLERS[module]
        result_data = handler(action, extracted_data)

        # Step 3: Generate human-readable response
        message = generate_response_message(module, action, intent, result_data)

        return OrchestratorResponse(
            success=True,
            message=message,
            module=module,
            action=action,
            data=result_data,
            suggestions=generate_suggestions(module, action)
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Orchestrator error: {e}")
        print(f"❌ Full traceback:\n{error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Orchestrator error: {str(e)}"
        )


def generate_response_message(module: str, action: str, intent: str, data: Dict[str, Any]) -> str:
    """
    Generate human-readable message for Siri to speak back to user.
    """
    if module == "accounting":
        if action == "create":
            amount = data.get("amount", "unknown")
            desc = data.get("description", "transaction")
            return f"I've logged {desc} for ${amount:.2f}"
        elif action == "read":
            total = data.get("total_spent", 0)
            period = data.get("period", "this period")
            return f"You spent ${total:.2f} on {period}"

    elif module == "fleet":
        if action == "create":
            event_type = data.get("event_type", "event")
            if event_type == "refuel":
                gallons = data.get("gallons", "")
                cost = data.get("cost", "")
                return f"Logged refueling: {gallons} gallons for ${cost:.2f}"
            else:
                return f"Logged fleet {event_type}"

    return f"Completed {action} for {module}"


def generate_suggestions(module: str, action: str) -> List[str]:
    """
    Generate follow-up suggestions based on the action taken.
    """
    suggestions = []

    if module == "accounting" and action == "create":
        suggestions = [
            "Would you like to see your spending summary?",
            "Want to check your budget status?"
        ]
    elif module == "fleet" and action == "create":
        suggestions = [
            "Would you like to see your MPG trends?",
            "Want to check upcoming maintenance?"
        ]

    return suggestions


@router.get("/health")
async def orchestrator_health():
    """Health check for orchestrator"""
    return {
        "status": "ok",
        "orchestrator": "active",
        "claude_configured": client is not None,
        "modules": list(MODULE_HANDLERS.keys())
    }
