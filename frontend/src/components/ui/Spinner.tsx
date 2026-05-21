import { Loader2 } from 'lucide-react';

interface SpinnerProps {
  /** 'inline' for buttons/small areas, 'fullPage' for center-screen */
  variant?: 'inline' | 'fullPage';
  /** Optional text to show below the spinner */
  text?: string;
}

export default function Spinner({ variant = 'fullPage', text }: SpinnerProps) {
  if (variant === 'inline') {
    return <Loader2 className="animate-spin text-primary-600" size={18} />;
  }

  return (
    <div className="flex flex-col items-center justify-center py-24 px-4 glass-panel rounded-2xl border-none shadow-none bg-transparent">
      <Loader2 className="animate-spin text-primary-600 mb-4" size={40} />
      {text && <p className="text-sm font-medium text-gray-500 animate-pulse">{text}</p>}
    </div>
  );
}
