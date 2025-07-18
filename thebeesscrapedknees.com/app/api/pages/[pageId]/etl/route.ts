import { createClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";
import { TablesInsert } from "@/lib/supabase/db.types";

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

    // Get query parameters
    const { searchParams } = new URL(request.url);
    const etlId = searchParams.get("id");

    if (etlId) {
      // Get specific ETL configuration
      const { data: etl, error } = await supabase
        .from("etl")
        .select("*")
        .eq("id", etlId)
        .eq("page_id", pageId)
        .eq("user_id", user.id)
        .single();

      if (error) {
        return NextResponse.json({ error: error.message }, { status: 400 });
      }

      return NextResponse.json({ data: etl });
    } else {
      // Get all ETL configurations for this page
      const { data: etls, error } = await supabase
        .from("etl")
        .select("*")
        .eq("page_id", pageId)
        .eq("user_id", user.id)
        .order("created_at", { ascending: false });

      if (error) {
        return NextResponse.json({ error: error.message }, { status: 400 });
      }

      return NextResponse.json({ data: etls, page_id: pageId });
    }
  } catch (error) {
    console.error("ETL configurations GET error:", error);
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

    const body: Omit<
      TablesInsert<"etl">,
      "page_id" | "user_id"
    > = await request.json();

    // Validate required fields
    if (!body.goal) {
      return NextResponse.json({ error: "Goal is required" }, { status: 400 });
    }

    if (!body.html_page_run_id) {
      return NextResponse.json(
        { error: "HTML run selection is required" },
        { status: 400 }
      );
    }

    // Verify that the HTML run exists and belongs to the user
    const { data: htmlRun, error: htmlRunError } = await supabase
      .from("html")
      .select("id")
      .eq("id", body.html_page_run_id)
      .eq("page_id", pageId)
      .eq("user_id", user.id)
      .single();

    if (htmlRunError || !htmlRun) {
      return NextResponse.json(
        { error: "HTML run not found or access denied" },
        { status: 404 }
      );
    }

    // Create the ETL configuration
    const etlData = {
      ...body,
      page_id: pageId,
      user_id: user.id,
    };

    const { data: etl, error } = await supabase
      .from("etl")
      .insert([etlData])
      .select()
      .single();

    if (error) {
      console.error("Error creating ETL configuration:", error);
      return NextResponse.json({ error: error.message }, { status: 400 });
    }

    return NextResponse.json(
      {
        data: etl,
        message: "ETL configuration created successfully",
      },
      { status: 201 }
    );
  } catch (error) {
    console.error("ETL configuration creation error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
