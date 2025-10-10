import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Alert,
  CircularProgress,
} from '@mui/material';
import { TrendingUp, TrendingDown } from '@mui/icons-material';
import { useAccounts } from '../hooks/useAccounts';
import { useBudgetEnvelopes } from '../hooks/useEnvelopes';
import { useTransactions } from '../hooks/useTransactions';
import SpendingPieChart from '../components/charts/SpendingPieChart';
import BalanceTrendChart from '../components/charts/BalanceTrendChart';
import { subDays, format } from 'date-fns';

export default function Dashboard() {
  const { data: accounts = [], isLoading: accountsLoading } = useAccounts({ is_active: true });
  const { data: envelopes = [], isLoading: envelopesLoading } = useBudgetEnvelopes();
  const { data: transactions = [], isLoading: transactionsLoading } = useTransactions({ limit: 5 });

  if (accountsLoading || envelopesLoading || transactionsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const assetAccounts = accounts.filter(a => a.account_type === 'asset');

  // Prepare spending data for pie chart
  const spendingByEnvelope = envelopes.map(env => ({
    name: env.envelope_name,
    value: env.monthly_allocation - env.current_balance, // Amount spent
    color: '', // Will use default colors
  })).filter(item => item.value > 0); // Only show envelopes with spending

  // Prepare balance trend data (mock data for now - would need historical API)
  const balanceTrendData = Array.from({ length: 30 }, (_, i) => {
    const date = format(subDays(new Date(), 29 - i), 'yyyy-MM-dd');
    // Mock data - in production would fetch from API
    const primaryAccount = assetAccounts[0];
    const randomVariance = (Math.random() - 0.5) * 200;
    return {
      date,
      balance: primaryAccount ? primaryAccount.current_balance + randomVariance : 0,
    };
  });

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* Account Cards */}
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom>
            Accounts
          </Typography>
        </Grid>
        {assetAccounts.map((account) => (
          <Grid item xs={12} sm={6} md={4} key={account.account_id}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  {account.account_name}
                </Typography>
                <Typography variant="h4">
                  ${account.current_balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </Typography>
                <Box display="flex" alignItems="center" mt={1}>
                  {account.current_balance >= account.opening_balance ? (
                    <TrendingUp color="success" fontSize="small" />
                  ) : (
                    <TrendingDown color="error" fontSize="small" />
                  )}
                  <Typography variant="body2" color="textSecondary" ml={0.5}>
                    {((account.current_balance - account.opening_balance) / account.opening_balance * 100).toFixed(1)}%
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}

        {/* Budget Envelopes */}
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom mt={2}>
            Budget Status
          </Typography>
        </Grid>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              {envelopes.length === 0 ? (
                <Alert severity="info">No budget envelopes configured yet.</Alert>
              ) : (
                <Grid container spacing={2}>
                  {envelopes.map((envelope) => {
                    const percentUsed = envelope.monthly_allocation > 0
                      ? ((envelope.monthly_allocation - envelope.current_balance) / envelope.monthly_allocation) * 100
                      : 0;

                    return (
                      <Grid item xs={12} key={envelope.envelope_id}>
                        <Box>
                          <Box display="flex" justifyContent="space-between" mb={0.5}>
                            <Typography variant="body2">
                              {envelope.envelope_name}
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                              ${envelope.current_balance.toFixed(2)} / ${envelope.monthly_allocation.toFixed(2)}
                            </Typography>
                          </Box>
                          <LinearProgress
                            variant="determinate"
                            value={Math.min(percentUsed, 100)}
                            color={percentUsed > 90 ? 'error' : percentUsed > 70 ? 'warning' : 'primary'}
                          />
                          <Typography variant="caption" color="textSecondary">
                            {percentUsed.toFixed(0)}% used
                          </Typography>
                        </Box>
                      </Grid>
                    );
                  })}
                </Grid>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Charts */}
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom mt={2}>
            Analytics
          </Typography>
        </Grid>

        {/* Spending Pie Chart */}
        <Grid item xs={12} md={6}>
          <SpendingPieChart data={spendingByEnvelope} title="Current Month Spending" />
        </Grid>

        {/* Balance Trend Chart */}
        <Grid item xs={12} md={6}>
          <BalanceTrendChart
            data={balanceTrendData}
            title="30-Day Balance Trend"
            accountName={assetAccounts[0]?.account_name}
          />
        </Grid>

        {/* Recent Transactions */}
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom mt={2}>
            Recent Transactions
          </Typography>
        </Grid>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              {transactions.length === 0 ? (
                <Alert severity="info">No transactions yet.</Alert>
              ) : (
                <Box>
                  {transactions.map((tx) => {
                    const amount = tx.distributions.find(d => d.flow_direction === 'from')?.amount || 0;
                    return (
                      <Box
                        key={tx.journal_entry_id}
                        display="flex"
                        justifyContent="space-between"
                        alignItems="center"
                        py={1}
                        borderBottom="1px solid #eee"
                      >
                        <Box>
                          <Typography variant="body1">{tx.description}</Typography>
                          <Typography variant="caption" color="textSecondary">
                            {new Date(tx.entry_date).toLocaleDateString()}
                          </Typography>
                        </Box>
                        <Typography variant="body1" fontWeight="bold">
                          ${amount.toFixed(2)}
                        </Typography>
                      </Box>
                    );
                  })}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
