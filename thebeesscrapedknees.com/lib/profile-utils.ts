import { createClient } from "@/lib/supabase/server";
import type { User } from "@supabase/supabase-js";

interface Profile {
  id: string;
  user_id: string;
  email: string;
  display_name?: string;
  avatar_url?: string;
  created_at: string;
  updated_at: string;
}

/**
 * Ensure a profile exists for the given user ID, creating one if necessary
 */
export async function ensureProfile(userId: string): Promise<Profile> {
  const supabase = await createClient();

  // Try to get existing profile
  const existingProfile = await getProfileByUserId(userId);
  if (existingProfile) {
    return existingProfile;
  }

  // Get the user data to create a profile
  const {
    data: { user },
    error: userError,
  } = await supabase.auth.getUser();

  if (userError || !user || user.id !== userId) {
    throw new Error("Cannot create profile: user not found or unauthorized");
  }

  return createProfileFromUser(user);
}

export async function getProfileByUserId(
  userId: string
): Promise<Profile | null> {
  const supabase = await createClient();

  const { data: profile, error } = await supabase
    .from("profiles")
    .select("*")
    .eq("user_id", userId)
    .single();

  if (error || !profile) {
    return null;
  }

  // Get user data to fill in missing fields
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return {
    id: profile.id,
    user_id: profile.user_id,
    email: user?.email || "",
    display_name:
      user?.user_metadata?.display_name || user?.user_metadata?.full_name,
    avatar_url: user?.user_metadata?.avatar_url,
    created_at: profile.created_at || new Date().toISOString(),
    updated_at: profile.created_at || new Date().toISOString(),
  };
}

export async function createProfileFromUser(user: User): Promise<Profile> {
  const supabase = await createClient();

  const { data: profile, error } = await supabase
    .from("profiles")
    .insert({
      user_id: user.id,
      nickname: user.user_metadata?.full_name || "New User",
    })
    .select()
    .single();

  if (error) {
    console.error("Error creating profile:", error);
    throw new Error(`Failed to create profile: ${error.message}`);
  }

  return {
    id: profile.id,
    user_id: profile.user_id,
    email: user.email || "",
    display_name:
      user.user_metadata?.display_name || user.user_metadata?.full_name,
    avatar_url: user.user_metadata?.avatar_url,
    created_at: profile.created_at || new Date().toISOString(),
    updated_at: profile.created_at || new Date().toISOString(),
  };
}

export async function updateProfile(
  userId: string,
  updates: Partial<Omit<Profile, "id" | "user_id" | "created_at">>
): Promise<Profile> {
  // Note: The current profiles table only has id, user_id, and created_at
  // So we can't actually update most fields in the database yet
  // This function returns the profile with metadata from auth.users

  const existingProfile = await getProfileByUserId(userId);
  if (!existingProfile) {
    throw new Error("Profile not found");
  }

  // For now, just return the existing profile since we can't update most fields
  // TODO: Extend profiles table to include more fields like display_name, avatar_url, etc.
  return {
    ...existingProfile,
    ...updates,
    updated_at: new Date().toISOString(),
  };
}

/**
 * Check if a user is an admin based on their email
 */
export async function isUserAdmin(user: User | null): Promise<boolean> {
  if (!user?.email) return false;

  // Check environment variable for admin emails
  const adminEmails = process.env.ADMIN_EMAILS?.split(",") || [];
  return adminEmails.includes(user.email);
}

/**
 * Get or create user profile from auth user
 */
export async function getOrCreateProfile(user: User): Promise<Profile> {
  // First try to get existing profile
  const existingProfile = await getProfileByUserId(user.id);
  if (existingProfile) {
    return existingProfile;
  }

  // If no profile exists, create one
  return createProfileFromUser(user);
}

/**
 * Get current authenticated user with their profile
 */
export async function getCurrentUserWithProfile(): Promise<{
  user: User;
  profile: Profile;
}> {
  const supabase = await createClient();

  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser();

  if (authError || !user) {
    throw new Error("User not authenticated");
  }

  const profile = await getOrCreateProfile(user);

  return { user, profile };
}
