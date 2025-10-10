# Option D: Mobile App Design

**Date:** 2025-10-08
**Status:** 📋 Design Phase

---

## Overview

A native-quality mobile application for iOS and Android that provides the full LiMOS Accounting experience optimized for mobile devices. Includes features like receipt scanning, GPS-based merchant detection, push notifications for budget alerts, and offline capability.

---

## Why Mobile App?

### Mobile-First Use Cases

1. **Point-of-Purchase Entry**
   - User buys coffee → Opens app → Logs transaction in 5 seconds
   - Can't wait until home computer

2. **Receipt Scanning**
   - Take photo of receipt → AI extracts line items
   - Automatic categorization
   - Store digital receipt

3. **Location-Based**
   - GPS detects "You're at Whole Foods"
   - App suggests: "Log grocery purchase?"
   - Pre-fills merchant, category

4. **Push Notifications**
   - "You've spent $280 of $300 dining budget (93%)"
   - "Mortgage payment due tomorrow"
   - "Your checking balance will dip below $1000 on Friday"

5. **Widgets**
   - Home screen widget showing budget status
   - Quick entry button
   - Today's spending summary

6. **Always Available**
   - Phone always in pocket
   - Fastest transaction entry method
   - Works offline, syncs later

---

## Technology Stack

### Cross-Platform: React Native (Recommended)

**Why React Native:**
✅ Single codebase for iOS + Android
✅ JavaScript/TypeScript (same as Web UI)
✅ 90% code sharing with web
✅ Native performance
✅ Large ecosystem
✅ Expo for rapid development
✅ Can share business logic with Web UI

**Alternatives:**
- **Flutter** (Dart language, beautiful UI, slightly better performance)
- **Native** (Swift for iOS, Kotlin for Android - best performance, double effort)

### Key Libraries

```json
{
  "dependencies": {
    "react-native": "0.73.0",
    "expo": "~50.0.0",
    "react-navigation": "6.x",
    "@tanstack/react-query": "5.x",
    "react-native-paper": "5.x",
    "react-native-vision-camera": "3.x",
    "react-native-ocr": "1.x",
    "expo-location": "~16.x",
    "expo-notifications": "~0.27.x",
    "zustand": "4.x",
    "react-hook-form": "7.x",
    "date-fns": "3.x",
    "@react-native-async-storage/async-storage": "1.x",
    "react-native-reanimated": "3.x",
    "react-native-gesture-handler": "~2.x"
  }
}
```

**Core Capabilities:**
- **Vision Camera** - High-quality camera for receipt scanning
- **OCR** - Text extraction from receipts
- **Location** - GPS for merchant detection
- **Notifications** - Push alerts for budgets, bills
- **Async Storage** - Offline data persistence
- **Reanimated** - Smooth 60fps animations
- **Paper** - Material Design components

---

## Application Architecture

### Project Structure

```
mobile-app/
├── src/
│   ├── navigation/
│   │   ├── AppNavigator.tsx
│   │   ├── TabNavigator.tsx
│   │   └── StackNavigator.tsx
│   ├── screens/
│   │   ├── home/
│   │   │   ├── DashboardScreen.tsx
│   │   │   └── QuickEntryModal.tsx
│   │   ├── transactions/
│   │   │   ├── TransactionsScreen.tsx
│   │   │   ├── TransactionDetailScreen.tsx
│   │   │   └── AddTransactionScreen.tsx
│   │   ├── envelopes/
│   │   │   ├── EnvelopesScreen.tsx
│   │   │   └── EnvelopeDetailScreen.tsx
│   │   ├── forecast/
│   │   │   └── ForecastScreen.tsx
│   │   ├── camera/
│   │   │   ├── ReceiptScannerScreen.tsx
│   │   │   └── ReceiptReviewScreen.tsx
│   │   └── settings/
│   │       └── SettingsScreen.tsx
│   ├── components/
│   │   ├── transactions/
│   │   │   ├── TransactionCard.tsx
│   │   │   ├── QuickEntryForm.tsx
│   │   │   └── TransactionList.tsx
│   │   ├── envelopes/
│   │   │   ├── EnvelopeCard.tsx
│   │   │   └── BudgetProgressBar.tsx
│   │   ├── camera/
│   │   │   ├── ReceiptCamera.tsx
│   │   │   └── OCRPreview.tsx
│   │   └── shared/
│   │       ├── AmountInput.tsx
│   │       ├── AccountPicker.tsx
│   │       └── DatePicker.tsx
│   ├── hooks/
│   │   ├── useTransactions.ts
│   │   ├── useEnvelopes.ts
│   │   ├── useCamera.ts
│   │   ├── useLocation.ts
│   │   └── useOfflineSync.ts
│   ├── services/
│   │   ├── api.ts
│   │   ├── ocr.ts
│   │   ├── location.ts
│   │   ├── notifications.ts
│   │   └── offline.ts
│   ├── stores/
│   │   ├── transactionStore.ts
│   │   ├── offlineStore.ts
│   │   └── uiStore.ts
│   ├── utils/
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   └── merchantMapping.ts
│   ├── types/
│   │   └── index.ts
│   └── App.tsx
├── app.json (Expo config)
├── package.json
└── tsconfig.json
```

---

## Screen Designs

### 1. Home Dashboard

```
┌─────────────────────────────────────┐
│  ☰  LiMOS               🔔  👤      │ ← Header
├─────────────────────────────────────┤
│                                      │
│  💰 Accounts                         │
│  ┌────────────┐  ┌────────────┐    │
│  │ Checking   │  │ Savings    │    │
│  │ $25,482    │  │ $50,125    │    │
│  │ ↗ +5.1%    │  │ ↔ +0.2%    │    │
│  └────────────┘  └────────────┘    │
│                                      │
│  📊 This Month                       │
│  Income:        $7,000               │
│  Expenses:      $4,230               │
│  Remaining:     $2,770               │
│                                      │
│  🎯 Budget Status                    │
│  ┌──────────────────────────────┐  │
│  │ Groceries   ███████░  73%    │  │
│  │ Dining      ██████░░  70%    │  │
│  │ Gas         █████████ 90% ⚠️  │  │
│  └──────────────────────────────┘  │
│                                      │
│  🔄 Upcoming                         │
│  • Oct 15  Mortgage      $1,439     │
│  • Oct 20  Electric      $185       │
│                                      │
│       [+] Quick Entry                │ ← FAB
└─────────────────────────────────────┘
│  🏠  💰  📊  🔄  ⚙️                │ ← Tab Bar
│ Home Budget Trans Rec Settings     │
└─────────────────────────────────────┘
```

**Features:**
- Pull-to-refresh
- Swipe accounts left/right to see more
- Tap account → AccountDetailScreen
- Tap budget bar → EnvelopeDetailScreen
- Tap upcoming → Recurring templates

---

### 2. Quick Entry (Floating Action Button)

Tap `[+]` FAB → Modal slides up from bottom:

```
┌─────────────────────────────────────┐
│  New Transaction            [Done]  │
├─────────────────────────────────────┤
│                                      │
│  [🎤 Voice]  [📷 Receipt]  [⌨️ Type] │ ← Mode tabs
│                                      │
│  Amount                              │
│  ┌──────────────────────────────┐  │
│  │  $  125.50                   │  │ ← Large, easy tap
│  └──────────────────────────────┘  │
│                                      │
│  Description                         │
│  ┌──────────────────────────────┐  │
│  │  Whole Foods                 │  │
│  │                              │  │
│  │  Suggestions:                │  │
│  │  • Whole Foods (recent)      │  │ ← Smart suggestions
│  │  • Walmart                   │  │
│  │  • Target                    │  │
│  └──────────────────────────────┘  │
│                                      │
│  Category                            │
│  ┌──────────────────────────────┐  │
│  │  🛒 Groceries         ▼      │  │
│  └──────────────────────────────┘  │
│                                      │
│  From                                │
│  ┌──────────────────────────────┐  │
│  │  Cash - Checking      ▼      │  │
│  └──────────────────────────────┘  │
│                                      │
│  Date                                │
│  ┌──────────────────────────────┐  │
│  │  Today, Oct 8         📅     │  │
│  └──────────────────────────────┘  │
│                                      │
│           [Save & Post]              │
│                                      │
└─────────────────────────────────────┘
```

**Interaction:**
- Tap `[🎤 Voice]` → Record voice → Transcribe → Auto-fill form
- Tap `[📷 Receipt]` → Camera → OCR → Auto-fill form
- Tap `[⌨️ Type]` → Manual entry (shown above)
- Amount input has big, easy-to-tap number pad
- Description auto-suggests based on:
  - Recent transactions
  - Current GPS location (if at known merchant)
  - Common merchants
- Swipe down to dismiss
- Keyboard shortcuts: "Return" to save

---

### 3. Receipt Scanner Flow

**Step 1: Camera Screen**

```
┌─────────────────────────────────────┐
│  📷 Scan Receipt          [×]       │
├─────────────────────────────────────┤
│                                      │
│     ┌──────────────────────────┐   │
│     │                           │   │
│     │                           │   │
│     │   [Camera viewfinder]    │   │
│     │                           │   │
│     │   Position receipt in     │   │
│     │   frame, tap to capture   │   │
│     │                           │   │
│     │                           │   │
│     └──────────────────────────┘   │
│                                      │
│              [○ Capture]             │
│                                      │
│  [💡] Tips:                          │
│  • Use good lighting                 │
│  • Flatten receipt                   │
│  • Include all text                  │
│                                      │
└─────────────────────────────────────┘
```

**Step 2: Processing**

```
┌─────────────────────────────────────┐
│  Processing Receipt...               │
├─────────────────────────────────────┤
│                                      │
│        ┌────────────────┐           │
│        │                 │           │
│        │  [Spinner]      │           │
│        │                 │           │
│        └────────────────┘           │
│                                      │
│  Extracting text...                  │
│  Finding amounts...                  │
│  Detecting merchant...               │
│                                      │
└─────────────────────────────────────┘
```

**Step 3: Review & Edit**

```
┌─────────────────────────────────────┐
│  Review Receipt          [Done]     │
├─────────────────────────────────────┤
│  ┌──────────────────────────────┐  │
│  │ [Receipt thumbnail]          │  │
│  └──────────────────────────────┘  │
│                                      │
│  Detected:                           │
│  Merchant:  Whole Foods Market      │
│  Date:      Oct 8, 2025              │
│  Total:     $125.50                  │
│                                      │
│  Items:                              │
│  ☑ Organic Bananas      $3.99       │
│  ☑ Almond Milk          $5.49       │
│  ☑ Chicken Breast       $12.99      │
│  ☑ Broccoli             $4.99       │
│  ☑ ...                  ...          │
│                                      │
│  Category:                           │
│  🛒 Groceries                        │
│                                      │
│  From Account:                       │
│  Cash - Checking                     │
│                                      │
│         [Create Transaction]         │
│                                      │
└─────────────────────────────────────┘
```

**Features:**
- OCR powered by Google Vision API or Tesseract
- Smart merchant detection (fuzzy matching)
- Line item extraction (optional: save for future analytics)
- Manual correction if OCR wrong
- Store receipt image (attached to transaction)

---

### 4. Transactions List

```
┌─────────────────────────────────────┐
│  ← Transactions          [Filter]   │
├─────────────────────────────────────┤
│  🔍 Search transactions...           │
│                                      │
│  Today                               │
│  ┌──────────────────────────────┐  │
│  │ ☕ Starbucks                 │  │
│  │ Dining Out                   │  │
│  │ -$5.50              2:45 PM  │  │ ← Swipe for actions
│  └──────────────────────────────┘  │
│                                      │
│  ┌──────────────────────────────┐  │
│  │ 🛒 Whole Foods               │  │
│  │ Groceries                    │  │
│  │ -$125.50            10:23 AM │  │
│  └──────────────────────────────┘  │
│                                      │
│  Yesterday                           │
│  ┌──────────────────────────────┐  │
│  │ ⛽ Shell                      │  │
│  │ Gas & Auto                   │  │
│  │ -$45.00              5:12 PM │  │
│  └──────────────────────────────┘  │
│                                      │
│  Oct 6                               │
│  ┌──────────────────────────────┐  │
│  │ 💰 Salary Deposit            │  │
│  │ Income                       │  │
│  │ +$3,500.00          12:00 AM │  │
│  └──────────────────────────────┘  │
│                                      │
└─────────────────────────────────────┘
│  🏠  💰  📊  🔄  ⚙️                │
└─────────────────────────────────────┘
```

**Gestures:**
- Swipe left → [Void] [Edit] buttons appear
- Swipe right → [Duplicate]
- Tap transaction → Detail screen
- Pull down → Refresh from server
- Infinite scroll (load more as scroll down)

---

### 5. Budget Envelopes Screen

```
┌─────────────────────────────────────┐
│  ← Budget Envelopes    [Allocate]   │
├─────────────────────────────────────┤
│                                      │
│  Monthly Total: $2,400               │
│  Allocated: $1,950 (81%)             │
│                                      │
│  ┌──────────────────────────────┐  │
│  │  🛒 Groceries                 │  │
│  │  ─────────────────────────────│  │
│  │  $366 / $800                  │  │
│  │  ███████░░░░░ 46%             │  │
│  │  This month: -$434            │  │
│  └──────────────────────────────┘  │
│                                      │
│  ┌──────────────────────────────┐  │
│  │  🍽️ Dining Out                │  │
│  │  ─────────────────────────────│  │
│  │  $210 / $300                  │  │
│  │  ██████████████░░ 70%         │  │
│  │  This month: -$90             │  │
│  └──────────────────────────────┘  │
│                                      │
│  ┌──────────────────────────────┐  │
│  │  ⛽ Gas & Auto           ⚠️   │  │
│  │  ─────────────────────────────│  │
│  │  $225 / $250                  │  │
│  │  █████████████████░ 90%       │  │
│  │  This month: -$225            │  │
│  │  💡 Almost at limit!          │  │
│  └──────────────────────────────┘  │
│                                      │
└─────────────────────────────────────┘
```

**Interactions:**
- Tap envelope card → Envelope detail (transaction history)
- Tap [Allocate] → Monthly allocation modal
- Visual warnings:
  - 🟢 Green when <70% used
  - 🟡 Yellow when 70-90% used
  - 🔴 Red when >90% used
  - ⚠️ Alert icon when over budget

---

### 6. Forecast Screen

```
┌─────────────────────────────────────┐
│  ← Forecast              [⚙️]        │
├─────────────────────────────────────┤
│                                      │
│  Target Date: [Dec 31, 2025 ▼]      │
│                                      │
│  📊 Cash - Checking                  │
│  ┌──────────────────────────────┐  │
│  │                               │  │
│  │  [Line chart]                │  │
│  │  Current: $25,482             │  │
│  │  Projected: $49,316           │  │
│  │                               │  │
│  └──────────────────────────────┘  │
│                                      │
│  Change: +$23,834 (↗ 93%)            │
│  Transactions: 87 applied            │
│                                      │
│  💡 Insights                         │
│  ┌──────────────────────────────┐  │
│  │ ✓ Healthy growth trajectory   │  │
│  │ ⚠️ Large expense on Nov 1      │  │
│  │ 💰 Consider $15k investment   │  │
│  └──────────────────────────────┘  │
│                                      │
│  Breakdown                           │
│  Income:      +$45,500               │
│  Expenses:    -$21,666               │
│  Net:         +$23,834               │
│                                      │
└─────────────────────────────────────┘
```

**Features:**
- Interactive chart (pinch to zoom, drag to pan)
- Tap data point → See exact balance on that date
- Toggle income/expense overlays
- Swipe between accounts

---

## Mobile-Specific Features

### 1. Location-Based Merchant Detection

**Scenario:** User walks into Whole Foods

**System Behavior:**
1. GPS detects user at known merchant location
2. Push notification: "At Whole Foods? Tap to log purchase"
3. User taps notification
4. Quick entry modal pre-filled:
   - Merchant: "Whole Foods"
   - Category: "Groceries" (based on merchant)
   - From Account: Last used account
5. User just enters amount, taps save

**Implementation:**
```typescript
// services/location.ts
import * as Location from 'expo-location';

const KNOWN_MERCHANTS = [
  {
    name: "Whole Foods Market",
    lat: 37.7749,
    lon: -122.4194,
    radius: 100, // meters
    defaultCategory: "groceries"
  },
  // ... more merchants
];

export async function detectNearbyMerchant() {
  const location = await Location.getCurrentPositionAsync();

  for (const merchant of KNOWN_MERCHANTS) {
    const distance = calculateDistance(
      location.coords.latitude,
      location.coords.longitude,
      merchant.lat,
      merchant.lon
    );

    if (distance <= merchant.radius) {
      return merchant;
    }
  }

  return null;
}

// In background task
setInterval(async () => {
  const merchant = await detectNearbyMerchant();
  if (merchant) {
    sendNotification(`At ${merchant.name}? Tap to log purchase`);
  }
}, 60000); // Check every minute
```

---

### 2. Push Notifications

**Types of Notifications:**

**Budget Alerts:**
- "You've spent 90% of your Gas budget ($225/$250)"
- "Dining budget exceeded! -$50 over limit"

**Upcoming Bills:**
- "Mortgage payment due tomorrow ($1,439)"
- "Electric bill auto-pay in 2 days ($185)"

**Positive Reinforcement:**
- "Great job! Under budget in 7 of 8 envelopes this month 🎉"
- "You're on track to save $2,500 this month"

**Forecasting:**
- "Heads up: Checking will dip to $800 on Friday before payday"

**Implementation:**
```typescript
// services/notifications.ts
import * as Notifications from 'expo-notifications';

export async function scheduleNotification(
  title: string,
  body: string,
  data: any,
  trigger: Date | number
) {
  await Notifications.scheduleNotificationAsync({
    content: {
      title,
      body,
      data,
    },
    trigger,
  });
}

// Example: Budget threshold
export function checkBudgetThresholds(envelopes) {
  envelopes.forEach((envelope) => {
    const percentUsed = (envelope.spent / envelope.monthly_allocation) * 100;

    if (percentUsed >= 90 && !envelope.notified_90) {
      scheduleNotification(
        "Budget Alert",
        `You've spent ${percentUsed.toFixed(0)}% of your ${envelope.name} budget`,
        { envelope_id: envelope.id },
        new Date()
      );
      envelope.notified_90 = true;
    }
  });
}
```

---

### 3. Offline Support

**How It Works:**

1. **Queue Transactions Offline:**
   - User creates transaction while offline
   - Stored in AsyncStorage queue
   - Marked as "pending sync"

2. **Auto-Sync When Online:**
   - App detects network connectivity
   - Uploads queued transactions
   - Updates local state with server response

3. **Conflict Resolution:**
   - If server rejects (e.g., duplicate), show user alert
   - Allow manual resolution

**Implementation:**
```typescript
// stores/offlineStore.ts
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';

export const offlineStore = create((set, get) => ({
  queue: [],

  addToQueue: async (transaction) => {
    const queue = [...get().queue, transaction];
    set({ queue });
    await AsyncStorage.setItem('offline_queue', JSON.stringify(queue));
  },

  syncQueue: async () => {
    const queue = get().queue;
    const synced = [];

    for (const transaction of queue) {
      try {
        await apiClient.post('/journal-entries', transaction);
        synced.push(transaction);
      } catch (error) {
        console.error('Sync failed:', error);
        // Keep in queue for retry
      }
    }

    // Remove synced items
    const remaining = queue.filter(t => !synced.includes(t));
    set({ queue: remaining });
    await AsyncStorage.setItem('offline_queue', JSON.stringify(remaining));
  },
}));

// Auto-sync when online
NetInfo.addEventListener((state) => {
  if (state.isConnected) {
    offlineStore.getState().syncQueue();
  }
});
```

---

### 4. Home Screen Widgets

**iOS Widget (Small):**
```
┌──────────────┐
│ LiMOS        │
├──────────────┤
│ Checking     │
│ $25,482      │
│              │
│ Dining:  70% │
│ ████░        │
└──────────────┘
```

**iOS Widget (Medium):**
```
┌────────────────────────────┐
│ LiMOS Budget Status        │
├────────────────────────────┤
│ Groceries     ███░  46%    │
│ Dining        ███░  70%    │
│ Gas           ████  90% ⚠️  │
│                             │
│ [+ Quick Entry]             │
└────────────────────────────┘
```

Tap widget → Opens app to that section
Tap [+ Quick Entry] → Opens quick entry modal

---

### 5. Biometric Authentication

**Setup:**
- First launch → "Enable Face ID to secure your finances?"
- User enables → All sensitive screens require auth

**Screens Requiring Auth:**
- App launch (if backgrounded > 5 minutes)
- Transaction detail view
- Account balances
- Settings

**Implementation:**
```typescript
import * as LocalAuthentication from 'expo-local-authentication';

export async function authenticateAsync() {
  const hasHardware = await LocalAuthentication.hasHardwareAsync();
  const isEnrolled = await LocalAuthentication.isEnrolledAsync();

  if (!hasHardware || !isEnrolled) {
    return true; // Skip if not available
  }

  const result = await LocalAuthentication.authenticateAsync({
    promptMessage: 'Authenticate to view your finances',
    fallbackLabel: 'Use Passcode',
  });

  return result.success;
}
```

---

## Performance Optimizations

### 1. List Virtualization
- Use `FlatList` with `windowSize` optimization
- Render only visible transactions (not all 1000+)

### 2. Image Optimization
- Compress receipt images before upload
- Use thumbnail for list view, full res for detail

### 3. Lazy Loading
- Load recent transactions first
- Paginate older transactions on demand

### 4. Optimistic Updates
- Immediately show transaction in list after save
- Revert if server rejects

---

## App Store Presence

### App Name
**"LiMOS: Smart Budget Envelopes"**

### Description
```
Take control of your finances with LiMOS, the intelligent budget envelope system.

✨ KEY FEATURES:
• Virtual budget envelopes - allocate money without physical cash
• Smart forecasting - see your balance months ahead
• Receipt scanner - snap photos, auto-extract data
• Voice entry - "I spent $50 on groceries" - done!
• Location-aware - detects when you're at merchants
• Offline support - works without internet, syncs later
• Push notifications - stay on budget effortlessly

💰 BUDGET ENVELOPES:
Traditional envelope budgeting meets modern technology. Allocate money to virtual envelopes (groceries, dining, gas) while keeping it in your bank account.

📊 FORECASTING:
See your future balance based on recurring income and expenses. Plan large purchases with confidence.

📸 RECEIPT SCANNING:
Take a photo of any receipt - AI extracts merchant, amount, and items automatically.

🎤 VOICE ENTRY:
Hands full? Just say "Add $25 gas purchase" and you're done.

🔒 PRIVACY FIRST:
Your data stays yours. Self-hosted option available. Biometric authentication. No ads. No selling your data.
```

### Screenshots
1. Dashboard with budget status
2. Quick entry modal
3. Receipt scanner in action
4. Forecast chart
5. Envelope management

---

## Development Plan

### Phase 1: Core App (Weeks 1-2)
- [x] Set up React Native + Expo project
- [ ] Navigation (tabs + stack)
- [ ] Dashboard screen
- [ ] Quick entry form
- [ ] Transaction list
- [ ] API integration

### Phase 2: Budget Features (Week 3)
- [ ] Envelope cards
- [ ] Budget progress bars
- [ ] Monthly allocation flow
- [ ] Push notifications

### Phase 3: Camera & OCR (Week 4)
- [ ] Receipt camera
- [ ] OCR integration (Google Vision API)
- [ ] Receipt review screen
- [ ] Image storage

### Phase 4: Advanced Features (Week 5)
- [ ] Location services
- [ ] Merchant detection
- [ ] Forecast charts
- [ ] Offline support

### Phase 5: Polish (Week 6)
- [ ] Widgets
- [ ] Biometric auth
- [ ] Animations & transitions
- [ ] Dark mode
- [ ] Testing
- [ ] App Store submission

---

## Platform-Specific Considerations

### iOS
- **TestFlight** for beta testing
- **App Store** submission (1-2 week review)
- **Size:** Aim for <50 MB download
- **iOS 14+** minimum

### Android
- **Google Play** submission (faster review)
- **Size:** Aim for <50 MB download
- **Android 8.0+** minimum
- **APK + AAB** formats

---

## Monetization (Optional Future)

**Free Tier:**
- Single user
- All core features
- Up to 500 transactions/month

**Premium ($4.99/month or $49/year):**
- Unlimited transactions
- Multi-user (family)
- Advanced forecasting
- Receipt storage (unlimited)
- Priority support
- Custom categories
- Export to Excel/QuickBooks

---

## Summary

### Pros of Mobile App
✅ **Always Available** - Phone always in pocket
✅ **Point-of-Purchase** - Log transactions instantly
✅ **Camera Integration** - Receipt scanning
✅ **Location Aware** - Merchant detection
✅ **Push Notifications** - Proactive budget alerts
✅ **Offline Support** - Works anywhere
✅ **Native Performance** - Smooth, fast
✅ **Widgets** - At-a-glance info on home screen

### Cons
❌ **Development Time** - 6+ weeks for full features
❌ **Maintenance** - Two platforms to support
❌ **App Store Fees** - $99/year (iOS), $25 one-time (Android)
❌ **Review Process** - Delays for updates
❌ **Storage** - Uses phone storage for offline data

### Best For
- Primary interface for most users
- On-the-go transaction entry
- Users who want instant access
- People who forget to log expenses
- Visual learners (charts, progress bars)
- Anyone who wants push notifications

---

**Ready to implement upon approval.**

**Recommendation: Start with iOS (React Native + Expo), add Android support later by enabling in app.json (minimal extra work).**
