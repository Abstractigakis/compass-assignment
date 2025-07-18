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
        hasCustomer: false,
        subscription: null,
        paymentHistory: [],
        paymentMethods: [],
      });
    }

    const customer = customers.data[0];

    // Get subscription details
    const subscriptions = await stripe.subscriptions.list({
      customer: customer.id,
      status: "all", // Get all subscription statuses
      limit: 10,
    });

    console.log("Found subscriptions:", subscriptions.data.length);

    let activeSubscription = null;
    if (subscriptions.data.length > 0) {
      const sub = subscriptions.data[0];

      // Debug: Log the entire subscription object as JSON
      console.log("=== BILLING API - FULL STRIPE SUBSCRIPTION ===");
      console.log(JSON.stringify(sub, null, 2));
      console.log("=== END BILLING SUBSCRIPTION OBJECT ===");

      const product = await stripe.products.retrieve(
        sub.items.data[0].price.product as string
      );

      // Access Stripe subscription period fields - these definitely exist in Stripe API
      // Define a more permissive interface for the subscription object
      interface StripeSubscriptionWithPeriods {
        current_period_start: number;
        current_period_end: number;
        [key: string]: unknown;
      }

      const subscriptionObj = sub as unknown as StripeSubscriptionWithPeriods;

      console.log(
        "current_period_start:",
        subscriptionObj.current_period_start
      );
      console.log("current_period_end:", subscriptionObj.current_period_end);
      console.log(
        "Type of current_period_start:",
        typeof subscriptionObj.current_period_start
      );
      console.log(
        "Type of current_period_end:",
        typeof subscriptionObj.current_period_end
      );

      activeSubscription = {
        id: sub.id,
        status: sub.status,
        cancel_at_period_end: sub.cancel_at_period_end,
        canceled_at: sub.canceled_at,
        // Use the properly typed object to access period fields
        current_period_start: subscriptionObj.current_period_start,
        current_period_end: subscriptionObj.current_period_end,
        product_name: product.name,
        amount: sub.items.data[0].price.unit_amount,
        currency: sub.items.data[0].price.currency,
        interval: sub.items.data[0].price.recurring?.interval,
        trial_end: sub.trial_end,
        trial_start: sub.trial_start,
      };
    }

    // Get payment history (invoices)
    const invoices = await stripe.invoices.list({
      customer: customer.id,
      limit: 50,
    });

    const paymentHistory = invoices.data.map((invoice) => ({
      id: invoice.id,
      amount_paid: invoice.amount_paid,
      amount_due: invoice.amount_due,
      currency: invoice.currency,
      status: invoice.status,
      created: invoice.created,
      paid_at: invoice.status_transitions.paid_at,
      invoice_pdf: invoice.invoice_pdf,
      hosted_invoice_url: invoice.hosted_invoice_url,
      description: invoice.description || invoice.lines.data[0]?.description,
      period_start: invoice.period_start,
      period_end: invoice.period_end,
    }));

    // Get payment methods
    const paymentMethods = await stripe.paymentMethods.list({
      customer: customer.id,
      type: "card",
    });

    const formattedPaymentMethods = paymentMethods.data.map((pm) => ({
      id: pm.id,
      brand: pm.card?.brand,
      last4: pm.card?.last4,
      exp_month: pm.card?.exp_month,
      exp_year: pm.card?.exp_year,
      is_default: customer.invoice_settings.default_payment_method === pm.id,
    }));

    return NextResponse.json({
      hasCustomer: true,
      customer: {
        id: customer.id,
        email: customer.email,
        created: customer.created,
      },
      subscription: activeSubscription,
      paymentHistory,
      paymentMethods: formattedPaymentMethods,
    });
  } catch (error) {
    console.error("Billing data error:", error);
    return NextResponse.json(
      { error: "Failed to fetch billing data" },
      { status: 500 }
    );
  }
}
