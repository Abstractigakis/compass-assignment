import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import PrettyJson from "@/components/pretty-json";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import Link from "next/link";
import { AddPageDialog } from "@/components/add-page-dialog";

export default async function Page() {
  const sb = await createClient();
  ////////////////////////////////////////////////////////////////////////
  // First call to get the user
  ////////////////////////////////////////////////////////////////////////
  const {
    data: { user },
  } = await sb.auth.getUser();
  if (!user) return redirect("/auth/sign-in");

  ////////////////////////////////////////////////////////////////////////
  // 2nd call to get the profile
  ////////////////////////////////////////////////////////////////////////
  const { data: profileData, error: profileError } = await sb
    .from("profiles")
    .select("*")
    .eq("user_id", user.id)
    .single();

  if (profileError && profileError.code !== "PGRST116")
    return <PrettyJson json={profileError} />;

  let profile = profileData;
  if (profileError?.code === "PGRST116") {
    ////////////////////////////////////////////////////////////////////////
    // call to get the profile (only happens 1st time a user signs up)
    ////////////////////////////////////////////////////////////////////////
    const { data: profileCreationResponse, error: profileCreationError } =
      await sb
        .from("profiles")
        .insert({
          user_id: user.id,
          nickname: user.user_metadata?.full_name || "New User",
        })
        .single();
    if (profileCreationError) return <PrettyJson json={profileCreationError} />;
    profile = profileCreationResponse;
  }

  if (!profile) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="text-center py-12">
          <CardHeader>
            <CardTitle className="text-muted-foreground">
              Profile not found
            </CardTitle>
            <CardDescription>
              Please complete your profile setup to continue
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  ////////////////////////////////////////////////////////////////////////
  // 3rd call for pages
  ////////////////////////////////////////////////////////////////////////
  const { data: pagesData, error: pagesError } = await sb
    .from("pages")
    .select("*")
    .eq("user_id", user.id);

  if (pagesError && pagesError.code !== "PGRST116")
    return <PrettyJson json={pagesError} />;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Your Pages</h1>
          <p className="text-muted-foreground">
            Manage your web scraping pages
          </p>
        </div>
        <AddPageDialog />
      </div>

      {pagesData && pagesData.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {pagesData.map((page) => (
            <Link
              key={page.id}
              href={`/app/pages/${page.id}`}
              className="group"
            >
              <Card className="h-full transition-all duration-200 hover:shadow-md hover:scale-[1.02] cursor-pointer">
                <CardHeader>
                  <CardTitle className="group-hover:text-primary transition-colors">
                    {new URL(page.url).hostname}
                  </CardTitle>
                  <CardDescription className="text-xs font-mono bg-muted px-2 py-1 rounded mt-2 truncate">
                    {page.url}
                  </CardDescription>
                  <CardDescription className="mt-2">
                    Click to configure your Page and view extraction data
                  </CardDescription>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      ) : (
        <Card className="text-center py-12">
          <CardHeader>
            <CardTitle className="text-muted-foreground">
              No pages found
            </CardTitle>
            <CardDescription>
              Get started by adding your first page to scrape with a Page
            </CardDescription>
          </CardHeader>
        </Card>
      )}
    </div>
  );
}
