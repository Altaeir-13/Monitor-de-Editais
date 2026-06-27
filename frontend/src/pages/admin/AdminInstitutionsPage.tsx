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
import type { InstitutionCreate, InstitutionResponse, InstitutionUpdate } from '../../services/api';
import type { AxiosError } from 'axios';

const PAGE_SIZE = 20;

// No date formatting needed on this page

// â”€â”€ Institution Modal â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
      setValidationError('Preencha todos os campos obrigatÃ³rios.');
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
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-bold text-gray-900">
            {institution ? 'Editar InstituiÃ§Ã£o' : 'Nova InstituiÃ§Ã£o'}
          </h2>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={20} />
          </button>
        </div>
        <p className="text-sm text-gray-500 mb-6">
          Preencha os dados da instituiÃ§Ã£o para rastreabilidade dos editais.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {(error || validationError) && (
            <div className="app-error-box text-sm mb-4">
              {error || validationError}
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
              placeholder="Ex: Universidade Federal do PiauÃ­"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
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
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
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
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 uppercase"
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
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
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
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
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
              {isSaving ? 'Salvando...' : institution ? 'Salvar' : 'Criar InstituiÃ§Ã£o'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// â”€â”€ Confirm Modal â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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

// â”€â”€ Main Page â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
    return <Spinner text="Carregando instituiÃ§Ãµes..." />;
  }

  if (isError) {
    return (
      <ErrorMessage
        message="NÃ£o foi possÃ­vel carregar as instituiÃ§Ãµes."
        onRetry={() => refetch()}
      />
    );
  }

  const instList = institutions ?? [];
  const hasNextPage = instList.length === PAGE_SIZE;
  const currentPage = page + 1;

  const handleCreate = async (data: InstitutionCreate) => {
    setModalError('');
    try {
      await createMutation.mutateAsync(data);
      setShowCreateModal(false);
    } catch (err) {
      const axiosErr = err as AxiosError<{ detail: string }>;
      setModalError(axiosErr.response?.data?.detail || 'Erro ao criar instituiÃ§Ã£o.');
    }
  };

  const handleUpdate = async (data: InstitutionUpdate) => {
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
      setModalError(axiosErr.response?.data?.detail || 'Erro ao atualizar instituiÃ§Ã£o.');
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
          <h1 className="text-2xl font-bold text-gray-900">InstituiÃ§Ãµes</h1>
          <p className="text-sm text-gray-500 mt-1">
            Gerencie as instituiÃ§Ãµes de ensino ou pÃºblicas da plataforma.
          </p>
        </div>
        <button
          onClick={() => { setModalError(''); setShowCreateModal(true); }}
          className="inline-flex items-center gap-1.5 btn-primary"
        >
          <Plus size={16} />
          Nova InstituiÃ§Ã£o
        </button>
      </div>

      {instList.length === 0 && page === 0 ? (
        <EmptyState
          icon={<Building2 className="text-gray-400" size={32} />}
          title="Nenhuma instituiÃ§Ã£o encontrada"
          description="Ainda nÃ£o existem instituiÃ§Ãµes cadastradas no sistema."
          actionLabel="Criar instituiÃ§Ã£o"
          onAction={() => { setModalError(''); setShowCreateModal(true); }}
        />
      ) : (
        <>
          <div className="overflow-x-auto glass-panel rounded-2xl">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nome / Sigla</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">UF</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">AÃ§Ãµes</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {instList.map((inst) => (
                  <tr key={inst.id} className={!inst.is_active ? 'opacity-60 ' : ''}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      #{inst.id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-3">
                        {inst.logo_url ? (
                          <div className="institution-logo-frame">
                            <img src={inst.logo_url} alt={`${inst.initials} logo`} className="institution-logo-image" />
                          </div>
                        ) : (
                           <div className="institution-logo-frame">
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
                      <span className={`app-badge ${inst.is_active ? 'app-badge-success' : 'app-badge-muted'}`}>
                        {inst.is_active ? 'Ativo' : 'Inativo'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium flex justify-end items-center gap-2">
                       <a href={inst.official_site_url} target="_blank" rel="noopener noreferrer" className="p-1.5 text-gray-400 hover:text-primary-600 transition-colors" title="Site Oficial">
                          <ExternalLink size={16}/>
                       </a>
                       {inst.is_active ? (
                         <>
                           <button onClick={() => { setModalError(''); setEditingInst(inst); }} className="p-1.5 text-gray-400 hover:text-primary-600 transition-colors" title="Editar">
                              <Pencil size={16} />
                           </button>
                           <button onClick={() => setDeactivatingInstId(inst.id)} className="p-1.5 text-gray-400 hover:text-orange-600 transition-colors" title="Desativar">
                              <Power size={16} />
                           </button>
                         </>
                       ) : (
                         <button onClick={() => handleReactivate(inst.id)} className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-primary-600 bg-primary-50 rounded hover:bg-primary-100 transition-colors" title="Reativar">
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
            <span className="text-sm text-gray-500">PÃ¡gina {currentPage}</span>
            <button onClick={() => setPage((p) => p + 1)} disabled={!hasNextPage} className="flex items-center gap-1 px-3 py-2 text-sm font-medium rounded-lg text-gray-600 hover:bg-gray-100 transition-colors disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent">
              PrÃ³ximo <ChevronRight size={16} />
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
          title="Desativar instituiÃ§Ã£o"
          message="Tem certeza que deseja desativar esta instituiÃ§Ã£o? Fontes ligadas a ela continuarÃ£o intactas, mas poderÃ£o nÃ£o ser exibidas a usuÃ¡rios finais."
          confirmLabel="Desativar"
          onConfirm={handleDeactivate}
          onCancel={() => setDeactivatingInstId(null)}
          isLoading={updateMutation.isPending}
        />
      )}
    </div>
  );
}
