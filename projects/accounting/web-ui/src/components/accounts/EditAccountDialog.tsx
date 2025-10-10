import { useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  MenuItem,
  Stack,
  FormControlLabel,
  Switch,
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import toast from 'react-hot-toast';
import { useUpdateAccount } from '../../hooks/useAccounts';
import { useBudgetEnvelopes, usePaymentEnvelopes } from '../../hooks/useEnvelopes';
import type { ChartOfAccounts, AccountType } from '../../types';

interface EditAccountForm {
  account_name: string;
  account_type: AccountType;
  account_subtype?: string;
  description?: string;
  is_active: boolean;
  budget_envelope_id?: string;
  payment_envelope_id?: string;
}

interface EditAccountDialogProps {
  open: boolean;
  onClose: () => void;
  account: ChartOfAccounts | null;
}

const ACCOUNT_TYPES: AccountType[] = ['asset', 'liability', 'equity', 'revenue', 'expense'];

export default function EditAccountDialog({ open, onClose, account }: EditAccountDialogProps) {
  const { control, handleSubmit, reset, formState: { errors }, watch } = useForm<EditAccountForm>();
  const updateAccount = useUpdateAccount();
  const { data: budgetEnvelopes = [] } = useBudgetEnvelopes();
  const { data: paymentEnvelopes = [] } = usePaymentEnvelopes();

  const accountType = watch('account_type');

  // Populate form when account changes
  useEffect(() => {
    if (account) {
      reset({
        account_name: account.account_name,
        account_type: account.account_type,
        account_subtype: account.account_subtype || '',
        description: account.description || '',
        is_active: account.is_active,
        budget_envelope_id: account.budget_envelope_id || '',
        payment_envelope_id: account.payment_envelope_id || '',
      });
    }
  }, [account, reset]);

  const onSubmit = async (data: EditAccountForm) => {
    if (!account) return;

    try {
      // Create updated account with all existing fields preserved
      const updatedAccount: ChartOfAccounts = {
        ...account,
        account_name: data.account_name,
        account_type: data.account_type,
        account_subtype: data.account_subtype || null,
        description: data.description || null,
        is_active: data.is_active,
        budget_envelope_id: data.budget_envelope_id || null,
        payment_envelope_id: data.payment_envelope_id || null,
      };

      await updateAccount.mutateAsync({
        id: account.account_id,
        account: updatedAccount,
      });
      toast.success(`Account "${data.account_name}" updated successfully!`);
      onClose();
    } catch (error) {
      console.error('Update account error:', error);
      toast.error('Failed to update account. Please try again.');
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <form onSubmit={handleSubmit(onSubmit)}>
        <DialogTitle>Edit Account</DialogTitle>
        <DialogContent>
          <Stack spacing={2.5} sx={{ mt: 1 }}>
            <Controller
              name="account_name"
              control={control}
              rules={{
                required: 'Account name is required',
                minLength: { value: 2, message: 'Name must be at least 2 characters' }
              }}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Account Name"
                  fullWidth
                  error={!!errors.account_name}
                  helperText={errors.account_name?.message}
                  placeholder="e.g., Cash - Checking, Groceries, Credit Card A"
                />
              )}
            />

            <Controller
              name="account_type"
              control={control}
              rules={{ required: 'Account type is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  select
                  label="Account Type"
                  fullWidth
                  error={!!errors.account_type}
                  helperText={errors.account_type?.message}
                >
                  {ACCOUNT_TYPES.map((type) => (
                    <MenuItem key={type} value={type}>
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />

            <Controller
              name="account_subtype"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Account Subtype (Optional)"
                  fullWidth
                  error={!!errors.account_subtype}
                  helperText={errors.account_subtype?.message || 'e.g., Checking, Savings, Credit Card'}
                  placeholder="e.g., Checking, Savings, Credit Card"
                />
              )}
            />

            <Controller
              name="description"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Description (Optional)"
                  fullWidth
                  multiline
                  rows={2}
                  error={!!errors.description}
                  helperText={errors.description?.message}
                  placeholder="Additional notes about this account"
                />
              )}
            />

            {accountType === 'expense' && (
              <Controller
                name="budget_envelope_id"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    select
                    label="Budget Envelope (Optional)"
                    fullWidth
                    helperText="Link this expense account to a budget envelope for tracking"
                  >
                    <MenuItem value="">
                      <em>None</em>
                    </MenuItem>
                    {budgetEnvelopes.map((envelope) => (
                      <MenuItem key={envelope.envelope_id} value={envelope.envelope_id}>
                        {envelope.envelope_name} (${envelope.monthly_allocation.toFixed(2)}/month)
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />
            )}

            {accountType === 'liability' && (
              <Controller
                name="payment_envelope_id"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    select
                    label="Payment Envelope (Optional)"
                    fullWidth
                    helperText="Link this liability account to a payment envelope for tracking"
                  >
                    <MenuItem value="">
                      <em>None</em>
                    </MenuItem>
                    {paymentEnvelopes.map((envelope) => (
                      <MenuItem key={envelope.envelope_id} value={envelope.envelope_id}>
                        {envelope.envelope_name}
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />
            )}

            <Controller
              name="is_active"
              control={control}
              render={({ field }) => (
                <FormControlLabel
                  control={
                    <Switch
                      checked={field.value}
                      onChange={(e) => field.onChange(e.target.checked)}
                    />
                  }
                  label="Active Account"
                />
              )}
            />

          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button
            type="submit"
            variant="contained"
            disabled={updateAccount.isPending}
          >
            {updateAccount.isPending ? 'Saving...' : 'Save Changes'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
