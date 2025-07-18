import { createClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";
import { gzip } from "zlib";
import { promisify } from "util";

const gzipAsync = promisify(gzip);

interface RouteParams {
  params: Promise<{
    pageId: string;
    etlId: string;
  }>;
}

export async function POST(request: NextRequest, { params }: RouteParams) {
  try {
    const supabase = await createClient();
    const { pageId, etlId } = await params;

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

    // Verify that the ETL configuration exists and belongs to the user
    const { data: etlConfig, error: etlError } = await supabase
      .from("etl")
      .select("*")
      .eq("id", etlId)
      .eq("page_id", pageId)
      .eq("user_id", user.id)
      .single();

    if (etlError || !etlConfig) {
      return NextResponse.json(
        { error: "ETL configuration not found or access denied" },
        { status: 404 }
      );
    }

    // Check if ETL has source code - if not, it's still in training/loading state
    if (!etlConfig.src_code || etlConfig.src_code.trim() === "") {
      return NextResponse.json(
        {
          error:
            "ETL configuration is still being trained. Please wait for training to complete.",
        },
        { status: 400 }
      );
    }

    // Get the request body for optional HTML run selection
    const body = await request.json().catch(() => ({}));
    const { html_run_id } = body;

    let selectedHtmlRun;

    if (html_run_id) {
      // Use specified HTML run
      const { data: htmlRun, error: htmlRunError } = await supabase
        .from("html")
        .select("*")
        .eq("id", html_run_id)
        .eq("page_id", pageId)
        .eq("user_id", user.id)
        .single();

      if (htmlRunError || !htmlRun) {
        return NextResponse.json(
          { error: "HTML run not found or access denied" },
          { status: 404 }
        );
      }
      selectedHtmlRun = htmlRun;
    } else {
      // Default to the ETL's associated HTML run
      const { data: htmlRun, error: htmlRunError } = await supabase
        .from("html")
        .select("*")
        .eq("id", etlConfig.html_page_run_id)
        .eq("page_id", pageId)
        .eq("user_id", user.id)
        .single();

      if (htmlRunError || !htmlRun) {
        return NextResponse.json(
          {
            error:
              "ETL's associated HTML run not found. Please select a different HTML run.",
          },
          { status: 404 }
        );
      }
      selectedHtmlRun = htmlRun;
    }

    // Compress the HTML content for the execute API
    const compressedHtml = await gzipAsync(
      Buffer.from(selectedHtmlRun.html, "utf-8")
    );

    // Check if WEB_SCRAPE_URL is configured
    if (!process.env.WEB_SCRAPE_URL) {
      console.error("WEB_SCRAPE_URL environment variable is not set");
      return NextResponse.json(
        { error: "Web scraping service not configured" },
        { status: 500 }
      );
    }

    console.log(
      `Calling execute API at: ${process.env.WEB_SCRAPE_URL}/pages/execute-etl/${etlId}`
    );
    console.log(`ETL ID: ${etlId} (type: ${typeof etlId})`);
    console.log(`HTML length: ${selectedHtmlRun.html.length}`);
    console.log(`Compressed HTML length: ${compressedHtml.length}`);

    // Call the execute endpoint on the web scraping server
    let executeResponse;
    console.log(etlConfig);
    try {
      executeResponse = await fetch(
        `${process.env.WEB_SCRAPE_URL}/pages/execute-etl`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            html_gzip_base64: compressedHtml.toString("base64"),
            html_compressed: true,
            url: page.url,
            goal: etlConfig.goal,
            etl_function_code: etlConfig.src_code,
          }),
        }
      );
    } catch (fetchError) {
      console.error("Failed to connect to web scraping server:", fetchError);
      return NextResponse.json(
        {
          error:
            "Web scraping service is unavailable. Please ensure the server is running.",
          details:
            fetchError instanceof Error ? fetchError.message : "Unknown error",
        },
        { status: 503 }
      );
    }

    if (!executeResponse.ok) {
      const errorText = await executeResponse.text();
      console.error("Execute API error:", errorText);
      return NextResponse.json(
        { error: "Failed to execute ETL extraction" },
        { status: 500 }
      );
    }

    const extractionResult = await executeResponse.json();

    // Create the ETL run record
    const { data: etlRun, error: insertError } = await supabase
      .from("etl_run")
      .insert([
        {
          html: selectedHtmlRun.id,
          etl_id: etlId,
          output_json: extractionResult,
          user_id: user.id,
        },
      ])
      .select()
      .single();

    if (insertError) {
      console.error("Error creating ETL run:", insertError);
      return NextResponse.json(
        { error: "Failed to save extraction run" },
        { status: 500 }
      );
    }

    return NextResponse.json(
      {
        data: etlRun,
        etl_config: etlConfig,
        html_run: {
          id: selectedHtmlRun.id,
          created_at: selectedHtmlRun.created_at,
          html_length: selectedHtmlRun.html.length,
        },
        message: "Extraction run completed successfully",
      },
      { status: 201 }
    );
  } catch (error) {
    console.error("ETL run creation error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
