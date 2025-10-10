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
  Checkbox,
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import toast from 'react-hot-toast';
import { useUpdateRecurringTemplate } from '../../hooks/useRecurring';
import { useAccounts } from '../../hooks/useAccounts';
import { format } from 'date-fns';
import type { RecurringJournalEntry } from '../../types';

interface EditTemplateForm {
  template_name: string;
  description: string;
  from_account: string;
  to_account: string;
  amount: number;
  frequency: 'biweekly' | 'monthly' | 'quarterly' | 'semiannually' | 'annually';
  start_date: string;
  auto_post: boolean;
}

interface EditTemplateDialogProps {
  open: boolean;
  onClose: () => void;
  template: RecurringJournalEntry | null;
}

export default function EditTemplateDialog({ open, onClose, template }: EditTemplateDialogProps) {
  const { control, handleSubmit, reset, formState: { errors } } = useForm<EditTemplateForm>();
  const { data: accounts = [] } = useAccounts({ is_active: true });
  const updateTemplate = useUpdateRecurringTemplate();

  // Populate form when template changes
  useEffect(() => {
    if (template) {
      const fromDist = template.distribution_template.find(d => d.flow_direction === 'from');
      const toDist = template.distribution_template.find(d => d.flow_direction === 'to');

      reset({
        template_name: template.template_name,
        description: template.description,
        from_account: fromDist?.account_id || '',
        to_account: toDist?.account_id || '',
        amount: fromDist?.amount || 0,
        frequency: template.frequency as any,
        start_date: template.start_date,
        auto_post: template.auto_post,
      });
    }
  }, [template, reset]);

  const onSubmit = async (data: EditTemplateForm) => {
    if (!template) return;

    try {
      await updateTemplate.mutateAsync({
        id: template.recurring_entry_id,
        template: {
          template_name: data.template_name,
          description: data.description,
          entry_type: 'standard',
          distribution_template: [
            {
              account_id: data.from_account,
              amount: data.amount,
              flow_direction: 'from',
            },
            {
              account_id: data.to_account,
              amount: data.amount,
              flow_direction: 'to',
            },
          ],
          frequency: data.frequency,
          start_date: data.start_date,
          auto_post: data.auto_post,
          auto_create_days_before: template.auto_create_days_before,
          require_approval: template.require_approval,
          is_active: template.is_active,
          total_generated: template.total_generated,
          tags: template.tags,
        },
      });
      toast.success(`Template "${data.template_name}" updated successfully!`);
      onClose();
    } catch (error) {
      console.error('Update template error:', error);
      toast.error('Failed to update template. Please try again.');
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const frequencyLabels: Record<string, string> = {
    biweekly: 'Every 2 weeks',
    monthly: 'Monthly',
    quarterly: 'Quarterly (every 3 months)',
    semiannually: 'Semi-annually (every 6 months)',
    annually: 'Annually',
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <form onSubmit={handleSubmit(onSubmit)}>
        <DialogTitle>Edit Recurring Template</DialogTitle>
        <DialogContent>
          <Stack spacing={2.5} sx={{ mt: 1 }}>
            <Controller
              name="template_name"
              control={control}
              rules={{
                required: 'Template name is required',
                minLength: { value: 2, message: 'Name must be at least 2 characters' }
              }}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Template Name"
                  fullWidth
                  error={!!errors.template_name}
                  helperText={errors.template_name?.message}
                  placeholder="e.g., Monthly Rent, Biweekly Paycheck"
                />
              )}
            />

            <Controller
              name="description"
              control={control}
              rules={{
                required: 'Description is required',
                minLength: { value: 3, message: 'Description must be at least 3 characters' }
              }}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Description"
                  fullWidth
                  multiline
                  rows={2}
                  error={!!errors.description}
                  helperText={errors.description?.message}
                  placeholder="Brief description of this recurring transaction"
                />
              )}
            />

            <Controller
              name="from_account"
              control={control}
              rules={{ required: 'From account is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  select
                  label="From Account (Source)"
                  fullWidth
                  error={!!errors.from_account}
                  helperText={errors.from_account?.message || 'Account money comes from'}
                >
                  {accounts.map((account) => (
                    <MenuItem key={account.account_id} value={account.account_id}>
                      {account.account_name} ({account.account_type})
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />

            <Controller
              name="to_account"
              control={control}
              rules={{ required: 'To account is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  select
                  label="To Account (Destination)"
                  fullWidth
                  error={!!errors.to_account}
                  helperText={errors.to_account?.message || 'Account money goes to'}
                >
                  {accounts.map((account) => (
                    <MenuItem key={account.account_id} value={account.account_id}>
                      {account.account_name} ({account.account_type})
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />

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
                  error={!!errors.amount}
                  helperText={errors.amount?.message}
                  InputProps={{
                    startAdornment: <span style={{ marginRight: '4px' }}>$</span>,
                  }}
                  onChange={(e) => field.onChange(parseFloat(e.target.value) || 0)}
                />
              )}
            />

            <Controller
              name="frequency"
              control={control}
              rules={{ required: 'Frequency is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  select
                  label="Frequency"
                  fullWidth
                  error={!!errors.frequency}
                  helperText={field.value ? frequencyLabels[field.value] : 'How often this transaction occurs'}
                >
                  <MenuItem value="biweekly">Every 2 weeks</MenuItem>
                  <MenuItem value="monthly">Monthly</MenuItem>
                  <MenuItem value="quarterly">Quarterly</MenuItem>
                  <MenuItem value="semiannually">Semi-annually</MenuItem>
                  <MenuItem value="annually">Annually</MenuItem>
                </TextField>
              )}
            />

            <Controller
              name="start_date"
              control={control}
              rules={{ required: 'Start date is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  label="Start Date"
                  type="date"
                  fullWidth
                  error={!!errors.start_date}
                  helperText={errors.start_date?.message || 'Date of first occurrence'}
                  InputLabelProps={{ shrink: true }}
                />
              )}
            />

            <Controller
              name="auto_post"
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

          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button
            type="submit"
            variant="contained"
            disabled={updateTemplate.isPending}
          >
            {updateTemplate.isPending ? 'Saving...' : 'Save Changes'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
