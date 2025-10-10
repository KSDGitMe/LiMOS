# Option A: Web UI Design

**Date:** 2025-10-08
**Status:** 📋 Design Phase

---

## Overview

A modern, responsive web application for LiMOS Accounting that provides a visual, intuitive interface for managing transactions, budgets, and financial forecasting. Built as a Single Page Application (SPA) consuming the existing REST API.

---

## Technology Stack

### Frontend Framework: **React** (Recommended)
**Why React:**
- Large ecosystem and component libraries
- Excellent state management options (Redux, Zustand)
- Strong TypeScript support
- Virtual DOM for performance
- Wide adoption and community support

**Alternative:** Vue.js (simpler, gentler learning curve)

### UI Component Library: **Material-UI (MUI)**
**Why MUI:**
- Professional, polished components out-of-the-box
- Excellent form components (critical for financial data entry)
- Built-in theming and dark mode support
- Responsive by default
- Strong accessibility features

**Alternatives:**
- Ant Design (finance-focused components)
- Chakra UI (simpler, more flexible)
- Tailwind CSS + Headless UI (maximum customization)

### State Management: **Zustand** or **React Query**
**Why Zustand:**
- Simple, minimal boilerplate
- Perfect for client state
- TypeScript-friendly

**Why React Query:**
- Excellent for API state management
- Built-in caching, refetching
- Optimistic updates
- Perfect for our REST API

**Recommendation:** Combine both
- Zustand for UI state (modals, selected items, filters)
- React Query for API data (accounts, transactions, envelopes)

### Form Management: **React Hook Form**
**Why React Hook Form:**
- Minimal re-renders (performance)
- Built-in validation
- Easy integration with existing validation libraries (Zod, Yup)
- Perfect for our complex transaction forms

### Data Visualization: **Recharts**
**Why Recharts:**
- Built on React
- Beautiful, customizable charts
- Perfect for budget tracking, spending trends, forecasts

### Build Tool: **Vite**
**Why Vite:**
- Lightning-fast development server
- Instant Hot Module Replacement (HMR)
- Optimized production builds
- Native ES modules

---

## Application Architecture

### Project Structure
```
web-ui/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── transactions/
│   │   │   ├── TransactionForm.tsx
│   │   │   ├── TransactionList.tsx
│   │   │   ├── TransactionDetail.tsx
│   │   │   └── QuickEntry.tsx
│   │   ├── envelopes/
│   │   │   ├── BudgetEnvelopeCard.tsx
│   │   │   ├── PaymentEnvelopeCard.tsx
│   │   │   ├── EnvelopeAllocation.tsx
│   │   │   └── EnvelopeBalance.tsx
│   │   ├── accounts/
│   │   │   ├── AccountCard.tsx
│   │   │   ├── AccountView.tsx
│   │   │   └── AccountSelector.tsx
│   │   ├── forecasting/
│   │   │   ├── ForecastChart.tsx
│   │   │   ├── ForecastSummary.tsx
│   │   │   └── CashFlowProjection.tsx
│   │   ├── recurring/
│   │   │   ├── RecurringTemplateCard.tsx
│   │   │   ├── RecurringTemplateForm.tsx
│   │   │   └── TemplateCalendar.tsx
│   │   └── shared/
│   │       ├── AmountInput.tsx
│   │       ├── DatePicker.tsx
│   │       ├── AccountPicker.tsx
│   │       └── EnvelopePicker.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── Transactions.tsx
│   │   ├── Envelopes.tsx
│   │   ├── Forecasting.tsx
│   │   ├── Recurring.tsx
│   │   └── Reports.tsx
│   ├── hooks/
│   │   ├── useTransactions.ts
│   │   ├── useAccounts.ts
│   │   ├── useEnvelopes.ts
│   │   ├── useForecast.ts
│   │   └── useRecurring.ts
│   ├── api/
│   │   └── client.ts          # API client wrapper
│   ├── stores/
│   │   ├── uiStore.ts          # UI state (Zustand)
│   │   └── authStore.ts        # User session
│   ├── types/
│   │   └── index.ts            # TypeScript types
│   ├── utils/
│   │   ├── formatters.ts       # Currency, date formatting
│   │   └── validators.ts       # Form validation
│   ├── App.tsx
│   └── main.tsx
├── public/
├── package.json
├── vite.config.ts
└── tsconfig.json
```

---

## Key Features & User Flows

### 1. Dashboard (Home Screen)

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│  LiMOS Accounting                    [User] [⚙️]    │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌───────────────┐  ┌───────────────┐              │
│  │ Checking      │  │ Savings       │              │
│  │ $25,482.00   │  │ $50,125.00   │              │
│  │ ↗ +$1,240    │  │ ↔ +$125      │              │
│  └───────────────┘  └───────────────┘              │
│                                                      │
│  📊 Cash Flow (Next 90 Days)                        │
│  ┌────────────────────────────────────────────┐    │
│  │     [Line chart showing projected balance] │    │
│  │                                             │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  💰 Budget Envelopes                                │
│  ┌────────────────────────────────────────────┐    │
│  │ Groceries        ███████░░  $366 / $800    │    │
│  │ Dining Out       ██████░░░  $210 / $300    │    │
│  │ Gas & Auto       █████████  $185 / $250    │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  🔄 Upcoming Recurring                              │
│  • Mortgage Payment         Oct 15  $1,439.00      │
│  • Electric Bill            Oct 20  $185.00        │
│  • Auto Loan                Oct 25  $425.00        │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**Components:**
- `AccountSummaryCards` - Quick balance view
- `CashFlowChart` - Projected balance over time
- `EnvelopeProgressBars` - Budget spending visualization
- `UpcomingRecurring` - Next 30 days of scheduled transactions

---

### 2. Quick Transaction Entry

**Primary Method: Quick Entry Modal**

User clicks **[+ New Transaction]** button anywhere in app → Modal appears:

```
┌───────────────────────────────────────┐
│  New Transaction                  [×] │
├───────────────────────────────────────┤
│                                       │
│  Description                          │
│  ┌─────────────────────────────────┐ │
│  │ Starbucks coffee               │ │
│  └─────────────────────────────────┘ │
│                                       │
│  Amount                               │
│  ┌─────────────────────────────────┐ │
│  │ $ 5.50                         │ │
│  └─────────────────────────────────┘ │
│                                       │
│  From Account                         │
│  ┌─────────────────────────────────┐ │
│  │ Cash - Checking         ▼      │ │
│  └─────────────────────────────────┘ │
│                                       │
│  To Account/Envelope                  │
│  ┌─────────────────────────────────┐ │
│  │ Dining Out (Budget)     ▼      │ │
│  └─────────────────────────────────┘ │
│                                       │
│  Date                                 │
│  ┌─────────────────────────────────┐ │
│  │ Today (2025-10-08)      📅     │ │
│  └─────────────────────────────────┘ │
│                                       │
│  ┌──────────┐  ┌─────────────────┐  │
│  │  Cancel  │  │  Save & Post ✓  │  │
│  └──────────┘  └─────────────────┘  │
└───────────────────────────────────────┘
```

**Features:**
- Auto-focus on description field
- Smart account/envelope picker with search
- Keyboard shortcuts (Cmd/Ctrl + N for new, Enter to save)
- Recent transactions suggestions
- Split transaction mode for complex entries

**Smart Suggestions:**
Based on description typing, suggest:
- Previous similar transactions
- Common merchant → envelope mappings
- Typical amounts

Example: User types "Star..." → Suggests:
- "Starbucks coffee → Dining Out → $5.50"

---

### 3. Transaction List/Ledger

```
┌──────────────────────────────────────────────────────────┐
│  Transactions                              [+ New] [⚙️]  │
├──────────────────────────────────────────────────────────┤
│  Filters: [All] [This Month] [Posted] [Draft]           │
│  Search: [                              ] 🔍             │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Oct 8, 2025                                             │
│  ┌─────────────────────────────────────────────────┐    │
│  │ ☕ Starbucks coffee                             │    │
│  │ Cash - Checking → Dining Out        -$5.50     │    │
│  │ Posted • 2:45 PM                               │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ 🛒 Whole Foods                                  │    │
│  │ Cash - Checking → Groceries        -$125.50    │    │
│  │ Posted • 10:23 AM                              │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  Oct 7, 2025                                             │
│  ┌─────────────────────────────────────────────────┐    │
│  │ ⛽ Shell Gas Station                            │    │
│  │ Cash - Checking → Gas & Auto        -$45.00    │    │
│  │ Posted • Yesterday                             │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

**Features:**
- Infinite scroll / pagination
- Click transaction → Detail modal
- Swipe actions (mobile): Edit, Void, Duplicate
- Batch operations: Select multiple → Post, Void, Export
- Export to CSV/Excel

---

### 4. Envelope Management Screen

```
┌──────────────────────────────────────────────────────────┐
│  Budget Envelopes                         [Allocate ↻]  │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Groceries                         Accumulate   │    │
│  │  ─────────────────────────────────────────────  │    │
│  │  Monthly: $800                                  │    │
│  │  Balance: $366.90                               │    │
│  │  ████████████░░░░░░░░ 46% used                 │    │
│  │                                                  │    │
│  │  📊 This Month: -$433.10 spent                 │    │
│  │  📈 Trend: ↗ 5% higher than last month        │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Dining Out                        Reset        │    │
│  │  ─────────────────────────────────────────────  │    │
│  │  Monthly: $300                                  │    │
│  │  Balance: $210.50                               │    │
│  │  ██████████████░░░░░░ 30% used                 │    │
│  │                                                  │    │
│  │  📊 This Month: -$89.50 spent                  │    │
│  │  ⚠️  Only 10 days left this month              │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

**Envelope Card Interactions:**
- Click card → Expand to show transaction history
- Click "Allocate" → Manually adjust envelope balance
- Visual warnings when over budget (red)
- Celebration when under budget at month-end (green, confetti)

**Monthly Allocation Flow:**
```
Click [Allocate ↻] →
┌────────────────────────────────────┐
│  Apply Monthly Allocations         │
├────────────────────────────────────┤
│  Period: [October 2025    ▼]       │
│  Source: [Cash - Checking  ▼]      │
│                                    │
│  Will allocate:                    │
│  • Groceries      +$800.00         │
│  • Dining Out     +$300.00         │
│  • Gas & Auto     +$250.00         │
│  • Entertainment  +$150.00         │
│  • Clothing       +$200.00         │
│  • Home Maint.    +$500.00         │
│  • Gifts          +$100.00         │
│  • Personal Care  +$100.00         │
│  ───────────────────────────       │
│  Total: -$2,400.00 from checking   │
│                                    │
│  ┌──────────┐  ┌───────────────┐  │
│  │  Cancel  │  │  Allocate ✓   │  │
│  └──────────┘  └───────────────┘  │
└────────────────────────────────────┘
```

---

### 5. Forecasting Dashboard

```
┌──────────────────────────────────────────────────────────┐
│  Financial Forecast                      [Settings ⚙️]   │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Forecast Date: [Dec 31, 2025 ▼]   📅 3 months out      │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │  📊 Projected Account Balances                   │    │
│  │                                                   │    │
│  │  Cash - Checking                                 │    │
│  │  Current:   $25,482 → Projected:   $49,316      │    │
│  │  Change:    +$23,834 (+93%)                      │    │
│  │  ─────────────────────────────────────────────   │    │
│  │  [Line chart: Today → Dec 31]                   │    │
│  │  Shows: Income spikes (paychecks)               │    │
│  │         Expense dips (bills)                     │    │
│  │                                                   │    │
│  │  Transactions Applied: 87                        │    │
│  │  • 13 salary deposits     +$45,500              │    │
│  │  • 6 mortgage payments    -$8,634               │    │
│  │  • 74 other recurring     -$13,032              │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  💡 Insights                                             │
│  ┌─────────────────────────────────────────────────┐    │
│  │  ✓ You'll have $49,316 on Dec 31               │    │
│  │  ⚠️  Large mortgage payment on Nov 1 ($1,439)  │    │
│  │  ✓ Budget surplus: $23,834 above current       │    │
│  │  💰 Opportunity: Consider $15,000 investment   │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

**Interactive Chart Features:**
- Hover over chart → See exact balance on that date
- Click spike/dip → See which transaction caused it
- Toggle income/expense overlays
- Zoom/pan timeline
- "What if" scenarios: Add hypothetical large purchase

---

### 6. Recurring Transactions Manager

```
┌──────────────────────────────────────────────────────────┐
│  Recurring Transactions                   [+ New Template]│
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Calendar View  |  List View                             │
│                                                           │
│  [Calendar showing next 3 months with dots on dates]     │
│                                                           │
│  Oct 15 • Mortgage Payment            $1,439.00          │
│  Oct 20 • Electric Bill               $185.00            │
│  Oct 25 • Auto Loan                   $425.00            │
│  Nov 1  • Mortgage Payment            $1,439.00          │
│  Nov 3  • Salary (Biweekly)          $3,500.00           │
│                                                           │
│  Templates (11)                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  💰 Salary - Biweekly Paycheck                  │    │
│  │  Every 2 weeks • Fridays • $3,500               │    │
│  │  Next: Nov 3, 2025                              │    │
│  │  [Edit] [Pause] [View History]                  │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │  🏠 Mortgage Payment                             │    │
│  │  Monthly • 1st of month • $1,439                │    │
│  │  Split: $766 principal + $673 interest          │    │
│  │  Next: Nov 1, 2025                              │    │
│  │  [Edit] [Pause] [View History]                  │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## Visual Design Principles

### Color Palette

**Light Mode:**
- Primary: Blue (#1976D2) - Trust, stability (financial apps)
- Success: Green (#2E7D32) - Income, positive balance
- Warning: Orange (#ED6C02) - Over budget warnings
- Error: Red (#D32F2F) - Negative, void transactions
- Neutral: Gray scale (#212121 → #FAFAFA)

**Dark Mode:**
- Background: #121212
- Surface: #1E1E1E
- Primary: Light Blue (#64B5F6)
- Success: Light Green (#81C784)

### Typography

- **Headlines:** Inter or Roboto (clean, modern)
- **Body:** System fonts (performance)
- **Numbers:** Tabular figures (alignment)
- **Currency:** Always 2 decimal places, $ prefix

### Spacing & Layout

- 8px grid system
- Cards with subtle shadows
- Generous white space
- Mobile-first responsive breakpoints:
  - Mobile: 0-599px
  - Tablet: 600-959px
  - Desktop: 960px+

---

## User Experience Enhancements

### 1. Keyboard Shortcuts
- `Cmd/Ctrl + N` - New transaction
- `Cmd/Ctrl + F` - Search transactions
- `Cmd/Ctrl + D` - Dashboard
- `Cmd/Ctrl + B` - Budget envelopes
- `Cmd/Ctrl + R` - Recurring templates
- `Esc` - Close modals

### 2. Accessibility
- ARIA labels on all interactive elements
- Keyboard navigation throughout
- High contrast mode support
- Screen reader optimized
- Focus indicators

### 3. Progressive Enhancement
- Works without JavaScript (server-side render initial state)
- Graceful degradation for older browsers
- Offline support with Service Workers (cache recent data)

### 4. Animations & Feedback
- Smooth transitions between views
- Loading skeletons (not spinners)
- Success toast notifications
- Error inline validation
- Optimistic UI updates (instant feedback)

---

## Mobile Responsiveness

### Mobile-Specific Features

**Bottom Navigation Bar:**
```
┌────────────────────────────────┐
│                                 │
│  [Transaction content]          │
│                                 │
│                                 │
└─────────────────────────────────┘
┌─────────────────────────────────┐
│  🏠    💰    📊    🔄    ⚙️     │
│ Home  Budget Forecast Rec Settings│
└─────────────────────────────────┘
```

**Swipe Gestures:**
- Swipe left on transaction → Void
- Swipe right on transaction → Edit
- Pull to refresh

**Quick Entry FAB (Floating Action Button):**
- Always visible `[+]` button in bottom-right
- Tap → Quick transaction modal

---

## API Integration Strategy

### API Client (`api/client.ts`)

```typescript
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor (add auth token)
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
      // Redirect to login
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### React Query Hooks

**Example: `useTransactions` hook**

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/client';

export function useTransactions(filters?: TransactionFilters) {
  return useQuery({
    queryKey: ['transactions', filters],
    queryFn: async () => {
      const { data } = await apiClient.get('/journal-entries', { params: filters });
      return data;
    },
  });
}

export function useCreateTransaction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (transaction: CreateTransactionInput) => {
      const { data } = await apiClient.post('/journal-entries', transaction);
      return data;
    },
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      queryClient.invalidateQueries({ queryKey: ['envelopes'] });
    },
  });
}
```

**Optimistic Updates:**
When user posts transaction, immediately update UI before API responds:

```typescript
onMutate: async (newTransaction) => {
  // Cancel outgoing refetches
  await queryClient.cancelQueries({ queryKey: ['transactions'] });

  // Snapshot previous value
  const previousTransactions = queryClient.getQueryData(['transactions']);

  // Optimistically update
  queryClient.setQueryData(['transactions'], (old) => [...old, newTransaction]);

  // Return rollback function
  return { previousTransactions };
},
onError: (err, newTransaction, context) => {
  // Rollback on error
  queryClient.setQueryData(['transactions'], context.previousTransactions);
},
```

---

## Performance Optimizations

### 1. Code Splitting
- Route-based splitting (Dashboard, Transactions, etc. loaded on-demand)
- Component-based splitting (Charts loaded only when needed)

### 2. Lazy Loading
- Images lazy loaded
- Charts rendered only when visible
- Infinite scroll for transaction lists

### 3. Memoization
- `React.memo` for expensive components
- `useMemo` for calculated values (totals, projections)
- `useCallback` for stable function references

### 4. Virtualization
- Use `react-window` for long transaction lists (render only visible rows)

---

## Security Considerations

### Authentication
- JWT tokens stored in memory (not localStorage for XSS protection)
- Refresh token in httpOnly cookie
- Auto-logout after inactivity

### Data Validation
- Client-side validation (immediate feedback)
- Trust API validation (server is source of truth)
- Sanitize all user input

### HTTPS
- Force HTTPS in production
- Secure cookie flags

---

## Development Plan

### Phase 1: Foundation (Week 1)
- [ ] Set up Vite + React + TypeScript project
- [ ] Install dependencies (MUI, React Query, etc.)
- [ ] Create API client
- [ ] Set up routing (React Router)
- [ ] Basic layout shell (AppBar, Drawer, Content)

### Phase 2: Core Features (Week 2-3)
- [ ] Dashboard with account cards
- [ ] Transaction list/ledger
- [ ] Quick transaction entry modal
- [ ] Account management

### Phase 3: Budget Features (Week 4)
- [ ] Envelope cards and progress bars
- [ ] Monthly allocation flow
- [ ] Envelope transaction history

### Phase 4: Advanced Features (Week 5)
- [ ] Forecasting dashboard with charts
- [ ] Recurring template manager
- [ ] Calendar view

### Phase 5: Polish (Week 6)
- [ ] Dark mode
- [ ] Keyboard shortcuts
- [ ] Mobile optimizations
- [ ] Loading states
- [ ] Error boundaries
- [ ] Testing

---

## Example: Quick Entry Form Component

```typescript
import { useForm } from 'react-hook-form';
import { Dialog, TextField, Button, Autocomplete } from '@mui/material';
import { useCreateTransaction } from '../hooks/useTransactions';
import { useAccounts } from '../hooks/useAccounts';

interface QuickEntryFormData {
  description: string;
  amount: number;
  fromAccount: string;
  toAccountOrEnvelope: string;
  date: string;
}

export function QuickTransactionEntry({ open, onClose }) {
  const { register, handleSubmit, formState: { errors } } = useForm<QuickEntryFormData>();
  const createTransaction = useCreateTransaction();
  const { data: accounts } = useAccounts();

  const onSubmit = async (data: QuickEntryFormData) => {
    const transaction = {
      entry_date: data.date,
      description: data.description,
      distributions: [
        {
          account_id: data.fromAccount,
          flow_direction: 'from',
          amount: data.amount,
          // ... other fields
        },
        {
          account_id: data.toAccountOrEnvelope,
          flow_direction: 'to',
          amount: data.amount,
          // ... other fields
        },
      ],
      status: 'posted',
    };

    await createTransaction.mutateAsync(transaction);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <form onSubmit={handleSubmit(onSubmit)}>
        <DialogTitle>New Transaction</DialogTitle>
        <DialogContent>
          <TextField
            label="Description"
            fullWidth
            margin="normal"
            {...register('description', { required: 'Description is required' })}
            error={!!errors.description}
            helperText={errors.description?.message}
            autoFocus
          />

          <TextField
            label="Amount"
            type="number"
            fullWidth
            margin="normal"
            {...register('amount', { required: 'Amount is required', min: 0.01 })}
            error={!!errors.amount}
            helperText={errors.amount?.message}
            InputProps={{ startAdornment: '$' }}
          />

          <Autocomplete
            options={accounts || []}
            getOptionLabel={(option) => option.account_name}
            renderInput={(params) => (
              <TextField {...params} label="From Account" margin="normal" />
            )}
          />

          {/* ... more fields ... */}
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained">Save & Post</Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
```

---

## Summary

### Pros of Web UI
✅ **Universal Access** - Works on any device with a browser
✅ **No Installation** - Just visit the URL
✅ **Easy Updates** - Deploy once, all users get new version
✅ **Rich Visualizations** - Charts, graphs, interactive elements
✅ **Responsive** - Adapts to desktop, tablet, mobile
✅ **Familiar UX** - Users comfortable with web apps

### Cons
❌ **Requires Internet** - Unless implementing offline support
❌ **Browser Compatibility** - Need to test across browsers
❌ **Performance** - Can be slower than native apps

### Best For
- Primary interface for most users
- Desktop users
- Users who want visual dashboards
- Multi-device access
- Collaborative scenarios (future: multi-user)

---

**Ready to implement upon approval.**
