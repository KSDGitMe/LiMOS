import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Stack,
  Box,
  Typography,
  IconButton,
  Divider,
  MenuItem,
  Alert,
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { useForm, Controller, useFieldArray } from 'react-hook-form';
import toast from 'react-hot-toast';
import { useUpdateTransaction } from '../../hooks/useTransactions';
import { useAccounts } from '../../hooks/useAccounts';
import type { JournalEntry, Distribution } from '../../types';
import { format } from 'date-fns';

interface EditTransactionForm {
  entry_date: string;
  description: string;
  memo: string;
  distributions: Array<{
    account_id: string;
    flow_direction: 'from' | 'to';
    amount: number;
    description: string;
  }>;
}

interface EditTransactionDialogProps {
  open: boolean;
  onClose: () => void;
  transaction: JournalEntry | null;
}

export default function EditTransactionDialog({
  open,
  onClose,
  transaction,
}: EditTransactionDialogProps) {
  const { data: accounts = [] } = useAccounts({ is_active: true });
  const updateTransaction = useUpdateTransaction();

  const { control, handleSubmit, reset, watch, formState: { errors } } = useForm<EditTransactionForm>({
    defaultValues: {
      entry_date: '',
      description: '',
      memo: '',
      distributions: [
        { account_id: '', flow_direction: 'from', amount: 0, description: '' },
        { account_id: '', flow_direction: 'to', amount: 0, description: '' },
      ],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'distributions',
  });

  // Populate form when transaction changes
  useEffect(() => {
    if (transaction && open) {
      reset({
        entry_date: format(new Date(transaction.entry_date), 'yyyy-MM-dd'),
        description: transaction.description,
        memo: transaction.memo || '',
        distributions: transaction.distributions.map(d => ({
          account_id: d.account_id,
          flow_direction: d.flow_direction,
          amount: d.amount,
          description: d.description || '',
        })),
      });
    }
  }, [transaction, open, reset]);

  // Calculate balance
  const distributions = watch('distributions');
  const fromTotal = distributions
    .filter(d => d.flow_direction === 'from')
    .reduce((sum, d) => sum + (Number(d.amount) || 0), 0);
  const toTotal = distributions
    .filter(d => d.flow_direction === 'to')
    .reduce((sum, d) => sum + (Number(d.amount) || 0), 0);
  const isBalanced = Math.abs(fromTotal - toTotal) < 0.01;

  const onSubmit = async (data: EditTransactionForm) => {
    if (!transaction?.journal_entry_id) return;

    // Check if balanced
    if (!isBalanced) {
      toast.error('Transaction must be balanced (FROM total = TO total)');
      return;
    }

    try {
      // Build updated transaction
      const updatedTransaction: JournalEntry = {
        ...transaction,
        entry_date: data.entry_date,
        description: data.description,
        memo: data.memo || undefined,
        distributions: data.distributions.map((dist, index) => ({
          ...transaction.distributions[index],
          account_id: dist.account_id,
          flow_direction: dist.flow_direction,
          amount: Number(dist.amount),
          description: dist.description || undefined,
          // Determine account type from accounts list
          account_type: accounts.find(a => a.account_id === dist.account_id)?.account_type || 'asset',
          // Calculate debit/credit based on flow and account type
          debit_credit: calculateDebitCredit(
            dist.flow_direction,
            accounts.find(a => a.account_id === dist.account_id)?.account_type || 'asset'
          ),
        })),
      };

      await updateTransaction.mutateAsync({
        id: transaction.journal_entry_id,
        data: updatedTransaction,
      });

      toast.success('Transaction updated successfully!');
      reset();
      onClose();
    } catch (error) {
      console.error('Update transaction error:', error);
      toast.error('Failed to update transaction');
    }
  };

  const calculateDebitCredit = (flowDirection: 'from' | 'to', accountType: string): 'Dr' | 'Cr' => {
    // Debit/Credit rules based on accounting principles
    const isDebit =
      (accountType === 'asset' && flowDirection === 'to') ||
      (accountType === 'expense' && flowDirection === 'to') ||
      (accountType === 'liability' && flowDirection === 'from') ||
      (accountType === 'equity' && flowDirection === 'from') ||
      (accountType === 'revenue' && flowDirection === 'from');

    return isDebit ? 'Dr' : 'Cr';
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  // Can only edit draft transactions
  if (transaction && transaction.status !== 'draft') {
    return (
      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>Cannot Edit Transaction</DialogTitle>
        <DialogContent>
          <Alert severity="warning">
            Only <strong>draft</strong> transactions can be edited.
            This transaction has status: <strong>{transaction.status}</strong>.
            <br /><br />
            To modify a posted transaction, you must void it and create a new one.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Close</Button>
        </DialogActions>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <form onSubmit={handleSubmit(onSubmit)}>
        <DialogTitle>Edit Transaction (Draft)</DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            {/* Basic Info */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Transaction Details
              </Typography>
              <Stack spacing={2}>
                <Controller
                  name="entry_date"
                  control={control}
                  rules={{ required: 'Date is required' }}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Entry Date"
                      type="date"
                      fullWidth
                      InputLabelProps={{ shrink: true }}
                      error={!!errors.entry_date}
                      helperText={errors.entry_date?.message}
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
                      error={!!errors.description}
                      helperText={errors.description?.message}
                    />
                  )}
                />

                <Controller
                  name="memo"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Memo (Optional)"
                      fullWidth
                      multiline
                      rows={2}
                    />
                  )}
                />
              </Stack>
            </Box>

            <Divider />

            {/* Distributions */}
            <Box>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="subtitle2">
                  Distributions
                </Typography>
                <Button
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={() => append({ account_id: '', flow_direction: 'to', amount: 0, description: '' })}
                >
                  Add Distribution
                </Button>
              </Box>

              {fields.map((field, index) => (
                <Box key={field.id} mb={2} p={2} border="1px solid #e0e0e0" borderRadius={1}>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                    <Typography variant="caption" color="textSecondary">
                      Distribution {index + 1}
                    </Typography>
                    {fields.length > 2 && (
                      <IconButton size="small" onClick={() => remove(index)} color="error">
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    )}
                  </Box>

                  <Stack spacing={2}>
                    <Controller
                      name={`distributions.${index}.account_id`}
                      control={control}
                      rules={{ required: 'Account is required' }}
                      render={({ field }) => (
                        <TextField
                          {...field}
                          select
                          label="Account"
                          fullWidth
                          size="small"
                          error={!!errors.distributions?.[index]?.account_id}
                          helperText={errors.distributions?.[index]?.account_id?.message}
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
                      name={`distributions.${index}.flow_direction`}
                      control={control}
                      render={({ field }) => (
                        <TextField
                          {...field}
                          select
                          label="Flow Direction"
                          fullWidth
                          size="small"
                        >
                          <MenuItem value="from">FROM (Money Out)</MenuItem>
                          <MenuItem value="to">TO (Money In)</MenuItem>
                        </TextField>
                      )}
                    />

                    <Controller
                      name={`distributions.${index}.amount`}
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
                          size="small"
                          InputProps={{
                            startAdornment: <span style={{ marginRight: '4px' }}>$</span>,
                          }}
                          onChange={(e) => field.onChange(parseFloat(e.target.value) || 0)}
                          error={!!errors.distributions?.[index]?.amount}
                          helperText={errors.distributions?.[index]?.amount?.message}
                        />
                      )}
                    />

                    <Controller
                      name={`distributions.${index}.description`}
                      control={control}
                      render={({ field }) => (
                        <TextField
                          {...field}
                          label="Distribution Description (Optional)"
                          fullWidth
                          size="small"
                        />
                      )}
                    />
                  </Stack>
                </Box>
              ))}

              {/* Balance Check */}
              <Box mt={2} p={2} bgcolor={isBalanced ? '#e8f5e9' : '#ffebee'} borderRadius={1}>
                <Stack spacing={1}>
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="body2">FROM Total:</Typography>
                    <Typography variant="body2" fontWeight="bold">
                      ${fromTotal.toFixed(2)}
                    </Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="body2">TO Total:</Typography>
                    <Typography variant="body2" fontWeight="bold">
                      ${toTotal.toFixed(2)}
                    </Typography>
                  </Box>
                  <Divider />
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="body2" fontWeight="bold">
                      {isBalanced ? '✅ Balanced' : '❌ Not Balanced'}
                    </Typography>
                    <Typography variant="body2" fontWeight="bold" color={isBalanced ? 'success.main' : 'error.main'}>
                      Difference: ${Math.abs(fromTotal - toTotal).toFixed(2)}
                    </Typography>
                  </Box>
                </Stack>
              </Box>
            </Box>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button
            type="submit"
            variant="contained"
            disabled={!isBalanced || updateTransaction.isPending}
          >
            {updateTransaction.isPending ? 'Saving...' : 'Save Changes'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
