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
    const profileId = searchParams.get("id");

    if (profileId) {
      // Get specific profile
      const { data, error } = await supabase
        .from("profiles")
        .select("*")
        .eq("id", profileId)
        .single();

      if (error) {
        return NextResponse.json({ error: error.message }, { status: 400 });
      }

      return NextResponse.json({ data });
    } else {
      // Get user's own profile
      const { data, error } = await supabase
        .from("profiles")
        .select("*")
        .eq("user_id", user.id)
        .single();

      if (error) {
        return NextResponse.json({ error: error.message }, { status: 400 });
      }

      return NextResponse.json({ data });
    }
  } catch (error) {
    console.error("Profiles GET error:", error);
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

    const body: TablesInsert<"profiles"> = await request.json();

    // Ensure the profile is created for the authenticated user
    const profileData = {
      ...body,
      user_id: user.id,
    };

    const { data, error } = await supabase
      .from("profiles")
      .insert([profileData])
      .select()
      .single();

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }

    return NextResponse.json({ data }, { status: 201 });
  } catch (error) {
    console.error("Profiles POST error:", error);
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

    const body: TablesUpdate<"profiles"> & { id: string } =
      await request.json();
    const { id, ...updateData } = body;

    const { data, error } = await supabase
      .from("profiles")
      .update(updateData)
      .eq("id", id)
      .eq("user_id", user.id) // Ensure user can only update their own profile
      .select()
      .single();

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }

    return NextResponse.json({ data });
  } catch (error) {
    console.error("Profiles PUT error:", error);
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
    const profileId = searchParams.get("id");

    if (!profileId) {
      return NextResponse.json(
        { error: "Profile ID is required" },
        { status: 400 }
      );
    }

    const { error } = await supabase
      .from("profiles")
      .delete()
      .eq("id", profileId)
      .eq("user_id", user.id); // Ensure user can only delete their own profile

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }

    return NextResponse.json({ message: "Profile deleted successfully" });
  } catch (error) {
    console.error("Profiles DELETE error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
