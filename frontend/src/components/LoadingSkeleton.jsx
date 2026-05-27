export default function LoadingSkeleton() {
  return (
    <div className="animate-pulse space-y-3">
      <div className="h-5 w-2/3 rounded-full bg-white/10" />
      <div className="h-5 w-1/2 rounded-full bg-white/10" />
      <div className="h-5 w-full rounded-full bg-white/10" />
    </div>
  );
}
