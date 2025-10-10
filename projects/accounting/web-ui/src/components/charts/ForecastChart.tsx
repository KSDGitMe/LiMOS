import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, ComposedChart } from 'recharts';
import { Box, Typography, Card, CardContent } from '@mui/material';
import { format, parseISO } from 'date-fns';

interface ForecastChartProps {
  currentBalance: number;
  projectedBalance: number;
  asOfDate: string;
  targetDate: string;
  title?: string;
}

export default function ForecastChart({
  currentBalance,
  projectedBalance,
  asOfDate,
  targetDate,
  title = 'Balance Forecast'
}: ForecastChartProps) {
  // Generate chart data points
  const data = [
    {
      date: format(parseISO(asOfDate), 'MMM d'),
      balance: currentBalance,
      fullDate: asOfDate,
      isProjected: false,
    },
    {
      date: format(parseISO(targetDate), 'MMM d'),
      balance: projectedBalance,
      fullDate: targetDate,
      isProjected: true,
    },
  ];

  const change = projectedBalance - currentBalance;
  const changePercent = currentBalance !== 0 ? ((change / currentBalance) * 100).toFixed(1) : '0';

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <Card sx={{ p: 1 }}>
          <Typography variant="body2" fontWeight="bold">
            {format(parseISO(data.fullDate), 'MMM d, yyyy')}
          </Typography>
          <Typography variant="body2" color={data.isProjected ? 'primary' : 'inherit'}>
            {data.isProjected ? 'Projected' : 'Current'}: ${data.balance.toFixed(2)}
          </Typography>
        </Card>
      );
    }
    return null;
  };

  const minValue = Math.min(currentBalance, projectedBalance);
  const maxValue = Math.max(currentBalance, projectedBalance);
  const padding = Math.abs(maxValue - minValue) * 0.2 || 100;

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">{title}</Typography>
          <Box textAlign="right">
            <Typography variant="body2" color="textSecondary">
              Projected Change
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
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              domain={[Math.floor(minValue - padding), Math.ceil(maxValue + padding)]}
              tickFormatter={(value) => `$${value.toFixed(0)}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Line
              type="linear"
              dataKey="balance"
              stroke="#1976D2"
              strokeWidth={3}
              strokeDasharray="5 5"
              dot={{ fill: '#1976D2', r: 6 }}
              activeDot={{ r: 8 }}
              name="Projected Balance"
            />
          </LineChart>
        </ResponsiveContainer>

        <Box mt={2} display="flex" justifyContent="space-around">
          <Box textAlign="center">
            <Typography variant="caption" color="textSecondary">
              Current Balance
            </Typography>
            <Typography variant="body1" fontWeight="bold">
              ${currentBalance.toFixed(2)}
            </Typography>
            <Typography variant="caption" color="textSecondary">
              {format(parseISO(asOfDate), 'MMM d, yyyy')}
            </Typography>
          </Box>
          <Box textAlign="center">
            <Typography variant="caption" color="textSecondary">
              Projected Balance
            </Typography>
            <Typography variant="body1" fontWeight="bold" color="primary">
              ${projectedBalance.toFixed(2)}
            </Typography>
            <Typography variant="caption" color="textSecondary">
              {format(parseISO(targetDate), 'MMM d, yyyy')}
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}
