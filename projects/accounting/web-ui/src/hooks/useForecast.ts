// React Query hooks for forecasting

import { useQuery } from '@tanstack/react-query';
import { forecastApi } from '../api/client';

export function useForecastAccount(accountId: string, targetDate: string) {
  return useQuery({
    queryKey: ['forecast', 'account', accountId, targetDate],
    queryFn: async () => {
      const { data } = await forecastApi.account(accountId, targetDate);
      return data;
    },
    enabled: !!accountId && !!targetDate,
  });
}

export function useForecastEnvelope(envelopeId: string, targetDate: string) {
  return useQuery({
    queryKey: ['forecast', 'envelope', envelopeId, targetDate],
    queryFn: async () => {
      const { data } = await forecastApi.envelope(envelopeId, targetDate);
      return data;
    },
    enabled: !!envelopeId && !!targetDate,
  });
}
