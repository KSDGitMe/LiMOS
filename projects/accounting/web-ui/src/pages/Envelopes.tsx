import { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Alert,
  CircularProgress,
  Stack,
  Tooltip,
  IconButton,
} from '@mui/material';
import { Info as InfoIcon, Edit as EditIcon } from '@mui/icons-material';
import { useForm, Controller } from 'react-hook-form';
import { useBudgetEnvelopes, usePaymentEnvelopes, useAllocateEnvelopes } from '../hooks/useEnvelopes';
import { useAccounts } from '../hooks/useAccounts';
import CreateEnvelopeDialog from '../components/envelopes/CreateEnvelopeDialog';
import EditBudgetEnvelopeDialog from '../components/envelopes/EditBudgetEnvelopeDialog';
import EditPaymentEnvelopeDialog from '../components/envelopes/EditPaymentEnvelopeDialog';
import type { BudgetEnvelope, PaymentEnvelope } from '../types';

interface AllocateForm {
  month: string;
  sourceAccount: string;
}

export default function Envelopes() {
  const { data: budgetEnvelopes = [], isLoading: budgetLoading } = useBudgetEnvelopes();
  const { data: paymentEnvelopes = [], isLoading: paymentLoading } = usePaymentEnvelopes();
  const { data: accounts = [] } = useAccounts({ account_type: 'asset' });
  const [allocateOpen, setAllocateOpen] = useState(false);
  const [createEnvelopeOpen, setCreateEnvelopeOpen] = useState(false);
  const [editBudgetOpen, setEditBudgetOpen] = useState(false);
  const [editPaymentOpen, setEditPaymentOpen] = useState(false);
  const [selectedBudgetEnvelope, setSelectedBudgetEnvelope] = useState<BudgetEnvelope | null>(null);
  const [selectedPaymentEnvelope, setSelectedPaymentEnvelope] = useState<PaymentEnvelope | null>(null);

  const { control, handleSubmit, reset } = useForm<AllocateForm>({
    defaultValues: {
      month: new Date().toISOString().slice(0, 7),
      sourceAccount: '1000',
    },
  });

  const allocateEnvelopes = useAllocateEnvelopes();

  const getRolloverPolicyTooltip = (policy: string) => {
    const tooltips: Record<string, string> = {
      reset: "Reset: Unused balance resets to $0 each month. Use it or lose it!",
      accumulate: "Accumulate: Unused balance carries forward indefinitely. Build up savings!",
      cap: "Cap: Unused balance carries forward up to the monthly allocation amount.",
    };
    return tooltips[policy] || policy;
  };

  const onAllocate = async (data: AllocateForm) => {
    try {
      const [year, month] = data.month.split('-');
      const allocationDate = `${year}-${month}-01`;
      const periodLabel = data.month;

      await allocateEnvelopes.mutateAsync({
        sourceAccountId: data.sourceAccount,
        allocationDate,
        periodLabel,
      });

      reset();
      setAllocateOpen(false);
    } catch (error) {
      console.error('Allocation error:', error);
    }
  };

  if (budgetLoading || paymentLoading) {
    return (
      <Box display="flex" justifyContent="center" py={4}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Budget Envelopes</Typography>
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            onClick={() => setCreateEnvelopeOpen(true)}
          >
            Create Envelope
          </Button>
          <Button
            variant="contained"
            onClick={() => setAllocateOpen(true)}
          >
            Apply Monthly Allocations
          </Button>
        </Stack>
      </Box>


      {/* Budget Envelopes */}
      <Typography variant="h6" gutterBottom>
        Budget Envelopes ({budgetEnvelopes.length})
      </Typography>
      <Grid container spacing={3} mb={4}>
        {budgetEnvelopes.map((envelope) => {
          const percentUsed = envelope.monthly_allocation > 0
            ? ((envelope.monthly_allocation - envelope.current_balance) / envelope.monthly_allocation) * 100
            : 0;

          const getColor = () => {
            if (percentUsed >= 100) return 'error';
            if (percentUsed >= 90) return 'error';
            if (percentUsed >= 70) return 'warning';
            return 'primary';
          };

          return (
            <Grid item xs={12} sm={6} md={4} key={envelope.envelope_id}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                    <Typography variant="h6" sx={{ fontSize: '1.1rem' }}>
                      {envelope.envelope_name}
                    </Typography>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Tooltip title={getRolloverPolicyTooltip(envelope.rollover_policy)} arrow>
                        <Chip
                          label={envelope.rollover_policy}
                          size="small"
                          variant="outlined"
                          icon={<InfoIcon fontSize="small" />}
                        />
                      </Tooltip>
                      <Tooltip title="Edit envelope">
                        <IconButton
                          size="small"
                          onClick={() => {
                            setSelectedBudgetEnvelope(envelope);
                            setEditBudgetOpen(true);
                          }}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Stack>
                  </Box>

                  <Box mb={2}>
                    <Box display="flex" justifyContent="space-between" mb={0.5}>
                      <Typography variant="body2" color="textSecondary">
                        Balance
                      </Typography>
                      <Typography variant="body2" fontWeight="bold">
                        ${envelope.current_balance.toFixed(2)} / ${envelope.monthly_allocation.toFixed(2)}
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={Math.min(percentUsed, 100)}
                      color={getColor()}
                      sx={{ height: 8, borderRadius: 1 }}
                    />
                    <Typography variant="caption" color="textSecondary" mt={0.5}>
                      {percentUsed.toFixed(0)}% used
                    </Typography>
                  </Box>

                  <Stack spacing={0.5}>
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="caption" color="textSecondary">
                        Monthly
                      </Typography>
                      <Typography variant="caption">
                        ${envelope.monthly_allocation.toFixed(2)}
                      </Typography>
                    </Box>
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="caption" color="textSecondary">
                        Spent
                      </Typography>
                      <Typography variant="caption">
                        ${(envelope.monthly_allocation - envelope.current_balance).toFixed(2)}
                      </Typography>
                    </Box>
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="caption" color="textSecondary">
                        Remaining
                      </Typography>
                      <Typography variant="caption" color={envelope.current_balance < 0 ? 'error.main' : 'inherit'}>
                        ${envelope.current_balance.toFixed(2)}
                      </Typography>
                    </Box>
                  </Stack>

                  {percentUsed >= 90 && (
                    <Alert severity={percentUsed >= 100 ? 'error' : 'warning'} sx={{ mt: 2 }}>
                      {percentUsed >= 100 ? 'Over budget!' : 'Almost at limit'}
                    </Alert>
                  )}
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Payment Envelopes */}
      <Typography variant="h6" gutterBottom mt={4}>
        Payment Envelopes ({paymentEnvelopes.length})
      </Typography>
      <Grid container spacing={3}>
        {paymentEnvelopes.map((envelope) => (
          <Grid item xs={12} sm={6} md={4} key={envelope.envelope_id}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                  <Typography variant="h6" sx={{ fontSize: '1.1rem' }}>
                    {envelope.envelope_name}
                  </Typography>
                  <Tooltip title="Edit payment envelope">
                    <IconButton
                      size="small"
                      onClick={() => {
                        setSelectedPaymentEnvelope(envelope);
                        setEditPaymentOpen(true);
                      }}
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2" color="textSecondary">
                    Reserved Amount
                  </Typography>
                  <Typography variant="h6" color="primary">
                    ${envelope.current_balance.toFixed(2)}
                  </Typography>
                </Box>
                <Typography variant="caption" color="textSecondary" mt={1}>
                  For liability: {envelope.liability_account_id}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Allocate Dialog */}
      <Dialog open={allocateOpen} onClose={() => setAllocateOpen(false)} maxWidth="sm" fullWidth>
        <form onSubmit={handleSubmit(onAllocate)}>
          <DialogTitle>Apply Monthly Allocations</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <Controller
                name="month"
                control={control}
                rules={{ required: 'Month is required' }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Month"
                    type="month"
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                  />
                )}
              />

              <Controller
                name="sourceAccount"
                control={control}
                rules={{ required: 'Source account is required' }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    select
                    label="Source Account"
                    fullWidth
                  >
                    {accounts.map((account) => (
                      <MenuItem key={account.account_id} value={account.account_id}>
                        {account.account_name} (${account.current_balance.toFixed(2)})
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />

              <Alert severity="info">
                This will allocate monthly amounts to all active budget envelopes from the selected account.
              </Alert>
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setAllocateOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={allocateEnvelopes.isPending}>
              {allocateEnvelopes.isPending ? 'Allocating...' : 'Allocate'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Create Envelope Dialog */}
      <CreateEnvelopeDialog
        open={createEnvelopeOpen}
        onClose={() => setCreateEnvelopeOpen(false)}
      />

      {/* Edit Budget Envelope Dialog */}
      <EditBudgetEnvelopeDialog
        open={editBudgetOpen}
        onClose={() => {
          setEditBudgetOpen(false);
          setSelectedBudgetEnvelope(null);
        }}
        envelope={selectedBudgetEnvelope}
      />

      {/* Edit Payment Envelope Dialog */}
      <EditPaymentEnvelopeDialog
        open={editPaymentOpen}
        onClose={() => {
          setEditPaymentOpen(false);
          setSelectedPaymentEnvelope(null);
        }}
        envelope={selectedPaymentEnvelope}
      />
    </Box>
  );
}
