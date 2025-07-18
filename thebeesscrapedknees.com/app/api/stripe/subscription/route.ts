import { NextResponse } from "next/server";
import { stripe } from "@/lib/stripe";
import { createClient } from "@/lib/supabase/server";

export async function GET() {
  try {
    const supabase = await createClient();

    // Check if user is authenticated
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();

    if (authError || !user || !user.email) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Find customer by email
    const customers = await stripe.customers.list({
      email: user.email,
      limit: 1,
    });

    if (customers.data.length === 0) {
      return NextResponse.json({
        hasActiveSubscription: false,
        subscription: null,
      });
    }

    const customer = customers.data[0];

    // Get active subscriptions for this customer
    const subscriptions = await stripe.subscriptions.list({
      customer: customer.id,
      status: "all", // Get all statuses to include trialing, etc.
      limit: 10,
      expand: ["data.default_payment_method"], // Expand additional data
    });

    const activeSubscriptions = subscriptions.data.filter((sub) =>
      ["active", "trialing"].includes(sub.status)
    );

    if (activeSubscriptions.length === 0) {
      return NextResponse.json({
        hasActiveSubscription: false,
        subscription: null,
      });
    }

    // Return the first active subscription with details
    const subscription = activeSubscriptions[0];

    // Debug: Log the subscription object to see what fields are available
    console.log("=== FULL STRIPE SUBSCRIPTION OBJECT ===");
    console.log(JSON.stringify(subscription, null, 2));
    console.log("=== END SUBSCRIPTION OBJECT ===");

    console.log("Stripe subscription object keys:", Object.keys(subscription));
    const debugSub = subscription as unknown as Record<string, unknown>;

    // Log all the date-related and billing-related properties
    console.log("=== DATE AND BILLING PROPERTIES ===");
    console.log("current_period_end:", debugSub.current_period_end);
    console.log("current_period_start:", debugSub.current_period_start);
    console.log("billing_cycle_anchor:", debugSub.billing_cycle_anchor);
    console.log("days_until_due:", debugSub.days_until_due);
    console.log("cancel_at:", debugSub.cancel_at);
    console.log("cancel_at_period_end:", debugSub.cancel_at_period_end);
    console.log("canceled_at:", debugSub.canceled_at);
    console.log("ended_at:", debugSub.ended_at);
    console.log("trial_start:", debugSub.trial_start);
    console.log("trial_end:", debugSub.trial_end);
    console.log("start_date:", debugSub.start_date);
    console.log("created:", debugSub.created);
    console.log("status:", debugSub.status);
    console.log("collection_method:", debugSub.collection_method);
    console.log("=== END DATE PROPERTIES ===");

    const product = await stripe.products.retrieve(
      subscription.items.data[0].price.product as string
    );

    // Access Stripe subscription period fields - use the same approach as billing API
    interface StripeSubscriptionWithPeriods {
      current_period_start: number;
      current_period_end: number;
      [key: string]: unknown;
    }

    const subscriptionObj =
      subscription as unknown as StripeSubscriptionWithPeriods;

    console.log(
      "Subscription current_period_start:",
      subscriptionObj.current_period_start
    );
    console.log(
      "Subscription current_period_end:",
      subscriptionObj.current_period_end
    );

    const currentPeriodEnd = subscriptionObj.current_period_end;
    const currentPeriodStart = subscriptionObj.current_period_start;

    console.log("Extracted currentPeriodEnd:", currentPeriodEnd);
    console.log("Extracted currentPeriodStart:", currentPeriodStart);

    return NextResponse.json({
      hasActiveSubscription: true,
      subscription: {
        id: subscription.id,
        status: subscription.status,
        current_period_end: currentPeriodEnd,
        current_period_start: currentPeriodStart,
        cancel_at_period_end: subscription.cancel_at_period_end,
        canceled_at: subscription.canceled_at,
        product_name: product.name,
        amount: subscription.items.data[0].price.unit_amount,
        currency: subscription.items.data[0].price.currency,
        interval: subscription.items.data[0].price.recurring?.interval,
      },
    });
  } catch (error) {
    console.error("Subscription status error:", error);
    return NextResponse.json(
      { error: "Failed to check subscription status" },
      { status: 500 }
    );
  }
}
