import { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  MenuItem,
  Grid,
  Alert,
  CircularProgress,
  Stack,
  Chip,
} from '@mui/material';
import { TrendingUp, TrendingDown } from '@mui/icons-material';
import { useAccounts } from '../hooks/useAccounts';
import { useForecastAccount } from '../hooks/useForecast';
import { format, addMonths } from 'date-fns';
import ForecastChart from '../components/charts/ForecastChart';

export default function Forecast() {
  const { data: accounts = [] } = useAccounts({ account_type: 'asset' });
  const [selectedAccount, setSelectedAccount] = useState('1000');
  const [monthsAhead, setMonthsAhead] = useState(3);

  const targetDate = format(addMonths(new Date(), monthsAhead), 'yyyy-MM-dd');

  const { data: forecast, isLoading, error } = useForecastAccount(selectedAccount, targetDate);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Account Forecast
      </Typography>

      {/* Controls */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                select
                label="Account"
                fullWidth
                value={selectedAccount}
                onChange={(e) => setSelectedAccount(e.target.value)}
              >
                {accounts.map((account) => (
                  <MenuItem key={account.account_id} value={account.account_id}>
                    {account.account_name}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                select
                label="Forecast Period"
                fullWidth
                value={monthsAhead}
                onChange={(e) => setMonthsAhead(Number(e.target.value))}
              >
                <MenuItem value={1}>1 Month</MenuItem>
                <MenuItem value={3}>3 Months</MenuItem>
                <MenuItem value={6}>6 Months</MenuItem>
                <MenuItem value={12}>1 Year</MenuItem>
              </TextField>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Forecast Results */}
      {isLoading ? (
        <Box display="flex" justifyContent="center" py={4}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error">Failed to load forecast: {error.message}</Alert>
      ) : forecast ? (
        <Grid container spacing={3}>
          {/* Forecast Chart */}
          <Grid item xs={12}>
            <ForecastChart
              currentBalance={forecast.current_balance}
              projectedBalance={forecast.projected_balance}
              asOfDate={forecast.as_of_date}
              targetDate={forecast.target_date}
            />
          </Grid>

          {/* Current Balance */}
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Current Balance
                </Typography>
                <Typography variant="h4">
                  ${forecast.current_balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  As of {format(new Date(forecast.as_of_date), 'MMM d, yyyy')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Projected Balance */}
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Projected Balance
                </Typography>
                <Typography variant="h4" color="primary">
                  ${forecast.projected_balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  On {format(new Date(forecast.target_date), 'MMM d, yyyy')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Balance Change */}
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Expected Change
                </Typography>
                <Box display="flex" alignItems="center" gap={1}>
                  {forecast.balance_change >= 0 ? (
                    <TrendingUp color="success" />
                  ) : (
                    <TrendingDown color="error" />
                  )}
                  <Typography
                    variant="h4"
                    color={forecast.balance_change >= 0 ? 'success.main' : 'error.main'}
                  >
                    ${Math.abs(forecast.balance_change).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </Typography>
                </Box>
                <Typography variant="caption" color="textSecondary">
                  {forecast.balance_change >= 0 ? 'Increase' : 'Decrease'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Details */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Forecast Details
                </Typography>
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      Account
                    </Typography>
                    <Typography variant="body1">{forecast.account_name}</Typography>
                  </Box>

                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      Recurring Transactions Applied
                    </Typography>
                    <Typography variant="body1">
                      {forecast.transactions_applied} transactions
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      Forecast Period
                    </Typography>
                    <Typography variant="body1">
                      {format(new Date(forecast.as_of_date), 'MMM d, yyyy')} → {format(new Date(forecast.target_date), 'MMM d, yyyy')}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      Trend
                    </Typography>
                    {forecast.balance_change > 0 ? (
                      <Chip
                        icon={<TrendingUp />}
                        label={`Growing by $${forecast.balance_change.toFixed(2)}`}
                        color="success"
                        variant="outlined"
                      />
                    ) : forecast.balance_change < 0 ? (
                      <Chip
                        icon={<TrendingDown />}
                        label={`Declining by $${Math.abs(forecast.balance_change).toFixed(2)}`}
                        color="error"
                        variant="outlined"
                      />
                    ) : (
                      <Chip label="Stable" color="default" variant="outlined" />
                    )}
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          {/* Insights */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  💡 Insights
                </Typography>
                <Stack spacing={1}>
                  {forecast.balance_change > 1000 && (
                    <Alert severity="success">
                      Great news! Your balance is projected to increase significantly by ${forecast.balance_change.toFixed(2)}.
                    </Alert>
                  )}
                  {forecast.balance_change < -1000 && (
                    <Alert severity="warning">
                      Your balance is projected to decrease by ${Math.abs(forecast.balance_change).toFixed(2)}. Consider reviewing upcoming expenses.
                    </Alert>
                  )}
                  {forecast.projected_balance < 1000 && (
                    <Alert severity="error">
                      Warning: Your projected balance will be below $1,000. Consider building up your reserves.
                    </Alert>
                  )}
                  {forecast.projected_balance > 50000 && (
                    <Alert severity="info">
                      You'll have a strong financial position with ${forecast.projected_balance.toFixed(2)}. Consider investment opportunities.
                    </Alert>
                  )}
                  {forecast.transactions_applied === 0 && (
                    <Alert severity="info">
                      No recurring transactions scheduled for this period. Set up recurring templates for better forecasting.
                    </Alert>
                  )}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      ) : null}
    </Box>
  );
}
