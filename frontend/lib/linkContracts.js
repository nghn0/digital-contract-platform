import { supabase } from "@/lib/supabaseClient";

export const linkContractsAfterLogin = async () => {
  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session) return;

    await fetch("http://127.0.0.1:5001/link-receiver", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${session.access_token}`,
      },
    });
  } catch (err) {
    console.error("Link receiver failed:", err);
  }
};
