import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";
import BillingDashboard from "@/components/billing-dashboard";

export default async function AccountPage() {
  const supabase = await createClient();

  const {
    data: { user },
    error,
  } = await supabase.auth.getUser();

  if (error || !user) {
    redirect("/sign-in");
  }

  return (
    <div className="container mx-auto py-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Account & Billing</h1>
        <p className="text-muted-foreground">
          Manage your subscription, payment methods, and billing history.
        </p>
      </div>

      <BillingDashboard />
    </div>
  );
}
