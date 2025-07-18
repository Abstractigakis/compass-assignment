"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

interface Profile {
  id: string;
  user_id: string;
  nickname: string;
  bio: string | null;
  avatar_url: string | null;
  created_at: string;
}

interface User {
  id: string;
  email: string | null;
  user_metadata: {
    full_name?: string;
    avatar_url?: string;
  };
}

interface ProfileFormProps {
  initialProfile: Profile | null;
  user: User;
}

export function ProfileForm({ initialProfile, user }: ProfileFormProps) {
  const [nickname, setNickname] = useState(initialProfile?.nickname || "");
  const [bio, setBio] = useState(initialProfile?.bio || "");
  const [isLoading, setIsLoading] = useState(false);

  // Get user initials for avatar fallback
  const getInitials = (name: string) => {
    if (!name) return "U";
    return name
      .split(/[\s._-]+/)
      .map((part) => part[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!nickname.trim()) {
      toast.error("Nickname is required");
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch("/api/profile", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          nickname: nickname.trim(),
          bio: bio.trim() || null,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to update profile");
      }

      toast.success(data.message || "Profile updated successfully!");
    } catch (error) {
      console.error("Error updating profile:", error);
      toast.error(
        error instanceof Error ? error.message : "Failed to update profile"
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Avatar Section */}
      <div className="flex items-center gap-6">
        <Avatar className="size-20">
          <AvatarImage
            src={initialProfile?.avatar_url || user.user_metadata?.avatar_url}
          />
          <AvatarFallback className="text-lg">
            {getInitials(
              nickname || user.user_metadata?.full_name || user.email || ""
            )}
          </AvatarFallback>
        </Avatar>
        <div className="space-y-2">
          <Button variant="outline" size="sm" type="button">
            Change Avatar
          </Button>
          <p className="text-sm text-muted-foreground">
            Upload a new profile picture (JPG, PNG, max 2MB)
          </p>
        </div>
      </div>

      {/* Profile Fields */}
      <div className="grid grid-cols-1 gap-4">
        <div>
          <Label htmlFor="nickname">Nickname *</Label>
          <Input
            id="nickname"
            type="text"
            placeholder="How would you like to be called?"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            required
          />
          <p className="text-sm text-muted-foreground mt-1">
            This is how you&apos;ll appear to AI agents and in the app
          </p>
        </div>

        <div>
          <Label htmlFor="bio">Bio</Label>
          <Textarea
            id="bio"
            placeholder="Tell us a bit about yourself, your goals, and what motivates you..."
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            rows={4}
            className="resize-none"
          />
          <p className="text-sm text-muted-foreground mt-1">
            Help AI coaches understand you better (optional)
          </p>
        </div>

        <div>
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            value={user.email || ""}
            disabled
            className="bg-muted"
          />
          <p className="text-sm text-muted-foreground mt-1">
            Email is managed in Account settings
          </p>
        </div>
      </div>

      <div className="flex justify-end">
        <Button
          type="submit"
          disabled={isLoading}
          className="bg-blue-600 hover:bg-blue-700"
        >
          {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {isLoading ? "Saving..." : "Save Profile"}
        </Button>
      </div>
    </form>
  );
}
