"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Copy,
  Check,
  Code,
  FileText,
  Maximize2,
  X,
  Sparkles,
  RotateCcw,
} from "lucide-react";
import { useTheme } from "next-themes";
import Editor from "@monaco-editor/react";

interface EditorModalProps {
  title: string;
  content: string;
  language: "json" | "python" | "html" | "javascript" | "typescript";
  trigger?: React.ReactNode;
  triggerText?: string;
  description?: string;
  size?: "sm" | "md" | "lg" | "xl" | "full";
}

export function EditorModal({
  title,
  content,
  language,
  trigger,
  triggerText,
  description,
}: EditorModalProps) {
  const [isCopied, setIsCopied] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [editorContent, setEditorContent] = useState(content);
  const [isFormatted, setIsFormatted] = useState(false);
  const { theme } = useTheme();

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(editorContent);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  const handleFormat = () => {
    if (language === "json") {
      try {
        const parsed = JSON.parse(editorContent);
        const formatted = JSON.stringify(parsed, null, 2);
        setEditorContent(formatted);
        setIsFormatted(true);
      } catch (err) {
        console.error("Failed to format JSON:", err);
      }
    }
  };

  const handleReset = () => {
    setEditorContent(content);
    setIsFormatted(false);
  };

  // Add keyboard support
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  const getLanguageIcon = () => {
    switch (language) {
      case "json":
        return <FileText className="h-4 w-4" />;
      case "python":
        return <Code className="h-4 w-4" />;
      case "html":
        return <FileText className="h-4 w-4" />;
      case "javascript":
      case "typescript":
        return <Code className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  const getLanguageColor = () => {
    switch (language) {
      case "json":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
      case "python":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "html":
        return "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200";
      case "javascript":
      case "typescript":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200";
    }
  };

  // Map our language types to Monaco editor language IDs
  const getMonacoLanguage = () => {
    switch (language) {
      case "javascript":
        return "javascript";
      case "typescript":
        return "typescript";
      case "python":
        return "python";
      case "html":
        return "html";
      case "json":
        return "json";
      default:
        return "plaintext";
    }
  };

  const defaultTrigger = (
    <Button variant="outline" size="sm" className="gap-2">
      <Maximize2 className="h-4 w-4" />
      {triggerText || `View ${language.toUpperCase()}`}
    </Button>
  );

  return (
    <>
      {/* Trigger */}
      <div onClick={() => setIsOpen(true)}>
        {trigger || defaultTrigger}
      </div>
      
      {/* Custom full-screen modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm">
          <div className="fixed inset-0 bg-background">
            <div className="flex flex-col h-full w-full">
              {/* Header */}
              <div className="flex-shrink-0 px-6 py-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      {getLanguageIcon()}
                      <h2 className="text-lg font-semibold">{title}</h2>
                    </div>
                    <Badge variant="secondary" className={getLanguageColor()}>
                      {language.toUpperCase()}
                    </Badge>
                    {isFormatted && (
                      <Badge variant="outline" className="text-green-600">
                        Formatted
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs">
                      {editorContent.length.toLocaleString()} chars
                    </Badge>
                    {language === "json" && (
                      <>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={handleFormat}
                          className="gap-2"
                          disabled={isFormatted}
                        >
                          <Sparkles className="h-4 w-4" />
                          Format
                        </Button>
                        {isFormatted && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={handleReset}
                            className="gap-2"
                          >
                            <RotateCcw className="h-4 w-4" />
                            Reset
                          </Button>
                        )}
                      </>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleCopy}
                      className="gap-2"
                    >
                      {isCopied ? (
                        <>
                          <Check className="h-4 w-4 text-green-600" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="h-4 w-4" />
                          Copy
                        </>
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setIsOpen(false)}
                      className="gap-2"
                    >
                      <X className="h-4 w-4" />
                      Close
                    </Button>
                  </div>
                </div>
                {description && (
                  <p className="mt-2 text-sm text-muted-foreground">{description}</p>
                )}
              </div>

              {/* Monaco Editor */}
              <div className="flex-1 min-h-0">
                <Editor
                  height="100%"
                  language={getMonacoLanguage()}
                  value={editorContent}
                  theme={theme === "dark" ? "vs-dark" : "light"}
                  options={{
                    readOnly: true,
                    minimap: { enabled: true },
                    fontSize: 14,
                    lineNumbers: "on",
                    roundedSelection: false,
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                    tabSize: 2,
                    wordWrap: "on",
                    folding: true,
                    lineDecorationsWidth: 0,
                    lineNumbersMinChars: 0,
                    glyphMargin: false,
                    scrollbar: {
                      verticalScrollbarSize: 12,
                      horizontalScrollbarSize: 12,
                    },
                    overviewRulerBorder: false,
                    overviewRulerLanes: 0,
                    hideCursorInOverviewRuler: true,
                    contextmenu: false,
                    links: false,
                    selectOnLineNumbers: true,
                    smoothScrolling: true,
                    cursorBlinking: "smooth",
                    renderLineHighlight: "line",
                    renderWhitespace: "selection",
                    showFoldingControls: "mouseover",
                  }}
                  loading={
                    <div
                      className={`flex items-center justify-center h-full ${
                        theme === "dark"
                          ? "bg-[#1e1e1e] text-white"
                          : "bg-white text-black"
                      }`}
                    >
                      <div className="text-center">
                        <div
                          className={`animate-spin rounded-full h-8 w-8 border-b-2 ${
                            theme === "dark" ? "border-white" : "border-black"
                          } mx-auto mb-2`}
                        ></div>
                        <p>Loading editor...</p>
                      </div>
                    </div>
                  }
                />
              </div>

              {/* Footer */}
              <div className="flex-shrink-0 px-6 py-2 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>
                    {editorContent.split("\n").length} lines •{" "}
                    {language.toUpperCase()}
                  </span>
                  <span>Read-only • Monaco Editor</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
