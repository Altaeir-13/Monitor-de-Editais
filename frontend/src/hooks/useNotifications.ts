import { useQuery } from '@tanstack/react-query';
import { getNotifications } from '../services/api';

/**
 * Fetches notifications for the authenticated user.
 */
export function useNotifications(skip = 0, limit = 50) {
  return useQuery({
    queryKey: ['notifications', skip, limit],
    queryFn: () => getNotifications(skip, limit),
  });
}
