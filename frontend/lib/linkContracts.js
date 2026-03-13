import { supabase } from "@/lib/supabaseClient";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export const linkContractsAfterLogin = async () => {
  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session) return;

    await fetch(`${API_BASE_URL}/link-receiver`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${session.access_token}`,
      },
    });
  } catch (err) {
    console.error("Link receiver failed:", err);
  }
};
