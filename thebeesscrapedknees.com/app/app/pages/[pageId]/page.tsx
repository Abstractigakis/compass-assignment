import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { ArrowLeft, ExternalLink, Calendar, Globe } from "lucide-react";
import Link from "next/link";
import { PageDetailsClient } from "@/components/page-details-client";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";

interface PageProps {
  params: Promise<{
    pageId: string;
  }>;
}

export default async function PageDetails({ params }: PageProps) {
  const { pageId } = await params;
  const sb = await createClient();

  // Check authentication
  const {
    data: { user },
  } = await sb.auth.getUser();
  if (!user) return redirect("/auth/sign-in");

  // Get the specific page
  const { data: page, error: pageError } = await sb
    .from("pages")
    .select("*")
    .eq("id", pageId)
    .eq("user_id", user.id)
    .single();

  if (pageError) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="mb-6">
          <Link
            href="/app"
            className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Pages
          </Link>
        </div>
        <Card>
          <CardHeader>
            <CardTitle className="text-destructive">Page Not Found</CardTitle>
            <CardDescription>
              The page you&apos;re looking for doesn&apos;t exist or you
              don&apos;t have permission to view it.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  // Get recent HTML runs
  const { data: htmlRuns } = await sb
    .from("html")
    .select("*")
    .eq("page_id", pageId)
    .eq("user_id", user.id)
    .order("created_at", { ascending: false })
    .limit(10);

  // Get ETL configurations for this page
  const { data: pageEtls } = await sb
    .from("etl")
    .select("*")
    .eq("page_id", pageId)
    .eq("user_id", user.id)
    .order("created_at", { ascending: false });

  // Get recent ETL runs (these should be linked to page_etl somehow, but the schema seems incomplete)
  const { data: etlRuns } = await sb
    .from("etl_run")
    .select("*")
    .eq("user_id", user.id)
    .order("created_at", { ascending: false })
    .limit(10);

  const pageUrl = new URL(page.url);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="mb-8">
          <Link
            href="/app"
            className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground mb-6 transition-colors"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Pages
          </Link>

          <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-3">
                  <Globe className="h-8 w-8 text-primary" />
                  <h1 className="text-3xl font-bold text-foreground">
                    {pageUrl.hostname}
                  </h1>
                </div>
                <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-3">
                  <code className="bg-slate-100 dark:bg-slate-700 px-3 py-2 rounded-md text-sm font-mono break-all">
                    {page.url}
                  </code>
                  <Link
                    href={page.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-primary transition-colors"
                  >
                    <ExternalLink className="h-4 w-4" />
                    Visit Page
                  </Link>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Calendar className="h-4 w-4" />
                  Created{" "}
                  {page.created_at
                    ? new Date(page.created_at).toLocaleDateString()
                    : "Unknown"}
                </div>
              </div>
              <div className="flex flex-col gap-2 text-right">
                <div className="text-sm text-muted-foreground">
                  {htmlRuns?.length || 0} HTML runs
                </div>
                <div className="text-sm text-muted-foreground">
                  {pageEtls?.length || 0} extractions
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <PageDetailsClient
          pageId={pageId}
          userId={user.id}
          pageUrl={page.url}
          initialHtmlRuns={htmlRuns}
          initialPageEtls={pageEtls}
          initialEtlRuns={etlRuns}
        />
      </div>
    </div>
  );
}
