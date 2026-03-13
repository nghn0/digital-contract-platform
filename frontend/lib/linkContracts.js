import { supabase } from "@/lib/supabaseClient";

export const linkContractsAfterLogin = async () => {
  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session) return;

    await fetch("https://digital-contract-platform.onrender.com/link-receiver", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${session.access_token}`,
      },
    });
  } catch (err) {
    console.error("Link receiver failed:", err);
  }
};
