// LiMOS Accounting - API Client

import axios from 'axios';
import type {
  JournalEntry,
  ChartOfAccounts,
  BudgetEnvelope,
  PaymentEnvelope,
  RecurringJournalEntry,
  AccountForecast,
  EnvelopeForecast,
  AccountView,
  SystemStats,
  TransactionFilters,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor (add auth token if needed)
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor (handle errors)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ============================================================================
// JOURNAL ENTRIES
// ============================================================================

export const journalEntriesApi = {
  getAll: (filters?: TransactionFilters) =>
    apiClient.get<JournalEntry[]>('/journal-entries', { params: filters }),

  getById: (id: string) =>
    apiClient.get<JournalEntry>(`/journal-entries/${id}`),

  create: (entry: Omit<JournalEntry, 'journal_entry_id'>) =>
    apiClient.post<JournalEntry>('/journal-entries', entry),

  update: (id: string, entry: Partial<JournalEntry>) =>
    apiClient.put<JournalEntry>(`/journal-entries/${id}`, entry),

  delete: (id: string) =>
    apiClient.delete(`/journal-entries/${id}`),

  post: (id: string) =>
    apiClient.post(`/journal-entries/${id}/post`),
};

// ============================================================================
// CHART OF ACCOUNTS
// ============================================================================

export const accountsApi = {
  getAll: (params?: { account_type?: string; is_active?: boolean }) =>
    apiClient.get<ChartOfAccounts[]>('/accounts', { params }),

  getById: (id: string) =>
    apiClient.get<ChartOfAccounts>(`/accounts/${id}`),

  getView: (id: string, asOfDate?: string) =>
    apiClient.get<AccountView>(`/accounts/${id}/view`, {
      params: { as_of_date: asOfDate },
    }),

  create: (account: Omit<ChartOfAccounts, 'account_id'>) =>
    apiClient.post<ChartOfAccounts>('/accounts', account),

  update: (id: string, account: ChartOfAccounts) =>
    apiClient.put<ChartOfAccounts>(`/accounts/${id}`, account),
};

// ============================================================================
// ENVELOPES
// ============================================================================

export const envelopesApi = {
  getBudget: (activeOnly?: boolean) =>
    apiClient.get<BudgetEnvelope[]>('/envelopes/budget', {
      params: { active_only: activeOnly },
    }),

  getPayment: (activeOnly?: boolean) =>
    apiClient.get<PaymentEnvelope[]>('/envelopes/payment', {
      params: { active_only: activeOnly },
    }),

  createBudget: (envelope: Omit<BudgetEnvelope, 'envelope_id'>) =>
    apiClient.post<BudgetEnvelope>('/envelopes/budget', envelope),

  updateBudget: (id: string, envelope: BudgetEnvelope) =>
    apiClient.put<BudgetEnvelope>(`/envelopes/budget/${id}`, envelope),

  deleteBudget: (id: string) =>
    apiClient.delete(`/envelopes/budget/${id}`),

  createPayment: (envelope: Omit<PaymentEnvelope, 'envelope_id'>) =>
    apiClient.post<PaymentEnvelope>('/envelopes/payment', envelope),

  updatePayment: (id: string, envelope: PaymentEnvelope) =>
    apiClient.put<PaymentEnvelope>(`/envelopes/payment/${id}`, envelope),

  deletePayment: (id: string) =>
    apiClient.delete(`/envelopes/payment/${id}`),

  allocate: (sourceAccountId: string, allocationDate: string, periodLabel: string) =>
    apiClient.post('/envelopes/allocate', null, {
      params: {
        source_account_id: sourceAccountId,
        allocation_date: allocationDate,
        period_label: periodLabel,
      },
    }),
};

// ============================================================================
// RECURRING TEMPLATES
// ============================================================================

export const recurringApi = {
  getAll: (activeOnly?: boolean) =>
    apiClient.get<RecurringJournalEntry[]>('/recurring-templates', {
      params: { active_only: activeOnly },
    }),

  getById: (id: string) =>
    apiClient.get<RecurringJournalEntry>(`/recurring-templates/${id}`),

  create: (template: Omit<RecurringJournalEntry, 'recurring_entry_id'>) =>
    apiClient.post<RecurringJournalEntry>('/recurring-templates', template),

  update: (id: string, template: RecurringJournalEntry) =>
    apiClient.put<RecurringJournalEntry>(`/recurring-templates/${id}`, template),

  delete: (id: string) =>
    apiClient.delete(`/recurring-templates/${id}`),

  toggleActive: (id: string) =>
    apiClient.patch<RecurringJournalEntry>(`/recurring-templates/${id}/toggle-active`),

  expand: (startDate: string, endDate: string, autoPost: boolean = false) =>
    apiClient.post<JournalEntry[]>('/recurring-templates/expand', null, {
      params: {
        start_date: startDate,
        end_date: endDate,
        auto_post: autoPost,
      },
    }),
};

// ============================================================================
// FORECASTING
// ============================================================================

export const forecastApi = {
  account: (accountId: string, targetDate: string) =>
    apiClient.get<AccountForecast>(`/forecast/account/${accountId}`, {
      params: { target_date: targetDate },
    }),

  envelope: (envelopeId: string, targetDate: string) =>
    apiClient.get<EnvelopeForecast>(`/forecast/envelope/${envelopeId}`, {
      params: { target_date: targetDate },
    }),
};

// ============================================================================
// STATISTICS
// ============================================================================

export const statsApi = {
  summary: () =>
    apiClient.get<SystemStats>('/stats/summary'),
};

export default apiClient;
