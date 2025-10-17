# Event Classification Rules

This document defines the rules for classifying user commands into event types. These rules are used by the Event Classification Layer to determine which events to trigger and which modules to route to.  IT also looks at the Data that was Received as Input and applies **Parsing Rules**** to determine how to handle Missing Data.  Once Parsing Conditionals have been ap0plied, then Validate that all **Required Data** are not null (missing data)

---

## Rule Format

Each rule follows this pattern:

```
IF [**Rule**] THEN classify as [EventType]
  → Route to: [module]
  → Confidence: [high|medium|low]
  → May trigger: [secondary events]
```

---

## Money Events

### Purchase Event

**Rule:** IF( command contains payment_method AND acquisition of goods/services) THEN EventType
**Keywords:** `bought`, `purchased`, `spent`, `paid for`, `cost`, `$`, `got`, `picked up`
**Required Data:** amount, description, Expense Distribution account
**Optional Data:** category, payment_method, date, vendor

**Examples:**
- "I bought $50 of groceries at Safeway"
- "Spent $29.99 on a book at Amazon"
- "Paid $15 for parking downtown"
- "Got coffee at Starbucks, $6.50"

**Confidence:**
- High (0.90+): Amount + specific merchant/item + past tense purchase verb
- Medium (0.70-0.89): Amount + purchase verb, but vague description
- Low (<0.70): Ambiguous whether it's a purchase or something else

**Route to:** accounting module
**Action:** create
**Transaction Type:** expense

---

### Return Event

**Rule:** IF command indicates returning goods for refund
**Keywords:** `returned`, `return`, `refund`, `took back`, `sent back`
**Required Data:** amount, description, merchant
**Optional Data:** original_transaction_id, reason

**Examples:**
- "I returned the shirt to Target for $29.99"
- "Got a refund from Amazon, $45"
- "Took back the shoes, received $89.99"

**Confidence:**
- High (0.90+): Clear return verb + amount + merchant
- Medium (0.70-0.89): Return mentioned but missing some details
- Low (<0.70): Unclear if it's an actual return or just considering one

**Route to:** accounting module
**Actions:** create
**Transaction Type:** expense reversal (negative expense)

---

### Transfer Event

**Rule:** IF command indicates moving money between accounts
**Keywords:** `transfer`, `moved`, `transferred`, `sent money`
**Required Data:** amount, from_account, to_account
**Optional Data:** date, memo

**Examples:**
- "Transfer $500 from checking to savings"
- "Moved $1,000 to my investment account"
- "Transferred $250 from savings to checking"

**Confidence:**
- High (0.90+): Clear transfer verb + amount + both accounts specified
- Medium (0.70-0.89): Transfer mentioned but one account implied
- Low (<0.70): Unclear which accounts involved

**Route to:** accounting module
**Action:** create
**Transaction Type:** transfer (two distributions: one FROM, one TO)

---

### AP Payment Event (Bill Payment)

**Rule:** IF command indicates paying an existing bill/invoice
**Keywords:** `paid bill`, `paid invoice`, `payment for`, `paid the`, `bill payment`
**Required Data:** amount, payee/description
**Optional Data:** bill_date, due_date, account_number

**Examples:**
- "Paid the electric bill of $85"
- "Made payment for internet service, $79.99"
- "Paid Comcast bill, $120"

**Confidence:**
- High (0.90+): "paid" + "bill" + amount + payee
- Medium (0.70-0.89): Payment mentioned but unclear if it's a bill
- Low (<0.70): Could be a purchase instead of bill payment

**Route to:** accounting module
**Action:** create
**Transaction Type:** liability decrease + asset decrease

---

### AP Invoice Event (Receiving Bill)

**Rule:** IF command indicates receiving a bill/invoice (not yet paid)
**Keywords:** `received bill`, `got invoice`, `bill came`, `was billed`, `charged`
**Required Data:** amount, vendor/description
**Optional Data:** due_date, bill_date, account_number

**Examples:**
- "Received electric bill for $85"
- "Got invoice from plumber for $350"
- "Credit card bill came in, $1,245"

**Confidence:**
- High (0.90+): "received" + "bill/invoice" + amount + vendor
- Medium (0.70-0.89): Bill mentioned but unclear if received or paid
- Low (<0.70): Ambiguous event type

**Route to:** accounting module
**Action:** create
**Transaction Type:** expense increase + liability increase

---

### Deposit Event

**Rule:** IF command indicates money coming in (income/revenue)
**Keywords:** `deposit`, `received`, `got paid`, `income`, `paycheck`, `earned`, `revenue`, `payment received`
**Required Data:** amount, source
**Optional Data:** date, deposit_account, category

**Examples:**
- "Received paycheck deposit of $3,200"
- "Got paid $500 for consulting work"
- "Deposited $1,000 from client payment"
- "Earned $250 from freelance project"

**Confidence:**
- High (0.90+): Income verb + amount + source
- Medium (0.70-0.89): Amount mentioned but source unclear
- Low (<0.70): Unclear if it's income or something else

**Route to:** accounting module
**Action:** create
**Transaction Type:** asset increase + income increase

---

### ACH Event

**Rule:** IF command explicitly mentions ACH or automated payment
**Keywords:** `ACH`, `automated payment`, `auto-pay`, `automatic deduction`
**Required Data:** amount, account, description
**Optional Data:** recurring_schedule, vendor

**Examples:**
- "ACH payment to credit card of $1,500"
- "Automated payment of $250 to Discover"
- "Auto-pay deducted $89 for gym membership"

**Confidence:**
- High (0.90+): "ACH" or "automated" + amount + accounts
- Medium (0.70-0.89): Automated payment but unclear accounts
- Low (<0.70): Could be a regular purchase or transfer

**Route to:** accounting module
**Action:** create
**Transaction Type:** varies (often liability decrease + asset decrease)

---

### Sales Event

**Rule:** IF command indicates selling goods or services
**Keywords:** `sold`, `sale`, `sold for`, `revenue from sale`
**Required Data:** amount, item/description
**Optional Data:** cost_basis, buyer, sale_date

**Examples:**
- "Sold old laptop for $400"
- "Made a sale of vintage books, $125"
- "Got $50 for selling furniture on Craigslist"

**Confidence:**
- High (0.90+): "sold" + item + amount
- Medium (0.70-0.89): Sale mentioned but unclear details
- Low (<0.70): Could be income instead of sale

**Route to:** accounting module
**Action:** create
**Transaction Type:** asset increase (cash) + either asset decrease (item) or revenue

---

## Fleet Events

### PumpEvent

**Rule:** IF command indicates vehicle refueling, Then PumpEvent
**Keywords:** 
  [`gas`, `fuel`, `filled up`, `refuel`, `pump`, `gallons`, `diesel`, `premium`, `additive`, `DEF`]
**Identifiable Data**: 
  [price,quantity, unit-of-measure, odometer, cost, date-time, fuel-gauge, payment-method, from-account, to-account, fuel-type, location, vehicle]
**Conditionals:** 
  - IF( Have('cost') and Have('price') and Missing('gallons') ) -> calculate 'gallons'
  - IF( Have('gallons') and Have('price') and Missing('cost') ) -> calculate 'cost'
**Required Data:**
  [price, quantity, unit-of-measure, cost, date-time, from-account, to-account, fuel-type, location]
**Error Handling:**
  
**Examples:**
  - "Filled up gas, 12 gallons, $45, odometer 45000"
  - "Got gas, $52, regular unleaded"
  - "Refueled at Shell, 15 gallons, $48.75"

**Confidence:**
  - High (0.90+): Fuel keyword + gallons + cost + odometer
  - Medium (0.70-0.89): Fuel keyword + cost, but missing odometer or gallons
  - Low (<0.70): Only mentions gas, unclear if refueling

**Route to:** fleet module (primary) + accounting module (secondary)
**Action:** create
**Secondary Events:** Purchase (Money Event)

---

### RepairEvent

**Rule:** IF command indicates vehicle repair or service by a vendor
**Keywords:** `repair`, `fixed`, `mechanic`, `service`, `shop`, `repaired`
**Required Data:** description, cost OR quote
**Optional Data:** odometer, vendor, repair_type, parts, labor

**Examples:**
- "Brake repair at Midas, $450, odometer 46000"
- "Mechanic fixed the exhaust, $275"
- "Car repair shop charged $850 for transmission work"

**Confidence:**
- High (0.90+): Repair keyword + specific work + cost + odometer
- Medium (0.70-0.89): Repair mentioned but missing details
- Low (<0.70): Could be maintenance instead of repair

**Route to:** fleet module (primary) + accounting module (secondary)
**Action:** create
**Secondary Events:** Purchase (Money Event) if cost > 0

---

### MaintEvent (Maintenance)

**Rule:** IF command indicates scheduled or DIY vehicle maintenance
**Keywords:** `oil change`, `maintenance`, `replaced`, `changed`, `serviced`, `tune-up`, `filter`, `fluids`, `DIY`
**Required Data:** maintenance_type, description
**Optional Data:** cost, odometer, parts, labor_type (DIY vs professional)

**Examples:**
- "Oil change at Jiffy Lube, $59.99, odometer 45500"
- "Replaced air filter, $25, DIY"
- "Changed wiper blades, $18"
- "Tire rotation at Costco, free"

**Confidence:**
- High (0.90+): Maintenance keyword + specific work + odometer
- Medium (0.70-0.89): Maintenance mentioned but missing details
- Low (<0.70): Could be a repair instead of maintenance

**Route to:** fleet module (primary) + accounting module (secondary)
**Action:** create
**Secondary Events:** Purchase (Money Event) if cost > 0

---

### TravelEvent

**Rule:** IF command indicates a trip/drive for mileage tracking
**Keywords:** `drove`, `trip to`, `drive`, `traveled`, `miles`, `mileage`, `business trip`, "Started driving", "stopped for the day"
**Required Data:** distance OR (start_location AND end_location)
**Optional Data:** purpose, vehicle, odometer_start, odometer_end, duration

**Examples:**
- "Drove to San Francisco, 240 miles, business"
- "Trip to client site, 45 miles round trip"
- "Business mileage: 120 miles"
- "Drove from Sacramento to Los Angeles, 385 miles"

**Confidence:**
- High (0.90+): Drive keyword + distance/locations + purpose
- Medium (0.70-0.89): Drive mentioned but missing distance or purpose
- Low (<0.70): Unclear if tracking is needed

**Route to:** fleet module
**Action:** create
**Secondary Events:** None (unless business mileage reimbursement flagged)

---

## Health Events

### MealEvent

**Rule:** IF command indicates recording a meal
**Keywords:** `ate`, `had`, `meal`, `breakfast`, `lunch`, `dinner`, `snack`, `food`, `calories`
**Required Data:** meal_type OR time, items/description
**Optional Data:** calories, macros (protein, carbs, fat), location, cost

**Examples:**
- "Had oatmeal with blueberries for breakfast, 350 calories"
- "Ate a turkey sandwich for lunch"
- "Dinner: salmon, rice, and vegetables, 650 cal"
- "Snack: protein bar, 200 calories"

**Confidence:**
- High (0.90+): Meal keyword + food items + meal type/time
- Medium (0.70-0.89): Food mentioned but unclear which meal
- Low (<0.70): Could be a purchase instead of meal logging

**Route to:** health module
**Action:** create
**Secondary Events:** Purchase (Money Event) if cost mentioned

---

### ExerciseEvent

**Rule:** IF command indicates physical activity
**Keywords:** `ran`, `walked`, `jogged`, `workout`, `exercise`, `gym`, `lifted`, `swam`, `biked`, `cardio`, `training`
**Required Data:** activity_type, duration OR distance
**Optional Data:** calories_burned, heart_rate, pace, location, intensity

**Examples:**
- "Ran 5 miles in 42 minutes"
- "Workout at the gym, 60 minutes, weightlifting"
- "Walked 10,000 steps today"
- "Swam 30 laps, 45 minutes"

**Confidence:**
- High (0.90+): Exercise verb + activity + duration/distance
- Medium (0.70-0.89): Exercise mentioned but vague details
- Low (<0.70): Unclear if logging or just mentioning

**Route to:** health module
**Action:** create
**Secondary Events:** None

---

### HikeEvent

**Rule:** IF command specifically indicates hiking activity
**Keywords:** `hiked`, `hike`, `trail`, `trekking`, `mountain`, `elevation gain`
**Required Data:** trail_name OR location, distance
**Optional Data:** elevation_gain, duration, difficulty, terrain

**Examples:**
- "Hiked Mt. Tam, 8 miles, 2000ft elevation gain"
- "Trail run at Point Reyes, 6 miles"
- "Hiked the Steep Ravine Trail, 3.5 hours, moderate difficulty"

**Confidence:**
- High (0.90+): Hike keyword + trail name + distance + elevation
- Medium (0.70-0.89): Hike mentioned but missing trail or distance
- Low (<0.70): Could be a general walk instead of hike

**Route to:** health module
**Action:** create
**Secondary Events:** None

---

## Food Inventory Events

### StockEvent

**Rule:** IF command indicates adding items to inventory with expiration tracking
**Keywords:** `bought` + `expires`, `stocked`, `got` + `expiry`, `purchased` + `best by`
**Required Data:** item_name, quantity
**Optional Data:** container, expiration_date, location, cost, brand

**Examples:**
- "Bought 2 gallons of milk, expires 10/20"
- "Stocked up on canned goods, 12 cans, expire 2026"
- "Got eggs, 18 count, best by 10/25"

**Confidence:**
- High (0.90+): Purchase + item + quantity + expiration
- Medium (0.70-0.89): Purchase + item but no expiration
- Low (<0.70): Could be a simple purchase without inventory tracking

**Route to:** inventory module (primary) + accounting module (secondary)
**Action:** create
**Secondary Events:** Purchase (Money Event) if cost mentioned

---

### UseFoodEvent

**Rule:** IF command indicates consuming or using inventory items
**Keywords:** `used`, `consumed`, `ate`, `finished`, `ran out of`, `opened`
**Required Data:** item_name
**Optional Data:** quantity_used, remaining_quantity

**Examples:**
- "Used 1 can of tomato sauce"
- "Finished the milk"
- "Opened a new jar of peanut butter"
- "Consumed 2 servings of protein powder"

**Confidence:**
- High (0.90+): Use verb + specific item + quantity
- Medium (0.70-0.89): Use mentioned but vague
- Low (<0.70): Could be a meal log instead

**Route to:** inventory module
**Action:** update (decrease quantity)
**Secondary Events:** None

---

### FoodExpiryCheck

**Rule:** IF command is a query about expiring items
**Keywords:** `expiring`, `expired`, `about to expire`, `check expiration`, `what's expiring`, `going bad`
**Required Data:** None (query)
**Optional Data:** location, days_threshold, category

**Examples:**
- "What's about to expire in the fridge?"
- "Check for expired items in the pantry"
- "What food is expiring this week?"
- "Show me items expiring in the next 3 days"

**Confidence:**
- High (0.90+): Expiry keyword + query form + location/timeframe
- Medium (0.70-0.89): Expiry mentioned but unclear scope
- Low (<0.70): Could be asking about a specific item

**Route to:** inventory module
**Action:** read (query)
**Secondary Events:** None

---

## Calendar Events

### AppointmentEvent

**Rule:** IF command indicates scheduling an appointment or meeting
**Keywords:** `appointment`, `meeting`, `scheduled`, `book`, `reserve`, `doctor`, `dentist`, `call scheduled`
**Required Data:** date, time, description/title
**Optional Data:** duration, location, attendees, reminder_time

**Examples:**
- "Doctor appointment Tuesday at 2pm"
- "Meeting with client on Friday at 10am"
- "Dentist appointment next Monday, 9:30am"
- "Scheduled hair cut for 3pm tomorrow"

**Confidence:**
- High (0.90+): Appointment keyword + specific date + time + title
- Medium (0.70-0.89): Appointment mentioned but date/time vague
- Low (<0.70): Unclear if it's confirmed or just thinking about it

**Route to:** calendar module
**Action:** create
**Secondary Events:** None

---

### ReminderEvent

**Rule:** IF command is setting a reminder
**Keywords:** `remind me`, `reminder`, `don't forget`, `alert me`, `notification`
**Required Data:** reminder_text, reminder_time
**Optional Data:** recurrence_rule, priority

**Examples:**
- "Remind me to call mom tomorrow at 9am"
- "Set a reminder to pay rent on the 1st"
- "Don't forget to pick up dry cleaning Friday afternoon"
- "Remind me about the meeting 15 minutes before"

**Confidence:**
- High (0.90+): Remind keyword + action + specific time
- Medium (0.70-0.89): Remind mentioned but time vague
- Low (<0.70): Could be a note instead of reminder

**Route to:** calendar module
**Action:** create
**Secondary Events:** None

---

### TaskEvent

**Rule:** IF command is creating a to-do item or task
**Keywords:** `task`, `todo`, `to-do`, `need to`, `must`, `add task`, `due`
**Required Data:** task_title
**Optional Data:** description, due_date, priority, status, tags

**Examples:**
- "Add task: clean garage, due Friday"
- "Todo: review contract by end of week"
- "Need to call insurance company"
- "Task: prepare presentation, high priority"

**Confidence:**
- High (0.90+): Task keyword + clear action + due date
- Medium (0.70-0.89): Task mentioned but unclear deadline
- Low (<0.70): Could be a note or reminder instead

**Route to:** calendar module
**Action:** create
**Secondary Events:** None

---

## Multi-Event Detection Rules

### Rule 1: Purchase + Inventory
**Condition:** Purchase event AND FoodItem
**Action:** Trigger both Purchase (money) and StockEvent (inventory)
**Example:** "Bought 2 gallons of milk for $7.50, expires 10/20"

### Rule 2: Fleet Event + Purchase
**Condition:** Any fleet event with cost > 0
**Action:** Trigger fleet event AND Purchase (money)
**Examples:**
- PumpEvent → Purchase
- RepairEvent → Purchase
- MaintEvent → Purchase

### Rule 3: Meal + Purchase
**Condition:** MealEvent AND cost mentioned
**Action:** Trigger MealEvent (health) AND Purchase (money)
**Example:** "Had lunch at Chipotle, $12, burrito bowl"

### Rule 4: Business Travel + Mileage Reimbursement
**Condition:** TravelEvent AND purpose = "business"
**Action:** Trigger TravelEvent (fleet) AND create note for reimbursement tracking
**Example:** "Drove to client site, 45 miles, business"

---

## Confidence Scoring Guidelines

### High Confidence (0.85 - 1.0)
- All required fields can be extracted
- Keywords are unambiguous
- Context makes the event type clear
- Minimal risk of misclassification

### Medium Confidence (0.70 - 0.84)
- Most required fields present
- Some ambiguity in keywords
- Context helps but isn't definitive
- May need clarification for edge cases

### Low Confidence (< 0.70)
- Missing required fields
- Keywords are ambiguous or missing
- Context doesn't help
- SHOULD trigger clarification request

---

## Conflict Resolution

When multiple event types match, use this priority order:

1. **Explicit Keywords Win**: If user explicitly says A Fuel Event Keyword or "refuel" vs just "spent $45", classify as PumpEvent
2. **More Specific Wins**: RepairEvent > MaintEvent > Purchase
3. **Context Helps**: "at Safeway" → likely Purchase, "at gym" → likely ExerciseEvent
4. **Multi-Event When Both Clear**: If both events have high confidence, trigger both
5. **Ask When Ambiguous**: If confidence < 0.70, ask user for clarification

---

## Special Cases

### Case 1: Zero-Cost Events
**Example:** "Tire rotation at Costco, free"
**Action:** Trigger MaintEvent but NOT Purchase event

### Case 2: Returns with Exchanges
**Example:** "Returned shirt and bought a different one"
**Action:** Trigger both Return event AND Purchase event

### Case 3: Reimbursable Expenses
**Example:** "Client dinner, $85, will be reimbursed"
**Action:** Trigger Purchase and flag for reimbursement tracking

### Case 4: DIY Maintenance with Parts
**Example:** "Changed oil myself, bought 5 quarts for $23"
**Action:** Trigger MaintEvent (fleet) AND Purchase (money)

---

## Status

**Version:** 1.0
**Last Updated:** 2025-10-16
**Next Review:** When new event types are added or classification accuracy drops below 90%
