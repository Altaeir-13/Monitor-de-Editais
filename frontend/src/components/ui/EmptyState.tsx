import { FileX } from 'lucide-react';
import type { ReactNode } from 'react';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export default function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  onAction,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center glass-panel rounded-2xl">
      <div className="p-4 bg-gray-50 rounded-2xl mb-5 shadow-sm border border-gray-100">
        {icon || <FileX className="text-gray-400" size={32} />}
      </div>
      <h3 className="text-xl font-bold text-gray-900">{title}</h3>
      {description && (
        <p className="text-sm text-gray-500 mt-2 max-w-md leading-relaxed">{description}</p>
      )}
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="btn-primary mt-6"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
