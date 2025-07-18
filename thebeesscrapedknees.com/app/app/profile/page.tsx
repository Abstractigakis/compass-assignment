"use client";

import React, { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  updateDisplayNameAction,
  getProfileAction,
} from "@/app/profile-actions";
import { User, Mail, Calendar, Edit2, Check, X } from "lucide-react";

interface Profile {
  id: string;
  user_id: string;
  email: string;
  display_name?: string;
  avatar_url?: string;
  created_at: string;
  updated_at: string;
}

const ProfilePage = () => {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [nickname, setNickname] = useState("");
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateMessage, setUpdateMessage] = useState<string | null>(null);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const result = await getProfileAction();

      if (result.success && result.data) {
        setProfile(result.data);
        setNickname(result.data.display_name || "");
      } else {
        setError(result.error || "Failed to fetch profile");
      }
    } catch {
      setError("Failed to fetch profile");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const handleUpdateNickname = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsUpdating(true);
    setUpdateMessage(null);

    try {
      const formData = new FormData();
      formData.append("display_name", nickname);

      const result = await updateDisplayNameAction(formData);

      if (result.success) {
        setProfile((prev) =>
          prev ? { ...prev, display_name: nickname } : null
        );
        setIsEditing(false);
        setUpdateMessage("Nickname updated successfully!");
        setTimeout(() => setUpdateMessage(null), 3000);
      } else {
        setError(result.error || "Failed to update nickname");
      }
    } catch {
      setError("Failed to update nickname");
    } finally {
      setIsUpdating(false);
    }
  };

  const handleCancelEdit = () => {
    setNickname(profile?.display_name || "");
    setIsEditing(false);
    setError(null);
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6 max-w-2xl">
        <Card>
          <CardHeader>
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-64" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error && !profile) {
    return (
      <div className="container mx-auto p-6 max-w-2xl">
        <Card>
          <CardHeader>
            <CardTitle className="text-destructive">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">{error}</p>
            <Button onClick={fetchProfile} className="mt-4">
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-6 w-6" />
            My Profile
          </CardTitle>
          <CardDescription>
            Manage your profile information and preferences
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {updateMessage && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-md text-green-700 text-sm">
              {updateMessage}
            </div>
          )}

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* Email */}
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2">
              <Mail className="h-4 w-4" />
              Email
            </label>
            <div className="flex items-center gap-2">
              <Input
                value={profile?.email || ""}
                disabled
                className="bg-muted"
              />
              <Badge variant="secondary">Verified</Badge>
            </div>
          </div>

          {/* Nickname */}
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2">
              <Edit2 className="h-4 w-4" />
              Nickname
            </label>

            {isEditing ? (
              <form onSubmit={handleUpdateNickname} className="space-y-3">
                <Input
                  value={nickname}
                  onChange={(e) => setNickname(e.target.value)}
                  placeholder="Enter your nickname"
                  disabled={isUpdating}
                  maxLength={50}
                />
                <div className="flex gap-2">
                  <Button
                    type="submit"
                    size="sm"
                    disabled={isUpdating || nickname.trim().length === 0}
                  >
                    {isUpdating ? (
                      <>Saving...</>
                    ) : (
                      <>
                        <Check className="h-4 w-4" />
                        Save
                      </>
                    )}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleCancelEdit}
                    disabled={isUpdating}
                  >
                    <X className="h-4 w-4" />
                    Cancel
                  </Button>
                </div>
              </form>
            ) : (
              <div className="flex items-center gap-2">
                <Input
                  value={profile?.display_name || "No nickname set"}
                  disabled
                  className="bg-muted"
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsEditing(true)}
                >
                  <Edit2 className="h-4 w-4" />
                  Edit
                </Button>
              </div>
            )}
          </div>

          {/* Account Info */}
          <div className="pt-4 border-t space-y-4">
            <h3 className="text-sm font-medium text-muted-foreground">
              Account Information
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Calendar className="h-4 w-4" />
                  Member since
                </div>
                <div>
                  {profile?.created_at
                    ? new Date(profile.created_at).toLocaleDateString("en-US", {
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                      })
                    : "Unknown"}
                </div>
              </div>

              <div className="space-y-1">
                <div className="text-muted-foreground">User ID</div>
                <div className="font-mono text-xs bg-muted p-2 rounded">
                  {profile?.user_id}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ProfilePage;
