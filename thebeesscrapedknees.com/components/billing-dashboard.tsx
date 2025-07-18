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
  Download,
  AlertTriangle,
  RefreshCw,
  ExternalLink,
  Clock,
  Shield,
} from "lucide-react";

interface BillingData {
  hasCustomer: boolean;
  customer?: {
    id: string;
    email: string;
    created: number;
  };
  subscription?: {
    id: string;
    status: string;
    cancel_at_period_end: boolean;
    canceled_at: number | null;
    current_period_start?: number;
    current_period_end?: number;
    product_name: string;
    amount: number | null;
    currency: string;
    interval: string | null;
    trial_end: number | null;
    trial_start: number | null;
  } | null;
  paymentHistory: Array<{
    id: string;
    amount_paid: number;
    amount_due: number;
    currency: string;
    status: string;
    created: number;
    paid_at: number | null;
    invoice_pdf: string | null;
    hosted_invoice_url: string | null;
    description: string | null;
    period_start: number | null;
    period_end: number | null;
  }>;
  paymentMethods: Array<{
    id: string;
    brand: string;
    last4: string;
    exp_month: number;
    exp_year: number;
    is_default: boolean;
  }>;
}

export default function BillingDashboard() {
  const [billingData, setBillingData] = useState<BillingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchBillingData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch("/api/stripe/billing");

      if (!response.ok) {
        throw new Error("Failed to fetch billing data");
      }

      const data = await response.json();
      setBillingData(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load billing data"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBillingData();
  }, []);

  const handleSubscriptionAction = async (action: string) => {
    if (!billingData?.subscription?.id) return;

    try {
      setActionLoading(action);
      const response = await fetch("/api/stripe/manage-subscription", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action,
          subscriptionId: billingData.subscription.id,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to update subscription");
      }

      // Refresh billing data after action
      await fetchBillingData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setActionLoading(null);
    }
  };

  const handleSubscribe = async () => {
    try {
      setActionLoading("subscribe");
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
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start checkout");
      setActionLoading(null);
    }
  };

  const formatAmount = (amount: number, currency: string) => {
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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "active":
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case "trialing":
        return <Clock className="h-5 w-5 text-blue-600" />;
      case "past_due":
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
      case "canceled":
      case "incomplete":
        return <XCircle className="h-5 w-5 text-red-600" />;
      default:
        return <XCircle className="h-5 w-5 text-muted-foreground" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<
      string,
      "default" | "secondary" | "destructive" | "outline"
    > = {
      active: "default",
      trialing: "secondary",
      past_due: "destructive",
      canceled: "outline",
      incomplete: "destructive",
    };

    return (
      <Badge variant={variants[status] || "outline"}>
        {status.replace("_", " ").toUpperCase()}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-32 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!billingData?.hasCustomer) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-6 w-6" />
            Billing & Payments
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-center py-8">
            <CreditCard className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">No Billing Information</h3>
            <p className="text-muted-foreground mb-4">
              Subscribe to a plan to access premium features.
            </p>
            <Button
              onClick={handleSubscribe}
              disabled={actionLoading === "subscribe"}
            >
              {actionLoading === "subscribe"
                ? "Processing..."
                : "Subscribe Now"}
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Subscription Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-6 w-6" />
            Current Subscription
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {billingData.subscription ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getStatusIcon(billingData.subscription.status)}
                  <div>
                    <span className="font-medium">
                      {billingData.subscription.product_name}
                    </span>
                    {billingData.subscription.interval && (
                      <div className="text-xs text-muted-foreground">
                        Billing{" "}
                        {billingData.subscription.interval === "month"
                          ? "monthly"
                          : billingData.subscription.interval === "year"
                          ? "yearly"
                          : billingData.subscription.interval}
                      </div>
                    )}
                  </div>
                </div>
                {getStatusBadge(billingData.subscription.status)}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="font-medium mb-1 flex items-center gap-1">
                    <DollarSign className="h-4 w-4" />
                    Price
                  </div>
                  <div className="text-muted-foreground">
                    {billingData.subscription.amount
                      ? formatAmount(
                          billingData.subscription.amount,
                          billingData.subscription.currency
                        )
                      : "Free"}
                    {billingData.subscription.interval &&
                      ` / ${billingData.subscription.interval}`}
                  </div>
                </div>

                <div>
                  <div className="font-medium mb-1 flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    {billingData.subscription.cancel_at_period_end
                      ? "Access Ends"
                      : "Next Billing"}
                  </div>
                  <div className="text-muted-foreground">
                    {formatDate(billingData.subscription.current_period_end)}
                  </div>
                </div>

                {billingData.subscription.trial_end && (
                  <div className="md:col-span-2">
                    <div className="font-medium mb-1 flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      Trial Ends
                    </div>
                    <div className="text-muted-foreground">
                      {formatDate(billingData.subscription.trial_end)}
                    </div>
                  </div>
                )}

                <div className="md:col-span-2">
                  <div className="font-medium mb-1">Current Billing Period</div>
                  <div className="text-muted-foreground text-xs">
                    {formatDate(billingData.subscription.current_period_start)}{" "}
                    - {formatDate(billingData.subscription.current_period_end)}
                  </div>
                </div>
              </div>

              {billingData.subscription.cancel_at_period_end && (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    Your subscription will be canceled on{" "}
                    {formatDate(billingData.subscription.current_period_end)}.
                    You&apos;ll continue to have access until then.
                  </AlertDescription>
                </Alert>
              )}

              <div className="flex gap-2 pt-2">
                {billingData.subscription.status === "active" && (
                  <>
                    {billingData.subscription.cancel_at_period_end ? (
                      <Button
                        variant="default"
                        size="sm"
                        onClick={() => handleSubscriptionAction("reactivate")}
                        disabled={actionLoading === "reactivate"}
                      >
                        {actionLoading === "reactivate"
                          ? "Processing..."
                          : "Reactivate Subscription"}
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleSubscriptionAction("cancel")}
                        disabled={actionLoading === "cancel"}
                      >
                        {actionLoading === "cancel"
                          ? "Processing..."
                          : "Cancel Subscription"}
                      </Button>
                    )}
                  </>
                )}
              </div>
            </div>
          ) : (
            <div className="text-center py-4">
              <p className="text-muted-foreground mb-4">
                No active subscription
              </p>
              <Button
                onClick={handleSubscribe}
                disabled={actionLoading === "subscribe"}
              >
                {actionLoading === "subscribe"
                  ? "Processing..."
                  : "Subscribe Now"}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Payment Methods */}
      {billingData.paymentMethods.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-6 w-6" />
              Payment Methods
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {billingData.paymentMethods.map((method) => (
                <div
                  key={method.id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <CreditCard className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <div className="font-medium">
                        **** **** **** {method.last4}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {method.brand.toUpperCase()} • Expires{" "}
                        {method.exp_month}/{method.exp_year}
                      </div>
                    </div>
                  </div>
                  {method.is_default && (
                    <Badge variant="secondary">Default</Badge>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Payment History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-6 w-6" />
            Payment History
          </CardTitle>
        </CardHeader>
        <CardContent>
          {billingData.paymentHistory.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No payment history found
            </div>
          ) : (
            <div className="space-y-4">
              {billingData.paymentHistory.slice(0, 10).map((payment) => (
                <div
                  key={payment.id}
                  className="flex items-center justify-between p-4 border rounded-lg"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">
                        {formatAmount(payment.amount_paid, payment.currency)}
                      </span>
                      {getStatusBadge(payment.status)}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {formatDate(payment.created)}
                      {payment.description && ` • ${payment.description}`}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {payment.invoice_pdf && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          window.open(payment.invoice_pdf!, "_blank")
                        }
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                    )}
                    {payment.hosted_invoice_url && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          window.open(payment.hosted_invoice_url!, "_blank")
                        }
                      >
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Customer Info */}
      {billingData.customer && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="h-6 w-6" />
              Billing Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <div className="font-medium mb-1">Customer ID</div>
                <div className="font-mono text-xs bg-muted p-2 rounded">
                  {billingData.customer.id}
                </div>
              </div>
              <div>
                <div className="font-medium mb-1">Customer Since</div>
                <div className="text-muted-foreground">
                  {formatDate(billingData.customer.created)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex justify-center">
        <Button variant="outline" onClick={fetchBillingData} disabled={loading}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh Data
        </Button>
      </div>
    </div>
  );
}
