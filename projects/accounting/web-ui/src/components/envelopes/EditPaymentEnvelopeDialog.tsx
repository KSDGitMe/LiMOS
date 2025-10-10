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
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import toast from 'react-hot-toast';
import { useUpdatePaymentEnvelope } from '../../hooks/useEnvelopes';
import { useAccounts } from '../../hooks/useAccounts';
import type { PaymentEnvelope } from '../../types';

interface EditPaymentEnvelopeForm {
  envelope_name: string;
  linked_account_id: string;
  description?: string;
}

interface EditPaymentEnvelopeDialogProps {
  open: boolean;
  onClose: () => void;
  envelope: PaymentEnvelope | null;
}

export default function EditPaymentEnvelopeDialog({ open, onClose, envelope }: EditPaymentEnvelopeDialogProps) {
  const { control, handleSubmit, reset, formState: { errors } } = useForm<EditPaymentEnvelopeForm>();
  const updateEnvelope = useUpdatePaymentEnvelope();
  const { data: liabilityAccounts = [] } = useAccounts({ account_type: 'liability', is_active: true });

  // Populate form when envelope changes
  useEffect(() => {
    if (envelope) {
      reset({
        envelope_name: envelope.envelope_name,
        linked_account_id: envelope.linked_account_id,
        description: envelope.description || '',
      });
    }
  }, [envelope, reset]);

  const onSubmit = async (data: EditPaymentEnvelopeForm) => {
    if (!envelope) return;

    try {
      // Create updated envelope with all existing fields preserved
      const updatedEnvelope: PaymentEnvelope = {
        ...envelope,
        envelope_name: data.envelope_name,
        linked_account_id: data.linked_account_id,
        description: data.description || null,
      };

      await updateEnvelope.mutateAsync({
        id: envelope.envelope_id,
        envelope: updatedEnvelope,
      });
      toast.success(`Payment envelope "${data.envelope_name}" updated successfully!`);
      onClose();
    } catch (error) {
      console.error('Update payment envelope error:', error);
      toast.error('Failed to update payment envelope. Please try again.');
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <form onSubmit={handleSubmit(onSubmit)}>
        <DialogTitle>Edit Payment Envelope</DialogTitle>
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
                  placeholder="e.g., Credit Card Payment, Mortgage Payment"
                />
              )}
            />

            <Controller
              name="linked_account_id"
              control={control}
              rules={{ required: 'Liability account is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  select
                  label="Liability Account"
                  fullWidth
                  error={!!errors.linked_account_id}
                  helperText={errors.linked_account_id?.message || 'The liability account this envelope tracks payments for'}
                >
                  {liabilityAccounts.map((account) => (
                    <MenuItem key={account.account_id} value={account.account_id}>
                      {account.account_name} ({account.account_id}) - Balance: ${account.current_balance.toFixed(2)}
                    </MenuItem>
                  ))}
                </TextField>
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
                  placeholder="Additional notes about this payment envelope"
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
            disabled={updateEnvelope.isPending}
          >
            {updateEnvelope.isPending ? 'Saving...' : 'Save Changes'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
