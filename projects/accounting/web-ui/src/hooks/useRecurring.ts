// React Query hooks for recurring templates

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { recurringApi } from '../api/client';

export function useRecurringTemplates(activeOnly: boolean = true) {
  return useQuery({
    queryKey: ['recurring-templates', activeOnly],
    queryFn: async () => {
      const { data } = await recurringApi.getAll(activeOnly);
      return data;
    },
  });
}

export function useUpdateRecurringTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, template }: { id: string; template: any }) => {
      const { data } = await recurringApi.update(id, template);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recurring-templates'] });
    },
  });
}

export function useDeleteRecurringTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await recurringApi.delete(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recurring-templates'] });
    },
  });
}

export function useToggleTemplateActive() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await recurringApi.toggleActive(id);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recurring-templates'] });
    },
  });
}

export function useExpandTemplates() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      startDate,
      endDate,
      autoPost,
    }: {
      startDate: string;
      endDate: string;
      autoPost: boolean;
    }) => {
      const { data} = await recurringApi.expand(startDate, endDate, autoPost);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
    },
  });
}
