import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getAdminInstitutions,
  createAdminInstitution,
  updateAdminInstitution,
  deleteAdminInstitution,
} from '../services/api';
import type { InstitutionCreate, InstitutionUpdate } from '../services/api';

export function useInstitutions(skip = 0, limit = 20) {
  return useQuery({
    queryKey: ['admin-institutions', skip, limit],
    queryFn: () => getAdminInstitutions(skip, limit),
  });
}

export function useCreateInstitution() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: InstitutionCreate) => createAdminInstitution(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-institutions'] });
    },
  });
}

export function useUpdateInstitution() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: InstitutionUpdate }) =>
      updateAdminInstitution(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-institutions'] });
    },
  });
}

export function useDeleteInstitution() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteAdminInstitution(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-institutions'] });
    },
  });
}
