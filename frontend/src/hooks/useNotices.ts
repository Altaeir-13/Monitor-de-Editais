import { useQuery } from '@tanstack/react-query';
import { getNotices, getNoticeById } from '../services/api';
import type { NoticesFilters } from '../services/api';

/**
 * Fetches a paginated, filtered list of active notices.
 * Re-fetches whenever filters change.
 */
export function useNotices(filters: NoticesFilters = {}) {
  return useQuery({
    queryKey: ['notices', filters],
    queryFn: () => getNotices(filters),
  });
}

/**
 * Fetches a single notice by ID with institution details.
 */
export function useNotice(id: number) {
  return useQuery({
    queryKey: ['notice', id],
    queryFn: () => getNoticeById(id),
    enabled: !!id,
  });
}
