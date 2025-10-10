# Option B: Voice / Natural Language Interface Design

**Date:** 2025-10-08
**Status:** 📋 Design Phase

---

## Overview

A hands-free, conversational interface for LiMOS Accounting that allows users to enter transactions, check balances, and get financial insights using natural voice commands or text-based natural language. Built on speech-to-text (Whisper) and large language models (OpenAI GPT) for structured data extraction.

**Note:** You already have a working prototype in `/Users/ksd/Finance/` - This design leverages and extends that system!

---

## Why Voice/NLP?

### Use Cases

1. **On-the-Go Entry**
   - "I just spent $45 on gas at Shell"
   - While driving, walking, shopping - capture transactions immediately

2. **Hands-Free Cooking**
   - "Add $125 grocery purchase at Whole Foods"
   - While unloading groceries, hands full

3. **Quick Balance Checks**
   - "How much do I have left in my dining out budget?"
   - "What's my checking balance?"

4. **Natural Conversation**
   - "Is it okay if I buy a $500 couch?"
   - System checks budget, forecasts, responds: "Yes, you'll still have $1,200 left in your furniture envelope"

5. **Receipt Capture**
   - Take photo of receipt → Voice: "Add this receipt to groceries"
   - System OCRs receipt, extracts items, confirms with user

---

## Architecture

### System Components

```
┌──────────────────────────────────────────────────────────┐
│                    USER INTERFACES                        │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐   │
│  │   Voice    │  │    Text    │  │  Mobile Widget   │   │
│  │  (Siri/    │  │  (Slack/   │  │  (iOS Shortcut)  │   │
│  │  Alexa)    │  │  WhatsApp) │  │                  │   │
│  └────────────┘  └────────────┘  └──────────────────┘   │
└────────────┬───────────────┬────────────────┬───────────┘
             │               │                 │
             ▼               ▼                 ▼
┌──────────────────────────────────────────────────────────┐
│              VOICE/NLP PROCESSING LAYER                   │
│                                                            │
│  ┌─────────────────────────────────────────────────┐     │
│  │  1. Speech-to-Text (OpenAI Whisper)             │     │
│  │     Audio → Transcript                          │     │
│  └─────────────────────────────────────────────────┘     │
│                         │                                 │
│                         ▼                                 │
│  ┌─────────────────────────────────────────────────┐     │
│  │  2. Intent Detection (GPT-4 Function Calling)   │     │
│  │     Transcript → Structured Command             │     │
│  └─────────────────────────────────────────────────┘     │
│                         │                                 │
│                         ▼                                 │
│  ┌─────────────────────────────────────────────────┐     │
│  │  3. Entity Extraction                            │     │
│  │     Amount, Merchant, Category, Date            │     │
│  └─────────────────────────────────────────────────┘     │
│                         │                                 │
│                         ▼                                 │
│  ┌─────────────────────────────────────────────────┐     │
│  │  4. Confirmation & Validation                    │     │
│  │     Check for errors, ask for clarification     │     │
│  └─────────────────────────────────────────────────┘     │
│                         │                                 │
│                         ▼                                 │
│  ┌─────────────────────────────────────────────────┐     │
│  │  5. Text-to-Speech Response (Optional)           │     │
│  │     Feedback → Audio                             │     │
│  └─────────────────────────────────────────────────┘     │
└────────────┬────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────┐
│              LIMOS ACCOUNTING REST API                    │
│  POST /api/journal-entries                                │
│  GET  /api/forecast/account/{id}                          │
│  GET  /api/envelopes/budget                               │
└──────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Core Components

**1. Speech-to-Text:**
- **OpenAI Whisper API** (already in your Finance project!)
- Alternatives: Google Speech-to-Text, Azure Speech

**2. Natural Language Understanding:**
- **OpenAI GPT-4** with Function Calling
- Structured output extraction
- Context-aware responses

**3. Text-to-Speech (Optional):**
- **OpenAI TTS API**
- Alternatives: Google TTS, Azure TTS, ElevenLabs

**4. Voice Platforms:**
- **iOS Shortcuts** (Quick Start)
- **Siri Integration** (via Shortcuts)
- **Android** (Tasker or dedicated app)
- **Amazon Alexa** (Custom Skill)
- **Google Assistant** (Custom Action)

**5. Text Platforms:**
- **Telegram Bot**
- **WhatsApp Business API**
- **Slack Bot**
- **Discord Bot**
- **SMS** (Twilio)

---

## Existing Implementation (Finance Project)

You already have this working! Let's analyze what you have:

### `/Users/ksd/Finance/WhisperCapture.py`
```python
def transcribe_audio(audio_file_path):
    """Transcribes audio using OpenAI Whisper API"""
    with open(audio_file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript.text
```

### `/Users/ksd/Finance/main.py`
```python
def process_transaction_voice(transcript: str):
    """Uses OpenAI Function Calling to extract structured data"""
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[{
            "role": "user",
            "content": f"Extract transaction from: {transcript}"
        }],
        functions=[{
            "name": "create_transaction",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "amount": {"type": "number"},
                    "account": {"type": "string"},
                    "category": {"type": "string"},
                    "date": {"type": "string"}
                }
            }
        }]
    )
```

**This is exactly what we need!** We just need to:
1. Connect it to LiMOS API instead of Notion
2. Add more function definitions (balance queries, forecasts)
3. Create interface options (shortcuts, bots)

---

## Enhanced Design for LiMOS

### Function Definitions for GPT-4

```python
LIMOS_FUNCTIONS = [
    {
        "name": "create_transaction",
        "description": "Create a new financial transaction",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Transaction description (e.g., 'Starbucks coffee')"
                },
                "amount": {
                    "type": "number",
                    "description": "Transaction amount in dollars"
                },
                "from_account": {
                    "type": "string",
                    "description": "Source account (e.g., 'checking', 'savings', 'credit card')",
                    "enum": ["checking", "savings", "credit_card_a", "credit_card_b"]
                },
                "to_envelope": {
                    "type": "string",
                    "description": "Budget envelope or expense category",
                    "enum": ["groceries", "dining", "gas", "entertainment", "clothing", "gifts"]
                },
                "date": {
                    "type": "string",
                    "description": "Transaction date (YYYY-MM-DD). If not specified, use today."
                }
            },
            "required": ["description", "amount"]
        }
    },
    {
        "name": "check_balance",
        "description": "Check account or envelope balance",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "What to check (account name or envelope name)"
                },
                "target_type": {
                    "type": "string",
                    "enum": ["account", "envelope"],
                    "description": "Type of target"
                }
            },
            "required": ["target", "target_type"]
        }
    },
    {
        "name": "forecast_balance",
        "description": "Forecast account balance on a future date",
        "parameters": {
            "type": "object",
            "properties": {
                "account": {
                    "type": "string",
                    "description": "Account name"
                },
                "date": {
                    "type": "string",
                    "description": "Target date (YYYY-MM-DD)"
                }
            },
            "required": ["account", "date"]
        }
    },
    {
        "name": "check_affordability",
        "description": "Check if a planned purchase is affordable",
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "Purchase amount"
                },
                "category": {
                    "type": "string",
                    "description": "Spending category"
                }
            },
            "required": ["amount"]
        }
    }
]
```

---

## User Interaction Flows

### Flow 1: Simple Transaction Entry

**User:** 🎤 "I spent $45 on gas at Shell"

**System Processing:**
1. Whisper transcribes → "I spent $45 on gas at Shell"
2. GPT-4 extracts:
   ```json
   {
     "function": "create_transaction",
     "arguments": {
       "description": "Gas at Shell",
       "amount": 45.00,
       "from_account": "checking",
       "to_envelope": "gas",
       "date": "2025-10-08"
     }
   }
   ```
3. System maps to API call:
   ```python
   POST /api/journal-entries
   {
     "entry_date": "2025-10-08",
     "description": "Gas at Shell",
     "distributions": [
       {
         "account_id": "1000",
         "flow_direction": "from",
         "amount": 45.00,
         ...
       },
       {
         "account_id": "6400",  # Gas & Auto
         "flow_direction": "to",
         "amount": 45.00,
         "budget_envelope_id": "1530"
       }
     ]
   }
   ```
4. Response: 🔊 "Got it! Added $45 for gas at Shell. You have $205 left in your gas budget."

---

### Flow 2: Balance Check

**User:** 🎤 "How much is left in my dining out budget?"

**System Processing:**
1. Whisper → "How much is left in my dining out budget?"
2. GPT-4 extracts:
   ```json
   {
     "function": "check_balance",
     "arguments": {
       "target": "dining out",
       "target_type": "envelope"
     }
   }
   ```
3. System calls API:
   ```python
   GET /api/envelopes/budget
   # Find envelope with name matching "dining out"
   ```
4. Response: 🔊 "You have $210.50 remaining in your dining out budget for this month."

---

### Flow 3: Affordability Check

**User:** 🎤 "Can I afford a $500 couch?"

**System Processing:**
1. Whisper → "Can I afford a $500 couch?"
2. GPT-4 extracts:
   ```json
   {
     "function": "check_affordability",
     "arguments": {
       "amount": 500.00,
       "category": "furniture"
     }
   }
   ```
3. System logic:
   ```python
   # Get current checking balance
   balance = get_account_balance("1000")

   # Get forecast for end of month
   forecast = get_forecast("1000", end_of_month)

   # Check furniture/home maintenance envelope
   envelope = get_envelope("home_maintenance")

   # Calculate
   if envelope.current_balance >= 500:
       return "Yes! Use home maintenance envelope"
   elif balance - 500 > 1000:  # Maintain $1k buffer
       return "Yes, but creates envelope"
   else:
       return "Not recommended"
   ```
4. Response: 🔊 "Yes! You have $850 in your home maintenance envelope. After buying the $500 couch, you'll still have $350 left for other home expenses this month."

---

### Flow 4: Complex Transaction (Split)

**User:** 🎤 "I spent $150 at Target, $100 was groceries and $50 was clothing"

**System Processing:**
1. Whisper → "I spent $150 at Target, $100 was groceries and $50 was clothing"
2. GPT-4 extracts:
   ```json
   {
     "function": "create_transaction",
     "arguments": {
       "description": "Target",
       "amount": 150.00,
       "from_account": "checking",
       "splits": [
         {"envelope": "groceries", "amount": 100.00},
         {"envelope": "clothing", "amount": 50.00}
       ]
     }
   }
   ```
3. System creates multi-distribution entry
4. Response: 🔊 "Added $150 at Target, split between $100 groceries and $50 clothing."

---

### Flow 5: Forecast Query

**User:** 🎤 "What will my checking balance be at the end of December?"

**System Processing:**
1. Whisper → "What will my checking balance be at the end of December?"
2. GPT-4 extracts:
   ```json
   {
     "function": "forecast_balance",
     "arguments": {
       "account": "checking",
       "date": "2025-12-31"
     }
   }
   ```
3. System calls API:
   ```python
   GET /api/forecast/account/1000?target_date=2025-12-31
   ```
4. Response: 🔊 "Your checking account will have approximately $49,316 on December 31st. That's an increase of $23,834 from now, based on 28 scheduled transactions."

---

## Interface Options

### Option B1: iOS Shortcuts (Quickest to Implement)

**Setup:**

1. Create iOS Shortcut named "Log Expense"
2. Shortcut actions:
   ```
   1. Get text from: "Dictate text"
   2. Set variable "Transcript" to (Result of 1)
   3. URL: POST https://your-server.com/api/voice/process
      Body: {"transcript": (Transcript)}
   4. Get contents of URL (from step 3)
   5. Show result (spoken or notification)
   ```

**User Experience:**
- Say "Hey Siri, log expense"
- Siri: "What's the expense?"
- User: "Starbucks coffee, five fifty"
- Siri: "Added $5.50 for Starbucks. You have $295 left in dining out."

**Pros:**
✅ No app development needed
✅ Works immediately on iPhone
✅ Leverages built-in Siri
✅ Hands-free

**Cons:**
❌ iOS only
❌ Requires custom server endpoint
❌ Limited UI feedback

---

### Option B2: Telegram Bot

**Setup:**

```python
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler

async def handle_voice(update: Update, context):
    """Handle voice messages"""
    # Download voice file
    voice = await update.message.voice.get_file()
    audio_path = await voice.download_to_drive()

    # Transcribe with Whisper
    transcript = transcribe_audio(audio_path)

    # Process with GPT
    result = process_nlp_command(transcript)

    # Execute action
    response = execute_limos_action(result)

    # Reply to user
    await update.message.reply_text(response)

async def handle_text(update: Update, context):
    """Handle text messages"""
    text = update.message.text

    # Process with GPT (skip Whisper)
    result = process_nlp_command(text)
    response = execute_limos_action(result)

    await update.message.reply_text(response)

app = Application.builder().token("YOUR_BOT_TOKEN").build()
app.add_handler(MessageHandler(filters.VOICE, handle_voice))
app.add_handler(MessageHandler(filters.TEXT, handle_text))
app.run_polling()
```

**User Experience:**
- Open Telegram
- Send voice message: 🎤 "Spent $25 on lunch"
- Bot replies: "✅ Added $25 lunch expense. Dining out: $275/$300"

OR text:
- Type: "spent $25 on lunch"
- Same response

**Pros:**
✅ Works on any platform (iOS, Android, Desktop)
✅ Both voice AND text
✅ Rich formatting (buttons, inline keyboards)
✅ Push notifications
✅ Can send photos (for receipt capture)

**Cons:**
❌ Requires Telegram app
❌ Users must remember to open Telegram
❌ Requires hosting bot server

---

### Option B3: WhatsApp Business API

Similar to Telegram but on WhatsApp platform.

**Pros:**
✅ More universal than Telegram
✅ Users already on WhatsApp
✅ Voice + text + images

**Cons:**
❌ Requires WhatsApp Business API approval
❌ Costs money for messages
❌ More complex setup

---

### Option B4: Amazon Alexa Skill

**Setup:** Create custom Alexa Skill

**Invocation:**
- "Alexa, tell Money Manager I spent $45 on gas"
- "Alexa, ask Money Manager what's my dining budget"

**Pros:**
✅ Natural voice interaction
✅ Works with all Alexa devices (Echo, etc.)
✅ Hands-free in home

**Cons:**
❌ Requires AWS setup
❌ Alexa device required
❌ Skill certification process

---

### Option B5: Dedicated Mobile App with Widget

**iOS Widget:**
```
┌──────────────────────────┐
│  LiMOS Quick Entry       │
├──────────────────────────┤
│  🎤 Tap to speak         │
│                           │
│  Recent:                  │
│  • Groceries    $125.50  │
│  • Coffee       $5.50    │
│                           │
│  Budget Status:           │
│  Groceries ████░ $366/$800│
└──────────────────────────┘
```

Tap microphone → Speak → Transaction logged

**Pros:**
✅ Always visible on home screen
✅ One-tap access
✅ Native performance
✅ Can show context (recent, budget status)

**Cons:**
❌ Requires full mobile app development
❌ Separate iOS and Android apps

---

## Implementation Plan

### Phase 1: Server-Side Processing (Week 1)

**Create `/projects/accounting/voice/nlp_processor.py`**

```python
from openai import OpenAI
import requests

client = OpenAI(api_key="...")
LIMOS_API = "http://localhost:8000/api"

def process_voice_command(audio_file_path: str) -> dict:
    """Main entry point for voice commands"""
    # Step 1: Transcribe
    transcript = transcribe_audio(audio_file_path)

    # Step 2: Extract intent
    command = extract_intent(transcript)

    # Step 3: Execute
    result = execute_command(command)

    # Step 4: Generate response
    response = generate_response(result)

    return response

def transcribe_audio(audio_file_path: str) -> str:
    """Transcribe audio using Whisper"""
    with open(audio_file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript.text

def extract_intent(transcript: str) -> dict:
    """Extract structured command from transcript using GPT-4"""
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {
                "role": "system",
                "content": "You are a financial assistant. Extract structured data from user commands."
            },
            {
                "role": "user",
                "content": transcript
            }
        ],
        functions=LIMOS_FUNCTIONS,
        function_call="auto"
    )

    # Parse function call
    message = response.choices[0].message
    if message.function_call:
        return {
            "function": message.function_call.name,
            "arguments": json.loads(message.function_call.arguments)
        }

    return {"error": "Could not understand command"}

def execute_command(command: dict) -> dict:
    """Execute command against LiMOS API"""
    if command["function"] == "create_transaction":
        return create_transaction_from_nlp(command["arguments"])
    elif command["function"] == "check_balance":
        return check_balance_from_nlp(command["arguments"])
    # ... other commands ...

def create_transaction_from_nlp(args: dict) -> dict:
    """Create transaction via API"""
    # Map natural language to account IDs
    account_map = {
        "checking": "1000",
        "savings": "1100",
        "credit_card_a": "2100"
    }

    envelope_map = {
        "groceries": {"account": "6300", "envelope": "1500"},
        "dining": {"account": "6310", "envelope": "1510"},
        # ... more mappings
    }

    from_account = account_map.get(args.get("from_account", "checking"))
    to_mapping = envelope_map.get(args.get("to_envelope", "groceries"))

    transaction = {
        "entry_date": args.get("date", datetime.now().isoformat()[:10]),
        "description": args["description"],
        "distributions": [
            {
                "account_id": from_account,
                "account_type": "asset",
                "flow_direction": "from",
                "amount": args["amount"],
                "multiplier": -1,
                "debit_credit": "Cr"
            },
            {
                "account_id": to_mapping["account"],
                "account_type": "expense",
                "flow_direction": "to",
                "amount": args["amount"],
                "multiplier": 1,
                "debit_credit": "Dr",
                "budget_envelope_id": to_mapping["envelope"]
            }
        ],
        "status": "posted"
    }

    response = requests.post(f"{LIMOS_API}/journal-entries", json=transaction)
    return response.json()

def generate_response(result: dict) -> str:
    """Generate natural language response"""
    if "journal_entry_id" in result:
        # Successful transaction
        amount = result["distributions"][0]["amount"]
        desc = result["description"]
        return f"✅ Added ${amount:.2f} for {desc}"

    # ... handle other response types ...
```

---

### Phase 2: REST Endpoint (Week 1)

**Add to `/projects/accounting/api/main.py`**

```python
from .voice.nlp_processor import process_voice_command, extract_intent

@app.post("/api/voice/process", tags=["Voice"])
async def process_voice(file: UploadFile = File(...)):
    """Process voice command"""
    # Save uploaded audio
    audio_path = f"/tmp/{file.filename}"
    with open(audio_path, "wb") as f:
        f.write(await file.read())

    # Process
    result = process_voice_command(audio_path)

    # Cleanup
    os.remove(audio_path)

    return result

@app.post("/api/nlp/command", tags=["Voice"])
async def process_text_command(command: str):
    """Process text command (no audio)"""
    intent = extract_intent(command)
    result = execute_command(intent)
    response = generate_response(result)
    return {"response": response, "result": result}
```

---

### Phase 3: Choose Interface (Week 2)

Pick ONE to start:
- **iOS Shortcuts** (easiest, iOS-only)
- **Telegram Bot** (universal, best for prototyping)
- **Web-based voice** (add to Web UI)

---

## Conversation Intelligence

### Context Awareness

System remembers recent context:

**User:** "I spent $50 on groceries"
**System:** "Added $50 groceries. You have $750 left."

**User:** "Actually, make that $55"
**System:** (Updates last transaction) "Updated to $55. You have $745 left."

**User:** "Add $20 more to that"
**System:** (Creates new transaction linked to same merchant) "Added $20 more groceries. Total spent: $75. You have $725 left."

### Proactive Insights

System can volunteer information:

**User:** "Add $150 dining out at Fogo de Chao"
**System:** "Added $150. **Warning:** That puts you $50 over your $300 dining budget for this month. You have -$50 remaining."

**User:** "Can I afford a $1000 laptop?"
**System:** "Based on your forecast, yes. You'll have $5,200 available on payday Friday. However, you have no electronics budget envelope. Would you like me to create one?"

---

## Voice Feedback Options

### Option 1: Text Response Only
- Fast, simple
- Works everywhere
- Good for text interfaces (Telegram, Slack)

### Option 2: Text + Audio
- Use OpenAI TTS to speak response
- More natural for voice workflows
- Higher latency

### Option 3: Rich Media
- Send formatted response with buttons
- "Add $50 groceries → [✓ Confirm] [✗ Cancel] [Edit]"
- Best for Telegram/messaging apps

---

## Privacy & Security

### Audio Handling
- Audio files deleted immediately after transcription
- Never stored long-term
- Transcripts encrypted at rest

### API Security
- Require API key for voice endpoint
- Rate limiting (prevent abuse)
- User authentication (future: multi-user)

### OpenAI Data
- OpenAI does NOT use API data for training
- Transcripts sent to OpenAI, not stored by them
- Follow OpenAI's data usage policies

---

## Cost Analysis

### OpenAI Whisper
- $0.006 per minute
- Average transaction: 5 seconds = $0.0005
- 1000 transactions/month = $0.50

### OpenAI GPT-4
- $0.01 per 1K input tokens
- $0.03 per 1K output tokens
- Average command: ~100 tokens in + 200 out = $0.007
- 1000 commands/month = $7.00

### Total: ~$7.50/month for 1000 voice transactions

Very affordable!

---

## Summary

### Pros of Voice/NLP
✅ **Hands-Free** - Perfect for on-the-go
✅ **Fast Entry** - Seconds to log transaction
✅ **Natural** - Just talk normally
✅ **Universal** - Works via phone, smart speaker, chat
✅ **Intelligent** - Understands context, provides insights
✅ **Low Cost** - ~$0.007 per transaction

### Cons
❌ **Requires Internet** - Can't work offline
❌ **Privacy Concerns** - Audio sent to OpenAI
❌ **Accuracy** - May misunderstand complex commands
❌ **Setup Required** - Need to create interface

### Best For
- Busy users who want quick entry
- On-the-go transaction capture
- Users comfortable with voice tech
- Supplement to other interfaces (not primary)

---

**You already have the foundation in `/Users/ksd/Finance/`! Just need to connect it to LiMOS API and add interface options.**

**Ready to implement upon approval.**
