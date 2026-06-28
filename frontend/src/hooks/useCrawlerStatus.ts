import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  getCrawlerRuns,
  getCrawlerSourcesStatus,
  getCrawlerStatus,
  runAdminCrawler,
  runAdminCrawlerSource,
} from '../services/api';

const crawlerQueryKeys = [
  ['crawler-status'],
  ['crawler-sources-status'],
  ['crawler-runs'],
  ['admin-sources'],
];

function invalidateCrawlerQueries(queryClient: ReturnType<typeof useQueryClient>) {
  crawlerQueryKeys.forEach((queryKey) => {
    queryClient.invalidateQueries({ queryKey });
  });
}

export function useCrawlerStatus() {
  return useQuery({
    queryKey: ['crawler-status'],
    queryFn: getCrawlerStatus,
  });
}

export function useCrawlerSourcesStatus() {
  return useQuery({
    queryKey: ['crawler-sources-status'],
    queryFn: getCrawlerSourcesStatus,
  });
}

export function useCrawlerRuns(skip = 0, limit = 20) {
  return useQuery({
    queryKey: ['crawler-runs', skip, limit],
    queryFn: () => getCrawlerRuns(skip, limit),
  });
}

export function useRunCrawlerOperational() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: runAdminCrawler,
    onSuccess: () => invalidateCrawlerQueries(queryClient),
  });
}

export function useRunCrawlerSource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sourceId: number) => runAdminCrawlerSource(sourceId),
    onSuccess: () => invalidateCrawlerQueries(queryClient),
  });
}
