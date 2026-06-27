import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getAdminSources,
  createAdminSource,
  updateAdminSource,
  deleteAdminSource,
  runAdminCrawler,
} from '../services/api';
import type { MonitoredSourceCreate, MonitoredSourceUpdate } from '../services/api';

export function useSources(skip = 0, limit = 20) {
  return useQuery({
    queryKey: ['admin-sources', skip, limit],
    queryFn: () => getAdminSources(skip, limit),
  });
}

export function useCreateSource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: MonitoredSourceCreate) => createAdminSource(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-sources'] });
    },
  });
}

export function useUpdateSource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: MonitoredSourceUpdate }) =>
      updateAdminSource(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-sources'] });
    },
  });
}

export function useDeleteSource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteAdminSource(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-sources'] });
    },
  });
}

export function useRunCrawler() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => runAdminCrawler(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-sources'] });
    },
  });
}
