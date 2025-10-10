import { useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  MenuItem,
  Alert,
  Stack,
  Typography,
  Divider,
  FormControlLabel,
  Switch,
  Checkbox,
} from '@mui/material';
import toast from 'react-hot-toast';
import { useAccounts } from '../../hooks/useAccounts';
import { useBudgetEnvelopes } from '../../hooks/useEnvelopes';
import { useCreateTransaction } from '../../hooks/useTransactions';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { recurringApi } from '../../api/client';
import type { CreateTransactionForm, AccountType } from '../../types';

interface QuickEntryDialogProps {
  open: boolean;
  onClose: () => void;
}

// Transaction type definitions with account rules
const TRANSACTION_TYPES = {
  purchase: {
    label: 'Purchase',
    description: 'Buy goods or services',
    fromTypes: ['asset', 'liability'], // Bank, Credit Card
    toTypes: ['expense'], // Expense accounts
    icon: '🛒',
  },
  return: {
    label: 'Return/Refund',
    description: 'Return purchase or receive refund',
    fromTypes: ['expense'], // Expense accounts
    toTypes: ['asset', 'liability'], // Bank, Credit Card
    icon: '↩️',
  },
  income: {
    label: 'Income/Deposit',
    description: 'Salary, Social Security, Pension, etc.',
    fromTypes: ['revenue'], // Income accounts
    toTypes: ['asset'], // Bank accounts
    icon: '💰',
  },
  transfer: {
    label: 'Transfer',
    description: 'Move money between accounts',
    fromTypes: ['asset'], // Bank to Bank
    toTypes: ['asset'],
    icon: '↔️',
  },
  loanPayment: {
    label: 'Loan Payment',
    description: 'Pay down loan or mortgage',
    fromTypes: ['asset'], // Bank
    toTypes: ['liability', 'expense'], // Loan + Interest expense
    icon: '🏦',
  },
  billPayment: {
    label: 'Bill Payment (A/P)',
    description: 'Pay bills or accounts payable',
    fromTypes: ['asset'], // Bank
    toTypes: ['liability'], // Payable account
    icon: '📄',
  },
  withdrawal: {
    label: 'ATM/Cash Withdrawal',
    description: 'Withdraw cash from account',
    fromTypes: ['asset'], // Bank
    toTypes: ['asset'], // Cash account
    icon: '💵',
  },
  investment: {
    label: 'Investment',
    description: 'Buy stocks, bonds, etc.',
    fromTypes: ['asset'], // Bank
    toTypes: ['asset'], // Investment account
    icon: '📈',
  },
};

type TransactionType = keyof typeof TRANSACTION_TYPES;

interface ExtendedTransactionForm extends CreateTransactionForm {
  transactionType: TransactionType;
  isRecurring: boolean;
  frequency?: 'biweekly' | 'monthly' | 'quarterly' | 'semiannually' | 'annually';
  startDate?: string;
  autoPost?: boolean;
  templateName?: string;
}

export default function QuickEntryDialog({ open, onClose }: QuickEntryDialogProps) {
  const queryClient = useQueryClient();
  const { control, handleSubmit, reset, watch, setValue, formState: { errors } } = useForm<ExtendedTransactionForm>({
    defaultValues: {
      transactionType: 'purchase',
      description: '',
      amount: 0,
      fromAccount: '',
      toAccount: '',
      date: new Date().toISOString().split('T')[0],
      isRecurring: false,
      frequency: 'monthly',
      startDate: new Date().toISOString().split('T')[0],
      autoPost: true,
      templateName: '',
    },
  });

  const { data: accounts = [] } = useAccounts();
  const { data: envelopes = [] } = useBudgetEnvelopes();
  const createTransaction = useCreateTransaction();

  const createRecurringTemplate = useMutation({
    mutationFn: async (template: any) => {
      const { data } = await recurringApi.create(template);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recurring-templates'] });
    },
  });

  const transactionType = watch('transactionType');
  const fromAccount = watch('fromAccount');
  const toAccount = watch('toAccount');
  const isRecurring = watch('isRecurring');

  // Filter accounts based on transaction type
  const getFromAccounts = () => {
    const allowedTypes = TRANSACTION_TYPES[transactionType].fromTypes;
    return accounts.filter(a => allowedTypes.includes(a.account_type) && a.is_active);
  };

  const getToAccounts = () => {
    const allowedTypes = TRANSACTION_TYPES[transactionType].toTypes;
    return accounts.filter(a => allowedTypes.includes(a.account_type) && a.is_active);
  };

  const getAccountType = (accountId: string): AccountType => {
    const account = accounts.find(a => a.account_id === accountId);
    return account?.account_type || 'expense';
  };

  // Reset account selections when transaction type changes
  const handleTransactionTypeChange = (newType: TransactionType) => {
    setValue('transactionType', newType);
    setValue('fromAccount', '');
    setValue('toAccount', '');
  };

  const onSubmit = async (data: ExtendedTransactionForm) => {
    try {
      const fromAccountType = getAccountType(data.fromAccount);
      const toAccountType = getAccountType(data.toAccount);

      // Find envelope for expense account
      let envelopeId: string | undefined;
      if (toAccountType === 'expense') {
        const envelope = envelopes.find(e => e.expense_account_id === data.toAccount);
        envelopeId = envelope?.envelope_id;
      }

      if (data.isRecurring) {
        // Create recurring template
        const template = {
          template_name: data.templateName || data.description,
          description: data.description,
          entry_type: data.transactionType,
          distribution_template: [
            {
              account_id: data.fromAccount,
              amount: data.amount,
              flow_direction: 'from',
            },
            {
              account_id: data.toAccount,
              amount: data.amount,
              flow_direction: 'to',
              budget_envelope_id: envelopeId,
            },
          ],
          frequency: data.frequency,
          start_date: data.startDate,
          auto_post: data.autoPost,
          auto_create_days_before: 0,
          require_approval: false,
          is_active: true,
          total_generated: 0,
          tags: [],
        };

        await createRecurringTemplate.mutateAsync(template);
        toast.success(`Recurring ${TRANSACTION_TYPES[data.transactionType].label} template created!`);
      } else {
        // Create one-time transaction
        // Determine status: posted if today or past, draft if future
        const transactionDate = new Date(data.date);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        transactionDate.setHours(0, 0, 0, 0);
        const status = transactionDate <= today ? 'posted' : 'draft';

        const transaction = {
          entry_date: data.date,
          description: data.description,
          entry_type: data.transactionType,
          distributions: [
            {
              account_id: data.fromAccount,
              account_type: fromAccountType,
              flow_direction: 'from' as const,
              amount: data.amount,
              multiplier: fromAccountType === 'asset' || fromAccountType === 'expense' ? -1 : 1,
              debit_credit: fromAccountType === 'asset' || fromAccountType === 'expense' ? 'Cr' as const : 'Dr' as const,
            },
            {
              account_id: data.toAccount,
              account_type: toAccountType,
              flow_direction: 'to' as const,
              amount: data.amount,
              multiplier: toAccountType === 'asset' || toAccountType === 'expense' ? 1 : -1,
              debit_credit: toAccountType === 'asset' || toAccountType === 'expense' ? 'Dr' as const : 'Cr' as const,
              budget_envelope_id: envelopeId,
            },
          ],
          status: status as const,
        };

        await createTransaction.mutateAsync(transaction);
        const statusMsg = status === 'posted' ? 'recorded' : 'saved as draft';
        toast.success(`${TRANSACTION_TYPES[data.transactionType].label} ${statusMsg}!`);
      }

      reset();
      onClose();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to create transaction');
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const fromAccounts = getFromAccounts();
  const toAccounts = getToAccounts();
  const selectedType = TRANSACTION_TYPES[transactionType];

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <form onSubmit={handleSubmit(onSubmit)}>
        <DialogTitle>New Transaction</DialogTitle>
        <DialogContent>
          <Stack spacing={2.5} sx={{ mt: 1 }}>
            {/* Transaction Type Selector */}
            <Controller
              name="transactionType"
              control={control}
              rules={{ required: 'Transaction type is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  select
                  label="Transaction Type"
                  fullWidth
                  onChange={(e) => handleTransactionTypeChange(e.target.value as TransactionType)}
                  error={!!errors.transactionType}
                  helperText={selectedType.description}
                >
                  {Object.entries(TRANSACTION_TYPES).map(([key, type]) => (
                    <MenuItem key={key} value={key}>
                      <Stack direction="row" spacing={1} alignItems="center">
                        <span>{type.icon}</span>
                        <span>{type.label}</span>
                      </Stack>
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />

            {/* Recurring Toggle */}
            <Controller
              name="isRecurring"
              control={control}
              render={({ field }) => (
                <FormControlLabel
                  control={
                    <Switch
                      {...field}
                      checked={field.value}
                    />
                  }
                  label={
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Typography>Make this recurring</Typography>
                      {field.value && (
                        <Typography variant="caption" color="primary" sx={{ fontWeight: 'bold' }}>
                          (Template will be created)
                        </Typography>
                      )}
                    </Stack>
                  }
                />
              )}
            />

            <Divider />

            {/* Template Name (only for recurring) */}
            {isRecurring && (
              <Controller
                name="templateName"
                control={control}
                rules={{ required: isRecurring ? 'Template name is required' : false }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Template Name"
                    fullWidth
                    error={!!errors.templateName}
                    helperText={errors.templateName?.message || 'Give this recurring transaction a name'}
                    placeholder="e.g., Monthly Rent, Biweekly Paycheck"
                  />
                )}
              />
            )}

            {/* Description */}
            <Controller
              name="description"
              control={control}
              rules={{ required: 'Description is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Description"
                  fullWidth
                  error={!!errors.description}
                  helperText={errors.description?.message}
                  placeholder={`e.g., ${
                    transactionType === 'purchase' ? 'Grocery store purchase' :
                    transactionType === 'income' ? 'Monthly salary' :
                    transactionType === 'transfer' ? 'Transfer to savings' :
                    'Transaction description'
                  }`}
                />
              )}
            />

            {/* Amount */}
            <Controller
              name="amount"
              control={control}
              rules={{
                required: 'Amount is required',
                min: { value: 0.01, message: 'Amount must be greater than 0' }
              }}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Amount"
                  type="number"
                  fullWidth
                  inputProps={{ step: '0.01', min: '0.01' }}
                  error={!!errors.amount}
                  helperText={errors.amount?.message}
                  InputProps={{
                    startAdornment: <span style={{ marginRight: 4 }}>$</span>,
                  }}
                  onChange={(e) => field.onChange(parseFloat(e.target.value) || 0)}
                />
              )}
            />

            {/* From Account - Filtered by transaction type */}
            <Controller
              name="fromAccount"
              control={control}
              rules={{ required: 'From account is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  select
                  label="From Account"
                  fullWidth
                  error={!!errors.fromAccount}
                  helperText={
                    errors.fromAccount?.message ||
                    `Select ${TRANSACTION_TYPES[transactionType].fromTypes.join('/')} account`
                  }
                >
                  {fromAccounts.length === 0 ? (
                    <MenuItem disabled>No accounts available for this transaction type</MenuItem>
                  ) : (
                    fromAccounts.map((account) => (
                      <MenuItem key={account.account_id} value={account.account_id}>
                        {account.account_name} ({account.account_type})
                        {account.account_type === 'asset' && ` - $${account.current_balance.toFixed(2)}`}
                      </MenuItem>
                    ))
                  )}
                </TextField>
              )}
            />

            {/* To Account - Filtered by transaction type */}
            <Controller
              name="toAccount"
              control={control}
              rules={{ required: 'To account is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  select
                  label="To Account"
                  fullWidth
                  error={!!errors.toAccount}
                  helperText={
                    errors.toAccount?.message ||
                    `Select ${TRANSACTION_TYPES[transactionType].toTypes.join('/')} account`
                  }
                >
                  {toAccounts.length === 0 ? (
                    <MenuItem disabled>No accounts available for this transaction type</MenuItem>
                  ) : (
                    toAccounts.map((account) => (
                      <MenuItem key={account.account_id} value={account.account_id}>
                        {account.account_name} ({account.account_type})
                        {account.account_type === 'asset' && ` - $${account.current_balance.toFixed(2)}`}
                      </MenuItem>
                    ))
                  )}
                </TextField>
              )}
            />

            {/* Recurring Pattern Fields */}
            {isRecurring ? (
              <>
                {/* Frequency */}
                <Controller
                  name="frequency"
                  control={control}
                  rules={{ required: isRecurring ? 'Frequency is required' : false }}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      select
                      label="Frequency"
                      fullWidth
                      error={!!errors.frequency}
                      helperText={errors.frequency?.message || 'How often this transaction occurs'}
                    >
                      <MenuItem value="biweekly">Every 2 weeks</MenuItem>
                      <MenuItem value="monthly">Monthly</MenuItem>
                      <MenuItem value="quarterly">Quarterly (every 3 months)</MenuItem>
                      <MenuItem value="semiannually">Semi-annually (every 6 months)</MenuItem>
                      <MenuItem value="annually">Annually</MenuItem>
                    </TextField>
                  )}
                />

                {/* Start Date */}
                <Controller
                  name="startDate"
                  control={control}
                  rules={{ required: isRecurring ? 'Start date is required' : false }}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Start Date"
                      type="date"
                      fullWidth
                      InputLabelProps={{ shrink: true }}
                      error={!!errors.startDate}
                      helperText={errors.startDate?.message || 'Date of first occurrence'}
                    />
                  )}
                />

                {/* Auto Post */}
                <Controller
                  name="autoPost"
                  control={control}
                  render={({ field }) => (
                    <FormControlLabel
                      control={
                        <Checkbox
                          {...field}
                          checked={field.value}
                        />
                      }
                      label="Automatically post generated transactions"
                    />
                  )}
                />
              </>
            ) : (
              /* One-time Date */
              <Controller
                name="date"
                control={control}
                rules={{ required: !isRecurring ? 'Date is required' : false }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Date"
                    type="date"
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                    error={!!errors.date}
                    helperText={errors.date?.message}
                  />
                )}
              />
            )}

            {/* Info message about envelope assignment */}
            {transactionType === 'purchase' && toAccount && (
              <Alert severity="info" sx={{ mt: 1 }}>
                {envelopes.find(e => e.expense_account_id === toAccount) ? (
                  <>
                    ✓ This expense will be tracked in the{' '}
                    <strong>{envelopes.find(e => e.expense_account_id === toAccount)?.envelope_name}</strong> envelope
                  </>
                ) : (
                  'This expense account is not assigned to a budget envelope'
                )}
              </Alert>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button
            type="submit"
            variant="contained"
            disabled={
              (isRecurring ? createRecurringTemplate.isPending : createTransaction.isPending) ||
              fromAccounts.length === 0 ||
              toAccounts.length === 0
            }
          >
            {isRecurring
              ? createRecurringTemplate.isPending
                ? 'Creating Template...'
                : 'Create Template'
              : createTransaction.isPending
              ? 'Saving...'
              : 'Save & Post'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
