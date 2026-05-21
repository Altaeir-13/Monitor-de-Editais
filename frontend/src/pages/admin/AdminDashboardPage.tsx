import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useInstitutions } from '../../hooks/useInstitutions';
import { useSources } from '../../hooks/useSources';
import {
  Building2,
  Database,
  ChevronRight,
} from 'lucide-react';
import Spinner from '../../components/ui/Spinner';
import ErrorMessage from '../../components/ui/ErrorMessage';

export default function AdminDashboardPage() {
  const { user } = useAuth();
  
  // Fetching a sample to just get counts of current page, per the plan scope 
  const { data: institutions, isLoading: instLoading, isError: instError, refetch: refetchInst } = useInstitutions(0, 20);
  const { data: sources, isLoading: srcLoading, isError: srcError, refetch: refetchSrc } = useSources(0, 20);

  const isLoading = instLoading || srcLoading;

  if (isLoading) {
    return <Spinner text="Carregando painel administrativo..." />;
  }

  return (
    <div>
      <div className="mb-8 p-8 glass-panel rounded-2xl">
        <h1 className="text-3xl font-bold text-gray-900 tracking-tight">
          Painel Administrativo
        </h1>
        <p className="text-base text-gray-500 mt-2">
          Bem-vindo, {user?.name}. Aqui você possui controle total sobre os cadastros base da plataforma.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Institutions Card */}
        <div className="glass-panel rounded-2xl overflow-hidden flex flex-col">
          <div className="flex items-center justify-between p-5 border-b border-gray-100">
            <div className="flex items-center gap-2">
              <Building2 className="text-primary-600" size={20} />
              <h2 className="font-semibold text-gray-900">Instituições</h2>
            </div>
          </div>
          <div className="p-5 flex-1 flex flex-col justify-center">
            {instError ? (
              <ErrorMessage message="Erro ao carregar instituições." onRetry={() => refetchInst()} />
            ) : (
              <div className="text-center">
                <p className="text-4xl font-bold text-primary-600 mb-1">{institutions?.length ?? 0}</p>
                <p className="text-sm text-gray-500">listadas na visualização atual</p>
              </div>
            )}
          </div>
          <div className="p-4  border-t border-gray-100">
             <Link
                to="/admin/institutions"
                className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center justify-center gap-1"
              >
                Gerenciar Instituições <ChevronRight size={16} />
              </Link>
          </div>
        </div>

        {/* Sources Card */}
        <div className="glass-panel rounded-2xl overflow-hidden flex flex-col">
          <div className="flex items-center justify-between p-5 border-b border-gray-100">
            <div className="flex items-center gap-2">
              <Database className="text-primary-600" size={20} />
              <h2 className="font-semibold text-gray-900">Fontes Monitoradas</h2>
            </div>
          </div>
          <div className="p-5 flex-1 flex flex-col justify-center">
             {srcError ? (
              <ErrorMessage message="Erro ao carregar fontes." onRetry={() => refetchSrc()} />
            ) : (
              <div className="text-center">
                <p className="text-4xl font-bold text-primary-600 mb-1">{sources?.length ?? 0}</p>
                <p className="text-sm text-gray-500">listadas na visualização atual</p>
              </div>
            )}
          </div>
          <div className="p-4  border-t border-gray-100">
             <Link
                to="/admin/sources"
                className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center justify-center gap-1"
              >
                Gerenciar Fontes <ChevronRight size={16} />
              </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
