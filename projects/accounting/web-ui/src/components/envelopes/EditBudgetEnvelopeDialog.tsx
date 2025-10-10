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
import { useUpdateBudgetEnvelope } from '../../hooks/useEnvelopes';
import type { BudgetEnvelope } from '../../types';

interface EditEnvelopeForm {
  envelope_name: string;
  monthly_allocation: number;
  rollover_policy: 'reset' | 'accumulate' | 'cap';
  description?: string;
}

interface EditBudgetEnvelopeDialogProps {
  open: boolean;
  onClose: () => void;
  envelope: BudgetEnvelope | null;
}

export default function EditBudgetEnvelopeDialog({ open, onClose, envelope }: EditBudgetEnvelopeDialogProps) {
  const { control, handleSubmit, reset, formState: { errors } } = useForm<EditEnvelopeForm>();
  const updateEnvelope = useUpdateBudgetEnvelope();

  // Populate form when envelope changes
  useEffect(() => {
    if (envelope) {
      reset({
        envelope_name: envelope.envelope_name,
        monthly_allocation: envelope.monthly_allocation,
        rollover_policy: envelope.rollover_policy,
        description: envelope.description || '',
      });
    }
  }, [envelope, reset]);

  const onSubmit = async (data: EditEnvelopeForm) => {
    if (!envelope) return;

    try {
      // Create updated envelope with all existing fields preserved
      const updatedEnvelope: BudgetEnvelope = {
        ...envelope,
        envelope_name: data.envelope_name,
        monthly_allocation: data.monthly_allocation,
        rollover_policy: data.rollover_policy,
        description: data.description || null,
      };

      await updateEnvelope.mutateAsync({
        id: envelope.envelope_id,
        envelope: updatedEnvelope,
      });
      toast.success(`Envelope "${data.envelope_name}" updated successfully!`);
      onClose();
    } catch (error) {
      console.error('Update envelope error:', error);
      toast.error('Failed to update envelope. Please try again.');
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <form onSubmit={handleSubmit(onSubmit)}>
        <DialogTitle>Edit Budget Envelope</DialogTitle>
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
                  placeholder="Additional notes about this envelope"
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
