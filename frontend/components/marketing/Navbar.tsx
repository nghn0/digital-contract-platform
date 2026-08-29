"use client";

import Link from "next/link";
import Image from "next/image";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useTheme } from "@/components/ThemeProvider";
import { supabase } from "@/lib/supabaseClient";
import { signOutUser } from "@/lib/auth";
import { Sun, Moon, LogOut } from "lucide-react";

export default function Navbar() {
  const router = useRouter();
  const { darkMode, toggleTheme } = useTheme();
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleSignOut = async () => {
    await signOutUser();
    router.refresh();
  };

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-[var(--color-border-color)] bg-[var(--color-background)]/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3 group">
          <Image src="/logo.png" alt="LegalVault Logo" width={36} height={36} className="object-contain" />
          <span className="hidden sm:block text-xl font-serif tracking-tight text-[var(--color-primary-text)]">
            Legal<span className="font-bold text-[var(--color-primary-gold)]">Vault</span>
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-[var(--color-muted-text)]">
          <Link href="#problem" className="hover:text-[var(--color-primary-text)] transition-colors">Product</Link>
          <Link href="#workflow" className="hover:text-[var(--color-primary-text)] transition-colors">How it works</Link>
          <Link href="#capabilities" className="hover:text-[var(--color-primary-text)] transition-colors">Capabilities</Link>
        </div>

        <div className="flex items-center gap-2 sm:gap-4">
          <button
            onClick={toggleTheme}
            className="p-2.5 rounded-full border transition-all bg-[var(--color-surface)] border-[var(--color-border-color)] text-[var(--color-primary-gold)] hover:brightness-110 cursor-pointer"
          >
            {darkMode ? <Sun size={20} /> : <Moon size={20} />}
          </button>

          {user ? (
            <div className="flex items-center gap-2 sm:gap-3">
              <span className="text-xs sm:text-sm font-medium text-[var(--color-primary-text)] truncate max-w-[70px] sm:max-w-[150px] md:max-w-none">
                {user.email}
              </span>
              <button 
                onClick={handleSignOut}
                className="text-[var(--color-muted-text)] hover:text-[var(--color-primary-text)] transition-colors p-1 cursor-pointer"
                title="Sign Out"
              >
                <LogOut size={18} />
              </button>
            </div>
          ) : (
            <Link href="/login" className="text-sm font-medium text-[var(--color-primary-text)] hover:text-[var(--color-primary-gold)] transition-colors hidden sm:block">
              Sign In
            </Link>
          )}

          <Link href="/dashboard" className="h-9 sm:h-10 px-3 sm:px-5 flex items-center justify-center rounded-lg bg-[var(--color-primary-gold)] text-[var(--color-surface)] text-xs sm:text-sm font-bold hover:bg-[var(--color-bright-gold)] transition-colors whitespace-nowrap">
            Access Vault
          </Link>
        </div>
      </div>
    </nav>
  );
}
