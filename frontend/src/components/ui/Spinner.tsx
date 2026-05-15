import { Loader2 } from 'lucide-react';

interface SpinnerProps {
  /** 'inline' for buttons/small areas, 'fullPage' for center-screen */
  variant?: 'inline' | 'fullPage';
  /** Optional text to show below the spinner */
  text?: string;
}

export default function Spinner({ variant = 'fullPage', text }: SpinnerProps) {
  if (variant === 'inline') {
    return <Loader2 className="animate-spin text-indigo-600" size={18} />;
  }

  return (
    <div className="flex flex-col items-center justify-center py-20">
      <Loader2 className="animate-spin text-indigo-600" size={32} />
      {text && <p className="text-sm text-gray-500 mt-3">{text}</p>}
    </div>
  );
}
