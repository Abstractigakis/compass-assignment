// Utility functions for calculating subscription dates

export interface SubscriptionDateInfo {
  nextPaymentDate: number | null;
  serviceEndDate: number | null;
  currentPeriodStart: number | null;
  currentPeriodEnd: number | null;
  isTrialing: boolean;
  isCanceled: boolean;
  willCancelAtPeriodEnd: boolean;
}

export function calculateSubscriptionDates(
  subscription: Record<string, unknown>
): SubscriptionDateInfo {
  const {
    current_period_start,
    current_period_end,
    trial_end,
    status,
    cancel_at_period_end,
    cancel_at,
    canceled_at,
    ended_at,
  } = subscription;

  const isTrialing = status === "trialing";
  const isCanceled = status === "canceled" || !!canceled_at;
  const willCancelAtPeriodEnd = cancel_at_period_end === true;

  // Helper function to safely convert to number
  const toNumber = (value: unknown): number | null => {
    return typeof value === "number" ? value : null;
  };

  // Calculate next payment date
  let nextPaymentDate: number | null = null;

  if (isTrialing && trial_end) {
    // If in trial, next payment is at trial end
    nextPaymentDate = toNumber(trial_end);
  } else if (
    status === "active" &&
    !willCancelAtPeriodEnd &&
    current_period_end
  ) {
    // If active and not canceling, next payment is at period end
    nextPaymentDate = toNumber(current_period_end);
  } else if (cancel_at) {
    // If there's a specific cancellation date set
    nextPaymentDate = toNumber(cancel_at);
  }

  // Calculate service end date
  let serviceEndDate: number | null = null;

  if (isCanceled && ended_at) {
    // Already ended
    serviceEndDate = toNumber(ended_at);
  } else if (willCancelAtPeriodEnd && current_period_end) {
    // Will end at current period end
    serviceEndDate = toNumber(current_period_end);
  } else if (cancel_at) {
    // Will end at specific cancel date
    serviceEndDate = toNumber(cancel_at);
  } else if (status === "active") {
    // Active subscription - service continues until next billing
    serviceEndDate = null; // No end date
  }

  return {
    nextPaymentDate,
    serviceEndDate,
    currentPeriodStart: toNumber(current_period_start),
    currentPeriodEnd: toNumber(current_period_end),
    isTrialing,
    isCanceled,
    willCancelAtPeriodEnd,
  };
}

export function formatSubscriptionDateInfo(dateInfo: SubscriptionDateInfo) {
  const {
    nextPaymentDate,
    serviceEndDate,
    isTrialing,
    isCanceled,
    willCancelAtPeriodEnd,
  } = dateInfo;

  let nextBillingLabel = "Next Billing";
  let nextBillingDate = nextPaymentDate;

  if (isTrialing) {
    nextBillingLabel = "Trial Ends / First Payment";
  } else if (willCancelAtPeriodEnd) {
    nextBillingLabel = "Access Ends";
    nextBillingDate = serviceEndDate;
  } else if (isCanceled) {
    nextBillingLabel = "Service Ended";
    nextBillingDate = serviceEndDate;
  }

  return {
    nextBillingLabel,
    nextBillingDate,
    serviceEndDate,
  };
}
