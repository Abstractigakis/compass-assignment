"use client";

import { useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { CheckCircle, XCircle } from "lucide-react";

export default function PaymentNotifications() {
  const searchParams = useSearchParams();
  const success = searchParams.get("success");
  const canceled = searchParams.get("canceled");
  const sessionId = searchParams.get("session_id");

  useEffect(() => {
    // Clear URL parameters after showing notification
    if (success || canceled) {
      const timer = setTimeout(() => {
        const url = new URL(window.location.href);
        url.searchParams.delete("success");
        url.searchParams.delete("canceled");
        url.searchParams.delete("session_id");
        window.history.replaceState({}, "", url.toString());
      }, 5000);

      return () => clearTimeout(timer);
    }
  }, [success, canceled]);

  if (success) {
    return (
      <Alert className="mb-6 border-green-200 bg-green-50">
        <CheckCircle className="h-4 w-4 text-green-600" />
        <AlertDescription className="text-green-800">
          Payment successful! Your subscription is now active.
          {sessionId && (
            <div className="text-xs mt-1 font-mono">Session: {sessionId}</div>
          )}
        </AlertDescription>
      </Alert>
    );
  }

  if (canceled) {
    return (
      <Alert variant="destructive" className="mb-6">
        <XCircle className="h-4 w-4" />
        <AlertDescription>
          Payment was canceled. You can try again anytime.
        </AlertDescription>
      </Alert>
    );
  }

  return null;
}
