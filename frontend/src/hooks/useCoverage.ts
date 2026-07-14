import { useQuery } from '@tanstack/react-query';

import {
  getAdminCoverage,
  getAdminCoverageInstitutions,
  getAdminCoverageRegions,
} from '../services/api';
import type {
  CoverageInstitutionFilters,
  CoverageSummaryFilters,
} from '../services/api';

const coverageKeys = {
  summary: (filters: CoverageSummaryFilters) => ['admin-coverage', 'summary', filters] as const,
  regions: ['admin-coverage', 'regions'] as const,
  institutions: (filters: CoverageInstitutionFilters) =>
    ['admin-coverage', 'institutions', filters] as const,
};

export function useCoverage(filters: CoverageSummaryFilters = {}) {
  return useQuery({
    queryKey: coverageKeys.summary(filters),
    queryFn: () => getAdminCoverage(filters),
  });
}

export function useCoverageRegions() {
  return useQuery({
    queryKey: coverageKeys.regions,
    queryFn: getAdminCoverageRegions,
  });
}

export function useCoverageInstitutions(filters: CoverageInstitutionFilters = {}) {
  return useQuery({
    queryKey: coverageKeys.institutions(filters),
    queryFn: () => getAdminCoverageInstitutions(filters),
  });
}
