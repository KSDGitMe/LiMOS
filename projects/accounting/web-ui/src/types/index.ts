// LiMOS Accounting - TypeScript Type Definitions

export type AccountType = 'asset' | 'liability' | 'equity' | 'revenue' | 'expense';
export type FlowDirection = 'from' | 'to';
export type DebitCredit = 'Dr' | 'Cr';
export type JournalEntryStatus = 'draft' | 'posted' | 'void';
export type EnvelopeType = 'budget' | 'payment';
export type RolloverPolicy = 'reset' | 'accumulate' | 'cap';
export type RecurrenceFrequency = 'daily' | 'weekly' | 'biweekly' | 'monthly' | 'quarterly' | 'semiannually' | 'annually';

export interface Distribution {
  distribution_id?: string;
  account_id: string;
  account_type: AccountType;
  flow_direction: FlowDirection;
  amount: number;
  multiplier: number;
  debit_credit: DebitCredit;
  description?: string;
  memo?: string;
  budget_envelope_id?: string;
  payment_envelope_id?: string;
  status?: string;
  created_at?: string;
  updated_at?: string;
}

export interface JournalEntry {
  journal_entry_id?: string;
  entry_number?: string;
  entry_type?: string;
  entry_date: string;
  posting_date?: string;
  distributions: Distribution[];
  description: string;
  memo?: string;
  notes?: string;
  status: JournalEntryStatus;
  created_by?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ChartOfAccounts {
  account_id: string;
  account_number: string;
  account_name: string;
  account_type: AccountType;
  account_subtype?: string;
  parent_account_id?: string;
  level: number;
  is_active: boolean;
  current_balance: number;
  opening_balance: number;
  opening_balance_date?: string;
  description?: string;
  created_at?: string;
  updated_at?: string;
}

export interface BudgetEnvelope {
  envelope_id: string;
  envelope_number: string;
  envelope_name: string;
  envelope_type: EnvelopeType;
  monthly_allocation: number;
  rollover_policy: RolloverPolicy;
  rollover_limit?: number;
  is_active: boolean;
  current_balance: number;
  last_allocation_date?: string;
  description?: string;
  created_at?: string;
  updated_at?: string;
}

export interface PaymentEnvelope {
  envelope_id: string;
  envelope_number: string;
  envelope_name: string;
  envelope_type: EnvelopeType;
  liability_account_id: string;
  current_balance: number;
  is_active: boolean;
  description?: string;
  created_at?: string;
  updated_at?: string;
}

export interface RecurringJournalEntry {
  recurring_entry_id: string;
  template_name: string;
  description: string;
  entry_type: string;
  distribution_template: Partial<Distribution>[];
  frequency: RecurrenceFrequency;
  interval?: number;
  day_of_month?: number;
  day_of_week?: number;
  month_of_quarter?: number;
  month_of_year?: number;
  start_date: string;
  end_date?: string;
  end_after_occurrences?: number;
  next_occurrence?: string;
  auto_post: boolean;
  auto_create_days_before: number;
  require_approval: boolean;
  is_active: boolean;
  last_generated_date?: string;
  total_generated: number;
  created_at?: string;
  updated_at?: string;
  created_by?: string;
  notes?: string;
  tags: string[];
}

export interface AccountForecast {
  account_id: string;
  account_name: string;
  current_balance: number;
  as_of_date: string;
  target_date: string;
  projected_balance: number;
  balance_change: number;
  transactions_applied: number;
}

export interface EnvelopeForecast {
  envelope_id: string;
  envelope_name: string;
  current_balance: number;
  as_of_date: string;
  target_date: string;
  projected_balance: number;
  balance_change: number;
  months_ahead: number;
  allocations_applied: number;
  scheduled_expenses_applied: number;
}

export interface AccountView {
  account_id: string;
  account_name: string;
  bank_balance: number;
  budget_allocated: number;
  payment_reserved: number;
  available_to_allocate: number;
  as_of_date: string;
  budget_envelopes: BudgetEnvelope[];
  payment_envelopes: PaymentEnvelope[];
  is_balanced: boolean;
}

export interface SystemStats {
  chart_of_accounts: {
    total: number;
    by_type: Record<AccountType, number>;
  };
  journal_entries: {
    total: number;
    posted: number;
    draft: number;
  };
  envelopes: {
    budget: number;
    payment: number;
    total_budget_allocated: number;
    total_payment_reserved: number;
  };
  recurring_templates: {
    total: number;
    active: number;
  };
}

// Form types for creating/editing
export interface CreateTransactionForm {
  description: string;
  amount: number;
  fromAccount: string;
  toAccount: string;
  date: string;
  envelopeId?: string;
}

export interface TransactionFilters {
  start_date?: string;
  end_date?: string;
  status?: JournalEntryStatus;
  account_id?: string;
  limit?: number;
}
