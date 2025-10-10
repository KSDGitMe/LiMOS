import { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Stack,
  Button,
  Grid,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import toast from 'react-hot-toast';
import { useAccounts } from '../hooks/useAccounts';
import EditAccountDialog from '../components/accounts/EditAccountDialog';
import type { AccountType, ChartOfAccounts } from '../types';

interface TabPanelProps {
  children?: React.ReactNode;
  value: string;
  index: string;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`account-tabpanel-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export default function ChartOfAccounts() {
  const [accountTypeFilter, setAccountTypeFilter] = useState<AccountType | 'all'>('all');
  const [selectedTab, setSelectedTab] = useState('all');
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState<ChartOfAccounts | null>(null);

  const { data: allAccounts = [], isLoading } = useAccounts({ is_active: true });

  const handleEditAccount = (account: ChartOfAccounts) => {
    setSelectedAccount(account);
    setEditDialogOpen(true);
  };

  const handleDeleteAccount = (account: ChartOfAccounts) => {
    toast.error('Account deletion is not yet implemented. Coming soon!');
    console.log('Delete account:', account);
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: string) => {
    setSelectedTab(newValue);
    if (newValue === 'all') {
      setAccountTypeFilter('all');
    } else {
      setAccountTypeFilter(newValue as AccountType);
    }
  };

  const filteredAccounts = accountTypeFilter === 'all'
    ? allAccounts
    : allAccounts.filter(acc => acc.account_type === accountTypeFilter);

  const getAccountTypeColor = (type: AccountType) => {
    switch (type) {
      case 'asset': return 'success';
      case 'liability': return 'error';
      case 'equity': return 'info';
      case 'revenue': return 'primary';
      case 'expense': return 'warning';
      default: return 'default';
    }
  };

  const accountsByType = {
    asset: allAccounts.filter(a => a.account_type === 'asset'),
    liability: allAccounts.filter(a => a.account_type === 'liability'),
    equity: allAccounts.filter(a => a.account_type === 'equity'),
    revenue: allAccounts.filter(a => a.account_type === 'revenue'),
    expense: allAccounts.filter(a => a.account_type === 'expense'),
  };

  const renderAccountsTable = (accounts: typeof allAccounts) => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Account #</TableCell>
            <TableCell>Account Name</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Subtype</TableCell>
            <TableCell align="right">Current Balance</TableCell>
            <TableCell>Description</TableCell>
            <TableCell align="center">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {accounts.length === 0 ? (
            <TableRow>
              <TableCell colSpan={7} align="center">
                <Typography variant="body2" color="textSecondary">
                  No accounts found
                </Typography>
              </TableCell>
            </TableRow>
          ) : (
            accounts.map((account) => (
              <TableRow key={account.account_id} hover>
                <TableCell>
                  <Typography variant="body2" fontWeight="medium">
                    {account.account_number}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {account.account_name}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={account.account_type}
                    size="small"
                    color={getAccountTypeColor(account.account_type)}
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="caption" color="textSecondary">
                    {account.account_subtype || '—'}
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Typography
                    variant="body2"
                    fontWeight="bold"
                    color={account.current_balance < 0 ? 'error.main' : 'inherit'}
                  >
                    ${account.current_balance.toFixed(2)}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="caption" color="textSecondary">
                    {account.description || '—'}
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  <Stack direction="row" spacing={0.5} justifyContent="center">
                    <IconButton
                      size="small"
                      title="Edit account"
                      onClick={() => handleEditAccount(account)}
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                    <IconButton
                      size="small"
                      title="Delete account"
                      color="error"
                      onClick={() => handleDeleteAccount(account)}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Stack>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </TableContainer>
  );

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" py={4}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Chart of Accounts</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {/* TODO: Open create dialog */}}
        >
          New Account
        </Button>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        <strong>Chart of Accounts:</strong> The foundation of your accounting system.
        All transactions must reference accounts defined here. Common account types include:
        <br />
        <strong>Revenue:</strong> Social Security, Pensions, Salary, Interest, Dividends
        <br />
        <strong>Expense:</strong> Groceries, Rent, Utilities, Gas, Entertainment
        <br />
        <strong>Asset:</strong> Checking, Savings, Investments
        <br />
        <strong>Liability:</strong> Credit Cards, Loans, Mortgages
      </Alert>

      {/* Summary Cards */}
      <Grid container spacing={2} mb={3}>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="body2" gutterBottom>
                Assets
              </Typography>
              <Typography variant="h5" color="success.main">
                {accountsByType.asset.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="body2" gutterBottom>
                Liabilities
              </Typography>
              <Typography variant="h5" color="error.main">
                {accountsByType.liability.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="body2" gutterBottom>
                Equity
              </Typography>
              <Typography variant="h5" color="info.main">
                {accountsByType.equity.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="body2" gutterBottom>
                Revenue
              </Typography>
              <Typography variant="h5" color="primary.main">
                {accountsByType.revenue.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="body2" gutterBottom>
                Expenses
              </Typography>
              <Typography variant="h5" color="warning.main">
                {accountsByType.expense.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs for filtering */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={selectedTab} onChange={handleTabChange}>
          <Tab label={`All (${allAccounts.length})`} value="all" />
          <Tab label={`Assets (${accountsByType.asset.length})`} value="asset" />
          <Tab label={`Liabilities (${accountsByType.liability.length})`} value="liability" />
          <Tab label={`Equity (${accountsByType.equity.length})`} value="equity" />
          <Tab label={`Revenue (${accountsByType.revenue.length})`} value="revenue" />
          <Tab label={`Expenses (${accountsByType.expense.length})`} value="expense" />
        </Tabs>
      </Box>

      {/* Accounts Table */}
      {renderAccountsTable(filteredAccounts)}

      {/* Edit Account Dialog */}
      <EditAccountDialog
        open={editDialogOpen}
        onClose={() => {
          setEditDialogOpen(false);
          setSelectedAccount(null);
        }}
        account={selectedAccount}
      />
    </Box>
  );
}
