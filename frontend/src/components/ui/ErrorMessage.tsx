import { AlertCircle } from 'lucide-react';

interface ErrorMessageProps {
  message?: string;
  onRetry?: () => void;
}

export default function ErrorMessage({
  message = 'Ocorreu um erro ao carregar os dados.',
  onRetry,
}: ErrorMessageProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center glass-panel rounded-2xl border-red-100">
      <div className="app-error-box rounded-2xl mb-5 shadow-sm">
        <AlertCircle size={32} />
      </div>
      <h3 className="text-xl font-bold text-gray-900">Erro</h3>
      <p className="app-muted-text mt-2 max-w-md leading-relaxed">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="btn-secondary mt-6"
        >
          Tentar novamente
        </button>
      )}
    </div>
  );
}
