// React Query hooks for envelopes

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { envelopesApi } from '../api/client';

export function useBudgetEnvelopes(activeOnly: boolean = true) {
  return useQuery({
    queryKey: ['envelopes', 'budget', activeOnly],
    queryFn: async () => {
      const { data } = await envelopesApi.getBudget(activeOnly);
      return data;
    },
  });
}

export function usePaymentEnvelopes(activeOnly: boolean = true) {
  return useQuery({
    queryKey: ['envelopes', 'payment', activeOnly],
    queryFn: async () => {
      const { data } = await envelopesApi.getPayment(activeOnly);
      return data;
    },
  });
}

export function useCreateBudgetEnvelope() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (envelope: any) => {
      const { data } = await envelopesApi.createBudget(envelope);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['envelopes'] });
    },
  });
}

export function useUpdateBudgetEnvelope() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, envelope }: { id: string; envelope: any }) => {
      const { data } = await envelopesApi.updateBudget(id, envelope);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['envelopes'] });
    },
  });
}

export function useDeleteBudgetEnvelope() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await envelopesApi.deleteBudget(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['envelopes'] });
    },
  });
}

export function useCreatePaymentEnvelope() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (envelope: any) => {
      const { data } = await envelopesApi.createPayment(envelope);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['envelopes'] });
    },
  });
}

export function useUpdatePaymentEnvelope() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, envelope }: { id: string; envelope: any }) => {
      const { data } = await envelopesApi.updatePayment(id, envelope);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['envelopes'] });
    },
  });
}

export function useDeletePaymentEnvelope() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await envelopesApi.deletePayment(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['envelopes'] });
    },
  });
}

export function useAllocateEnvelopes() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      sourceAccountId,
      allocationDate,
      periodLabel,
    }: {
      sourceAccountId: string;
      allocationDate: string;
      periodLabel: string;
    }) => {
      const { data } = await envelopesApi.allocate(
        sourceAccountId,
        allocationDate,
        periodLabel
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['envelopes'] });
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
    },
  });
}
