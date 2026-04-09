import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function ChartCard({
  title,
  description,
  actions,
  children
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <Card className="h-full">
      <CardHeader>
        <div>
          <CardTitle>{title}</CardTitle>
          {description ? <CardDescription className="mt-1">{description}</CardDescription> : null}
        </div>
        {actions}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

