import { NextRequest, NextResponse } from "next/server";
import { stripe } from "@/lib/stripe";
import { createClient } from "@/lib/supabase/server";

export async function POST(request: NextRequest) {
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

    const { action, subscriptionId } = await request.json();

    if (!action || !subscriptionId) {
      return NextResponse.json(
        { error: "Action and subscription ID are required" },
        { status: 400 }
      );
    }

    // Verify the subscription belongs to this user
    const subscription = await stripe.subscriptions.retrieve(subscriptionId);
    const customer = await stripe.customers.retrieve(
      subscription.customer as string
    );

    if (
      typeof customer === "string" ||
      customer.deleted ||
      customer.email !== user.email
    ) {
      return NextResponse.json(
        { error: "Subscription not found for this user" },
        { status: 403 }
      );
    }

    let updatedSubscription;

    switch (action) {
      case "cancel":
        // Cancel at period end
        updatedSubscription = await stripe.subscriptions.update(
          subscriptionId,
          {
            cancel_at_period_end: true,
          }
        );
        break;

      case "cancel_immediately":
        // Cancel immediately
        updatedSubscription = await stripe.subscriptions.cancel(subscriptionId);
        break;

      case "reactivate":
        // Reactivate subscription (remove cancel_at_period_end)
        updatedSubscription = await stripe.subscriptions.update(
          subscriptionId,
          {
            cancel_at_period_end: false,
          }
        );
        break;

      default:
        return NextResponse.json({ error: "Invalid action" }, { status: 400 });
    }

    return NextResponse.json({
      success: true,
      subscription: {
        id: updatedSubscription.id,
        status: updatedSubscription.status,
        cancel_at_period_end: updatedSubscription.cancel_at_period_end,
        canceled_at: updatedSubscription.canceled_at,
      },
    });
  } catch (error) {
    console.error("Subscription management error:", error);
    return NextResponse.json(
      { error: "Failed to update subscription" },
      { status: 500 }
    );
  }
}
