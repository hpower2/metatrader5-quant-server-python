export function SkeletonTable({ rows = 6, columns = 5 }: { rows?: number; columns?: number }) {
  return (
    <div className="overflow-hidden rounded-xl border border-border/60">
      <div className="animate-pulse divide-y divide-border/50">
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div key={rowIndex} className="grid gap-4 px-4 py-3" style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}>
            {Array.from({ length: columns }).map((__, columnIndex) => (
              <div key={columnIndex} className="h-4 rounded bg-muted/70" />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

