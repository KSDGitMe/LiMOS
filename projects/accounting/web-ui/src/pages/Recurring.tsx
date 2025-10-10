import { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
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
  Alert,
  CircularProgress,
  FormControlLabel,
  Checkbox,
} from '@mui/material';
import {
  PlayArrow as PlayArrowIcon,
  Pause as PauseIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  CalendarMonth as CalendarIcon,
} from '@mui/icons-material';
import { useForm, Controller } from 'react-hook-form';
import toast from 'react-hot-toast';
import { useRecurringTemplates, useExpandTemplates, useToggleTemplateActive, useDeleteRecurringTemplate } from '../hooks/useRecurring';
import { format, addMonths, parseISO } from 'date-fns';
import CreateTemplateDialog from '../components/recurring/CreateTemplateDialog';
import EditTemplateDialog from '../components/recurring/EditTemplateDialog';
import ConfirmDialog from '../components/common/ConfirmDialog';
import type { RecurringJournalEntry } from '../types';

interface ExpandForm {
  startDate: string;
  endDate: string;
  autoPost: boolean;
}

export default function Recurring() {
  const { data: templates = [], isLoading } = useRecurringTemplates(false); // Show all templates
  const [expandOpen, setExpandOpen] = useState(false);
  const [createTemplateOpen, setCreateTemplateOpen] = useState(false);
  const [editTemplateOpen, setEditTemplateOpen] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [templateToEdit, setTemplateToEdit] = useState<RecurringJournalEntry | null>(null);
  const [templateToDelete, setTemplateToDelete] = useState<string | null>(null);

  const { control, handleSubmit, reset, watch } = useForm<ExpandForm>({
    defaultValues: {
      startDate: format(new Date(), 'yyyy-MM-dd'),
      endDate: format(addMonths(new Date(), 3), 'yyyy-MM-dd'),
      autoPost: true,
    },
  });

  const expandTemplates = useExpandTemplates();
  const toggleActive = useToggleTemplateActive();
  const deleteTemplate = useDeleteRecurringTemplate();

  const handleToggleActive = async (id: string) => {
    try {
      await toggleActive.mutateAsync(id);
      const template = templates.find(t => t.recurring_entry_id === id);
      const newStatus = template?.is_active ? 'paused' : 'activated';
      toast.success(`Template ${newStatus} successfully!`);
    } catch (error) {
      toast.error('Failed to update template status');
    }
  };

  const handleEditClick = (template: RecurringJournalEntry) => {
    setTemplateToEdit(template);
    setEditTemplateOpen(true);
  };

  const handleDeleteClick = (id: string) => {
    setTemplateToDelete(id);
    setDeleteConfirmOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!templateToDelete) return;

    try {
      await deleteTemplate.mutateAsync(templateToDelete);
      toast.success('Template deleted successfully!');
      setDeleteConfirmOpen(false);
      setTemplateToDelete(null);
    } catch (error) {
      toast.error('Failed to delete template');
    }
  };

  const onExpand = async (data: ExpandForm) => {
    try {
      const result = await expandTemplates.mutateAsync({
        startDate: data.startDate,
        endDate: data.endDate,
        autoPost: data.autoPost,
      });
      toast.success(`Successfully generated ${result?.length || 0} transactions!`);
      reset();
      setExpandOpen(false);
    } catch (error) {
      console.error('Expand error:', error);
      toast.error('Failed to expand templates');
    }
  };

  const getFrequencyLabel = (freq: string) => {
    const labels: Record<string, string> = {
      biweekly: 'Every 2 weeks',
      monthly: 'Monthly',
      quarterly: 'Quarterly',
      semiannually: 'Semi-annually',
      annually: 'Annually',
    };
    return labels[freq] || freq;
  };

  const getNextOccurrence = (template: any) => {
    // Calculate next occurrence based on start_date and frequency
    const start = parseISO(template.start_date);
    const now = new Date();

    if (start > now) {
      return format(start, 'MMM d, yyyy');
    }

    // For active templates, show estimated next occurrence
    // This is simplified - real calculation would track last expansion
    switch (template.frequency) {
      case 'biweekly':
        return format(addMonths(now, 0.5), 'MMM d, yyyy');
      case 'monthly':
        return format(addMonths(now, 1), 'MMM d, yyyy');
      case 'quarterly':
        return format(addMonths(now, 3), 'MMM d, yyyy');
      case 'semiannually':
        return format(addMonths(now, 6), 'MMM d, yyyy');
      case 'annually':
        return format(addMonths(now, 12), 'MMM d, yyyy');
      default:
        return 'Unknown';
    }
  };

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
        <Typography variant="h4">Recurring Templates</Typography>
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            onClick={() => setCreateTemplateOpen(true)}
          >
            Create Template
          </Button>
          <Button
            variant="contained"
            startIcon={<CalendarIcon />}
            onClick={() => setExpandOpen(true)}
          >
            Expand Templates
          </Button>
        </Stack>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        <strong>How it works:</strong> Recurring templates automatically generate transactions based on their frequency.
        Use "Expand Templates" to generate transactions for a specific period.
      </Alert>

      {/* Summary Cards */}
      <Grid container spacing={2} mb={3}>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Total Templates
              </Typography>
              <Typography variant="h4">
                {templates.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Active Templates
              </Typography>
              <Typography variant="h4" color="success.main">
                {templates.filter(t => t.is_active).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom variant="body2">
                Inactive Templates
              </Typography>
              <Typography variant="h4" color="textSecondary">
                {templates.filter(t => !t.is_active).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Templates Table */}
      {templates.length === 0 ? (
        <Alert severity="info">
          No recurring templates found. Create recurring templates via the CLI to see them here.
        </Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Template Name</TableCell>
                <TableCell>Frequency</TableCell>
                <TableCell>Start Date</TableCell>
                <TableCell>Next Occurrence</TableCell>
                <TableCell>Amount</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {templates.map((template) => {
                const fromDist = template.distribution_template.find(d => d.flow_direction === 'from');
                const toDist = template.distribution_template.find(d => d.flow_direction === 'to');
                const amount = fromDist?.amount || 0;

                return (
                  <TableRow key={template.recurring_entry_id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {template.description}
                      </Typography>
                      {template.memo && (
                        <Typography variant="caption" color="textSecondary" display="block">
                          {template.memo}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={getFrequencyLabel(template.frequency)}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      {format(parseISO(template.start_date), 'MMM d, yyyy')}
                    </TableCell>
                    <TableCell>
                      {template.is_active ? (
                        <Typography variant="body2" color="primary">
                          {getNextOccurrence(template)}
                        </Typography>
                      ) : (
                        <Typography variant="body2" color="textSecondary">
                          —
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontWeight="bold">
                        ${amount.toFixed(2)}
                      </Typography>
                      <Typography variant="caption" color="textSecondary" display="block">
                        {fromDist?.account_id} → {toDist?.account_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={template.is_active ? 'Active' : 'Inactive'}
                        size="small"
                        color={template.is_active ? 'success' : 'default'}
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Stack direction="row" spacing={0.5} justifyContent="center">
                        <IconButton
                          size="small"
                          title={template.is_active ? 'Pause template' : 'Activate template'}
                          onClick={() => handleToggleActive(template.recurring_entry_id)}
                          disabled={toggleActive.isPending}
                        >
                          {template.is_active ? (
                            <PauseIcon fontSize="small" />
                          ) : (
                            <PlayArrowIcon fontSize="small" />
                          )}
                        </IconButton>
                        <IconButton
                          size="small"
                          title="Edit template"
                          onClick={() => handleEditClick(template)}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          title="Delete template"
                          onClick={() => handleDeleteClick(template.recurring_entry_id)}
                          disabled={deleteTemplate.isPending}
                          color="error"
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

      {/* Expand Templates Dialog */}
      <Dialog open={expandOpen} onClose={() => setExpandOpen(false)} maxWidth="sm" fullWidth>
        <form onSubmit={handleSubmit(onExpand)}>
          <DialogTitle>Expand Recurring Templates</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <Controller
                name="startDate"
                control={control}
                rules={{ required: 'Start date is required' }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Start Date"
                    type="date"
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                  />
                )}
              />

              <Controller
                name="endDate"
                control={control}
                rules={{ required: 'End date is required' }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="End Date"
                    type="date"
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                  />
                )}
              />

              <Controller
                name="autoPost"
                control={control}
                render={({ field }) => (
                  <FormControlLabel
                    control={
                      <Checkbox
                        {...field}
                        checked={field.value}
                      />
                    }
                    label="Automatically post generated transactions"
                  />
                )}
              />

              <Alert severity="info">
                This will generate transactions from all active recurring templates
                between the selected dates. Transactions dated today or in the past will be posted,
                future transactions will be saved as draft.
              </Alert>

              {expandTemplates.isSuccess && (
                <Alert severity="success">
                  Successfully expanded templates! Generated transactions are now visible in the Transactions page.
                </Alert>
              )}

              {expandTemplates.isError && (
                <Alert severity="error">
                  Failed to expand templates. Please try again.
                </Alert>
              )}
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setExpandOpen(false)}>Cancel</Button>
            <Button
              type="submit"
              variant="contained"
              disabled={expandTemplates.isPending}
            >
              {expandTemplates.isPending ? 'Expanding...' : 'Expand Templates'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Create Template Dialog */}
      <CreateTemplateDialog
        open={createTemplateOpen}
        onClose={() => setCreateTemplateOpen(false)}
      />

      {/* Edit Template Dialog */}
      <EditTemplateDialog
        open={editTemplateOpen}
        onClose={() => {
          setEditTemplateOpen(false);
          setTemplateToEdit(null);
        }}
        template={templateToEdit}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteConfirmOpen}
        title="Delete Template"
        message="Are you sure you want to delete this recurring template? This action cannot be undone."
        confirmLabel="Delete"
        confirmColor="error"
        onConfirm={handleDeleteConfirm}
        onCancel={() => {
          setDeleteConfirmOpen(false);
          setTemplateToDelete(null);
        }}
        isLoading={deleteTemplate.isPending}
      />
    </Box>
  );
}
