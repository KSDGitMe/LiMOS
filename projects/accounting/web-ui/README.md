# LiMOS Accounting - Web UI

Modern React-based web interface for LiMOS Accounting system with complete transaction management, budget envelopes, forecasting, and recurring templates.

## 🚀 Quick Start

```bash
# Start API server (separate terminal)
cd /Users/ksd/Projects/LiMOS/projects/accounting
python run_api_server.py

# Start web UI
cd web-ui
npm install  # First time only
npm run dev
```

Visit **http://localhost:5173/**

## ✨ Features

### Core Functionality
- ✅ **Dashboard** - Account balances with trend indicators, budget envelope progress, recent transactions
- ✅ **Quick Entry Dialog** - Floating `+` button for fast transaction entry with auto debit/credit calculation
- ✅ **Transactions Page** - Full transaction table with filters (date range, status, limit), void/edit actions
- ✅ **Envelopes Page** - Budget envelope cards with progress bars, monthly allocation dialog, payment envelopes
- ✅ **Forecast Page** - Account balance forecasting with smart insights and trend analysis
- ✅ **Recurring Templates** - Template management with expand dialog to generate transactions
- ✅ **Settings Page** - API configuration, appearance settings, application info

### Technical Features
- ✅ **Real-time Data** - React Query with automatic caching and invalidation
- ✅ **Material Design** - Professional UI with MUI components
- ✅ **Responsive** - Works on desktop, tablet, and mobile
- ✅ **Type-Safe** - Full TypeScript support matching backend Pydantic models
- ✅ **Form Validation** - React Hook Form with validation rules
- ✅ **Error Handling** - Graceful error states and loading indicators

## 🛠️ Tech Stack

- **React 18** - UI library with hooks
- **TypeScript** - Type-safe development
- **Vite** - Lightning-fast build tool and dev server
- **Material-UI (MUI)** - Material Design component library
- **React Query (@tanstack/react-query)** - Server state management
- **React Router** - Client-side routing
- **React Hook Form** - Form state and validation
- **Axios** - HTTP client for API calls
- **date-fns** - Date manipulation utilities
- **Recharts** - Charting library (ready for future charts)

## 📁 Project Structure

```
src/
├── api/
│   └── client.ts              # Axios client + all API endpoints
├── components/
│   ├── layout/
│   │   └── Layout.tsx         # Main app shell with drawer navigation
│   └── transactions/
│       └── QuickEntryDialog.tsx  # Fast transaction entry dialog
├── hooks/
│   ├── useAccounts.ts         # Account queries
│   ├── useEnvelopes.ts        # Budget/payment envelope queries & mutations
│   ├── useForecast.ts         # Account/envelope forecasting
│   ├── useRecurring.ts        # Recurring template queries & expand
│   └── useTransactions.ts     # Transaction CRUD operations
├── pages/
│   ├── Dashboard.tsx          # Financial overview dashboard
│   ├── Transactions.tsx       # Transaction list with filters
│   ├── Envelopes.tsx          # Budget envelope management
│   ├── Forecast.tsx           # Account balance forecasting
│   ├── Recurring.tsx          # Recurring template management
│   └── Settings.tsx           # Application settings
├── types/
│   └── index.ts               # TypeScript type definitions
└── App.tsx                    # Root component with providers & routing
```

## 🔧 Configuration

Create `.env` file in the `web-ui/` directory:
```env
VITE_API_URL=http://localhost:8000/api
```

## 📱 Pages Overview

### Dashboard
- Account balance cards with trend indicators (up/down arrows)
- Budget envelope progress bars with color coding (green < 70%, yellow 70-90%, red > 90%)
- Recent transactions list (last 5)
- Quick access via floating action button (FAB)

### Transactions
- Filterable table: date range, status (posted/draft/void), result limit
- Actions: View details, Edit, Void (with confirmation)
- Status chips with color coding
- Clear filters button
- Shows FROM → TO account flow

### Envelopes
- Budget envelope cards showing:
  - Monthly allocation vs current balance
  - Progress bar with % used
  - Spent/remaining amounts
  - Rollover policy chips
  - Warnings when > 90% used or over budget
- Payment envelope cards with reserved amounts
- "Apply Monthly Allocations" dialog:
  - Month picker
  - Source account selector
  - Allocates all budget envelopes for selected month

### Forecast
- Account selector (asset accounts)
- Forecast period selector (1/3/6/12 months)
- Three key metrics:
  - Current balance (with as-of date)
  - Projected balance (with target date)
  - Expected change (with trend icon)
- Smart insights:
  - Success: balance increasing > $1000
  - Warning: balance decreasing > $1000
  - Error: projected balance < $1000
  - Info: strong position > $50k or no recurring transactions

### Recurring Templates
- Summary cards: total, active, inactive templates
- Template table showing:
  - Frequency (biweekly, monthly, quarterly, etc.)
  - Start date
  - Next occurrence (estimated)
  - Amount and account flow
  - Active/inactive status
- Actions: Pause/Resume, Edit
- "Expand Templates" dialog:
  - Date range selection
  - Auto-post checkbox
  - Generates transactions from all active templates

### Settings
- API Configuration: Base URL setting
- Appearance: Dark mode toggle (placeholder for future)
- About: Application name, version, API status

## 🎯 Future Enhancements

1. **Dark Mode** - Complete dark theme implementation
2. **Charts & Visualizations** - Balance trends, spending categories (Recharts ready)
3. **Advanced Filters** - Account type, tags, search
4. **Transaction Detail Modal** - Full distribution view
5. **Envelope CRUD** - Create/edit/delete envelopes via UI
6. **Recurring Template CRUD** - Create/edit templates via UI
7. **Export/Import** - CSV/Excel export, data import
8. **Multi-currency** - Currency conversion support
9. **Notifications** - Budget alerts, recurring reminders
10. **Keyboard Shortcuts** - Power user navigation

## 🐛 Known Limitations

- Dark mode toggle is placeholder (not yet functional)
- Edit/View actions on transactions are placeholders
- Pause/Resume actions on recurring templates are placeholders
- Settings don't persist to localStorage yet
- No charts/graphs yet (Recharts installed but unused)

## 📝 Development Notes

### API Integration
All API calls go through `src/api/client.ts` which provides:
- Axios instance with base URL configuration
- Request interceptor for auth tokens (future)
- Response interceptor for error handling
- Type-safe API functions organized by domain

### React Query Patterns
- Queries use `['domain', ...filters]` key structure
- Mutations invalidate related queries on success
- All queries return typed data matching Pydantic models
- `enabled` flag prevents queries with missing required params

### Component Patterns
- React Hook Form for all forms with validation
- Material-UI Grid for responsive layouts
- Controlled components for all form inputs
- Loading states and error boundaries
- Optimistic updates for better UX
