# Budget Envelope System - Test Plan

**Date:** 2025-01-08
**Status:** Ready for Testing
**Module:** LiMOS Accounting - Budget Envelopes

---

## Test Objectives

1. Verify virtual envelope balance tracking accuracy
2. Validate fundamental equation: Bank = Budget + Payment + Available
3. Test transaction posting updates envelopes correctly
4. Verify monthly allocation rollover policies
5. Test forecasting calculations
6. Validate overspending prevention
7. Ensure audit trail completeness

---

## Test Data Requirements

### Setup Data

1. **Chart of Accounts** (27 accounts)
   - 5 Asset accounts (Cash, Savings, etc.)
   - 4 Liability accounts (Credit Cards, Mortgage, Auto Loan)
   - 1 Equity account (Owner's Equity)
   - 7 Revenue accounts (Salary, Interest, etc.)
   - 10 Expense accounts (Groceries, Dining, Gas, etc.)

2. **Budget Envelopes** (8 envelopes)
   - Groceries ($800/month, ACCUMULATE)
   - Dining Out ($300/month, RESET)
   - Gas & Auto ($250/month, ACCUMULATE)
   - Entertainment ($150/month, RESET)
   - Clothing ($200/month, CAP at $600)
   - Home Maintenance ($500/month, ACCUMULATE)
   - Gifts ($100/month, ACCUMULATE)
   - Personal Care ($100/month, RESET)

3. **Payment Envelopes** (3 envelopes)
   - Credit Card A - Payment Reserve
   - Credit Card B - Payment Reserve
   - Auto Loan - Payment Reserve

4. **Account-Envelope Links**
   - Link each expense account to its budget envelope
   - Link each liability account to its payment envelope

---

## Test Scenarios

### Test Suite 1: Basic Envelope Operations

#### Test 1.1: Create Budget Envelope
**Objective:** Verify budget envelope creation

**Steps:**
1. Create BudgetEnvelope "Groceries"
   - envelope_number: "1500"
   - monthly_allocation: $800
   - rollover_policy: ACCUMULATE
2. Verify envelope created successfully
3. Verify current_balance = 0

**Expected Results:**
- Envelope exists in system
- All fields set correctly
- Balance starts at 0

---

#### Test 1.2: Create Payment Envelope
**Objective:** Verify payment envelope creation

**Steps:**
1. Create PaymentEnvelope "Credit Card A"
   - envelope_number: "1600"
   - linked_account_id: "2100-CreditCard-A"
2. Verify envelope created successfully
3. Verify current_balance = 0

**Expected Results:**
- Envelope exists in system
- Linked to correct liability account
- Balance starts at 0

---

### Test Suite 2: Monthly Allocations

#### Test 2.1: Apply Monthly Allocation - RESET Policy
**Objective:** Verify RESET policy zeros out previous balance

**Setup:**
- Envelope: Dining Out ($300/month, RESET)
- Current balance: $45.23

**Steps:**
1. Call apply_monthly_allocation() for February 1
2. Verify new balance = $300.00
3. Verify old balance of $45.23 is discarded

**Expected Results:**
- current_balance = $300.00
- allocated_this_period = $300.00
- spent_this_period = $0.00
- BudgetAllocation record created

---

#### Test 2.2: Apply Monthly Allocation - ACCUMULATE Policy
**Objective:** Verify ACCUMULATE policy adds to existing balance

**Setup:**
- Envelope: Groceries ($800/month, ACCUMULATE)
- Current balance: $345.23

**Steps:**
1. Call apply_monthly_allocation() for February 1
2. Verify new balance = $1,145.23 ($345.23 + $800)

**Expected Results:**
- current_balance = $1,145.23
- allocated_this_period = $800.00
- BudgetAllocation record created

---

#### Test 2.3: Apply Monthly Allocation - CAP Policy
**Objective:** Verify CAP policy limits maximum balance

**Setup:**
- Envelope: Clothing ($200/month, CAP at $600)
- Current balance: $550.00

**Steps:**
1. Call apply_monthly_allocation() for February 1
2. Verify new balance = $600.00 (not $750)
3. Verify actual allocation = $50.00 (not $200)

**Expected Results:**
- current_balance = $600.00 (capped)
- allocated_this_period = $50.00
- $150 "returned" to Available

---

#### Test 2.4: Apply All Monthly Allocations
**Objective:** Verify batch allocation to all envelopes

**Steps:**
1. Call apply_monthly_allocations() for all envelopes
2. Verify each envelope receives its allocation
3. Verify total allocated matches sum of allocations
4. Verify BudgetAllocation records created for each

**Expected Results:**
- 8 BudgetAllocation records created
- Total allocated = sum of individual allocations
- Rollover policies correctly applied

---

### Test Suite 3: Transaction Posting

#### Test 3.1: Cash Purchase Updates Budget Envelope
**Objective:** Verify cash expense decreases budget envelope

**Setup:**
- Bank: $10,000
- Budget Envelope "Groceries": $800

**Transaction:**
```json
{
  "description": "Whole Foods",
  "distributions": [
    {
      "account_id": "1000-Cash",
      "account_type": "asset",
      "flow_direction": "from",
      "amount": 125.50
    },
    {
      "account_id": "6300-Groceries",
      "account_type": "expense",
      "flow_direction": "to",
      "amount": 125.50,
      "budget_envelope_id": "1500-Groceries"
    }
  ]
}
```

**Expected Results:**
- Bank balance: $9,874.50 (-$125.50)
- Budget Envelope "Groceries": $674.50 (-$125.50)
- Payment envelopes: unchanged
- Available: $9,874.50 - $674.50 = $9,200.00
- EnvelopeTransaction record created

---

#### Test 3.2: Credit Card Purchase Updates Both Envelopes
**Objective:** Verify credit purchase affects budget AND payment envelopes

**Setup:**
- Bank: $10,000
- Budget Envelope "Groceries": $800
- Payment Envelope "Credit Card A": $1,200
- Credit Card A Liability: $1,200

**Transaction:**
```json
{
  "description": "Costco on credit card",
  "distributions": [
    {
      "account_id": "2100-CreditCard-A",
      "account_type": "liability",
      "flow_direction": "from",
      "amount": 245.67,
      "payment_envelope_id": "1600-CC-A"
    },
    {
      "account_id": "6300-Groceries",
      "account_type": "expense",
      "flow_direction": "to",
      "amount": 245.67,
      "budget_envelope_id": "1500-Groceries"
    }
  ]
}
```

**Expected Results:**
- Bank balance: $10,000 (UNCHANGED)
- Credit Card Liability: $1,445.67 (+$245.67)
- Budget Envelope "Groceries": $554.33 (-$245.67)
- Payment Envelope "Credit Card A": $1,445.67 (+$245.67)
- Total Allocated: unchanged ($800 budget + $1,200 payment = $2,000 before; $554.33 + $1,445.67 = $2,000 after)
- Available: $8,000 (unchanged)
- 2 EnvelopeTransaction records created

---

#### Test 3.3: Credit Card Payment Updates Payment Envelope
**Objective:** Verify liability payment decreases payment envelope

**Setup:**
- Bank: $10,000
- Payment Envelope "Credit Card A": $1,445.67
- Credit Card A Liability: $1,445.67

**Transaction:**
```json
{
  "description": "Pay credit card",
  "distributions": [
    {
      "account_id": "1000-Cash",
      "account_type": "asset",
      "flow_direction": "from",
      "amount": 500.00
    },
    {
      "account_id": "2100-CreditCard-A",
      "account_type": "liability",
      "flow_direction": "to",
      "amount": 500.00,
      "payment_envelope_id": "1600-CC-A"
    }
  ]
}
```

**Expected Results:**
- Bank balance: $9,500.00 (-$500)
- Credit Card Liability: $945.67 (-$500)
- Payment Envelope "Credit Card A": $945.67 (-$500)
- Budget envelopes: unchanged
- Total Allocated: $1,500.00 ($554.33 budget + $945.67 payment)
- Available: $8,000.00 ($9,500 - $1,500) [unchanged from before]
- EnvelopeTransaction record created

---

#### Test 3.4: Expense Refund Increases Budget Envelope
**Objective:** Verify refund increases budget envelope

**Setup:**
- Budget Envelope "Groceries": $554.33

**Transaction:**
```json
{
  "description": "Return groceries",
  "distributions": [
    {
      "account_id": "6300-Groceries",
      "account_type": "expense",
      "flow_direction": "from",
      "amount": 25.00,
      "budget_envelope_id": "1500-Groceries"
    },
    {
      "account_id": "1000-Cash",
      "account_type": "asset",
      "flow_direction": "to",
      "amount": 25.00
    }
  ]
}
```

**Expected Results:**
- Bank balance: +$25.00
- Budget Envelope "Groceries": $579.33 (+$25.00)
- EnvelopeTransaction record type = "refund"

---

### Test Suite 4: Fundamental Equation Validation

#### Test 4.1: Equation Holds After Cash Purchase
**Scenario:** After Test 3.1

**Verification:**
```python
bank_balance = 9874.50
budget_allocated = 674.50
payment_reserved = 0.00
available = bank_balance - budget_allocated - payment_reserved

assert available == 9200.00
assert bank_balance == budget_allocated + payment_reserved + available
```

---

#### Test 4.2: Equation Holds After Credit Purchase
**Scenario:** After Test 3.2

**Verification:**
```python
bank_balance = 10000.00
budget_allocated = 554.33
payment_reserved = 1445.67
available = bank_balance - budget_allocated - payment_reserved

assert available == 8000.00
assert bank_balance == budget_allocated + payment_reserved + available
```

---

#### Test 4.3: Equation Holds After Payment
**Scenario:** After Test 3.3

**Verification:**
```python
bank_balance = 9500.00
budget_allocated = 554.33
payment_reserved = 945.67
available = bank_balance - budget_allocated - payment_reserved

assert available == 8000.00
assert bank_balance == budget_allocated + payment_reserved + available
```

---

### Test Suite 5: Validation

#### Test 5.1: Prevent Over-Allocation
**Objective:** Cannot allocate more than available funds

**Setup:**
- Bank balance: $5,000
- Budget allocated: $2,000
- Payment reserved: $1,500
- Available: $1,500

**Test:**
```python
is_valid, error = validate_allocation(
    bank_account_id="1000",
    allocation_amount=2000.00,
    current_bank_balance=5000.00
)
```

**Expected Results:**
- is_valid = False
- error message includes: "Only $1,500.00 available"

---

#### Test 5.2: Warn on Overspending
**Objective:** Detect when expense exceeds budget

**Setup:**
- Budget Envelope "Dining": $150.00

**Test:**
```python
is_valid, warning = validate_expense(
    budget_envelope_id="1510-Dining",
    expense_amount=200.00,
    allow_overspend=False
)
```

**Expected Results:**
- is_valid = False
- warning message includes: "exceeds budget" and "$50.00"

---

#### Test 5.3: Allow Overspending When Configured
**Objective:** Overspending allowed if flag set

**Test:**
```python
is_valid, warning = validate_expense(
    budget_envelope_id="1510-Dining",
    expense_amount=200.00,
    allow_overspend=True
)
```

**Expected Results:**
- is_valid = True
- warning = None

---

### Test Suite 6: Forecasting

#### Test 6.1: Forecast with RESET Policy
**Objective:** Verify forecast with RESET policy

**Setup:**
- Envelope: Dining ($300/month, RESET)
- Current balance: $150.00
- Current date: 2025-01-15
- Target date: 2025-03-31

**Test:**
```python
forecast = forecast_envelope_balance(
    envelope_id="1510-Dining",
    target_date=date(2025, 3, 31),
    scheduled_expenses=[
        {"date": date(2025, 2, 10), "amount": 75.00},
        {"date": date(2025, 3, 15), "amount": 100.00}
    ]
)
```

**Expected Results:**
- Months until target: 2
- Projected balance: $125.00
  - Calculation: $300 (March allocation) - $175 (expenses) = $125
  - January balance discarded (RESET)

---

#### Test 6.2: Forecast with ACCUMULATE Policy
**Objective:** Verify forecast with ACCUMULATE policy

**Setup:**
- Envelope: Groceries ($800/month, ACCUMULATE)
- Current balance: $345.23
- Current date: 2025-01-15
- Target date: 2025-03-31

**Test:**
```python
forecast = forecast_envelope_balance(
    envelope_id="1500-Groceries",
    target_date=date(2025, 3, 31),
    scheduled_expenses=[
        {"date": date(2025, 2, 15), "amount": 150.00},
        {"date": date(2025, 3, 15), "amount": 175.00}
    ]
)
```

**Expected Results:**
- Projected balance: $1,620.23
  - Calculation: $345.23 (current) + $1,600 (2 × $800 allocations) - $325 (expenses) = $1,620.23

---

#### Test 6.3: Forecast with CAP Policy
**Objective:** Verify forecast respects cap

**Setup:**
- Envelope: Clothing ($200/month, CAP $600)
- Current balance: $500.00
- Target date: 2025-03-31 (2 months)

**Expected Results:**
- Projected balance: $600.00 (capped, not $900)

---

### Test Suite 7: Audit Trail

#### Test 7.1: EnvelopeTransaction Created on Expense
**Objective:** Verify audit record on every envelope change

**After Test 3.1:**
```python
txn = get_envelope_transaction(envelope_id="1500-Groceries", latest=True)
```

**Expected Fields:**
- envelope_id: "1500-Groceries"
- transaction_type: "expense"
- amount: -125.50
- balance_before: 800.00
- balance_after: 674.50
- journal_entry_id: (link to transaction)
- distribution_id: (link to distribution)

---

#### Test 7.2: BudgetAllocation Created on Monthly Allocation
**Objective:** Verify allocation records

**After Test 2.1:**
```python
allocation = get_budget_allocation(envelope_id="1510-Dining", period="2025-02")
```

**Expected Fields:**
- source_account_id: "1000-Cash"
- envelope_id: "1510-Dining"
- amount: 300.00
- period_label: "2025-02"
- is_automatic: True

---

### Test Suite 8: Complex Scenarios

#### Test 8.1: Month-End Rollover All Policies
**Objective:** Test all three rollover policies simultaneously

**Setup:**
- 3 envelopes with different policies and balances
- Run monthly allocation

**Expected:** Each applies its policy correctly

---

#### Test 8.2: Multiple Distributions Same Transaction
**Objective:** Split transaction across multiple budget envelopes

**Transaction:**
```json
{
  "description": "Target - groceries and clothing",
  "distributions": [
    {"account": "1000-Cash", "flow": "from", "amount": 200.00},
    {"account": "6300-Groceries", "flow": "to", "amount": 125.00, "budget_envelope_id": "1500"},
    {"account": "6500-Clothing", "flow": "to", "amount": 75.00, "budget_envelope_id": "1520"}
  ]
}
```

**Expected:**
- Groceries envelope: -$125
- Clothing envelope: -$75
- 2 EnvelopeTransaction records

---

#### Test 8.3: Transfer Between Envelopes
**Future Enhancement:** Manual reallocation between envelopes

---

### Test Suite 9: Edge Cases

#### Test 9.1: Negative Budget Balance (Overspent)
**Scenario:** Spend more than allocated

**Steps:**
1. Budget Envelope "Dining": $50.00
2. Record expense: $75.00
3. Verify balance = -$25.00
4. Verify is_overspent() = True
5. Verify overspent_amount() = $25.00

---

#### Test 9.2: Zero Allocation
**Scenario:** Envelope with $0 monthly allocation

**Expected:** Envelope doesn't receive allocation, balance stays at 0

---

#### Test 9.3: Inactive Envelope
**Scenario:** Envelope marked inactive

**Expected:** Doesn't receive monthly allocation

---

#### Test 9.4: Missing Envelope Reference
**Scenario:** Transaction distribution has budget_envelope_id but envelope doesn't exist

**Expected:** Raise ValueError with clear message

---

## Test Data Generation

### Script: generate_envelope_test_data.py

Create test data file with:
1. Chart of Accounts (27 accounts with envelope links)
2. Budget Envelopes (8 envelopes)
3. Payment Envelopes (3 envelopes)
4. 3 months of transactions (existing dataset)
5. Monthly allocations for each month
6. Expected balances at key dates

**Output Files:**
- `envelope_test_data.json` - Complete test dataset
- `envelope_expected_results.json` - Expected results for each test
- `envelope_audit_trail.json` - Expected audit records

---

## Test Execution Plan

### Phase 1: Unit Tests
- Test individual methods on models
- Test envelope creation, updates, forecasting
- Run: `pytest test_budget_envelope_models.py`

### Phase 2: Service Tests
- Test EnvelopeService methods
- Test transaction posting, validation
- Run: `pytest test_envelope_service.py`

### Phase 3: Integration Tests
- Test complete workflows
- Test with actual database
- Run: `pytest test_envelope_integration.py`

### Phase 4: Scenario Tests
- Test realistic user scenarios
- Test month-end rollover
- Run: `pytest test_envelope_scenarios.py`

---

## Success Criteria

✅ All unit tests pass
✅ All integration tests pass
✅ Fundamental equation holds in every scenario
✅ Audit trail is complete (no missing records)
✅ Forecasts match manual calculations
✅ Validation prevents invalid states
✅ Rollover policies work correctly
✅ Performance acceptable (< 100ms per transaction post)

---

## Known Limitations (Future Enhancements)

1. Manual reallocation between envelopes not yet implemented
2. Envelope balance history/snapshots not stored
3. Multi-currency envelope support not included
4. Envelope sharing (joint budgets) not supported
5. Budget templates/copying not implemented
