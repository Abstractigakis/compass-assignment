"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { HtmlRunsSection } from "@/components/html-runs-section";
import { ExtractionsSection } from "@/components/extractions-section";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Tables } from "@/lib/supabase/db.types";
import { FileText, Settings, Eye } from "lucide-react";

type HtmlRun = Tables<"html">;
type PageEtl = Tables<"etl">;
type PageEtlRun = Tables<"etl_run">;

interface PageDetailsClientProps {
  pageId: string;
  userId: string;
  pageUrl: string;
  initialHtmlRuns: HtmlRun[] | null;
  initialPageEtls: PageEtl[] | null;
  initialEtlRuns: PageEtlRun[] | null;
}

export function PageDetailsClient({
  pageId,
  userId,
  pageUrl,
  initialHtmlRuns,
  initialPageEtls,
  initialEtlRuns,
}: PageDetailsClientProps) {
  const [htmlRuns, setHtmlRuns] = useState<HtmlRun[] | null>(initialHtmlRuns);
  const [pageEtls, setPageEtls] = useState<PageEtl[] | null>(initialPageEtls);
  const [etlRuns, setEtlRuns] = useState<PageEtlRun[] | null>(initialEtlRuns);

  useEffect(() => {
    const supabase = createClient();

    // Subscribe to HTML runs for this page
    const htmlChannel = supabase
      .channel("html_runs")
      .on(
        "postgres_changes",
        {
          event: "*",
          schema: "public",
          table: "html",
          filter: `page_id=eq.${pageId}`,
        },
        (payload) => {
          console.log("HTML runs change:", payload);

          if (payload.eventType === "INSERT") {
            setHtmlRuns((prev) => [payload.new as HtmlRun, ...(prev || [])]);
          } else if (payload.eventType === "UPDATE") {
            setHtmlRuns(
              (prev) =>
                prev?.map((run) =>
                  run.id === payload.new.id ? (payload.new as HtmlRun) : run
                ) || []
            );
          } else if (payload.eventType === "DELETE") {
            setHtmlRuns(
              (prev) => prev?.filter((run) => run.id !== payload.old.id) || []
            );
          }
        }
      )
      .subscribe();

    // Subscribe to ETL configurations for this page
    const etlChannel = supabase
      .channel("page_etls")
      .on(
        "postgres_changes",
        {
          event: "*",
          schema: "public",
          table: "etl",
          filter: `page_id=eq.${pageId}`,
        },
        (payload) => {
          console.log("ETL change:", payload);

          if (payload.eventType === "INSERT") {
            setPageEtls((prev) => [payload.new as PageEtl, ...(prev || [])]);
          } else if (payload.eventType === "UPDATE") {
            setPageEtls(
              (prev) =>
                prev?.map((etl) =>
                  etl.id === payload.new.id ? (payload.new as PageEtl) : etl
                ) || []
            );
          } else if (payload.eventType === "DELETE") {
            setPageEtls(
              (prev) => prev?.filter((etl) => etl.id !== payload.old.id) || []
            );
          }
        }
      )
      .subscribe();

    // Subscribe to ETL runs for this user
    const etlRunsChannel = supabase
      .channel("etl_runs")
      .on(
        "postgres_changes",
        {
          event: "*",
          schema: "public",
          table: "etl_run",
          filter: `user_id=eq.${userId}`,
        },
        (payload) => {
          console.log("ETL runs change:", payload);

          if (payload.eventType === "INSERT") {
            setEtlRuns((prev) => [payload.new as PageEtlRun, ...(prev || [])]);
          } else if (payload.eventType === "UPDATE") {
            setEtlRuns(
              (prev) =>
                prev?.map((run) =>
                  run.id === payload.new.id ? (payload.new as PageEtlRun) : run
                ) || []
            );
          } else if (payload.eventType === "DELETE") {
            setEtlRuns(
              (prev) => prev?.filter((run) => run.id !== payload.old.id) || []
            );
          }
        }
      )
      .subscribe();

    // Cleanup subscriptions on unmount
    return () => {
      htmlChannel.unsubscribe();
      etlChannel.unsubscribe();
      etlRunsChannel.unsubscribe();
    };
  }, [pageId, userId]);

  return (
    <div className="max-w-full">
      <Tabs defaultValue="html-runs" className="w-full">
        <TabsList className="grid w-full grid-cols-3 mb-6">
          <TabsTrigger value="html-runs" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            HTML Runs ({htmlRuns?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="extractions" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Extractions ({pageEtls?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="preview" className="flex items-center gap-2">
            <Eye className="h-4 w-4" />
            Preview
          </TabsTrigger>
        </TabsList>

        <TabsContent value="html-runs" className="mt-0">
          <HtmlRunsSection pageId={pageId} initialHtmlRuns={htmlRuns} />
        </TabsContent>

        <TabsContent value="extractions" className="mt-0">
          {htmlRuns && htmlRuns.length > 0 ? (
            <ExtractionsSection
              pageId={pageId}
              initialEtls={pageEtls}
              initialEtlRuns={etlRuns}
              htmlRuns={htmlRuns}
            />
          ) : (
            <Card className="h-fit">
              <CardHeader className="text-center py-12">
                <CardTitle className="text-lg text-muted-foreground">
                  Extractions Unavailable
                </CardTitle>
                <CardDescription>
                  Fetch HTML first to create extractions. Switch to the HTML
                  Runs tab to get started.
                </CardDescription>
              </CardHeader>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="preview" className="mt-0">
          <Card className="h-fit">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Eye className="h-5 w-5" />
                Page Preview
              </CardTitle>
              <CardDescription>
                Live preview of the webpage being analyzed
              </CardDescription>
            </CardHeader>
            <div className="p-6 pt-0">
              <div className="border rounded-lg overflow-hidden bg-white dark:bg-slate-900">
                <div className="bg-slate-100 dark:bg-slate-800 px-4 py-2 text-sm text-muted-foreground border-b">
                  {pageUrl}
                </div>
                <iframe
                  src={pageUrl}
                  className="w-full h-[600px] border-0"
                  title="Page Preview"
                  sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
                />
              </div>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
