import { supabase } from "./supabaseClient";

/* ================= SIGN UP ================= */

export const signUpUser = async (email, password) => {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
  });

  if (error) throw error;

  // create profile row
  if (data.user) {
    await supabase.from("users").upsert({
      id: data.user.id,
      email: data.user.email,
    });
  }

  return data;
};

/* ================= LOGIN ================= */

export const signInUser = async (email, password) => {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) throw error;

  return data;
};

/* ================= LOGOUT ================= */

export const signOutUser = async () => {
  await supabase.auth.signOut();
};

/* ================= GET CURRENT USER ================= */

export const getCurrentUser = async () => {
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return user;
};
