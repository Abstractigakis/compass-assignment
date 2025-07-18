"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Play, Plus, Code, FileText, Activity, RefreshCw } from "lucide-react";
import { useRouter } from "next/navigation";
import { Tables } from "@/lib/supabase/db.types";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EditorModal } from "@/components/editor-modal";

type PageEtl = Tables<"etl">;
type PageEtlRun = Tables<"etl_run">;
type PageHtmlRun = Tables<"html">;

interface ExtractionsSectionProps {
  pageId: string;
  initialEtls: PageEtl[] | null;
  initialEtlRuns: PageEtlRun[] | null;
  htmlRuns: PageHtmlRun[];
}

export function ExtractionsSection({
  pageId,
  initialEtls,
  initialEtlRuns,
  htmlRuns,
}: ExtractionsSectionProps) {
  const [etls, setEtls] = useState<PageEtl[] | null>(initialEtls);
  const [etlRuns, setEtlRuns] = useState<PageEtlRun[] | null>(initialEtlRuns);
  const [isCreating, setIsCreating] = useState(false);
  const [runningEtls, setRunningEtls] = useState<Set<string>>(new Set());
  const [newEtl, setNewEtl] = useState({
    goal: "",
    html_page_run_id: "",
  });
  const [selectedHtmlRun, setSelectedHtmlRun] = useState<string>("");
  const [showRunDialog, setShowRunDialog] = useState(false);
  const [currentEtlId, setCurrentEtlId] = useState<string>("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [error, setError] = useState("");
  const [showRetrainDialog, setShowRetrainDialog] = useState(false);
  const [retrainConfig, setRetrainConfig] = useState<PageEtl | null>(null);
  const [refinementGoal, setRefinementGoal] = useState("");
  const [isRetraining, setIsRetraining] = useState(false);
  const router = useRouter();

  // Update local state when props change (from real-time updates)
  useEffect(() => {
    setEtls(initialEtls);
  }, [initialEtls]);

  useEffect(() => {
    setEtlRuns(initialEtlRuns);
  }, [initialEtlRuns]);

  const handleCreateEtl = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreating(true);
    setError("");

    try {
      const response = await fetch(`/api/pages/${pageId}/etl/learn`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          goal: newEtl.goal,
          html_page_run_id: newEtl.html_page_run_id,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.error || "Failed to create extraction configuration"
        );
      }

      setNewEtl({ goal: "", html_page_run_id: "" });
      setDialogOpen(false);
      router.refresh();
    } catch (err) {
      console.error("Error creating ETL:", err);
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsCreating(false);
    }
  };

  const handleRunExtraction = async (etlId: string, htmlRunId?: string) => {
    setRunningEtls((prev) => new Set([...prev, etlId]));
    setError("");

    try {
      const body = htmlRunId ? { html_run_id: htmlRunId } : {};

      const response = await fetch(`/api/pages/${pageId}/etl/${etlId}/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to run extraction");
      }

      setShowRunDialog(false);
      setSelectedHtmlRun("");
      // Refresh the page to show the new run
      router.refresh();
    } catch (err) {
      console.error("Error running extraction:", err);
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setRunningEtls((prev) => {
        const newSet = new Set(prev);
        newSet.delete(etlId);
        return newSet;
      });
    }
  };

  const handleRunExtractionClick = (etlId: string) => {
    setCurrentEtlId(etlId);

    // Find the ETL to get its associated HTML run
    const etl = etls?.find((e) => e.id === etlId);
    if (etl) {
      // Check if ETL is still training
      if (!etl.src_code || etl.src_code.trim() === "") {
        setError(
          "ETL configuration is still being trained. Please wait for training to complete."
        );
        return;
      }

      // Default to the ETL's associated HTML run
      setSelectedHtmlRun(etl.html_page_run_id);
    }

    // Always show the dialog so users can choose a different HTML run if needed
    setShowRunDialog(true);
  };

  const confirmRunExtraction = () => {
    if (selectedHtmlRun && currentEtlId) {
      handleRunExtraction(currentEtlId, selectedHtmlRun);
    }
  };

  const getRunsForEtl = (etlId: string) => {
    if (!etlRuns || !etls) return [];

    // Find the specific ETL
    const etl = etls.find((e) => e.id === etlId);
    if (!etl) return [];

    // Filter runs by ETL ID (if the field exists) or fall back to HTML-based filtering
    const filteredRuns = etlRuns.filter((run) => {
      // If etl_id field exists in the run, use it for direct filtering
      if ("etl_id" in run && run.etl_id) {
        return run.etl_id === etlId;
      }

      // Fallback: Filter by HTML runs from this page (less precise)
      const pageHtmlRunIds = htmlRuns.map((htmlRun) => htmlRun.id);
      return pageHtmlRunIds.includes(run.html);
    });

    return filteredRuns;
  };

  const handleRetrain = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!retrainConfig || !refinementGoal.trim()) return;

    setIsRetraining(true);
    setError("");

    try {
      const response = await fetch(`/api/pages/${pageId}/etl`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          goal: `${retrainConfig.goal}\n\nRefinement Goal: ${refinementGoal}`,
          html_page_run_id: retrainConfig.html_page_run_id,
          etl_name: `${retrainConfig.etl_name || "Untitled"} - Retrained`,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to retrain extraction");
      }

      const data = await response.json();
      console.log("Retrain successful:", data);

      // Reset form and close dialog
      setRefinementGoal("");
      setShowRetrainDialog(false);
      setRetrainConfig(null);
      
      // Refresh the page to show the new extraction
      router.refresh();
    } catch (err) {
      console.error("Error retraining extraction:", err);
      setError(err instanceof Error ? err.message : "Failed to retrain extraction");
    } finally {
      setIsRetraining(false);
    }
  };

  const handleRetrainClick = (etl: PageEtl) => {
    setRetrainConfig(etl);
    setRefinementGoal("");
    setError("");
    setShowRetrainDialog(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-foreground">
            Extractions
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            AI extraction templates for this page
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button size="lg" className="gap-2 shadow-sm">
              <Plus className="h-4 w-4" />
              Train New
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Train New Extraction</DialogTitle>
              <DialogDescription>
                Create a new AI extraction configuration for this page
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreateEtl} className="space-y-4">
              <div>
                <Label htmlFor="goal">Extraction Goal</Label>
                <Input
                  id="goal"
                  value={newEtl.goal}
                  onChange={(e) =>
                    setNewEtl((prev) => ({ ...prev, goal: e.target.value }))
                  }
                  placeholder="e.g., Extract product prices and titles"
                  required
                />
                <p className="text-sm text-muted-foreground mt-1">
                  Describe what data you want to extract from this page
                </p>
              </div>
              <div>
                <Label htmlFor="html-run-select">Base HTML Run</Label>
                <Select
                  value={newEtl.html_page_run_id}
                  onValueChange={(value) =>
                    setNewEtl((prev) => ({ ...prev, html_page_run_id: value }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select an HTML run to base this extraction on" />
                  </SelectTrigger>
                  <SelectContent>
                    {htmlRuns.map((run) => (
                      <SelectItem key={run.id} value={run.id}>
                        <div className="flex items-center justify-between w-full">
                          <span>
                            {run.created_at
                              ? new Date(run.created_at).toLocaleString()
                              : "Unknown time"}
                          </span>
                          <span className="text-xs text-muted-foreground ml-2">
                            {run.html.length} chars
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-sm text-muted-foreground mt-1">
                  This extraction will be trained on the selected HTML snapshot
                </p>
              </div>
              {error && (
                <div className="text-sm text-destructive bg-destructive/10 p-3 rounded">
                  {error}
                </div>
              )}
              <div className="flex justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isCreating || !newEtl.html_page_run_id}
                >
                  {isCreating ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      Creating...
                    </>
                  ) : (
                    "Create Extraction"
                  )}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

        {/* HTML Run Selection Dialog */}
        <Dialog open={showRunDialog} onOpenChange={setShowRunDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Select HTML Run</DialogTitle>
              <DialogDescription>
                Choose which HTML snapshot to run the extraction against.
                Defaults to the HTML run this extraction was trained on.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="html-run">HTML Run</Label>
                <Select
                  value={selectedHtmlRun}
                  onValueChange={setSelectedHtmlRun}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select an HTML run" />
                  </SelectTrigger>
                  <SelectContent>
                    {htmlRuns.map((run) => (
                      <SelectItem key={run.id} value={run.id}>
                        <div className="flex items-center justify-between w-full">
                          <span>
                            {run.created_at
                              ? new Date(run.created_at).toLocaleString()
                              : "Unknown time"}
                          </span>
                          <span className="text-xs text-muted-foreground ml-2">
                            {run.html.length} chars
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowRunDialog(false)}
                >
                  Cancel
                </Button>
                <Button
                  onClick={confirmRunExtraction}
                  disabled={!selectedHtmlRun}
                >
                  Run Extraction
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Re-train Dialog */}
        <Dialog open={showRetrainDialog} onOpenChange={setShowRetrainDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Re-train Extraction</DialogTitle>
              <DialogDescription>
                Improve this extraction by providing additional context or refinement goals.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleRetrain} className="space-y-4">
              {retrainConfig && (
                <div className="bg-slate-50 dark:bg-slate-900 p-4 rounded-lg border">
                  <h4 className="font-medium text-sm mb-2">Current Goal:</h4>
                  <p className="text-sm text-muted-foreground">{retrainConfig.goal}</p>
                </div>
              )}
              <div>
                <Label htmlFor="refinement-goal">Refinement Goal</Label>
                <Textarea
                  id="refinement-goal"
                  placeholder="Describe what you want to improve or change about this extraction..."
                  value={refinementGoal}
                  onChange={(e) => setRefinementGoal(e.target.value)}
                  className="mt-1"
                  rows={4}
                />
                <p className="text-sm text-muted-foreground mt-1">
                  This will create a new extraction with the refined goal while preserving the original.
                </p>
              </div>
              {error && (
                <div className="text-sm text-destructive bg-destructive/10 p-3 rounded">
                  {error}
                </div>
              )}
              <div className="flex justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowRetrainDialog(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isRetraining || !refinementGoal.trim()}
                >
                  {isRetraining ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      Re-training...
                    </>
                  ) : (
                    "Re-train Extraction"
                  )}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
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

      {etls && etls.length > 0 ? (
        <div className="space-y-6">
          {etls.map((etl) => {
            const runs = getRunsForEtl(etl.id);
            const isRunning = runningEtls.has(etl.id);
            const isTraining = !etl.src_code || etl.src_code.trim() === "";

            return (
              <Card key={etl.id} className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <div
                        className={`w-2 h-2 rounded-full mt-2 ${
                          isTraining ? "bg-yellow-500" : "bg-blue-500"
                        }`}
                      ></div>
                      <div className="flex-1">
                        <CardTitle className="text-base font-medium">
                          {etl.goal}
                        </CardTitle>
                        <div className="flex flex-col gap-1 mt-1">
                          <CardDescription className="text-xs">
                            Created{" "}
                            {etl.created_at
                              ? new Date(etl.created_at).toLocaleDateString()
                              : "Unknown"}
                          </CardDescription>
                          <CardDescription className="text-xs">
                            Based on HTML from{" "}
                            {(() => {
                              const htmlRun = htmlRuns.find(
                                (run) => run.id === etl.html_page_run_id
                              );
                              return htmlRun?.created_at
                                ? new Date(htmlRun.created_at).toLocaleString()
                                : "Unknown time";
                            })()}
                          </CardDescription>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleRetrainClick(etl)}
                        disabled={isRunning || isTraining}
                        className="gap-2"
                      >
                        <RefreshCw className="h-4 w-4" />
                        Re-train
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => handleRunExtractionClick(etl.id)}
                        disabled={isRunning || isTraining}
                        className="gap-2 shrink-0"
                      >
                        {isRunning ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : isTraining ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Play className="h-4 w-4" />
                        )}
                        {isRunning
                          ? "Running..."
                          : isTraining
                          ? "Training..."
                          : "Run"}
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  {isTraining ? (
                    <div className="mb-4">
                      <div className="flex items-center gap-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
                        <Loader2 className="h-4 w-4 animate-spin text-yellow-600" />
                        <div>
                          <h4 className="text-sm font-medium text-yellow-900 dark:text-yellow-100">
                            Training in Progress
                          </h4>
                          <p className="text-xs text-yellow-700 dark:text-yellow-300 mt-1">
                            AI is learning how to extract data from your
                            selected HTML. This may take a few minutes.
                          </p>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <Tabs defaultValue="source" className="w-full">
                      <TabsList className="grid w-full grid-cols-3">
                        <TabsTrigger
                          value="source"
                          className="flex items-center gap-2"
                        >
                          <Code className="h-4 w-4" />
                          Source
                        </TabsTrigger>
                        <TabsTrigger
                          value="schema"
                          className="flex items-center gap-2"
                        >
                          <FileText className="h-4 w-4" />
                          Schema
                        </TabsTrigger>
                        <TabsTrigger
                          value="runs"
                          className="flex items-center gap-2"
                        >
                          <Activity className="h-4 w-4" />
                          Runs ({runs?.length || 0})
                        </TabsTrigger>
                      </TabsList>

                      <TabsContent value="source" className="mt-4">
                        {etl.src_code ? (
                          <div className="text-center py-8">
                            <EditorModal
                              title={`Source Code - ${etl.goal}`}
                              content={etl.src_code}
                              language="python"
                              triggerText="View Source Code"
                              description="Python code generated for this extraction"
                              size="xl"
                            />
                            <p className="text-sm text-muted-foreground mt-2">
                              Click to view the generated Python extraction code
                            </p>
                          </div>
                        ) : (
                          <div className="text-center py-8">
                            <p className="text-sm text-muted-foreground">
                              No source code available
                            </p>
                          </div>
                        )}
                      </TabsContent>

                      <TabsContent value="schema" className="mt-4">
                        {etl.output_json_schema &&
                        typeof etl.output_json_schema === "object" ? (
                          <div className="text-center py-8">
                            <EditorModal
                              title={`Output Schema - ${etl.goal}`}
                              content={JSON.stringify(
                                etl.output_json_schema,
                                null,
                                2
                              )}
                              language="json"
                              triggerText="View Output Schema"
                              description="JSON schema defining the structure of extraction results"
                              size="lg"
                            />
                            <p className="text-sm text-muted-foreground mt-2">
                              Click to view the JSON schema for extraction
                              output
                            </p>
                          </div>
                        ) : (
                          <div className="text-center py-8">
                            <p className="text-sm text-muted-foreground">
                              No output schema available
                            </p>
                          </div>
                        )}
                      </TabsContent>

                      <TabsContent value="runs" className="mt-4">
                        {runs && runs.length > 0 ? (
                          <div className="space-y-3">
                            {runs.slice(0, 5).map((run) => (
                              <div
                                key={run.id}
                                className="bg-slate-50 dark:bg-slate-900 p-4 rounded-lg border"
                              >
                                <div className="flex items-center justify-between mb-3">
                                  <Badge
                                    variant="secondary"
                                    className="text-xs"
                                  >
                                    {run.created_at
                                      ? new Date(
                                          run.created_at
                                        ).toLocaleString()
                                      : "Unknown"}
                                  </Badge>
                                  <span className="text-xs text-muted-foreground">
                                    HTML: {run.html.slice(0, 8)}...
                                  </span>
                                </div>
                                {run.output_json &&
                                  typeof run.output_json === "object" && (
                                    <div className="mt-3">
                                      <EditorModal
                                        title={`Extraction Results - ${new Date(
                                          run.created_at || ""
                                        ).toLocaleString()}`}
                                        content={JSON.stringify(
                                          run.output_json,
                                          null,
                                          2
                                        )}
                                        language="json"
                                        triggerText="View Results"
                                        description="JSON results from this extraction run"
                                        size="lg"
                                        trigger={
                                          <Button
                                            variant="outline"
                                            size="sm"
                                            className="w-full"
                                          >
                                            <FileText className="h-4 w-4 mr-2" />
                                            View Results
                                          </Button>
                                        }
                                      />
                                    </div>
                                  )}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="text-center py-8">
                            <p className="text-sm text-muted-foreground">
                              No runs yet. Click &quot;Run&quot; to execute this
                              extraction.
                            </p>
                          </div>
                        )}
                      </TabsContent>
                    </Tabs>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : (
        <Card className="border-dashed border-2">
          <CardContent className="text-center py-12">
            <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
              <Plus className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">
              No Extraction Configurations Yet
            </h3>
            <p className="text-sm text-muted-foreground mb-6 max-w-md mx-auto">
              Train your first AI extraction to automatically extract data from
              this page
            </p>
            <Button
              onClick={() => setDialogOpen(true)}
              size="lg"
              className="gap-2"
            >
              <Plus className="h-4 w-4" />
              Train First Extraction
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
