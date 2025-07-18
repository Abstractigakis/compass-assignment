"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Brain, Loader2, Zap } from "lucide-react";

interface DiagnosticFormProps {
  pageId: string;
  initialGoal?: string;
}

interface DiagnosticResult {
  pageId: string;
  url: string;
  goal: string;
  analysis?: {
    status: string;
    findings: string[];
    extractionStrategy: string;
    confidence: number;
    estimatedDataPoints: number;
  };
  timestamp: string;
  fallback?: boolean;
  error?: string;
}

export function DiagnosticForm({
  pageId,
  initialGoal = "",
}: DiagnosticFormProps) {
  const [goal, setGoal] = useState(initialGoal);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<DiagnosticResult | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(`/api/pages/${pageId}/run-diagnostic`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ goal }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to run diagnostic");
      }

      // Handle success - show results
      setResult(data.result);
      console.log("Diagnostic completed:", data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  if (result) {
    return (
      <Card className="max-w-2xl mx-auto">
        <CardHeader className="text-center">
          <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
            <Brain className="w-6 h-6 text-green-600" />
          </div>
          <CardTitle className="text-xl text-green-600">
            Analysis Complete!
          </CardTitle>
          <CardDescription>
            Your Page has analyzed the page structure
            {result.fallback && " (using fallback analysis)"}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-medium mb-2">Findings:</h4>
            <ul className="text-sm text-muted-foreground space-y-1">
              {result.analysis?.findings?.map(
                (finding: string, index: number) => (
                  <li key={index} className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 bg-purple-500 rounded-full" />
                    {finding}
                  </li>
                )
              )}
            </ul>
          </div>

          {result.analysis?.extractionStrategy && (
            <div>
              <h4 className="font-medium mb-2">Extraction Strategy:</h4>
              <p className="text-sm text-muted-foreground">
                {result.analysis.extractionStrategy}
              </p>
            </div>
          )}

          <div className="flex justify-between text-sm">
            <span>
              Confidence:{" "}
              <strong>
                {Math.round((result.analysis?.confidence || 0) * 100)}%
              </strong>
            </span>
            <span>
              Est. Data Points:{" "}
              <strong>{result.analysis?.estimatedDataPoints || 0}</strong>
            </span>
          </div>

          {result.fallback && (
            <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm text-yellow-800">
              ⚠️ Page server unavailable - showing fallback analysis
            </div>
          )}

          <Button
            onClick={() => setResult(null)}
            variant="outline"
            className="w-full"
          >
            Run Another Analysis
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="max-w-2xl mx-auto">
      <CardHeader className="text-center">
        <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
          <Brain className="w-6 h-6 text-purple-600" />
        </div>
        <CardTitle className="text-xl">Initialize Your Page</CardTitle>
        <CardDescription>
          Tell us what you&apos;re looking to extract and we&apos;ll analyze the
          page structure: : I want to get the categories entity
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="goal">What are you trying to scrape?</Label>
            <Textarea
              id="goal"
              placeholder="e.g., 'I want to extract product prices and reviews from this e-commerce page' or 'I need to collect job listings and their details' or 'I want to monitor news articles and their publication dates'"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              rows={4}
              required
              className="resize-none"
            />
            <p className="text-xs text-muted-foreground">
              Be specific about what data you need and why you&apos;re
              collecting it
            </p>
          </div>

          {error && (
            <div className="text-sm text-red-600 bg-red-50 p-3 rounded">
              {error}
            </div>
          )}

          <Button
            type="submit"
            disabled={isLoading || !goal.trim()}
            className="w-full bg-purple-600 hover:bg-purple-700"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Analyzing Page...
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 mr-2" />
                Run Diagnostic
              </>
            )}
          </Button>

          {isLoading && (
            <p className="text-xs text-muted-foreground text-center">
              This may take 30-60 seconds while we analyze the page structure
            </p>
          )}
        </form>
      </CardContent>
    </Card>
  );
}
