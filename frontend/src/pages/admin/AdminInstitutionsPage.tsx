import { useState } from 'react';
import { useInstitutions, useCreateInstitution, useUpdateInstitution } from '../../hooks/useInstitutions';
import Spinner from '../../components/ui/Spinner';
import EmptyState from '../../components/ui/EmptyState';
import ErrorMessage from '../../components/ui/ErrorMessage';
import {
  Plus,
  Pencil,
  Power,
  RotateCcw,
  X,
  Building2,
  ChevronLeft,
  ChevronRight,
  ExternalLink
} from 'lucide-react';
import type { InstitutionResponse } from '../../services/api';
import type { AxiosError } from 'axios';

const PAGE_SIZE = 20;

// No date formatting needed on this page

// ── Institution Modal ─────────────────────────────────────────────────────────

interface InstitutionModalProps {
  institution?: InstitutionResponse | null;
  onClose: () => void;
  onSave: (data: { name: string; initials: string; state: string; official_site_url: string; logo_url: string }) => Promise<void>;
  isSaving: boolean;
  error: string;
}

function InstitutionModal({ institution, onClose, onSave, isSaving, error }: InstitutionModalProps) {
  const [name, setName] = useState(institution?.name ?? '');
  const [initials, setInitials] = useState(institution?.initials ?? '');
  const [stateUF, setStateUF] = useState(institution?.state ?? '');
  const [siteUrl, setSiteUrl] = useState(institution?.official_site_url ?? '');
  const [logoUrl, setLogoUrl] = useState(institution?.logo_url ?? '');
  const [validationError, setValidationError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError('');

    const trimmedName = name.trim();
    const trimmedInitials = initials.trim().toUpperCase();
    const trimmedState = stateUF.trim().toUpperCase();
    const trimmedSite = siteUrl.trim();
    const trimmedLogo = logoUrl.trim();

    if (!trimmedName || !trimmedInitials || !trimmedState || !trimmedSite) {
      setValidationError('Preencha todos os campos obrigatórios.');
      return;
    }

    if (trimmedState.length !== 2) {
      setValidationError('O estado (UF) deve ter exatamente 2 letras (ex: SP, RJ).');
      return;
    }

    await onSave({
      name: trimmedName,
      initials: trimmedInitials,
      state: trimmedState,
      official_site_url: trimmedSite,
      logo_url: trimmedLogo
    });
  };

  const isFormEmpty = !name.trim() || !initials.trim() || !stateUF.trim() || !siteUrl.trim();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            {institution ? 'Editar Instituição' : 'Nova Instituição'}
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
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nome Completo <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => { setName(e.target.value); setValidationError(''); }}
              placeholder="Ex: Universidade Federal do Piauí"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              autoFocus
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Sigla <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={initials}
                onChange={(e) => { setInitials(e.target.value); setValidationError(''); }}
                placeholder="Ex: UFPI"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Estado (UF) <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={stateUF}
                maxLength={2}
                onChange={(e) => { setStateUF(e.target.value); setValidationError(''); }}
                placeholder="Ex: PI"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 uppercase"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Site Oficial <span className="text-red-500">*</span>
            </label>
            <input
              type="url"
              value={siteUrl}
              onChange={(e) => { setSiteUrl(e.target.value); setValidationError(''); }}
              placeholder="Ex: https://ufpi.br"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              URL do Logo <span className="text-gray-400 text-xs">(opcional)</span>
            </label>
            <input
              type="url"
              value={logoUrl}
              onChange={(e) => { setLogoUrl(e.target.value); setValidationError(''); }}
              placeholder="Ex: https://ufpi.br/logo.png"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isSaving || isFormEmpty}
              className="flex-1 px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSaving ? 'Salvando...' : institution ? 'Salvar' : 'Criar Instituição'}
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
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className="flex-1 px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Processando...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function AdminInstitutionsPage() {
  const [page, setPage] = useState(0);
  const skip = page * PAGE_SIZE;

  const { data: institutions, isLoading, isError, refetch } = useInstitutions(skip, PAGE_SIZE);
  const createMutation = useCreateInstitution();
  const updateMutation = useUpdateInstitution();

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingInst, setEditingInst] = useState<InstitutionResponse | null>(null);
  const [deactivatingInstId, setDeactivatingInstId] = useState<number | null>(null);
  const [modalError, setModalError] = useState('');

  if (isLoading) {
    return <Spinner text="Carregando instituições..." />;
  }

  if (isError) {
    return (
      <ErrorMessage
        message="Não foi possível carregar as instituições."
        onRetry={() => refetch()}
      />
    );
  }

  const instList = institutions ?? [];
  const hasNextPage = instList.length === PAGE_SIZE;
  const currentPage = page + 1;

  const handleCreate = async (data: any) => {
    setModalError('');
    try {
      await createMutation.mutateAsync(data);
      setShowCreateModal(false);
    } catch (err) {
      const axiosErr = err as AxiosError<{ detail: string }>;
      setModalError(axiosErr.response?.data?.detail || 'Erro ao criar instituição.');
    }
  };

  const handleUpdate = async (data: any) => {
    if (!editingInst) return;
    setModalError('');
    try {
      await updateMutation.mutateAsync({
        id: editingInst.id,
        data,
      });
      setEditingInst(null);
    } catch (err) {
      const axiosErr = err as AxiosError<{ detail: string }>;
      setModalError(axiosErr.response?.data?.detail || 'Erro ao atualizar instituição.');
    }
  };

  const handleDeactivate = async () => {
    if (deactivatingInstId === null) return;
    try {
      await updateMutation.mutateAsync({
        id: deactivatingInstId,
        data: { is_active: false }
      });
      setDeactivatingInstId(null);
    } catch {
      setDeactivatingInstId(null);
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
          <h1 className="text-2xl font-bold text-gray-900">Instituições</h1>
          <p className="text-sm text-gray-500 mt-1">
            Gerencie as instituições de ensino ou públicas da plataforma.
          </p>
        </div>
        <button
          onClick={() => { setModalError(''); setShowCreateModal(true); }}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <Plus size={16} />
          Nova Instituição
        </button>
      </div>

      {instList.length === 0 && page === 0 ? (
        <EmptyState
          icon={<Building2 className="text-gray-400" size={32} />}
          title="Nenhuma instituição encontrada"
          description="Ainda não existem instituições cadastradas no sistema."
          actionLabel="Criar instituição"
          onAction={() => { setModalError(''); setShowCreateModal(true); }}
        />
      ) : (
        <>
          <div className="overflow-x-auto bg-white rounded-xl border border-gray-200 shadow-sm">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nome / Sigla</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">UF</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Ações</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {instList.map((inst) => (
                  <tr key={inst.id} className={!inst.is_active ? 'opacity-60 bg-gray-50' : ''}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      #{inst.id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-3">
                        {inst.logo_url ? (
                           <img src={inst.logo_url} alt={`${inst.initials} logo`} className="w-8 h-8 rounded object-contain border border-gray-100 bg-white" />
                        ) : (
                           <div className="w-8 h-8 rounded border border-gray-100 bg-gray-50 flex items-center justify-center">
                             <Building2 size={14} className="text-gray-400"/>
                           </div>
                        )}
                        <div>
                          <p className="text-sm font-medium text-gray-900">{inst.initials}</p>
                          <p className="text-xs text-gray-500 max-w-[200px] truncate" title={inst.name}>{inst.name}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                      {inst.state}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${inst.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-200 text-gray-600'}`}>
                        {inst.is_active ? 'Ativo' : 'Inativo'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium flex justify-end items-center gap-2">
                       <a href={inst.official_site_url} target="_blank" rel="noopener noreferrer" className="p-1.5 text-gray-400 hover:text-indigo-600 transition-colors" title="Site Oficial">
                          <ExternalLink size={16}/>
                       </a>
                       {inst.is_active ? (
                         <>
                           <button onClick={() => { setModalError(''); setEditingInst(inst); }} className="p-1.5 text-gray-400 hover:text-indigo-600 transition-colors" title="Editar">
                              <Pencil size={16} />
                           </button>
                           <button onClick={() => setDeactivatingInstId(inst.id)} className="p-1.5 text-gray-400 hover:text-orange-600 transition-colors" title="Desativar">
                              <Power size={16} />
                           </button>
                         </>
                       ) : (
                         <button onClick={() => handleReactivate(inst.id)} className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-indigo-600 bg-indigo-50 rounded hover:bg-indigo-100 transition-colors" title="Reativar">
                           <RotateCcw size={14} /> Reativar
                         </button>
                       )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between mt-6 bg-white rounded-xl border border-gray-200 shadow-sm p-4">
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
        <InstitutionModal
          onClose={() => setShowCreateModal(false)}
          onSave={handleCreate}
          isSaving={createMutation.isPending}
          error={modalError}
        />
      )}

      {editingInst && (
        <InstitutionModal
          institution={editingInst}
          onClose={() => setEditingInst(null)}
          onSave={handleUpdate}
          isSaving={updateMutation.isPending}
          error={modalError}
        />
      )}

      {deactivatingInstId !== null && (
        <ConfirmModal
          title="Desativar instituição"
          message="Tem certeza que deseja desativar esta instituição? Fontes ligadas a ela continuarão intactas, mas poderão não ser exibidas a usuários finais."
          confirmLabel="Desativar"
          onConfirm={handleDeactivate}
          onCancel={() => setDeactivatingInstId(null)}
          isLoading={updateMutation.isPending}
        />
      )}
    </div>
  );
}
