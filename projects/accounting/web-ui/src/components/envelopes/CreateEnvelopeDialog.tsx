import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  MenuItem,
  Stack,
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import toast from 'react-hot-toast';
import { useCreateBudgetEnvelope } from '../../hooks/useEnvelopes';
import { useAccounts } from '../../hooks/useAccounts';

interface CreateEnvelopeForm {
  envelope_name: string;
  expense_account_id: string;
  monthly_allocation: number;
  rollover_policy: 'reset' | 'accumulate' | 'cap';
  asset_account_id: string;
}

interface CreateEnvelopeDialogProps {
  open: boolean;
  onClose: () => void;
}

export default function CreateEnvelopeDialog({ open, onClose }: CreateEnvelopeDialogProps) {
  const { control, handleSubmit, reset, formState: { errors } } = useForm<CreateEnvelopeForm>({
    defaultValues: {
      envelope_name: '',
      expense_account_id: '',
      monthly_allocation: 0,
      rollover_policy: 'reset',
      asset_account_id: '1000', // Default to primary checking
    },
  });

  const createEnvelope = useCreateBudgetEnvelope();
  const { data: expenseAccounts = [] } = useAccounts({ account_type: 'expense', is_active: true });
  const { data: assetAccounts = [] } = useAccounts({ account_type: 'asset', is_active: true });

  const onSubmit = async (data: CreateEnvelopeForm) => {
    try {
      await createEnvelope.mutateAsync({
        envelope_name: data.envelope_name,
        expense_account_id: data.expense_account_id,
        monthly_allocation: data.monthly_allocation,
        rollover_policy: data.rollover_policy,
        asset_account_id: data.asset_account_id,
        current_balance: data.monthly_allocation, // Start with full allocation
        is_active: true,
      });
      toast.success(`Envelope "${data.envelope_name}" created successfully!`);
      reset();
      onClose();
    } catch (error) {
      console.error('Create envelope error:', error);
      toast.error('Failed to create envelope. Please try again.');
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <form onSubmit={handleSubmit(onSubmit)}>
        <DialogTitle>Create Budget Envelope</DialogTitle>
        <DialogContent>
          <Stack spacing={2.5} sx={{ mt: 1 }}>
            <Controller
              name="envelope_name"
              control={control}
              rules={{
                required: 'Envelope name is required',
                minLength: { value: 2, message: 'Name must be at least 2 characters' }
              }}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Envelope Name"
                  fullWidth
                  error={!!errors.envelope_name}
                  helperText={errors.envelope_name?.message}
                  placeholder="e.g., Groceries, Entertainment, Gas"
                />
              )}
            />

            <Controller
              name="expense_account_id"
              control={control}
              rules={{ required: 'Expense account is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  select
                  label="Expense Account"
                  fullWidth
                  error={!!errors.expense_account_id}
                  helperText={errors.expense_account_id?.message || 'The account this envelope tracks spending for'}
                >
                  {expenseAccounts.map((account) => (
                    <MenuItem key={account.account_id} value={account.account_id}>
                      {account.account_name} ({account.account_id})
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />

            <Controller
              name="monthly_allocation"
              control={control}
              rules={{
                required: 'Monthly allocation is required',
                min: { value: 0, message: 'Amount must be positive' }
              }}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Monthly Allocation"
                  type="number"
                  fullWidth
                  error={!!errors.monthly_allocation}
                  helperText={errors.monthly_allocation?.message || 'Amount to allocate each month'}
                  InputProps={{
                    startAdornment: <span style={{ marginRight: '4px' }}>$</span>,
                  }}
                  onChange={(e) => field.onChange(parseFloat(e.target.value) || 0)}
                />
              )}
            />

            <Controller
              name="rollover_policy"
              control={control}
              rules={{ required: 'Rollover policy is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  select
                  label="Rollover Policy"
                  fullWidth
                  error={!!errors.rollover_policy}
                  helperText={
                    field.value === 'reset' ? 'Unused balance resets to $0 each month' :
                    field.value === 'accumulate' ? 'Unused balance carries forward indefinitely' :
                    field.value === 'cap' ? 'Balance carries forward up to monthly allocation' :
                    'Select how unused funds are handled'
                  }
                >
                  <MenuItem value="reset">Reset (Use it or lose it)</MenuItem>
                  <MenuItem value="accumulate">Accumulate (Build savings)</MenuItem>
                  <MenuItem value="cap">Cap (Up to monthly amount)</MenuItem>
                </TextField>
              )}
            />

            <Controller
              name="asset_account_id"
              control={control}
              rules={{ required: 'Funding source is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  select
                  label="Funding Source"
                  fullWidth
                  error={!!errors.asset_account_id}
                  helperText={errors.asset_account_id?.message || 'Account to fund allocations from'}
                >
                  {assetAccounts.map((account) => (
                    <MenuItem key={account.account_id} value={account.account_id}>
                      {account.account_name} (${account.current_balance.toFixed(2)})
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />

          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button
            type="submit"
            variant="contained"
            disabled={createEnvelope.isPending}
          >
            {createEnvelope.isPending ? 'Creating...' : 'Create Envelope'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
