import { signOutAction } from "@/app/actions";
import Link from "next/link";
import { Button } from "./ui/button";
import { createClient } from "@/lib/supabase/server";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { Settings, LogOut, Target, User, CreditCard } from "lucide-react";

export default async function AuthButton() {
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  // Get user initials for avatar fallback
  const getInitials = (email: string) => {
    const name = email.split("@")[0];
    return name
      .split(/[\s._-]+/)
      .map((part) => part[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  return user ? (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="relative h-8 w-8 rounded-full">
          <Avatar className="h-8 w-8">
            <AvatarImage
              src={user.user_metadata?.avatar_url}
              alt={user.email || ""}
            />
            <AvatarFallback>{getInitials(user.email || "")}</AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56" align="end" forceMount>
        <div className="flex flex-col space-y-1 p-2">
          <p className="text-sm font-medium leading-none">
            {user.user_metadata?.full_name || "User"}
          </p>
          <p className="text-xs leading-none text-muted-foreground">
            {user.email}
          </p>
        </div>
        <DropdownMenuSeparator />

        <DropdownMenuItem asChild>
          <Link href="/app/profile" className="flex items-center">
            <User className="mr-2 h-4 w-4" />
            Profile
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link href="/app/settings" className="flex items-center">
            <Settings className="mr-2 h-4 w-4" />
            Settings
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link href="/app/account" className="flex items-center">
            <CreditCard className="mr-2 h-4 w-4" />
            Account
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <form action={signOutAction} className="w-full">
            <button
              type="submit"
              className="flex items-center w-full text-left"
            >
              <LogOut className="mr-2 h-4 w-4" />
              Sign out
            </button>
          </form>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  ) : (
    <div className="flex gap-2">
      <Button asChild size="sm" variant={"outline"} id="to-sign-in-button">
        <Link href="/sign-in">Sign in</Link>
      </Button>
      <Button asChild size="sm" variant={"default"} id="to-sign-up-button">
        <Link href="/sign-up">Sign up</Link>
      </Button>
    </div>
  );
}
