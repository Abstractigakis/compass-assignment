import Stripe from "stripe";

if (!process.env.STRIPE_API_SECRET_KEY) {
  throw new Error("STRIPE_API_SECRET_KEY is not set");
}

export const stripe = new Stripe(process.env.STRIPE_API_SECRET_KEY, {
  apiVersion: "2025-06-30.basil",
});

export const getStripePublishableKey = () => {
  if (!process.env.NEXT_PUBLIC_STRIPE_API_PUBLISHABLE_KEY) {
    throw new Error("NEXT_PUBLIC_STRIPE_API_PUBLISHABLE_KEY is not set");
  }
  return process.env.NEXT_PUBLIC_STRIPE_API_PUBLISHABLE_KEY;
};

export const getStripeProductId = () => {
  if (!process.env.NEXT_PUBLIC_STRIPE_PRODUCT_ID) {
    throw new Error("NEXT_PUBLIC_STRIPE_PRODUCT_ID is not set");
  }
  return process.env.NEXT_PUBLIC_STRIPE_PRODUCT_ID;
};
