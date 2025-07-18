"use server";

import { createClient } from "@/lib/supabase/server";
import { getCurrentUserWithProfile, updateProfile } from "@/lib/profile-utils";
import { revalidatePath } from "next/cache";

export async function updateDisplayNameAction(formData: FormData) {
  try {
    const displayName = formData.get("display_name") as string;

    if (!displayName || displayName.trim().length === 0) {
      return {
        success: false,
        error: "Display name is required",
      };
    }

    const supabase = await createClient();
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();

    if (authError || !user) {
      return {
        success: false,
        error: "Unauthorized",
      };
    }

    // Update user metadata for display_name
    const { error: updateError } = await supabase.auth.updateUser({
      data: { display_name: displayName.trim() },
    });

    if (updateError) {
      return {
        success: false,
        error: updateError.message,
      };
    }

    // Update our profile record (though this mainly just updates the timestamp)
    await updateProfile(user.id, { display_name: displayName.trim() });

    // Revalidate the page to show updated data
    revalidatePath("/app");

    return {
      success: true,
      message: "Display name updated successfully",
    };
  } catch (error) {
    console.error("Update display name error:", error);
    return {
      success: false,
      error:
        error instanceof Error
          ? error.message
          : "Failed to update display name",
    };
  }
}

export async function getProfileAction() {
  try {
    const { profile } = await getCurrentUserWithProfile();
    return {
      success: true,
      data: profile,
    };
  } catch (error) {
    console.error("Get profile error:", error);
    return {
      success: false,
      error: error instanceof Error ? error.message : "Failed to fetch profile",
    };
  }
}
