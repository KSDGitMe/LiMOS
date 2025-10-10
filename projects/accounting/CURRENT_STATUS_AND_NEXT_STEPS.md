# LiMOS Accounting Module - Current Status & Next Steps

**Last Updated:** 2025-10-09
**Current Phase:** Web UI Polish & Feature Completion

---

## 🎯 What's Working Right Now

### ✅ Backend (100% Complete)
1. **6 Specialized Agents** - All implemented and tested
2. **REST API** - 60+ endpoints, fully documented
3. **CLI Tool** - `limos.py` with 9 commands
4. **Database** - SQLite with full schema
5. **Event Bus** - Message-driven architecture

### ✅ Web UI (85% Complete)
**Running at:** http://localhost:5173/
**API Server:** http://localhost:8000

**Completed Pages:**
- ✅ **Dashboard** - Account balances, budget envelopes, recent transactions
- ✅ **Transactions** - Full table with filters, void functionality
- ✅ **Envelopes** - Budget cards, progress bars, monthly allocation
- ✅ **Forecast** - Account projections with smart insights
- ✅ **Recurring** - Template list with expand functionality
- ✅ **Settings** - Basic config (API URL, about info)

**Recent Fixes (2025-10-09):**
- ✅ Fixed envelope assignment bug (transactions going to wrong envelope)
- ✅ Fixed grey/empty Recurring page (TypeScript types + API field mismatch)
- ✅ Added rollover policy tooltips (reset/accumulate/cap explanations)
- ✅ Added CLI guidance for envelope/template CRUD

---

## 🚧 What Needs Work

### Priority 1: Web UI Completion (RECOMMEND NEXT)

#### A. Envelope/Recurring CRUD via Web UI
**Current State:** Users must use CLI
**Gap:** No create/edit/delete buttons work in UI
**Effort:** Medium (2-3 hours)

**Tasks:**
1. Add API endpoints for envelope CRUD (backend)
2. Create envelope form dialog (frontend)
3. Add recurring template form dialog (frontend)
4. Wire up edit/delete actions
5. Add validation and error handling

**Files to Create/Modify:**
- Backend: `api/main.py` - Add POST/PUT/DELETE endpoints for envelopes/templates
- Frontend: `src/components/envelopes/CreateEnvelopeDialog.tsx`
- Frontend: `src/components/recurring/CreateTemplateDialog.tsx`
- Frontend: `src/hooks/useEnvelopes.ts` - Add mutation hooks
- Frontend: `src/hooks/useRecurring.ts` - Add mutation hooks

**Business Value:** High - Makes UI fully self-sufficient

---

#### B. Transaction Detail Modal
**Current State:** Can't view full transaction details
**Gap:** No detail view when clicking View icon
**Effort:** Low (1 hour)

**Tasks:**
1. Create `TransactionDetailDialog.tsx` component
2. Show all distributions (not just from/to)
3. Display envelope assignments
4. Show memo, tags, attachments
5. Add edit capability

**Files to Create:**
- `src/components/transactions/TransactionDetailDialog.tsx`

**Business Value:** Medium - Better transaction visibility

---

#### C. Charts & Visualizations
**Current State:** No graphs, Recharts library installed but unused
**Gap:** Users can't see trends visually
**Effort:** Medium (2-4 hours)

**Tasks:**
1. **Dashboard Charts:**
   - Spending by category (pie chart)
   - Balance trend over 30 days (line chart)
   - Budget burn rate (bar chart)

2. **Forecast Charts:**
   - Projected balance line chart
   - Confidence interval shading
   - Critical dates markers

3. **Transactions Charts:**
   - Monthly income/expense comparison
   - Category breakdown over time

**Files to Create/Modify:**
- `src/components/charts/BalanceTrendChart.tsx`
- `src/components/charts/SpendingPieChart.tsx`
- `src/components/charts/ForecastLineChart.tsx`
- `src/pages/Dashboard.tsx` - Add charts section
- `src/pages/Forecast.tsx` - Add chart visualization

**Business Value:** High - Much better user experience

---

### Priority 2: Business Logic Clarification (NEEDS SPEC)

#### D. Envelope Rollover & Over-Spending Behavior
**Current State:** Policies shown but behavior unclear
**Gap:** No spec for how reset/accumulate/cap actually work
**Effort:** Depends on complexity (spec first, then 2-4 hours implementation)

**Questions in NOTES.md:**
1. What happens when envelope goes negative?
2. When/how does "reset" trigger?
3. How does "cap" calculate next allocation?
4. Should UI prevent over-spending?
5. What warnings should show?

**Next Steps:**
1. **You provide specification** (see `web-ui/NOTES.md`)
2. Implement backend logic in `envelope_service.py`
3. Update API endpoints
4. Add UI warnings/validations
5. Write tests

**Business Value:** Critical - Core feature needs definition

---

### Priority 3: Quality & Polish

#### E. Dark Mode
**Current State:** Toggle exists but disabled
**Effort:** Medium (2-3 hours)

**Tasks:**
1. Implement theme switching with MUI
2. Store preference in localStorage
3. Add dark color palette
4. Test all pages in dark mode

**Files to Modify:**
- `src/App.tsx` - Theme provider with dark mode
- `src/hooks/useTheme.ts` - Theme state management

**Business Value:** Low - Nice to have

---

#### F. Advanced Filters
**Current State:** Basic filters only
**Effort:** Low-Medium (1-2 hours)

**Tasks:**
1. Add account type filter to transactions
2. Add tag/category filters
3. Add search by description
4. Add amount range filter
5. Save filter presets

**Business Value:** Medium - Power user feature

---

#### G. Export/Import
**Current State:** No data export
**Effort:** Medium (2-3 hours)

**Tasks:**
1. Export transactions to CSV/Excel
2. Export budget reports to PDF
3. Import transactions from CSV
4. Import recurring templates

**Business Value:** Medium - Important for backups

---

### Priority 4: Voice/Mobile UIs (FUTURE)

#### H. Voice/NLP Interface (Option B)
**Design:** Already completed (`docs/DESIGN_OPTION_B_VOICE_NLP.md`)
**Effort:** High (8-12 hours)

**Would Enable:**
- "Add $50 coffee expense to Entertainment"
- "What's my Groceries budget status?"
- "Show me last week's spending"
- Voice-to-transaction processing
- Natural language queries

**Business Value:** High - Hands-free operation

---

#### I. Mobile App (Option D)
**Design:** Already completed (`docs/DESIGN_OPTION_D_MOBILE_APP.md`)
**Effort:** Very High (20+ hours)

**Would Enable:**
- React Native iOS/Android apps
- Push notifications for budget alerts
- Photo receipt capture
- Offline mode
- Biometric auth

**Business Value:** High - Mobile-first users

---

## 📊 Effort vs Value Matrix

| Task | Effort | Business Value | Recommendation |
|------|--------|----------------|----------------|
| **Envelope/Recurring CRUD** | Medium | ⭐⭐⭐⭐⭐ High | **DO NEXT** |
| **Charts & Visualizations** | Medium | ⭐⭐⭐⭐⭐ High | **DO NEXT** |
| **Transaction Detail Modal** | Low | ⭐⭐⭐ Medium | Quick Win |
| **Rollover Policy Spec** | Spec Only | ⭐⭐⭐⭐⭐ Critical | **NEEDS YOUR INPUT** |
| **Advanced Filters** | Low-Med | ⭐⭐⭐ Medium | Polish |
| **Export/Import** | Medium | ⭐⭐⭐ Medium | Polish |
| **Dark Mode** | Medium | ⭐⭐ Low | Nice to Have |
| **Voice/NLP Interface** | High | ⭐⭐⭐⭐ High | Future Phase |
| **Mobile App** | Very High | ⭐⭐⭐⭐ High | Future Phase |

---

## 🎯 My Recommendations (Prioritized)

### Immediate (Next 1-2 Sessions)

1. **FIRST: Clarify Rollover Policy Behavior**
   - Review `web-ui/NOTES.md`
   - Provide specification
   - I'll implement backend + frontend logic
   - **Why:** Core feature needs definition before we go further

2. **SECOND: Add Charts to Dashboard & Forecast**
   - Spending pie chart
   - Balance trend line chart
   - Forecast projection chart
   - **Why:** Huge UX improvement, Recharts already installed

3. **THIRD: Implement Envelope/Recurring CRUD**
   - Backend API endpoints
   - Frontend form dialogs
   - Full create/edit/delete capability
   - **Why:** Makes Web UI fully self-sufficient

### Short-Term Polish (Next 2-4 Sessions)

4. **Transaction Detail Modal** - Quick win, better UX
5. **Advanced Filters** - Power user features
6. **Export to CSV/Excel** - Data portability
7. **Dark Mode** - UI polish

### Future Phases

8. **Voice/NLP Interface** - Natural language interaction
9. **Mobile App** - Native iOS/Android apps

---

## 🤔 Questions for You

1. **What's your priority?**
   - Finish Web UI to 100% before other interfaces?
   - Or start Voice/Mobile while Web UI is 85% done?

2. **Rollover Policy Behavior:**
   - Can you review `web-ui/NOTES.md` and provide answers?
   - Or should we implement a "standard" behavior and iterate?

3. **Charts - What do you want to see?**
   - Just basics (spending pie, balance line)?
   - Or advanced (category trends, forecast confidence intervals)?

4. **Quick Wins vs Big Features?**
   - Prefer finishing small things (detail modal, filters)?
   - Or big features (CRUD forms, charts)?

---

## 📝 Current Technical Debt

1. **Placeholder Actions** - Edit/View/Pause buttons don't do anything yet
2. **No Error Boundaries** - React errors could crash whole app
3. **No Loading Skeletons** - Just spinners, could be smoother
4. **No Offline Support** - Requires internet connection
5. **No Unit Tests** - Frontend has zero tests
6. **No E2E Tests** - No Playwright/Cypress tests

---

## 🚀 Quick Start (For Next Session)

**If you want to continue Web UI:**
```bash
# Terminal 1 - API Server (already running)
cd /Users/ksd/Projects/LiMOS
python projects/accounting/run_api_server.py

# Terminal 2 - Web UI (already running)
cd /Users/ksd/Projects/LiMOS/projects/accounting/web-ui
npm run dev

# Visit http://localhost:5173/
```

**If you want to work on Voice/NLP:**
```bash
# Review design doc
cat docs/DESIGN_OPTION_B_VOICE_NLP.md

# Install dependencies
pip install openai-whisper openai anthropic
```

**If you want to work on Mobile:**
```bash
# Review design doc
cat docs/DESIGN_OPTION_D_MOBILE_APP.md

# Set up React Native
npx react-native init AccountingMobile
```

---

## 💡 My Top 3 Recommendations

**RECOMMENDATION 1: Complete Web UI to 100% First** (4-6 hours total)
- Add charts (2-3 hrs)
- CRUD dialogs (2-3 hrs)
- Transaction detail modal (1 hr)
- Polish & test (1 hr)
- **Result:** Fully functional Web UI, ready for production

**RECOMMENDATION 2: Then Add Voice Interface** (8-12 hours)
- Natural language → transactions
- Voice queries for data
- Hands-free operation
- **Result:** Two complete UIs (Web + Voice)

**RECOMMENDATION 3: Mobile Last** (20+ hours)
- Native iOS/Android apps
- Push notifications
- Photo capture
- **Result:** Three complete UIs (Web + Voice + Mobile)

---

**What would you like to work on next?**
