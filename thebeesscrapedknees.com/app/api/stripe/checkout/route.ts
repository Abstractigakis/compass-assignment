import { NextResponse } from "next/server";
import { stripe, getStripeProductId } from "@/lib/stripe";
import { createClient } from "@/lib/supabase/server";
import { headers } from "next/headers";

export async function POST() {
  try {
    const supabase = await createClient();

    // Check if user is authenticated
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();

    if (authError || !user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const headersList = await headers();
    const origin =
      headersList.get("origin") || process.env.NEXT_PUBLIC_BASE_URL;

    // Get the product and its default price
    const productId = getStripeProductId();
    const product = await stripe.products.retrieve(productId);

    if (!product.active) {
      return NextResponse.json(
        { error: "Product is not available" },
        { status: 400 }
      );
    }

    // Get the prices for this product
    const prices = await stripe.prices.list({
      product: productId,
      active: true,
    });

    if (prices.data.length === 0) {
      return NextResponse.json(
        { error: "No active prices found for product" },
        { status: 400 }
      );
    }

    // Use the first active price (you might want to implement price selection logic)
    const price = prices.data[0];

    // Check if user already has an active subscription
    if (user.email) {
      const customers = await stripe.customers.list({
        email: user.email,
        limit: 1,
      });

      if (customers.data.length > 0) {
        const customerSubscriptions = await stripe.subscriptions.list({
          customer: customers.data[0].id,
          status: "active",
        });

        if (customerSubscriptions.data.length > 0) {
          return NextResponse.json(
            { error: "User already has an active subscription" },
            { status: 400 }
          );
        }
      }
    }

    // Create Stripe checkout session
    const session = await stripe.checkout.sessions.create({
      payment_method_types: ["card"],
      line_items: [
        {
          price: price.id,
          quantity: 1,
        },
      ],
      mode: price.type === "recurring" ? "subscription" : "payment",
      success_url: `${origin}/app/account?success=true&session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${origin}/app/account?canceled=true`,
      customer_email: user.email || undefined,
      metadata: {
        user_id: user.id,
        user_email: user.email || "",
      },
      allow_promotion_codes: true,
    });

    return NextResponse.json({
      sessionId: session.id,
      url: session.url,
    });
  } catch (error) {
    console.error("Stripe checkout error:", error);
    return NextResponse.json(
      { error: "Failed to create checkout session" },
      { status: 500 }
    );
  }
}
