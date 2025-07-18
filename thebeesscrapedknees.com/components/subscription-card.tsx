"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  CreditCard,
  CheckCircle,
  XCircle,
  Calendar,
  DollarSign,
  AlertTriangle,
} from "lucide-react";

interface SubscriptionData {
  hasActiveSubscription: boolean;
  subscription: {
    id: string;
    status: string;
    current_period_end?: number;
    current_period_start?: number;
    cancel_at_period_end: boolean;
    canceled_at: number | null;
    product_name: string;
    amount: number | null;
    currency: string;
    interval: string | null;
  } | null;
}

export default function SubscriptionCard() {
  const [subscriptionData, setSubscriptionData] =
    useState<SubscriptionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const fetchSubscriptionStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/stripe/subscription");

      if (!response.ok) {
        throw new Error("Failed to fetch subscription status");
      }

      const data = await response.json();
      setSubscriptionData(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load subscription"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubscriptionStatus();
  }, []);

  const handleSubscribe = async () => {
    try {
      setIsProcessing(true);
      setError(null);

      const response = await fetch("/api/stripe/checkout", {
        method: "POST",
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to create checkout session");
      }

      const { url } = await response.json();

      if (url) {
        window.location.href = url;
      } else {
        throw new Error("No checkout URL received");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start checkout");
      setIsProcessing(false);
    }
  };

  const formatAmount = (amount: number | null, currency: string) => {
    if (!amount) return "Free";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency.toUpperCase(),
    }).format(amount / 100);
  };

  const formatDate = (timestamp: number | undefined | null) => {
    if (!timestamp || isNaN(timestamp)) {
      return "Not available";
    }

    const date = new Date(timestamp * 1000);
    if (isNaN(date.getTime())) {
      return "Invalid date";
    }

    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-10 w-32" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CreditCard className="h-5 w-5" />
          Subscription
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            <XCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {subscriptionData?.hasActiveSubscription ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <span className="font-medium">Active Subscription</span>
              </div>
              <Badge variant="default" className="bg-green-100 text-green-800">
                {subscriptionData.subscription?.status}
              </Badge>
            </div>

            {subscriptionData.subscription && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="font-medium mb-1">Plan</div>
                  <div className="text-muted-foreground">
                    {subscriptionData.subscription.product_name}
                  </div>
                </div>

                <div>
                  <div className="font-medium mb-1 flex items-center gap-1">
                    <DollarSign className="h-4 w-4" />
                    Price
                  </div>
                  <div className="text-muted-foreground">
                    {formatAmount(
                      subscriptionData.subscription.amount,
                      subscriptionData.subscription.currency
                    )}
                    {subscriptionData.subscription.interval &&
                      ` / ${subscriptionData.subscription.interval}`}
                  </div>
                </div>

                <div className="md:col-span-2">
                  <div className="font-medium mb-1 flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    {subscriptionData.subscription.cancel_at_period_end
                      ? "Access Ends"
                      : "Next Billing Date"}
                  </div>
                  <div className="text-muted-foreground">
                    {formatDate(
                      subscriptionData.subscription.current_period_end
                    )}
                  </div>
                </div>
              </div>
            )}

            {subscriptionData.subscription?.cancel_at_period_end && (
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  Your subscription will be canceled on{" "}
                  {formatDate(subscriptionData.subscription.current_period_end)}
                  . You&apos;ll continue to have access until then.
                </AlertDescription>
              </Alert>
            )}

            <div className="pt-2">
              <Button variant="outline" size="sm" disabled>
                Manage Subscription
              </Button>
              <p className="text-xs text-muted-foreground mt-2">
                Contact support to manage your subscription
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <XCircle className="h-5 w-5 text-muted-foreground" />
              <span className="font-medium">No Active Subscription</span>
            </div>

            <p className="text-sm text-muted-foreground">
              Subscribe to unlock premium features and get the most out of your
              account.
            </p>

            <Button
              onClick={handleSubscribe}
              disabled={isProcessing}
              className="w-full sm:w-auto"
            >
              {isProcessing ? "Processing..." : "Subscribe Now"}
            </Button>
          </div>
        )}

        <div className="pt-4 border-t">
          <Button
            variant="ghost"
            size="sm"
            onClick={fetchSubscriptionStatus}
            disabled={loading}
          >
            Refresh Status
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
