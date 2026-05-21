import { useState } from 'react';
import { useSources, useCreateSource, useUpdateSource } from '../../hooks/useSources';
import Spinner from '../../components/ui/Spinner';
import EmptyState from '../../components/ui/EmptyState';
import ErrorMessage from '../../components/ui/ErrorMessage';
import {
  Plus,
  Pencil,
  Power,
  RotateCcw,
  X,
  Database,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  CheckCircle2,
  XCircle
} from 'lucide-react';
import type { MonitoredSourceResponse } from '../../services/api';
import type { AxiosError } from 'axios';

const PAGE_SIZE = 20;

const SOURCE_TYPES = [
  { value: 'HTML_STATIC', label: 'HTML Estático' },
  { value: 'HTML_DYNAMIC', label: 'HTML Dinâmico' },
  { value: 'RSS', label: 'RSS/Atom' },
  { value: 'PDF_LIST', label: 'Lista de PDFs' },
  { value: 'GENERIC_LINK_DISCOVERY', label: 'Descoberta Genérica de Links' }
];

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  try {
    return new Intl.DateTimeFormat('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(new Date(dateStr));
  } catch {
    return '—';
  }
}

// ── Source Modal ──────────────────────────────────────────────────────────────

interface SourceModalProps {
  source?: MonitoredSourceResponse | null;
  onClose: () => void;
  onSave: (data: { institution_id: number; name: string; url: string; source_type: string; check_frequency_minutes: number }) => Promise<void>;
  isSaving: boolean;
  error: string;
}

function SourceModal({ source, onClose, onSave, isSaving, error }: SourceModalProps) {
  const [institutionId, setInstitutionId] = useState(source?.institution_id.toString() ?? '');
  const [name, setName] = useState(source?.name ?? '');
  const [url, setUrl] = useState(source?.url ?? '');
  const [sourceType, setSourceType] = useState(source?.source_type ?? 'HTML_STATIC');
  const [freq, setFreq] = useState(source?.check_frequency_minutes.toString() ?? '1440');
  const [validationError, setValidationError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError('');

    const parsedInstId = parseInt(institutionId, 10);
    const parsedFreq = parseInt(freq, 10);
    const trimmedName = name.trim();
    const trimmedUrl = url.trim();

    if (!institutionId || isNaN(parsedInstId)) {
      setValidationError('O ID da instituição deve ser um número válido.');
      return;
    }

    if (!trimmedName || !trimmedUrl || !sourceType) {
      setValidationError('Preencha nome, URL e tipo da fonte.');
      return;
    }

    if (isNaN(parsedFreq) || parsedFreq <= 0) {
      setValidationError('A frequência de checagem deve ser um número inteiro positivo.');
      return;
    }

    await onSave({
      institution_id: parsedInstId,
      name: trimmedName,
      url: trimmedUrl,
      source_type: sourceType,
      check_frequency_minutes: parsedFreq
    });
  };

  const isFormEmpty = !institutionId || !name.trim() || !url.trim() || !freq;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-bold text-gray-900">
            {source ? 'Editar Fonte' : 'Nova Fonte'}
          </h2>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={20} />
          </button>
        </div>
        <p className="text-sm text-gray-500 mb-6">
          Defina de onde e com que frequência o Crawler deve capturar novos editais.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {(error || validationError) && (
            <div className="app-error-box text-sm mb-4">
              {error || validationError}
            </div>
          )}

          <div className="grid grid-cols-3 gap-4">
            <div className="col-span-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Institution ID <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                value={institutionId}
                onChange={(e) => { setInstitutionId(e.target.value); setValidationError(''); }}
                placeholder="Ex: 1"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                autoFocus
              />
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nome da Fonte <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => { setName(e.target.value); setValidationError(''); }}
                placeholder="Ex: Diário Oficial / Feed PROPESQ"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              URL da Fonte <span className="text-red-500">*</span>
            </label>
            <input
              type="url"
              value={url}
              onChange={(e) => { setUrl(e.target.value); setValidationError(''); }}
              placeholder="Ex: https://ufpi.br/editais"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tipo da Fonte <span className="text-red-500">*</span>
              </label>
              <select
                value={sourceType}
                onChange={(e) => setSourceType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
              >
                {SOURCE_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Check Freq. (minutos) <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                value={freq}
                onChange={(e) => { setFreq(e.target.value); setValidationError(''); }}
                placeholder="Ex: 1440"
                min="1"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary flex-1"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isSaving || isFormEmpty}
              className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSaving ? 'Salvando...' : source ? 'Salvar' : 'Criar Fonte'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Confirm Modal ─────────────────────────────────────────────────────────────

interface ConfirmModalProps {
  title: string;
  message: string;
  confirmLabel: string;
  onConfirm: () => void;
  onCancel: () => void;
  isLoading: boolean;
}

function ConfirmModal({ title, message, confirmLabel, onConfirm, onCancel, isLoading }: ConfirmModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/40" onClick={onCancel} />
      <div className="relative bg-white rounded-xl shadow-xl w-full max-w-sm mx-4 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">{title}</h2>
        <p className="text-sm text-gray-600 mb-4">{message}</p>
        <div className="flex gap-2">
          <button
            onClick={onCancel}
            className="btn-secondary flex-1"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className="flex-1 btn-danger disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Processando...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function AdminSourcesPage() {
  const [page, setPage] = useState(0);
  const skip = page * PAGE_SIZE;

  const { data: sources, isLoading, isError, refetch } = useSources(skip, PAGE_SIZE);
  const createMutation = useCreateSource();
  const updateMutation = useUpdateSource();

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingSource, setEditingSource] = useState<MonitoredSourceResponse | null>(null);
  const [deactivatingSourceId, setDeactivatingSourceId] = useState<number | null>(null);
  const [modalError, setModalError] = useState('');

  if (isLoading) {
    return <Spinner text="Carregando fontes monitoradas..." />;
  }

  if (isError) {
    return (
      <ErrorMessage
        message="Não foi possível carregar as fontes."
        onRetry={() => refetch()}
      />
    );
  }

  const sourcesList = sources ?? [];
  const hasNextPage = sourcesList.length === PAGE_SIZE;
  const currentPage = page + 1;

  const handleCreate = async (data: any) => {
    setModalError('');
    try {
      await createMutation.mutateAsync(data);
      setShowCreateModal(false);
    } catch (err) {
      const axiosErr = err as AxiosError<{ detail: string }>;
      setModalError(axiosErr.response?.data?.detail || 'Erro ao criar fonte (verifique o Institution ID).');
    }
  };

  const handleUpdate = async (data: any) => {
    if (!editingSource) return;
    setModalError('');
    try {
      await updateMutation.mutateAsync({
        id: editingSource.id,
        data,
      });
      setEditingSource(null);
    } catch (err) {
      const axiosErr = err as AxiosError<{ detail: string }>;
      setModalError(axiosErr.response?.data?.detail || 'Erro ao atualizar fonte.');
    }
  };

  const handleDeactivate = async () => {
    if (deactivatingSourceId === null) return;
    try {
      await updateMutation.mutateAsync({
        id: deactivatingSourceId,
        data: { is_active: false }
      });
      setDeactivatingSourceId(null);
    } catch {
      setDeactivatingSourceId(null);
    }
  };

  const handleReactivate = async (id: number) => {
    try {
      await updateMutation.mutateAsync({ id, data: { is_active: true } });
    } catch {
      // handled silently
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Fontes Monitoradas</h1>
          <p className="text-sm text-gray-500 mt-1">
            Gerencie as origens (links, feeds) rastreadas pelo Crawler.
          </p>
        </div>
        <button
          onClick={() => { setModalError(''); setShowCreateModal(true); }}
          className="inline-flex items-center gap-1.5 btn-primary"
        >
          <Plus size={16} />
          Nova Fonte
        </button>
      </div>

      {sourcesList.length === 0 && page === 0 ? (
        <EmptyState
          icon={<Database className="text-gray-400" size={32} />}
          title="Nenhuma fonte encontrada"
          description="Ainda não existem fontes monitoradas cadastradas no sistema."
          actionLabel="Criar fonte"
          onAction={() => { setModalError(''); setShowCreateModal(true); }}
        />
      ) : (
        <>
          <div className="overflow-x-auto glass-panel rounded-2xl">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID / Inst.</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nome / Tipo</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Métricas de Checagem</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Ações</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {sourcesList.map((source) => (
                  <tr key={source.id} className={!source.is_active ? 'opacity-60 ' : ''}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div><span className="font-medium text-gray-900">#{source.id}</span></div>
                      <div className="text-xs mt-0.5">Inst ID: {source.institution_id}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900 truncate max-w-[200px]" title={source.name}>{source.name}</div>
                      <div className="app-badge app-badge-muted mt-1">
                        HTML Estático
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                       <div className="text-xs text-gray-500 space-y-1">
                          <div className="flex items-center gap-1">
                            <span className="font-medium">Freq:</span> {source.check_frequency_minutes} min
                          </div>
                          <div className="flex items-center gap-1">
                            <span className="font-medium">Últ. Checagem:</span> {formatDate(source.last_checked_at)}
                          </div>
                          {source.last_error_message ? (
                             <div className="flex items-center gap-1 text-red-600" title={source.last_error_message}>
                                <XCircle size={12}/> Erro Recente
                             </div>
                          ) : source.last_success_at ? (
                             <div className="flex items-center gap-1 text-green-600">
                                <CheckCircle2 size={12}/> {formatDate(source.last_success_at)}
                             </div>
                          ) : null}
                       </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`app-badge ${source.is_active ? 'app-badge-success' : 'app-badge-muted'}`}>
                        {source.is_active ? 'Ativo' : 'Inativo'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium flex justify-end items-center gap-2">
                       <a href={source.url} target="_blank" rel="noopener noreferrer" className="p-1.5 text-gray-400 hover:text-primary-600 transition-colors" title="Abrir URL">
                          <ExternalLink size={16}/>
                       </a>
                       {source.is_active ? (
                         <>
                           <button onClick={() => { setModalError(''); setEditingSource(source); }} className="p-1.5 text-gray-400 hover:text-primary-600 transition-colors" title="Editar">
                              <Pencil size={16} />
                           </button>
                           <button onClick={() => setDeactivatingSourceId(source.id)} className="p-1.5 text-gray-400 hover:text-orange-600 transition-colors" title="Desativar">
                              <Power size={16} />
                           </button>
                         </>
                       ) : (
                         <button onClick={() => handleReactivate(source.id)} className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-primary-600 bg-primary-50 rounded hover:bg-primary-100 transition-colors" title="Reativar">
                           <RotateCcw size={14} /> Reativar
                         </button>
                       )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between mt-6 glass-panel rounded-2xl p-4">
            <button onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 0} className="flex items-center gap-1 px-3 py-2 text-sm font-medium rounded-lg text-gray-600 hover:bg-gray-100 transition-colors disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent">
              <ChevronLeft size={16} /> Anterior
            </button>
            <span className="text-sm text-gray-500">Página {currentPage}</span>
            <button onClick={() => setPage((p) => p + 1)} disabled={!hasNextPage} className="flex items-center gap-1 px-3 py-2 text-sm font-medium rounded-lg text-gray-600 hover:bg-gray-100 transition-colors disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent">
              Próximo <ChevronRight size={16} />
            </button>
          </div>
        </>
      )}

      {showCreateModal && (
        <SourceModal
          onClose={() => setShowCreateModal(false)}
          onSave={handleCreate}
          isSaving={createMutation.isPending}
          error={modalError}
        />
      )}

      {editingSource && (
        <SourceModal
          source={editingSource}
          onClose={() => setEditingSource(null)}
          onSave={handleUpdate}
          isSaving={updateMutation.isPending}
          error={modalError}
        />
      )}

      {deactivatingSourceId !== null && (
        <ConfirmModal
          title="Desativar fonte"
          message="Tem certeza que deseja desativar esta fonte? O crawler não irá mais inspecionar essa URL."
          confirmLabel="Desativar"
          onConfirm={handleDeactivate}
          onCancel={() => setDeactivatingSourceId(null)}
          isLoading={updateMutation.isPending}
        />
      )}
    </div>
  );
}
