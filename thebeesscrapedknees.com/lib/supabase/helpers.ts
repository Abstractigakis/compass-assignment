import { User } from "@supabase/supabase-js";
import { createClient } from "./server";

export const getUser = async (): Promise<User> => {
  const supabase = await createClient();
  const { data, error } = await supabase.auth.getUser();
  if (error) throw error;
  if (!data?.user) throw new Error("User not found");
  return data.user;
};
