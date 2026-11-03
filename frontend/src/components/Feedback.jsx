import { AlertCircle, LoaderCircle } from "lucide-react";

export function Loading({ label = "Loading your marketplace..." }) {
  return <div className="loading-state"><LoaderCircle className="spin" size={23} /><span>{label}</span></div>;
}

export function ErrorState({ message, onRetry }) {
  return <div className="error-state"><AlertCircle size={19} /><div><strong>Something went wrong</strong><p>{message}</p></div>{onRetry && <button className="button button-outline" onClick={onRetry}>Try again</button>}</div>;
}

export function EmptyState({ title, description, action }) {
  return <div className="empty-state"><div className="empty-icon"><AlertCircle size={21} /></div><strong>{title}</strong><p>{description}</p>{action}</div>;
}

export function Notice({ notice, onClose }) {
  if (!notice) return null;
  return <div className={`notice ${notice.type}`} role="status"><span>{notice.message}</span><button aria-label="Dismiss notification" onClick={onClose}>×</button></div>;
}
