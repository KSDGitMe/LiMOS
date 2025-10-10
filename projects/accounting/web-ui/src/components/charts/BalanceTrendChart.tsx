import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Box, Typography, Card, CardContent } from '@mui/material';
import { format, parseISO } from 'date-fns';

interface BalanceData {
  date: string;
  balance: number;
}

interface BalanceTrendChartProps {
  data: BalanceData[];
  title?: string;
  accountName?: string;
}

export default function BalanceTrendChart({
  data,
  title = 'Balance Trend',
  accountName
}: BalanceTrendChartProps) {
  // Format data for chart
  const chartData = data.map(item => ({
    date: format(parseISO(item.date), 'MMM d'),
    balance: item.balance,
    fullDate: item.date,
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <Card sx={{ p: 1 }}>
          <Typography variant="body2" fontWeight="bold">
            {format(parseISO(data.fullDate), 'MMM d, yyyy')}
          </Typography>
          <Typography variant="body2" color="primary">
            Balance: ${data.balance.toFixed(2)}
          </Typography>
        </Card>
      );
    }
    return null;
  };

  if (data.length === 0) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {title}
          </Typography>
          <Box display="flex" justifyContent="center" alignItems="center" height={300}>
            <Typography color="textSecondary">
              No balance data available
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  const minBalance = Math.min(...data.map(d => d.balance));
  const maxBalance = Math.max(...data.map(d => d.balance));
  const currentBalance = data[data.length - 1]?.balance || 0;
  const startBalance = data[0]?.balance || 0;
  const change = currentBalance - startBalance;
  const changePercent = startBalance !== 0 ? ((change / startBalance) * 100).toFixed(1) : '0';

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            {title}
            {accountName && (
              <Typography component="span" variant="body2" color="textSecondary" ml={1}>
                ({accountName})
              </Typography>
            )}
          </Typography>
          <Box textAlign="right">
            <Typography variant="body2" color="textSecondary">
              Change
            </Typography>
            <Typography
              variant="h6"
              color={change >= 0 ? 'success.main' : 'error.main'}
            >
              {change >= 0 ? '+' : ''}${change.toFixed(2)} ({changePercent}%)
            </Typography>
          </Box>
        </Box>

        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fontSize: 12 }}
              domain={[Math.floor(minBalance * 0.95), Math.ceil(maxBalance * 1.05)]}
              tickFormatter={(value) => `$${value.toFixed(0)}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Line
              type="monotone"
              dataKey="balance"
              stroke="#1976D2"
              strokeWidth={2}
              dot={{ fill: '#1976D2', r: 3 }}
              activeDot={{ r: 5 }}
              name="Balance"
            />
          </LineChart>
        </ResponsiveContainer>

        <Box mt={2} display="flex" justifyContent="space-around">
          <Box textAlign="center">
            <Typography variant="caption" color="textSecondary">
              Starting
            </Typography>
            <Typography variant="body2" fontWeight="bold">
              ${startBalance.toFixed(2)}
            </Typography>
          </Box>
          <Box textAlign="center">
            <Typography variant="caption" color="textSecondary">
              Current
            </Typography>
            <Typography variant="body2" fontWeight="bold" color="primary">
              ${currentBalance.toFixed(2)}
            </Typography>
          </Box>
          <Box textAlign="center">
            <Typography variant="caption" color="textSecondary">
              Range
            </Typography>
            <Typography variant="body2" fontWeight="bold">
              ${minBalance.toFixed(2)} - ${maxBalance.toFixed(2)}
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}
