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
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="p-3 bg-red-50 rounded-xl mb-4">
        <AlertCircle className="text-red-500" size={32} />
      </div>
      <h3 className="text-lg font-medium text-gray-700">Erro</h3>
      <p className="text-sm text-gray-500 mt-1 max-w-sm">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg
                     hover:bg-indigo-700 transition-colors"
        >
          Tentar novamente
        </button>
      )}
    </div>
  );
}
