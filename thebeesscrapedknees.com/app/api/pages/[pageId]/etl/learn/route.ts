import { createClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";
import { TablesInsert } from "@/lib/supabase/db.types";
import { gzip } from "zlib";
import { promisify } from "util";

const gzipAsync = promisify(gzip);

interface RouteParams {
  params: Promise<{
    pageId: string;
  }>;
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
    const { data: pageData, error: pageError } = await supabase
      .from("pages")
      .select("id,url")
      .eq("id", pageId)
      .eq("user_id", user.id)
      .single();

    if (pageError || !pageData) {
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
    const { data: htmlRunData, error: htmlRunError } = await supabase
      .from("html")
      .select("id,html")
      .eq("id", body.html_page_run_id)
      .eq("page_id", pageId)
      .eq("user_id", user.id)
      .single();

    if (htmlRunError || !htmlRunData) {
      return NextResponse.json(
        { error: "HTML run not found or access denied" },
        { status: 404 }
      );
    }

    // Compress the HTML content
    const compressedHtml = await gzipAsync(
      Buffer.from(htmlRunData.html, "utf-8")
    );

    const learnEtlResponse = await fetch(
      `${process.env.WEB_SCRAPE_URL}/pages/learn-etl`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url: pageData.url,
          html: compressedHtml.toString("base64"), // ← FIXED: Convert to base64
          html_compressed: true, // ← ADDED: Tell API it's compressed
          goal: body.goal, // ← ADDED: Pass the goal
        }),
      }
    );

    if (!learnEtlResponse.ok) {
      const errorText = await learnEtlResponse.text();
      console.error("Learn ETL API error:", errorText);
      return NextResponse.json(
        { error: "Failed to process ETL learning" },
        { status: 500 }
      );
    }

    const learnEtlData = await learnEtlResponse.json();
    const { etl_function_code, entities_schema } = learnEtlData;
    if (!etl_function_code) {
      return NextResponse.json(
        { error: "ETL function code not generated" },
        { status: 500 }
      );
    }

    console.log({ learnEtlData });

    const { data: etl, error } = await supabase
      .from("etl")
      .insert({
        user_id: user.id,
        page_id: pageId,
        goal: body.goal,
        output_json_schema: entities_schema || null,
        src_code: etl_function_code,
        html_page_run_id: body.html_page_run_id,
      })
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
