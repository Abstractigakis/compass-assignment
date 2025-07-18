"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, RefreshCw } from "lucide-react";
import { useRouter } from "next/navigation";
import { Tables } from "@/lib/supabase/db.types";
import { EditorModal } from "@/components/editor-modal";

type HtmlRun = Tables<"html">;

interface MetaData {
  content_type?: string;
  fetch_timestamp?: string;
  html_length?: number;
  url?: string;
}

interface HtmlRunsSectionProps {
  pageId: string;
  initialHtmlRuns: HtmlRun[] | null;
}

export function HtmlRunsSection({
  pageId,
  initialHtmlRuns,
}: HtmlRunsSectionProps) {
  const [htmlRuns, setHtmlRuns] = useState<HtmlRun[] | null>(initialHtmlRuns);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  // Update local state when props change (from real-time updates)
  useEffect(() => {
    setHtmlRuns(initialHtmlRuns);
  }, [initialHtmlRuns]);

  const handleFetchHtml = async () => {
    setIsLoading(true);
    setError("");

    try {
      const response = await fetch(`/api/pages/${pageId}/html`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to fetch HTML");
      }

      // Refresh the page to show the new HTML run
      router.refresh();
    } catch (err) {
      console.error("Error fetching HTML:", err);
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-foreground">HTML Runs</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Recent HTML fetches from this page
          </p>
        </div>
        <Button
          onClick={handleFetchHtml}
          disabled={isLoading}
          size="lg"
          className="gap-2 shadow-sm"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          {isLoading ? "Fetching..." : "Fetch Fresh HTML"}
        </Button>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-destructive rounded-full"></div>
            <p className="text-sm font-medium text-destructive">Error</p>
          </div>
          <p className="text-sm text-destructive mt-1">{error}</p>
        </div>
      )}

      {htmlRuns && htmlRuns.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {htmlRuns.map((run) => (
            <Card key={run.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <div>
                      <CardTitle className="text-base font-medium">
                        HTML Fetch
                      </CardTitle>
                      <p className="text-xs text-muted-foreground">
                        {run.created_at
                          ? new Date(run.created_at).toLocaleString()
                          : "Unknown time"}
                      </p>
                    </div>
                  </div>
                  <Badge variant="secondary" className="font-mono text-xs">
                    {run.html?.length || 0} chars
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="space-y-3">
                  <div className="flex flex-col gap-1 text-sm text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <span className="font-medium">Size:</span>
                      <span>
                        {(run.html?.length || 0).toLocaleString()} characters
                      </span>
                    </div>
                    {run.meta &&
                      typeof run.meta === "object" &&
                      "content_type" in run.meta && (
                        <div className="flex items-center gap-1">
                          <span className="font-medium">Type:</span>
                          <span className="truncate">
                            {(run.meta as MetaData).content_type || "unknown"}
                          </span>
                        </div>
                      )}
                  </div>
                  <div className="mt-3">
                    <EditorModal
                      title={`HTML Content - ${new Date(
                        run.created_at || ""
                      ).toLocaleString()}`}
                      content={run.html || ""}
                      language="html"
                      triggerText="View HTML Content"
                      description="Raw HTML content fetched from the page"
                      size="xl"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="border-dashed border-2">
          <CardContent className="text-center py-16">
            <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
              <RefreshCw className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">
              No HTML Runs Yet
            </h3>
            <p className="text-sm text-muted-foreground mb-6 max-w-md mx-auto">
              Fetch HTML from this page to see it here. This will create a
              snapshot of the page content.
            </p>
            <Button
              onClick={handleFetchHtml}
              disabled={isLoading}
              size="lg"
              className="gap-2"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              {isLoading ? "Fetching..." : "Fetch First HTML"}
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
