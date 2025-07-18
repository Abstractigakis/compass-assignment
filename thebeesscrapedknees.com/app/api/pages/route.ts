import { createClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";
import { TablesInsert, TablesUpdate } from "@/lib/supabase/db.types";

export async function GET(request: NextRequest) {
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

    const { searchParams } = new URL(request.url);
    const pageId = searchParams.get("id");
    const limit = searchParams.get("limit");
    const offset = searchParams.get("offset");

    if (pageId) {
      // Get specific page
      const { data, error } = await supabase
        .from("pages")
        .select("*")
        .eq("id", pageId)
        .eq("user_id", user.id)
        .single();

      if (error) {
        return NextResponse.json({ error: error.message }, { status: 400 });
      }

      return NextResponse.json({ data });
    } else {
      // Get all user's pages with pagination
      let query = supabase
        .from("pages")
        .select("*", { count: "exact" })
        .eq("user_id", user.id)
        .order("created_at", { ascending: false });

      if (limit) {
        query = query.limit(parseInt(limit));
      }
      if (offset) {
        query = query.range(
          parseInt(offset),
          parseInt(offset) + parseInt(limit || "10") - 1
        );
      }

      const { data, error, count } = await query;

      if (error) {
        return NextResponse.json({ error: error.message }, { status: 400 });
      }

      return NextResponse.json({ data, count });
    }
  } catch (error) {
    console.error("Pages GET error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
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

    const body: TablesInsert<"pages"> = await request.json();

    // Validate required fields - only URL is required
    if (!body.url) {
      return NextResponse.json({ error: "URL is required" }, { status: 400 });
    }

    // Ensure the page is created for the authenticated user
    const pageData = {
      ...body,
      user_id: user.id,
    };

    const { data, error } = await supabase
      .from("pages")
      .insert([pageData])
      .select()
      .single();

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }

    return NextResponse.json({ data }, { status: 201 });
  } catch (error) {
    console.error("Pages POST error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

export async function PUT(request: NextRequest) {
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

    const body: TablesUpdate<"pages"> & { id: string } = await request.json();
    const { id, ...updateData } = body;

    if (!id) {
      return NextResponse.json(
        { error: "Page ID is required" },
        { status: 400 }
      );
    }

    const { data, error } = await supabase
      .from("pages")
      .update(updateData)
      .eq("id", id)
      .eq("user_id", user.id) // Ensure user can only update their own pages
      .select()
      .single();

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }

    return NextResponse.json({ data });
  } catch (error) {
    console.error("Pages PUT error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest) {
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

    const { searchParams } = new URL(request.url);
    const pageId = searchParams.get("id");

    if (!pageId) {
      return NextResponse.json(
        { error: "Page ID is required" },
        { status: 400 }
      );
    }

    const { error } = await supabase
      .from("pages")
      .delete()
      .eq("id", pageId)
      .eq("user_id", user.id); // Ensure user can only delete their own pages

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }

    return NextResponse.json({ message: "Page deleted successfully" });
  } catch (error) {
    console.error("Pages DELETE error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
