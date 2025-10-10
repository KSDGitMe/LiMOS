import { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  MenuItem,
  Grid,
  Chip,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  Alert,
  Stack,
  Button,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { useTransactions, useDeleteTransaction } from '../hooks/useTransactions';
import { format } from 'date-fns';
import toast from 'react-hot-toast';
import type { JournalEntry, JournalEntryStatus } from '../types';
import TransactionDetailDialog from '../components/transactions/TransactionDetailDialog';
import ConfirmDialog from '../components/common/ConfirmDialog';

export default function Transactions() {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [status, setStatus] = useState<JournalEntryStatus | ''>('');
  const [limit, setLimit] = useState(50);
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedTransaction, setSelectedTransaction] = useState<JournalEntry | null>(null);
  const [voidConfirmOpen, setVoidConfirmOpen] = useState(false);
  const [transactionToVoid, setTransactionToVoid] = useState<string | null>(null);

  const { data: transactions = [], isLoading, error } = useTransactions({
    start_date: startDate || undefined,
    end_date: endDate || undefined,
    status: status || undefined,
    limit,
  });

  const deleteTransaction = useDeleteTransaction();

  const handleVoidClick = (id: string) => {
    setTransactionToVoid(id);
    setVoidConfirmOpen(true);
  };

  const handleVoidConfirm = async () => {
    if (!transactionToVoid) return;

    try {
      await deleteTransaction.mutateAsync(transactionToVoid);
      toast.success('Transaction voided successfully!');
      setVoidConfirmOpen(false);
      setTransactionToVoid(null);
    } catch (error) {
      toast.error('Failed to void transaction');
    }
  };

  const handleViewDetails = (transaction: JournalEntry) => {
    setSelectedTransaction(transaction);
    setDetailOpen(true);
  };

  const getStatusColor = (status: JournalEntryStatus) => {
    switch (status) {
      case 'posted':
        return 'success';
      case 'draft':
        return 'warning';
      case 'void':
        return 'error';
      default:
        return 'default';
    }
  };

  if (error) {
    return (
      <Alert severity="error">
        Failed to load transactions: {error.message}
      </Alert>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Transactions</Typography>
        <Typography variant="body2" color="textSecondary">
          {transactions.length} transactions
        </Typography>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                label="Start Date"
                type="date"
                fullWidth
                size="small"
                InputLabelProps={{ shrink: true }}
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                label="End Date"
                type="date"
                fullWidth
                size="small"
                InputLabelProps={{ shrink: true }}
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                select
                label="Status"
                fullWidth
                size="small"
                value={status}
                onChange={(e) => setStatus(e.target.value as JournalEntryStatus | '')}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="posted">Posted</MenuItem>
                <MenuItem value="draft">Draft</MenuItem>
                <MenuItem value="void">Void</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                select
                label="Limit"
                fullWidth
                size="small"
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
              >
                <MenuItem value={20}>20</MenuItem>
                <MenuItem value={50}>50</MenuItem>
                <MenuItem value={100}>100</MenuItem>
                <MenuItem value={500}>500</MenuItem>
              </TextField>
            </Grid>
          </Grid>
          {(startDate || endDate || status) && (
            <Box mt={2}>
              <Button
                size="small"
                onClick={() => {
                  setStartDate('');
                  setEndDate('');
                  setStatus('');
                }}
              >
                Clear Filters
              </Button>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Transactions Table */}
      {isLoading ? (
        <Box display="flex" justifyContent="center" py={4}>
          <CircularProgress />
        </Box>
      ) : transactions.length === 0 ? (
        <Alert severity="info">No transactions found. Try adjusting your filters.</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell>Description</TableCell>
                <TableCell>From</TableCell>
                <TableCell>To</TableCell>
                <TableCell align="right">Amount</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {transactions.map((tx) => {
                const fromDist = tx.distributions.find(d => d.flow_direction === 'from');
                const toDist = tx.distributions.find(d => d.flow_direction === 'to');
                const amount = fromDist?.amount || 0;

                return (
                  <TableRow key={tx.journal_entry_id} hover>
                    <TableCell>
                      {format(new Date(tx.entry_date), 'MMM d, yyyy')}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{tx.description}</Typography>
                      {tx.memo && (
                        <Typography variant="caption" color="textSecondary">
                          {tx.memo}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="textSecondary">
                        {fromDist?.account_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="textSecondary">
                        {toDist?.account_id}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" fontWeight="bold">
                        ${amount.toFixed(2)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={tx.status}
                        size="small"
                        color={getStatusColor(tx.status)}
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Stack direction="row" spacing={0.5} justifyContent="center">
                        <IconButton
                          size="small"
                          title="View details"
                          onClick={() => handleViewDetails(tx)}
                        >
                          <ViewIcon fontSize="small" />
                        </IconButton>
                        <IconButton size="small" title="Edit">
                          <EditIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          title="Void transaction"
                          onClick={() => handleVoidClick(tx.journal_entry_id!)}
                          disabled={tx.status === 'void'}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Stack>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Transaction Detail Dialog */}
      <TransactionDetailDialog
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
        transaction={selectedTransaction}
      />

      {/* Void Confirmation Dialog */}
      <ConfirmDialog
        open={voidConfirmOpen}
        title="Void Transaction"
        message="Are you sure you want to void this transaction? This will mark it as void but preserve the record."
        confirmLabel="Void"
        confirmColor="warning"
        onConfirm={handleVoidConfirm}
        onCancel={() => {
          setVoidConfirmOpen(false);
          setTransactionToVoid(null);
        }}
        isLoading={deleteTransaction.isPending}
      />
    </Box>
  );
}
