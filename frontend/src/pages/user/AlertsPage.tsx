import { useState } from 'react';
import { useAlerts, useCreateAlert, useUpdateAlert } from '../../hooks/useAlerts';
import Spinner from '../../components/ui/Spinner';
import EmptyState from '../../components/ui/EmptyState';
import ErrorMessage from '../../components/ui/ErrorMessage';
import {
  Plus,
  Pencil,
  BellOff,
  RotateCcw,
  X,
  AlertTriangle,
} from 'lucide-react';
import type { UserAlertResponse } from '../../services/api';
import type { AxiosError } from 'axios';

const NOTICE_TYPES = [
  { value: 'concurso', label: 'Concurso' },
  { value: 'bolsa', label: 'Bolsa' },
  { value: 'edital', label: 'Edital' },
  { value: 'licitacao', label: 'Licitação' },
  { value: 'selecao', label: 'Seleção' },
  { value: 'outro', label: 'Outro' },
];

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  try {
    return new Intl.DateTimeFormat('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    }).format(new Date(dateStr));
  } catch {
    return '—';
  }
}

// ── Alert Modal ───────────────────────────────────────────────────────────────

interface AlertModalProps {
  alert?: UserAlertResponse | null;
  onClose: () => void;
  onSave: (keyword: string, noticeType?: string) => Promise<void>;
  isSaving: boolean;
  error: string;
}

function AlertModal({ alert, onClose, onSave, isSaving, error }: AlertModalProps) {
  const [keyword, setKeyword] = useState(alert?.keyword ?? '');
  const [noticeType, setNoticeType] = useState(alert?.notice_type ?? '');
  const [validationError, setValidationError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError('');

    const trimmedKeyword = keyword.trim();
    if (!trimmedKeyword) {
      setValidationError('A palavra-chave é obrigatória.');
      return;
    }

    await onSave(trimmedKeyword, noticeType || undefined);
  };

  const isKeywordEmpty = keyword.trim() === '';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            {alert ? 'Editar Alerta' : 'Novo Alerta'}
          </h2>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {(error || validationError) && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {validationError || error}
            </div>
          )}

          <div>
            <label htmlFor="keyword" className="block text-sm font-medium text-gray-700 mb-1">
              Palavra-chave <span className="text-red-500">*</span>
            </label>
            <input
              id="keyword"
              type="text"
              value={keyword}
              onChange={(e) => {
                setKeyword(e.target.value);
                if (validationError) setValidationError('');
              }}
              placeholder="Ex: professor, bolsa, mestrado..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm
                         focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent
                         placeholder-gray-400"
              autoFocus
            />
          </div>

          <div>
            <label htmlFor="noticeType" className="block text-sm font-medium text-gray-700 mb-1">
              Tipo de edital <span className="text-gray-400 text-xs">(opcional)</span>
            </label>
            <select
              id="noticeType"
              value={noticeType}
              onChange={(e) => setNoticeType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm
                         focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent
                         bg-white"
            >
              <option value="">Qualquer tipo</option>
              {NOTICE_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>

          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium
                         rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isSaving || isKeywordEmpty}
              className="flex-1 px-4 py-2 bg-indigo-600 text-white text-sm font-medium
                         rounded-lg hover:bg-indigo-700 transition-colors
                         disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSaving ? 'Salvando...' : alert ? 'Salvar' : 'Criar Alerta'}
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
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium
                       rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className="flex-1 px-4 py-2 bg-red-600 text-white text-sm font-medium
                       rounded-lg hover:bg-red-700 transition-colors
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Processando...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function AlertsPage() {
  const { data: alerts, isLoading, isError, refetch } = useAlerts();
  const createMutation = useCreateAlert();
  const updateMutation = useUpdateAlert();

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingAlert, setEditingAlert] = useState<UserAlertResponse | null>(null);
  const [deactivatingAlertId, setDeactivatingAlertId] = useState<number | null>(null);
  const [modalError, setModalError] = useState('');

  if (isLoading) {
    return <Spinner text="Carregando alertas..." />;
  }

  if (isError) {
    return (
      <ErrorMessage
        message="Não foi possível carregar seus alertas."
        onRetry={() => refetch()}
      />
    );
  }

  const alertList = alerts ?? [];

  const handleCreate = async (keyword: string, noticeType?: string) => {
    setModalError('');
    try {
      await createMutation.mutateAsync({ keyword, notice_type: noticeType });
      setShowCreateModal(false);
    } catch (err) {
      const axiosErr = err as AxiosError<{ detail: string }>;
      setModalError(axiosErr.response?.data?.detail || 'Erro ao criar alerta.');
    }
  };

  const handleUpdate = async (keyword: string, noticeType?: string) => {
    if (!editingAlert) return;
    setModalError('');
    try {
      await updateMutation.mutateAsync({
        id: editingAlert.id,
        data: { keyword, notice_type: noticeType },
      });
      setEditingAlert(null);
    } catch (err) {
      const axiosErr = err as AxiosError<{ detail: string }>;
      setModalError(axiosErr.response?.data?.detail || 'Erro ao atualizar alerta.');
    }
  };

  const handleDeactivate = async () => {
    if (deactivatingAlertId === null) return;
    try {
      await updateMutation.mutateAsync({
        id: deactivatingAlertId,
        data: { is_active: false },
      });
      setDeactivatingAlertId(null);
    } catch {
      setDeactivatingAlertId(null);
    }
  };

  const handleReactivate = async (id: number) => {
    try {
      await updateMutation.mutateAsync({ id, data: { is_active: true } });
    } catch {
      // silently handled — cache will reflect actual state
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Meus Alertas</h1>
          <p className="text-sm text-gray-500 mt-1">
            Gerencie seus alertas de editais.
          </p>
        </div>
        <button
          onClick={() => { setModalError(''); setShowCreateModal(true); }}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white text-sm
                     font-medium rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <Plus size={16} />
          Novo Alerta
        </button>
      </div>

      {alertList.length === 0 ? (
        <EmptyState
          icon={<AlertTriangle className="text-gray-400" size={32} />}
          title="Nenhum alerta criado"
          description="Crie seu primeiro alerta para ser notificado quando novos editais corresponderem às suas palavras-chave."
          actionLabel="Criar meu primeiro alerta"
          onAction={() => { setModalError(''); setShowCreateModal(true); }}
        />
      ) : (
        <div className="grid gap-3">
          {alertList.map((alert) => (
            <div
              key={alert.id}
              className={`bg-white rounded-xl border shadow-sm p-4 flex items-center justify-between gap-4
                          ${alert.is_active ? 'border-gray-200' : 'border-gray-100 opacity-70'}`}
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={`text-xs font-medium px-2 py-0.5 rounded-full
                      ${alert.is_active
                        ? 'bg-green-50 text-green-700'
                        : 'bg-gray-100 text-gray-500'
                      }`}
                  >
                    {alert.is_active ? 'Ativo' : 'Inativo'}
                  </span>
                  {alert.notice_type && (
                    <span className="text-xs bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full capitalize">
                      {alert.notice_type}
                    </span>
                  )}
                </div>
                <p className="text-sm font-medium text-gray-900 truncate">
                  {alert.keyword}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">
                  Criado em {formatDate(alert.created_at)}
                </p>
              </div>

              <div className="flex items-center gap-1">
                {alert.is_active ? (
                  <>
                    <button
                      onClick={() => { setModalError(''); setEditingAlert(alert); }}
                      className="p-2 text-gray-400 hover:text-indigo-600 transition-colors"
                      title="Editar"
                    >
                      <Pencil size={16} />
                    </button>
                    <button
                      onClick={() => setDeactivatingAlertId(alert.id)}
                      className="p-2 text-gray-400 hover:text-amber-600 transition-colors"
                      title="Desativar"
                    >
                      <BellOff size={16} />
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => handleReactivate(alert.id)}
                    className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium
                               text-indigo-600 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition-colors"
                    title="Reativar"
                  >
                    <RotateCcw size={14} />
                    Reativar
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <AlertModal
          onClose={() => setShowCreateModal(false)}
          onSave={handleCreate}
          isSaving={createMutation.isPending}
          error={modalError}
        />
      )}

      {/* Edit Modal */}
      {editingAlert && (
        <AlertModal
          alert={editingAlert}
          onClose={() => setEditingAlert(null)}
          onSave={handleUpdate}
          isSaving={updateMutation.isPending}
          error={modalError}
        />
      )}

      {/* Delete Confirmation */}
      {deactivatingAlertId !== null && (
        <ConfirmModal
          title="Desativar alerta"
          message="Tem certeza que deseja desativar este alerta? Você poderá reativá-lo depois."
          confirmLabel="Desativar"
          onConfirm={handleDeactivate}
          onCancel={() => setDeactivatingAlertId(null)}
          isLoading={updateMutation.isPending}
        />
      )}
    </div>
  );
}
