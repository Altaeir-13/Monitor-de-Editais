import { useState, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import type { AxiosError } from 'axios';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ExternalLink,
  FileText,
  History,
  Pencil,
  Play,
  RefreshCw,
  XCircle,
} from 'lucide-react';
import Spinner from '../../components/ui/Spinner';
import ErrorMessage from '../../components/ui/ErrorMessage';
import {
  useCrawlerRuns,
  useCrawlerSourcesStatus,
  useCrawlerStatus,
  useRunCrawlerOperational,
  useRunCrawlerSource,
} from '../../hooks/useCrawlerStatus';
import type { CrawlerSourceStatusResponse } from '../../services/api';

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '-';
  try {
    return new Intl.DateTimeFormat('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(dateStr));
  } catch {
    return '-';
  }
}

function summarizeRun(result: { sources_checked: number; items_found: number; new_items: number; failed_sources: number }) {
  return `Fontes: ${result.sources_checked}. Itens: ${result.items_found}. Novos editais: ${result.new_items}. Falhas: ${result.failed_sources}.`;
}

function getErrorMessage(error: unknown, fallback: string) {
  const axiosError = error as AxiosError<{ detail?: string }>;
  return axiosError.response?.data?.detail || fallback;
}

const healthLabels: Record<CrawlerSourceStatusResponse['health_status'], string> = {
  inactive: 'Inativa',
  never_checked: 'Nunca checada',
  error: 'Erro',
  warning: 'Sem itens',
  ok: 'OK',
};

const healthClasses: Record<CrawlerSourceStatusResponse['health_status'], string> = {
  inactive: 'app-badge-muted',
  never_checked: 'app-badge-muted',
  error: 'app-badge-danger',
  warning: 'app-badge-warning',
  ok: 'app-badge-success',
};

function SummaryCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: number | string;
  icon: ReactNode;
}) {
  return (
    <div className="glass-panel rounded-2xl p-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
        <div className="app-icon-soft">{icon}</div>
      </div>
    </div>
  );
}

export default function AdminCrawlerPage() {
  const [feedback, setFeedback] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [runningSourceId, setRunningSourceId] = useState<number | null>(null);

  const {
    data: status,
    isLoading: statusLoading,
    isError: statusError,
    refetch: refetchStatus,
  } = useCrawlerStatus();
  const {
    data: sources,
    isLoading: sourcesLoading,
    isError: sourcesError,
    refetch: refetchSources,
  } = useCrawlerSourcesStatus();
  const {
    data: runs,
    isLoading: runsLoading,
    isError: runsError,
    refetch: refetchRuns,
  } = useCrawlerRuns(0, 20);
  const runCrawlerMutation = useRunCrawlerOperational();
  const runSourceMutation = useRunCrawlerSource();

  const isLoading = statusLoading || sourcesLoading || runsLoading;
  const isError = statusError || sourcesError || runsError;

  const refetchAll = () => {
    refetchStatus();
    refetchSources();
    refetchRuns();
  };

  const handleRunCrawler = async () => {
    setFeedback('');
    setErrorMessage('');
    try {
      const result = await runCrawlerMutation.mutateAsync();
      setFeedback(`Crawler geral concluido. ${summarizeRun(result)}`);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, 'Erro ao executar crawler geral.'));
    }
  };

  const handleRunSource = async (sourceId: number) => {
    setFeedback('');
    setErrorMessage('');
    setRunningSourceId(sourceId);
    try {
      const result = await runSourceMutation.mutateAsync(sourceId);
      setFeedback(`Fonte #${sourceId} concluida. ${summarizeRun(result)}`);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, 'Erro ao executar fonte.'));
    } finally {
      setRunningSourceId(null);
    }
  };

  if (isLoading) {
    return <Spinner text="Carregando painel operacional do crawler..." />;
  }

  if (isError) {
    return (
      <ErrorMessage
        message="Nao foi possivel carregar o painel operacional do crawler."
        onRetry={refetchAll}
      />
    );
  }

  const sourcesList = sources ?? [];
  const runsList = runs ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Painel Operacional do Crawler</h1>
          <p className="text-sm text-gray-500 mt-1">
            Saude das fontes monitoradas e historico recente de execucoes.
          </p>
        </div>
        <button
          onClick={handleRunCrawler}
          disabled={runCrawlerMutation.isPending || runSourceMutation.isPending}
          className="inline-flex items-center justify-center gap-2 btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RefreshCw size={16} className={runCrawlerMutation.isPending ? 'animate-spin' : ''} />
          {runCrawlerMutation.isPending ? 'Executando...' : 'Executar crawler'}
        </button>
      </div>

      {(feedback || errorMessage) && (
        <div className={`rounded-lg px-4 py-3 text-sm ${errorMessage ? 'border border-red-200 bg-red-50 text-red-700' : 'border border-green-200 bg-green-50 text-green-700'}`}>
          {errorMessage || feedback}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <SummaryCard label="Fontes ativas" value={status?.active_sources ?? 0} icon={<Activity className="text-primary-600" size={20} />} />
        <SummaryCard label="Fontes OK" value={status?.ok_sources ?? 0} icon={<CheckCircle2 className="text-green-600" size={20} />} />
        <SummaryCard label="Com erro" value={status?.error_sources ?? 0} icon={<XCircle className="text-red-600" size={20} />} />
        <SummaryCard label="Nunca checadas" value={status?.never_checked_sources ?? 0} icon={<Clock className="text-gray-600" size={20} />} />
        <SummaryCard label="Sem itens" value={status?.warning_sources ?? 0} icon={<AlertTriangle className="text-amber-600" size={20} />} />
        <SummaryCard label="Inativas" value={status?.inactive_sources ?? 0} icon={<Activity className="text-gray-500" size={20} />} />
        <SummaryCard label="Editais ativos" value={status?.total_active_notices ?? 0} icon={<FileText className="text-primary-600" size={20} />} />
        <SummaryCard label="Novos no ultimo run" value={status?.last_run_new_items ?? 0} icon={<History className="text-primary-600" size={20} />} />
      </div>

      <div className="glass-panel rounded-2xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <div>
            <h2 className="font-semibold text-gray-900">Status por fonte</h2>
            <p className="text-sm text-gray-500">Ultima checagem, resultado e acoes operacionais.</p>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fonte</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Execucao</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ultimo erro</th>
                <th className="px-5 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acoes</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sourcesList.map((source) => {
                const isRunningThisSource = runningSourceId === source.source_id && runSourceMutation.isPending;
                return (
                  <tr key={source.source_id} className={!source.is_active ? 'opacity-60' : ''}>
                    <td className="px-5 py-4 align-top">
                      <div className="text-sm font-medium text-gray-900">{source.source_name}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {source.institution_initials} - {source.source_type}
                      </div>
                    </td>
                    <td className="px-5 py-4 align-top">
                      <span className={`app-badge ${healthClasses[source.health_status]}`}>
                        {healthLabels[source.health_status]}
                      </span>
                      <div className="text-xs text-gray-500 mt-2">
                        Checagem: {formatDate(source.last_checked_at)}
                      </div>
                      <div className="text-xs text-gray-500">
                        Sucesso: {formatDate(source.last_success_at)}
                      </div>
                    </td>
                    <td className="px-5 py-4 align-top text-sm text-gray-600">
                      <div>Itens: {source.last_run?.items_found ?? 0}</div>
                      <div>Novos: {source.last_run?.new_items ?? 0}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {formatDate(source.last_run?.started_at)}
                      </div>
                    </td>
                    <td className="px-5 py-4 align-top">
                      <div className="max-w-xs truncate text-sm text-gray-600" title={source.last_error_message ?? source.last_run?.error_message ?? ''}>
                        {source.last_error_message || source.last_run?.error_message || '-'}
                      </div>
                    </td>
                    <td className="px-5 py-4 align-top">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleRunSource(source.source_id)}
                          disabled={!source.is_active || runCrawlerMutation.isPending || runSourceMutation.isPending}
                          className="p-1.5 text-gray-400 hover:text-primary-600 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                          title="Executar fonte"
                          aria-label="Executar fonte"
                        >
                          {isRunningThisSource ? <RefreshCw size={16} className="animate-spin" /> : <Play size={16} />}
                        </button>
                        <a
                          href={source.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-1.5 text-gray-400 hover:text-primary-600 transition-colors"
                          title="Abrir fonte"
                          aria-label="Abrir fonte"
                        >
                          <ExternalLink size={16} />
                        </a>
                        <Link
                          to="/admin/sources"
                          className="p-1.5 text-gray-400 hover:text-primary-600 transition-colors"
                          title="Editar fonte"
                          aria-label="Editar fonte"
                        >
                          <Pencil size={16} />
                        </Link>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="glass-panel rounded-2xl overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">Historico recente</h2>
          <p className="text-sm text-gray-500">Ultimas execucoes registradas por fonte.</p>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Inicio</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fonte</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Itens</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Erro</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {runsList.map((run) => (
                <tr key={run.id}>
                  <td className="px-5 py-4 text-sm text-gray-600">{formatDate(run.started_at)}</td>
                  <td className="px-5 py-4">
                    <div className="text-sm font-medium text-gray-900">{run.source_name}</div>
                    <div className="text-xs text-gray-500">{run.institution.initials}</div>
                  </td>
                  <td className="px-5 py-4">
                    <span className={`app-badge ${run.status === 'completed' ? 'app-badge-success' : run.status === 'failed' ? 'app-badge-danger' : 'app-badge-muted'}`}>
                      {run.status}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-sm text-gray-600">
                    {run.items_found} encontrados / {run.new_items} novos
                  </td>
                  <td className="px-5 py-4 text-sm text-gray-600 max-w-xs truncate" title={run.error_message ?? ''}>
                    {run.error_message || '-'}
                  </td>
                </tr>
              ))}
              {runsList.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-5 py-8 text-center text-sm text-gray-500">
                    Nenhuma execucao registrada.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
