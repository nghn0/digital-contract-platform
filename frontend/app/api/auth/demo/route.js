import { NextResponse } from 'next/server';
import { createClient } from '@/utils/supabase/server';

export async function POST() {
  const email = process.env.DEMO_USER_EMAIL;
  const password = process.env.DEMO_USER_PASSWORD;

  if (!email || !password) {
    return NextResponse.json(
      { error: "Demo authentication is not configured on this environment." },
      { status: 501 }
    );
  }

  try {
    const supabase = await createClient();

    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      // Return a generic error to avoid leaking details if the account doesn't exist
      return NextResponse.json(
        { error: "Demo authentication failed." },
        { status: 401 }
      );
    }

    return NextResponse.json({ success: true });
  } catch (err) {
    return NextResponse.json(
      { error: "An unexpected error occurred during demo authentication." },
      { status: 500 }
    );
  }
}
