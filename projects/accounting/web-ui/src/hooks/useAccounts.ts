// React Query hooks for accounts

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { accountsApi } from '../api/client';
import type { ChartOfAccounts } from '../types';

export function useAccounts(params?: { account_type?: string; is_active?: boolean }) {
  return useQuery({
    queryKey: ['accounts', params],
    queryFn: async () => {
      const { data } = await accountsApi.getAll(params);
      return data;
    },
  });
}

export function useAccount(id: string) {
  return useQuery({
    queryKey: ['account', id],
    queryFn: async () => {
      const { data } = await accountsApi.getById(id);
      return data;
    },
    enabled: !!id,
  });
}

export function useAccountView(id: string, asOfDate?: string) {
  return useQuery({
    queryKey: ['account-view', id, asOfDate],
    queryFn: async () => {
      const { data } = await accountsApi.getView(id, asOfDate);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (account: Omit<ChartOfAccounts, 'account_id'>) => {
      const { data } = await accountsApi.create(account);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
    },
  });
}

export function useUpdateAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, account }: { id: string; account: ChartOfAccounts }) => {
      const { data } = await accountsApi.update(id, account);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      queryClient.invalidateQueries({ queryKey: ['account'] });
      queryClient.invalidateQueries({ queryKey: ['account-view'] });
    },
  });
}
