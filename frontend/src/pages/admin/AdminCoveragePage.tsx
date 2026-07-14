import { useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import {
  Building2,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Database,
  Filter,
  Info,
  Loader2,
  RefreshCw,
} from 'lucide-react';

import EmptyState from '../../components/ui/EmptyState';
import ErrorMessage from '../../components/ui/ErrorMessage';
import Spinner from '../../components/ui/Spinner';
import {
  useCoverage,
  useCoverageInstitutions,
  useCoverageRegions,
} from '../../hooks/useCoverage';
import type {
  CoverageInstitutionFilters,
  CoverageInstitutionItem,
  CoverageResponse,
  CoverageStatus,
} from '../../services/api';

const PAGE_SIZE = 25;
const NUMBER_FORMAT = new Intl.NumberFormat('pt-BR');

const STATUS_OPTIONS: Array<{ value: CoverageStatus; label: string }> = [
  { value: 'verified', label: 'Verificada' },
  { value: 'partial', label: 'Parcial' },
  { value: 'manual_review', label: 'Revisão manual' },
  { value: 'source_not_found', label: 'Fonte não encontrada' },
  { value: 'temporarily_unavailable', label: 'Temporariamente indisponível' },
  { value: 'unsupported', label: 'Não suportada' },
  { value: 'inactive', label: 'Inativa' },
];

const STATUS_LABELS: Record<string, string> = Object.fromEntries(
  STATUS_OPTIONS.map((option) => [option.value, option.label])
);

const ELIGIBILITY_OPTIONS = [
  { value: 'included', label: 'Incluída pelo Censo 2024' },
  { value: 'included_pending_activation', label: 'Incluída pós-Censo, aguardando ativação' },
  { value: 'excluded_inactive', label: 'Excluída por inatividade' },
  { value: 'excluded_scope_manual_review', label: 'Excluída do escopo para revisão manual' },
];

const ELIGIBILITY_LABELS: Record<string, string> = Object.fromEntries(
  ELIGIBILITY_OPTIONS.map((option) => [option.value, option.label])
);

interface FilterFormState {
  region: string;
  state: string;
  administrative_category_code: string;
  academic_organization_code: string;
  eligibility_status: string;
  coverage_status: string;
  verification_status: string;
  institution_active: string;
  source_active: string;
  has_source: string;
  manual_review: string;
}

const EMPTY_FILTERS: FilterFormState = {
  region: '',
  state: '',
  administrative_category_code: '',
  academic_organization_code: '',
  eligibility_status: '',
  coverage_status: '',
  verification_status: '',
  institution_active: '',
  source_active: '',
  has_source: '',
  manual_review: '',
};

function formatNumber(value: number): string {
  return NUMBER_FORMAT.format(value);
}

function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status.replaceAll('_', ' ');
}

function statusBadgeClass(status: string): string {
  if (status === 'verified') return 'app-badge-success';
  if (status === 'partial' || status === 'temporarily_unavailable') {
    return 'app-badge-warning';
  }
  if (status === 'manual_review') return 'app-badge-info';
  if (status === 'source_not_found' || status === 'unsupported') {
    return 'app-badge-danger';
  }
  return 'app-badge-muted';
}

function eligibilityBadgeClass(status: string): string {
  if (status.startsWith('included')) return 'app-badge-success';
  if (status.includes('manual_review')) return 'app-badge-warning';
  return 'app-badge-muted';
}

function parseBoolean(value: string): boolean | undefined {
  if (value === 'true') return true;
  if (value === 'false') return false;
  return undefined;
}

function buildInstitutionFilters(
  form: FilterFormState,
  page: number
): CoverageInstitutionFilters {
  const filters: CoverageInstitutionFilters = {
    skip: page * PAGE_SIZE,
    limit: PAGE_SIZE,
  };

  if (form.region) filters.region = form.region;
  if (form.state) filters.state = form.state;
  if (form.administrative_category_code) {
    filters.administrative_category_code = Number(form.administrative_category_code);
  }
  if (form.academic_organization_code) {
    filters.academic_organization_code = Number(form.academic_organization_code);
  }
  if (form.eligibility_status) filters.eligibility_status = form.eligibility_status;
  if (form.coverage_status) {
    filters.coverage_status = form.coverage_status as CoverageStatus;
  }
  if (form.verification_status) {
    filters.verification_status = form.verification_status as CoverageStatus;
  }

  const institutionActive = parseBoolean(form.institution_active);
  const sourceActive = parseBoolean(form.source_active);
  const hasSource = parseBoolean(form.has_source);
  const manualReview = parseBoolean(form.manual_review);
  if (institutionActive !== undefined) filters.institution_active = institutionActive;
  if (sourceActive !== undefined) filters.source_active = sourceActive;
  if (hasSource !== undefined) filters.has_source = hasSource;
  if (manualReview !== undefined) filters.manual_review = manualReview;

  return filters;
}

function formatAuditDate(value: string | null): string {
  if (!value) return 'Nenhuma auditoria registrada';
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return value.split('-').reverse().join('/');
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

interface MetricCardProps {
  label: string;
  value: number;
  description: string;
}

function MetricCard({ label, value, description }: MetricCardProps) {
  return (
    <div className="glass-panel rounded-2xl p-5">
      <p className="text-sm font-medium text-gray-500">{label}</p>
      <p className="mt-2 text-3xl font-bold text-gray-900">{formatNumber(value)}</p>
      <p className="mt-2 text-xs leading-relaxed text-gray-500">{description}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`app-badge ${statusBadgeClass(status)}`}>
      {statusLabel(status)}
    </span>
  );
}

function InstitutionRow({ item }: { item: CoverageInstitutionItem }) {
  return (
    <tr className={item.eligibility_status.startsWith('included') ? '' : 'opacity-70'}>
      <td className="px-5 py-4 align-top">
        <p className="font-semibold text-gray-900">{item.initials}</p>
        <p className="mt-1 max-w-xs text-sm text-gray-600">{item.official_name}</p>
        <p className="mt-1 text-xs text-gray-400">Código oficial: {item.official_code}</p>
      </td>
      <td className="px-5 py-4 align-top">
        <p className="text-sm font-medium text-gray-900">{item.state}</p>
        <p className="mt-1 text-xs text-gray-500">{item.region}</p>
      </td>
      <td className="px-5 py-4 align-top">
        <p className="text-sm text-gray-900">
          {item.administrative_category ?? 'Categoria não informada'}
        </p>
        <p className="mt-2 text-xs text-gray-500">
          {item.academic_organization ?? 'Organização não informada'}
        </p>
      </td>
      <td className="px-5 py-4 align-top">
        <span
          className={`app-badge ${eligibilityBadgeClass(item.eligibility_status)}`}
          title={item.eligibility_reason ?? undefined}
        >
          {ELIGIBILITY_LABELS[item.eligibility_status] ?? item.eligibility_status}
        </span>
      </td>
      <td className="px-5 py-4 align-top">
        <div title={item.coverage_notes ?? undefined}>
          <StatusBadge status={item.coverage_status} />
        </div>
        <p className="mt-2 text-xs text-gray-500">
          {item.source_count} {item.source_count === 1 ? 'fonte' : 'fontes'}
        </p>
        {item.source_statuses.length > 0 && (
          <div className="mt-2 flex max-w-xs flex-wrap gap-1">
            {item.source_statuses.map((status, index) => (
              <StatusBadge key={`${status}-${index}`} status={status} />
            ))}
          </div>
        )}
      </td>
      <td className="px-5 py-4 align-top">
        <div className="flex max-w-sm flex-wrap gap-1">
          <span className={`app-badge ${item.registered ? 'app-badge-primary' : 'app-badge-muted'}`}>
            {item.registered ? 'Cadastrada' : 'Não cadastrada'}
          </span>
          {item.registered && (
            <span className={`app-badge ${item.institution_active ? 'app-badge-success' : 'app-badge-muted'}`}>
              {item.institution_active ? 'Instituição ativa' : 'Instituição inativa'}
            </span>
          )}
          <span className={`app-badge ${item.has_source && item.source_active ? 'app-badge-success' : 'app-badge-muted'}`}>
            {item.has_source ? (item.source_active ? 'Fonte ativa' : 'Fonte inativa') : 'Sem fonte cadastrada'}
          </span>
          <span className={`app-badge ${item.capture_validated ? 'app-badge-success' : 'app-badge-muted'}`}>
            {item.capture_validated ? 'Captura validada' : 'Captura não validada'}
          </span>
          <span className={`app-badge ${item.active_monitoring ? 'app-badge-success' : 'app-badge-muted'}`}>
            {item.active_monitoring ? 'Monitoramento ativo' : 'Monitoramento inativo'}
          </span>
        </div>
      </td>
    </tr>
  );
}

function SummaryMetrics({ summary }: { summary: CoverageResponse }) {
  return (
    <div className="space-y-8">
      <section>
        <div className="mb-3 flex items-center gap-2">
          <Building2 size={18} className="text-primary-600" />
          <h2 className="text-lg font-semibold text-gray-900">Escopo auditável</h2>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            label="Inventário institucional"
            value={summary.inventory_total}
            description="Inclui registros preservados para auditoria, mesmo quando excluídos do alvo."
          />
          <MetricCard
            label="Alvo operacional elegível"
            value={summary.eligible_target_total}
            description="Somente instituições cuja elegibilidade começa com included."
          />
          <MetricCard
            label="Fontes no inventário"
            value={summary.mapped_source_total_inventory}
            description="Inclui a fonte histórica ligada a uma instituição excluída."
          />
          <MetricCard
            label="Fontes elegíveis"
            value={summary.mapped_source_total_eligible}
            description="Fontes associadas às instituições do alvo operacional."
          />
        </div>
      </section>

      <section>
        <div className="mb-3 flex items-center gap-2">
          <Database size={18} className="text-primary-600" />
          <h2 className="text-lg font-semibold text-gray-900">Situação das fontes</h2>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <MetricCard
            label="Instituições com fonte"
            value={summary.institutions_with_source}
            description="Instituições elegíveis com ao menos uma fonte oficial mapeada."
          />
          <MetricCard
            label="Instituições sem fonte"
            value={summary.institutions_without_source}
            description="Pendências preservadas individualmente, sem desaparecer dos totais."
          />
          <MetricCard
            label="Instituições com fonte verificada"
            value={summary.verified_source_institutions}
            description="Instituições com fonte verificada; isso ainda não comprova captura."
          />
          <MetricCard
            label="Instituições com cobertura parcial"
            value={summary.partial_source_institutions}
            description="Instituições cuja estrutura ou aderência ainda precisa de validação."
          />
          <MetricCard
            label="Revisão manual"
            value={summary.manual_review_institutions}
            description="Casos que exigem decisão humana de fonte ou de escopo."
          />
          <MetricCard
            label="Fonte não encontrada"
            value={summary.source_not_found_institutions}
            description="Instituições elegíveis sem fonte oficial identificada nesta versão."
          />
        </div>
      </section>

      <section>
        <div className="mb-3 flex items-center gap-2">
          <CheckCircle2 size={18} className="text-primary-600" />
          <h2 className="text-lg font-semibold text-gray-900">Validação operacional</h2>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <MetricCard
            label="Capturas validadas"
            value={summary.validated_capture_total}
            description="Instituições com evidência registrada de extração de item válido."
          />
          <MetricCard
            label="Monitoramento ativo"
            value={summary.active_monitoring_total}
            description="Instituições com fonte ativa e execução operacional recente."
          />
        </div>
      </section>
    </div>
  );
}

export default function AdminCoveragePage() {
  const [draftFilters, setDraftFilters] = useState<FilterFormState>({ ...EMPTY_FILTERS });
  const [appliedFilters, setAppliedFilters] = useState<FilterFormState>({ ...EMPTY_FILTERS });
  const [filterError, setFilterError] = useState('');
  const [page, setPage] = useState(0);

  const institutionFilters = useMemo(
    () => buildInstitutionFilters(appliedFilters, page),
    [appliedFilters, page]
  );

  const summaryQuery = useCoverage();
  const regionsQuery = useCoverageRegions();
  const institutionsQuery = useCoverageInstitutions(institutionFilters);

  const updateFilter = (field: keyof FilterFormState, value: string) => {
    setDraftFilters((current) => ({ ...current, [field]: value }));
  };

  const handleApplyFilters = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const state = draftFilters.state.trim().toUpperCase();
    if (state && state.length !== 2) {
      setFilterError('Informe a UF com exatamente duas letras.');
      return;
    }

    setFilterError('');
    setAppliedFilters({ ...draftFilters, state });
    setDraftFilters((current) => ({ ...current, state }));
    setPage(0);
  };

  const handleClearFilters = () => {
    setDraftFilters({ ...EMPTY_FILTERS });
    setAppliedFilters({ ...EMPTY_FILTERS });
    setFilterError('');
    setPage(0);
  };

  if (summaryQuery.isLoading || regionsQuery.isLoading) {
    return <Spinner text="Carregando cobertura institucional..." />;
  }

  if (summaryQuery.isError || regionsQuery.isError) {
    return (
      <ErrorMessage
        message="Não foi possível carregar as métricas nacionais de cobertura."
        onRetry={() => {
          void summaryQuery.refetch();
          void regionsQuery.refetch();
        }}
      />
    );
  }

  const summary = summaryQuery.data;
  const regions = regionsQuery.data;
  if (!summary || !regions) {
    return <ErrorMessage message="A API de cobertura não retornou os dados esperados." />;
  }

  const institutionList = institutionsQuery.data;
  const totalPages = Math.max(1, Math.ceil((institutionList?.total ?? 0) / PAGE_SIZE));
  const activeFilterCount = Object.values(appliedFilters).filter(Boolean).length;

  return (
    <div className="space-y-8">
      <header className="glass-panel rounded-2xl p-6 sm:p-8">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">
          Cobertura institucional nacional
        </h1>
        <p className="mt-2 max-w-4xl text-sm leading-relaxed text-gray-600">
          O inventário institucional possui alcance nacional. A cobertura operacional das fontes
          permanece em validação progressiva.
        </p>
        <p className="mt-3 text-xs text-gray-500">
          Última auditoria registrada: {formatAuditDate(summary.last_audit)}
        </p>
      </header>

      <aside className="glass-panel rounded-2xl border-l-4 border-l-primary-500 p-5" role="note">
        <div className="flex items-start gap-3">
          <Info className="mt-0.5 shrink-0 text-primary-600" size={20} />
          <div>
            <h2 className="font-semibold text-gray-900">Como interpretar estes números</h2>
            <ul className="mt-2 grid gap-2 text-sm leading-relaxed text-gray-600 md:grid-cols-2">
              <li>Inventário nacional não significa monitoramento nacional.</li>
              <li>Fonte cadastrada não significa fonte ativa.</li>
              <li><code>verified</code> não significa captura validada.</li>
              <li>Captura validada não significa monitoramento contínuo.</li>
              <li className="md:col-span-2">
                Novas fontes permanecem inativas até uma ativação operacional explícita.
              </li>
            </ul>
          </div>
        </div>
      </aside>

      <SummaryMetrics summary={summary} />

      <section>
        <div className="mb-4">
          <h2 className="text-xl font-bold text-gray-900">Totais por região</h2>
          <p className="mt-1 text-sm text-gray-500">
            Comparação nacional do inventário, das fontes e dos estágios operacionais.
          </p>
        </div>
        <div className="overflow-x-auto glass-panel rounded-2xl">
          <table className="min-w-[1180px] divide-y divide-gray-200">
            <thead>
              <tr>
                {[
                  'Região',
                  'Inventário',
                  'Elegíveis',
                  'Fontes elegíveis',
                  'Com fonte',
                  'Sem fonte',
                  'Verificadas',
                  'Parciais',
                  'Revisão manual',
                  'Não encontrada',
                  'Captura',
                  'Ativo',
                ].map((heading) => (
                  <th
                    key={heading}
                    scope="col"
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                  >
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {regions.map((region) => (
                <tr key={region.key}>
                  <th scope="row" className="px-4 py-4 text-left text-sm font-semibold text-gray-900">
                    {region.label}
                  </th>
                  <td className="px-4 py-4 text-sm text-gray-600">{formatNumber(region.inventory_total)}</td>
                  <td className="px-4 py-4 text-sm text-gray-600">{formatNumber(region.eligible_total)}</td>
                  <td className="px-4 py-4 text-sm text-gray-600">{formatNumber(region.mapped_sources)}</td>
                  <td className="px-4 py-4 text-sm text-gray-600">{formatNumber(region.institutions_with_source)}</td>
                  <td className="px-4 py-4 text-sm text-gray-600">{formatNumber(region.institutions_without_source)}</td>
                  <td className="px-4 py-4 text-sm text-gray-600">{formatNumber(region.verified)}</td>
                  <td className="px-4 py-4 text-sm text-gray-600">{formatNumber(region.partial)}</td>
                  <td className="px-4 py-4 text-sm text-gray-600">{formatNumber(region.manual_review)}</td>
                  <td className="px-4 py-4 text-sm text-gray-600">{formatNumber(region.source_not_found)}</td>
                  <td className="px-4 py-4 text-sm text-gray-600">{formatNumber(region.capture_validated)}</td>
                  <td className="px-4 py-4 text-sm text-gray-600">{formatNumber(region.active_monitoring)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-4">
        <form onSubmit={handleApplyFilters} className="glass-panel rounded-2xl p-5">
          <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <Filter size={18} className="text-primary-600" />
                <h2 className="text-lg font-semibold text-gray-900">Filtrar instituições</h2>
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Os filtros afetam somente a lista abaixo; cards e tabela regional permanecem nacionais.
              </p>
            </div>
            {activeFilterCount > 0 && (
              <span className="app-badge app-badge-primary">
                {activeFilterCount} {activeFilterCount === 1 ? 'filtro aplicado' : 'filtros aplicados'}
              </span>
            )}
          </div>

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <label className="text-sm font-medium text-gray-600">
              Região
              <select
                className="input-field mt-1"
                value={draftFilters.region}
                onChange={(event) => updateFilter('region', event.target.value)}
              >
                <option value="">Todas</option>
                {regions.map((region) => (
                  <option key={region.key} value={region.key}>{region.label}</option>
                ))}
              </select>
            </label>

            <label className="text-sm font-medium text-gray-600">
              UF
              <input
                className="input-field mt-1 uppercase"
                value={draftFilters.state}
                maxLength={2}
                placeholder="Ex.: SP"
                onChange={(event) => updateFilter('state', event.target.value.toUpperCase())}
              />
            </label>

            <label className="text-sm font-medium text-gray-600">
              Categoria administrativa
              <select
                className="input-field mt-1"
                value={draftFilters.administrative_category_code}
                onChange={(event) => updateFilter('administrative_category_code', event.target.value)}
              >
                <option value="">Todas</option>
                {summary.breakdown.administrative_categories.map((item) => (
                  <option key={item.key} value={item.key}>{item.label}</option>
                ))}
              </select>
            </label>

            <label className="text-sm font-medium text-gray-600">
              Organização acadêmica
              <select
                className="input-field mt-1"
                value={draftFilters.academic_organization_code}
                onChange={(event) => updateFilter('academic_organization_code', event.target.value)}
              >
                <option value="">Todas</option>
                {summary.breakdown.academic_organizations.map((item) => (
                  <option key={item.key} value={item.key}>{item.label}</option>
                ))}
              </select>
            </label>

            <label className="text-sm font-medium text-gray-600">
              Elegibilidade
              <select
                className="input-field mt-1"
                value={draftFilters.eligibility_status}
                onChange={(event) => updateFilter('eligibility_status', event.target.value)}
              >
                <option value="">Todas</option>
                {ELIGIBILITY_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </label>

            <label className="text-sm font-medium text-gray-600">
              Cobertura
              <select
                className="input-field mt-1"
                value={draftFilters.coverage_status}
                onChange={(event) => updateFilter('coverage_status', event.target.value)}
              >
                <option value="">Todas</option>
                {STATUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </label>

            <label className="text-sm font-medium text-gray-600">
              Verificação da fonte
              <select
                className="input-field mt-1"
                value={draftFilters.verification_status}
                onChange={(event) => updateFilter('verification_status', event.target.value)}
              >
                <option value="">Todas</option>
                {STATUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </label>

            <label className="text-sm font-medium text-gray-600">
              Instituição ativa
              <select
                className="input-field mt-1"
                value={draftFilters.institution_active}
                onChange={(event) => updateFilter('institution_active', event.target.value)}
              >
                <option value="">Todas</option>
                <option value="true">Ativa</option>
                <option value="false">Inativa</option>
              </select>
            </label>

            <label className="text-sm font-medium text-gray-600">
              Fonte ativa
              <select
                className="input-field mt-1"
                value={draftFilters.source_active}
                onChange={(event) => updateFilter('source_active', event.target.value)}
              >
                <option value="">Todas</option>
                <option value="true">Com fonte ativa</option>
                <option value="false">Sem fonte ativa</option>
              </select>
            </label>

            <label className="text-sm font-medium text-gray-600">
              Possui fonte
              <select
                className="input-field mt-1"
                value={draftFilters.has_source}
                onChange={(event) => updateFilter('has_source', event.target.value)}
              >
                <option value="">Todas</option>
                <option value="true">Com fonte</option>
                <option value="false">Sem fonte</option>
              </select>
            </label>

            <label className="text-sm font-medium text-gray-600">
              Revisão manual
              <select
                className="input-field mt-1"
                value={draftFilters.manual_review}
                onChange={(event) => updateFilter('manual_review', event.target.value)}
              >
                <option value="">Todas</option>
                <option value="true">Somente revisão manual</option>
                <option value="false">Excluir revisão manual</option>
              </select>
            </label>
          </div>

          {filterError && <p className="mt-3 text-sm text-red-600">{filterError}</p>}

          <div className="mt-5 flex flex-wrap gap-3">
            <button type="submit" className="btn-primary">
              <Filter size={16} />
              Aplicar filtros
            </button>
            <button type="button" className="btn-secondary" onClick={handleClearFilters}>
              <RefreshCw size={16} />
              Limpar
            </button>
          </div>
        </form>

        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Instituições</h2>
            <p className="mt-1 text-sm text-gray-500">
              {institutionList ? `${formatNumber(institutionList.total)} resultado(s)` : 'Carregando resultados...'}
            </p>
          </div>
          {institutionsQuery.isFetching && (
            <span className="flex items-center gap-2 text-sm text-gray-500">
              <Loader2 className="animate-spin" size={16} />
              Atualizando
            </span>
          )}
        </div>

        {institutionsQuery.isError ? (
          <ErrorMessage
            message="Não foi possível carregar a lista de instituições."
            onRetry={() => void institutionsQuery.refetch()}
          />
        ) : institutionsQuery.isLoading || !institutionList ? (
          <Spinner text="Carregando instituições..." />
        ) : institutionList.items.length === 0 ? (
          <EmptyState
            icon={<Building2 className="text-gray-400" size={32} />}
            title="Nenhuma instituição encontrada"
            description="Ajuste ou limpe os filtros para consultar outro recorte."
          />
        ) : (
          <>
            <div className="overflow-x-auto glass-panel rounded-2xl">
              <table className="min-w-[1280px] divide-y divide-gray-200">
                <thead>
                  <tr>
                    {[
                      'Instituição',
                      'UF / Região',
                      'Classificação',
                      'Elegibilidade',
                      'Cobertura / Fontes',
                      'Situação operacional',
                    ].map((heading) => (
                      <th
                        key={heading}
                        scope="col"
                        className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                      >
                        {heading}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {institutionList.items.map((item) => (
                    <InstitutionRow key={item.official_code} item={item} />
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex items-center justify-between glass-panel rounded-2xl p-4">
              <button
                type="button"
                className="btn-secondary"
                disabled={page === 0}
                onClick={() => setPage((current) => Math.max(0, current - 1))}
              >
                <ChevronLeft size={16} />
                Anterior
              </button>
              <span className="text-sm text-gray-500">
                Página {page + 1} de {totalPages}
              </span>
              <button
                type="button"
                className="btn-secondary"
                disabled={page + 1 >= totalPages}
                onClick={() => setPage((current) => current + 1)}
              >
                Próxima
                <ChevronRight size={16} />
              </button>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
