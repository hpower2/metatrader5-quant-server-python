import { cn } from "@/lib/utils/cn";

export interface DataTableColumn<T> {
  key: string;
  header: string;
  className?: string;
  cell: (row: T) => React.ReactNode;
}

export function DataTable<T>({
  data,
  columns,
  emptyMessage = "No rows available"
}: {
  data: T[];
  columns: Array<DataTableColumn<T>>;
  emptyMessage?: string;
}) {
  return (
    <div className="overflow-hidden rounded-xl border border-border/60">
      <div className="max-h-[28rem] overflow-auto">
        <table className="min-w-full divide-y divide-border/60 text-sm">
          <thead className="sticky top-0 z-10 bg-card/95 backdrop-blur-sm">
            <tr>
              {columns.map((column) => (
                <th key={column.key} className={cn("px-4 py-3 text-left font-medium text-muted-foreground", column.className)}>
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border/50">
            {data.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-10 text-center text-muted-foreground">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              data.map((row, index) => (
                <tr key={index} className="bg-card/30 transition hover:bg-muted/20">
                  {columns.map((column) => (
                    <td key={column.key} className={cn("px-4 py-3 align-top", column.className)}>
                      {column.cell(row)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

