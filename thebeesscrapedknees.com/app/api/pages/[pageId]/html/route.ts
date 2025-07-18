import { createClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";

interface RouteParams {
  params: Promise<{
    pageId: string;
  }>;
}

export async function GET(request: NextRequest, { params }: RouteParams) {
  try {
    const supabase = await createClient();
    const { pageId } = await params;

    // Check if user is authenticated
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Verify that the page exists and belongs to the user
    const { data: page, error: pageError } = await supabase
      .from("pages")
      .select("id")
      .eq("id", pageId)
      .eq("user_id", user.id)
      .single();

    if (pageError || !page) {
      return NextResponse.json(
        { error: "Page not found or access denied" },
        { status: 404 }
      );
    }

    // Get query parameters for pagination
    const { searchParams } = new URL(request.url);
    const limit = searchParams.get("limit");
    const offset = searchParams.get("offset");

    // Build query for HTML runs
    let query = supabase
      .from("html")
      .select("*", { count: "exact" })
      .eq("page_id", pageId)
      .eq("user_id", user.id)
      .order("created_at", { ascending: false });

    // Apply pagination if provided
    if (limit) {
      query = query.limit(parseInt(limit));
    }
    if (offset) {
      query = query.range(
        parseInt(offset),
        parseInt(offset) + parseInt(limit || "10") - 1
      );
    }

    const { data: htmlRuns, error: queryError, count } = await query;

    if (queryError) {
      console.error("Error fetching HTML runs:", queryError);
      return NextResponse.json(
        { error: "Failed to fetch HTML runs" },
        { status: 500 }
      );
    }

    return NextResponse.json({
      data: htmlRuns,
      count,
      page_id: pageId,
    });
  } catch (error) {
    console.error("HTML runs GET error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest, { params }: RouteParams) {
  try {
    const supabase = await createClient();
    const { pageId } = await params;

    // Check if user is authenticated
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Verify that the page exists and belongs to the user
    const { data: page, error: pageError } = await supabase
      .from("pages")
      .select("id, url")
      .eq("id", pageId)
      .eq("user_id", user.id)
      .single();

    if (pageError || !page) {
      return NextResponse.json(
        { error: "Page not found or access denied" },
        { status: 404 }
      );
    }

    // Call the web scraping service
    const htmlRes = await fetch(
      process.env.WEB_SCRAPE_URL + `/pages/get-html`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url: page.url,
          format: "json",
        }),
      }
    );

    if (!htmlRes.ok) {
      const errorText = await htmlRes.text();
      console.error("Web scraping service error:", {
        status: htmlRes.status,
        statusText: htmlRes.statusText,
        error: errorText,
        url: page.url,
      });
      return NextResponse.json(
        {
          error: "Failed to fetch HTML from scraping service",
          details: errorText,
          status: htmlRes.status,
        },
        { status: htmlRes.status }
      );
    }

    const htmlData = await htmlRes.json();
    console.log("Web scraping response:", {
      hasData: !!htmlData,
      keys: Object.keys(htmlData || {}),
      htmlLength: htmlData?.html?.length,
      meta: htmlData?.meta,
    });

    if (!htmlData || !htmlData.html) {
      return NextResponse.json(
        {
          error: "No HTML data returned from the scraper",
          received: htmlData,
        },
        { status: 500 }
      );
    }

    const { html, meta: scrapeMeta } = htmlData;

    // Store the HTML run in the database
    const { data: htmlRun, error: insertError } = await supabase
      .from("html")
      .insert([
        {
          page_id: pageId,
          html: html,
          meta: {
            url: page.url,
            fetch_timestamp: new Date().toISOString(),
            html_length: html.length,
            scraper_service: "pagent-os-api",
            response_status: htmlRes.status,
            scraper_meta: scrapeMeta,
          },
          user_id: user.id,
        },
      ])
      .select()
      .single();

    if (insertError) {
      console.error("Error inserting HTML run:", insertError);
      return NextResponse.json(
        { error: "Failed to save HTML run" },
        { status: 500 }
      );
    }

    return NextResponse.json(
      {
        data: htmlRun,
        message: "HTML fetched and saved successfully",
      },
      { status: 201 }
    );
  } catch (error) {
    console.error("HTML run creation error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
