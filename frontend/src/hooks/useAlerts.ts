import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getAlerts,
  createAlert,
  updateAlert,
  deleteAlert,
} from '../services/api';
import type { UserAlertCreate, UserAlertUpdate } from '../services/api';

/**
 * Fetches all alerts for the authenticated user.
 */
export function useAlerts() {
  return useQuery({
    queryKey: ['alerts'],
    queryFn: () => getAlerts(),
  });
}

/**
 * Creates a new alert and invalidates the alerts cache.
 */
export function useCreateAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: UserAlertCreate) => createAlert(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });
}

/**
 * Updates an alert and invalidates the alerts cache.
 */
export function useUpdateAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UserAlertUpdate }) =>
      updateAlert(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });
}

/**
 * Soft-deletes an alert and invalidates the alerts cache.
 */
export function useDeleteAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteAlert(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });
}
