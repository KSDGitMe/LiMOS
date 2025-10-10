import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { Box, Typography, Card, CardContent } from '@mui/material';

interface SpendingData {
  name: string;
  value: number;
  color: string;
}

interface SpendingPieChartProps {
  data: SpendingData[];
  title?: string;
}

const COLORS = [
  '#1976D2', // Primary blue
  '#2E7D32', // Green
  '#ED6C02', // Orange
  '#D32F2F', // Red
  '#9C27B0', // Purple
  '#00897B', // Teal
  '#F57C00', // Dark orange
  '#5E35B1', // Deep purple
];

export default function SpendingPieChart({ data, title = 'Spending by Category' }: SpendingPieChartProps) {
  // Add colors to data
  const chartData = data.map((item, index) => ({
    ...item,
    color: item.color || COLORS[index % COLORS.length],
  }));

  const total = data.reduce((sum, item) => sum + item.value, 0);

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      const percentage = ((data.value / total) * 100).toFixed(1);
      return (
        <Card sx={{ p: 1 }}>
          <Typography variant="body2" fontWeight="bold">
            {data.name}
          </Typography>
          <Typography variant="body2" color="primary">
            ${data.value.toFixed(2)}
          </Typography>
          <Typography variant="caption" color="textSecondary">
            {percentage}% of total
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
              No spending data available
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
        <Box mt={2} textAlign="center">
          <Typography variant="body2" color="textSecondary">
            Total Spending: <strong>${total.toFixed(2)}</strong>
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
}
