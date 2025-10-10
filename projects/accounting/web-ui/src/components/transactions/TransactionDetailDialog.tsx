import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Divider,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Stack,
  IconButton,
  Tooltip,
  MenuItem,
  Menu,
} from '@mui/material';
import { MoreVert as MoreVertIcon } from '@mui/icons-material';
import { format } from 'date-fns';
import toast from 'react-hot-toast';
import { useState } from 'react';
import { useUpdateTransaction } from '../../hooks/useTransactions';
import type { JournalEntry, JournalEntryStatus } from '../../types';

interface TransactionDetailDialogProps {
  open: boolean;
  onClose: () => void;
  transaction: JournalEntry | null;
}

export default function TransactionDetailDialog({
  open,
  onClose,
  transaction,
}: TransactionDetailDialogProps) {
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const updateTransaction = useUpdateTransaction();

  if (!transaction) return null;

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

  const handleStatusChange = async (newStatus: JournalEntryStatus) => {
    if (!transaction.journal_entry_id) return;

    try {
      await updateTransaction.mutateAsync({
        id: transaction.journal_entry_id,
        data: {
          ...transaction,
          status: newStatus,
          posting_date: newStatus === 'posted' ? transaction.entry_date : null,
        },
      });
      toast.success(`Transaction status changed to ${newStatus}`);
      setMenuAnchor(null);
      onClose(); // Close dialog to refresh data
    } catch (error) {
      toast.error('Failed to update transaction status');
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setMenuAnchor(event.currentTarget);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
  };

  const totalAmount = transaction.distributions
    .filter(d => d.flow_direction === 'from')
    .reduce((sum, d) => sum + d.amount, 0);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">Transaction Details</Typography>
          <Stack direction="row" spacing={1} alignItems="center">
            <Chip
              label={transaction.status}
              size="small"
              color={getStatusColor(transaction.status)}
            />
            {transaction.status !== 'void' && (
              <Tooltip title="Change status">
                <IconButton size="small" onClick={handleMenuOpen}>
                  <MoreVertIcon />
                </IconButton>
              </Tooltip>
            )}
          </Stack>
        </Box>
        <Menu
          anchorEl={menuAnchor}
          open={Boolean(menuAnchor)}
          onClose={handleMenuClose}
        >
          {transaction.status !== 'draft' && (
            <MenuItem onClick={() => handleStatusChange('draft')}>
              Mark as Draft
            </MenuItem>
          )}
          {transaction.status !== 'posted' && (
            <MenuItem onClick={() => handleStatusChange('posted')}>
              Mark as Posted
            </MenuItem>
          )}
        </Menu>
      </DialogTitle>
      <DialogContent>
        <Stack spacing={3}>
          {/* Basic Information */}
          <Box>
            <Typography variant="overline" color="textSecondary" gutterBottom>
              Basic Information
            </Typography>
            <Stack spacing={1.5}>
              <Box display="flex" justifyContent="space-between">
                <Typography variant="body2" color="textSecondary">
                  Entry Number
                </Typography>
                <Typography variant="body2" fontWeight="medium">
                  {transaction.entry_number || 'N/A'}
                </Typography>
              </Box>
              <Box display="flex" justifyContent="space-between">
                <Typography variant="body2" color="textSecondary">
                  Entry Date
                </Typography>
                <Typography variant="body2" fontWeight="medium">
                  {format(new Date(transaction.entry_date), 'MMM d, yyyy')}
                </Typography>
              </Box>
              {transaction.posting_date && (
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="textSecondary">
                    Posting Date
                  </Typography>
                  <Typography variant="body2" fontWeight="medium">
                    {format(new Date(transaction.posting_date), 'MMM d, yyyy')}
                  </Typography>
                </Box>
              )}
              <Box display="flex" justifyContent="space-between">
                <Typography variant="body2" color="textSecondary">
                  Entry Type
                </Typography>
                <Typography variant="body2" fontWeight="medium">
                  {transaction.entry_type || 'Standard'}
                </Typography>
              </Box>
              <Box display="flex" justifyContent="space-between">
                <Typography variant="body2" color="textSecondary">
                  Total Amount
                </Typography>
                <Typography variant="h6" color="primary">
                  ${totalAmount.toFixed(2)}
                </Typography>
              </Box>
            </Stack>
          </Box>

          <Divider />

          {/* Description & Memo */}
          <Box>
            <Typography variant="overline" color="textSecondary" gutterBottom>
              Description
            </Typography>
            <Typography variant="body1" gutterBottom>
              {transaction.description}
            </Typography>
            {transaction.memo && (
              <>
                <Typography variant="overline" color="textSecondary" gutterBottom sx={{ mt: 2 }}>
                  Memo
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  {transaction.memo}
                </Typography>
              </>
            )}
            {transaction.notes && (
              <>
                <Typography variant="overline" color="textSecondary" gutterBottom sx={{ mt: 2 }}>
                  Notes
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  {transaction.notes}
                </Typography>
              </>
            )}
          </Box>

          <Divider />

          {/* Distributions */}
          <Box>
            <Typography variant="overline" color="textSecondary" gutterBottom>
              Distributions ({transaction.distributions.length})
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Account</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Flow</TableCell>
                    <TableCell align="right">Amount</TableCell>
                    <TableCell>Dr/Cr</TableCell>
                    <TableCell>Envelope</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {transaction.distributions.map((dist, index) => (
                    <TableRow key={dist.distribution_id || index}>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {dist.account_id}
                        </Typography>
                        {dist.description && (
                          <Typography variant="caption" color="textSecondary" display="block">
                            {dist.description}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip label={dist.account_type} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={dist.flow_direction}
                          size="small"
                          color={dist.flow_direction === 'from' ? 'error' : 'success'}
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight="bold">
                          ${dist.amount.toFixed(2)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={dist.debit_credit}
                          size="small"
                          color={dist.debit_credit === 'Dr' ? 'primary' : 'secondary'}
                        />
                      </TableCell>
                      <TableCell>
                        {dist.budget_envelope_id && (
                          <Chip
                            label={`Budget: ${dist.budget_envelope_id}`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                        {dist.payment_envelope_id && (
                          <Chip
                            label={`Payment: ${dist.payment_envelope_id}`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                        {!dist.budget_envelope_id && !dist.payment_envelope_id && (
                          <Typography variant="caption" color="textSecondary">
                            —
                          </Typography>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>

          {/* Metadata */}
          {(transaction.created_by || transaction.created_at || transaction.updated_at) && (
            <>
              <Divider />
              <Box>
                <Typography variant="overline" color="textSecondary" gutterBottom>
                  Metadata
                </Typography>
                <Stack spacing={1}>
                  {transaction.created_by && (
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="caption" color="textSecondary">
                        Created By
                      </Typography>
                      <Typography variant="caption">
                        {transaction.created_by}
                      </Typography>
                    </Box>
                  )}
                  {transaction.created_at && (
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="caption" color="textSecondary">
                        Created At
                      </Typography>
                      <Typography variant="caption">
                        {format(new Date(transaction.created_at), 'MMM d, yyyy h:mm a')}
                      </Typography>
                    </Box>
                  )}
                  {transaction.updated_at && (
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="caption" color="textSecondary">
                        Updated At
                      </Typography>
                      <Typography variant="caption">
                        {format(new Date(transaction.updated_at), 'MMM d, yyyy h:mm a')}
                      </Typography>
                    </Box>
                  )}
                </Stack>
              </Box>
            </>
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}
