import { NextRequest, NextResponse } from "next/server";
import { getCurrentUserWithProfile, updateProfile } from "@/lib/profile-utils";
import { createClient } from "@/lib/supabase/server";

export async function GET() {
  try {
    const { profile } = await getCurrentUserWithProfile();

    return NextResponse.json({
      success: true,
      data: profile,
    });
  } catch (error) {
    console.error("Profile fetch error:", error);
    return NextResponse.json(
      {
        success: false,
        error:
          error instanceof Error ? error.message : "Failed to fetch profile",
      },
      { status: 401 }
    );
  }
}

export async function PATCH(request: NextRequest) {
  try {
    const supabase = await createClient();
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();

    if (authError || !user) {
      return NextResponse.json(
        { success: false, error: "Unauthorized" },
        { status: 401 }
      );
    }

    const updates = await request.json();

    // For now, we can only update display_name via user metadata
    // since the profiles table doesn't have additional fields yet
    if (updates.display_name !== undefined) {
      const { error: updateError } = await supabase.auth.updateUser({
        data: { display_name: updates.display_name },
      });

      if (updateError) {
        throw new Error(updateError.message);
      }
    }

    const updatedProfile = await updateProfile(user.id, updates);

    return NextResponse.json({
      success: true,
      data: updatedProfile,
    });
  } catch (error) {
    console.error("Profile update error:", error);
    return NextResponse.json(
      {
        success: false,
        error:
          error instanceof Error ? error.message : "Failed to update profile",
      },
      { status: 500 }
    );
  }
}
