"use client";

import { useState } from "react";
import { signUpUser } from "@/lib/auth";
import { useRouter } from "next/navigation";

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const handleSignup = async () => {
    try {
      setLoading(true);
      setMsg("");

      await signUpUser(email, password);

      setMsg("✅ Account created!");
      router.push("/login");
    } catch (err) {
      setMsg("❌ " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FFF7D1] flex items-center justify-center">
      <div className="w-full max-w-md bg-white rounded-2xl p-8 shadow-lg">
        <h1 className="text-2xl font-bold text-center mb-6 text-[#563A9C]">
          Create Account
        </h1>

        <input
          type="email"
          placeholder="Email"
          className="w-full mb-4 p-3 border rounded-xl"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <input
          type="password"
          placeholder="Password"
          className="w-full mb-4 p-3 border rounded-xl"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <button
          onClick={handleSignup}
          disabled={loading}
          className="w-full bg-[#8B5DFF] hover:bg-[#6A42C2] text-white py-3 rounded-xl font-semibold"
        >
          {loading ? "Creating..." : "Sign Up"}
        </button>

        {msg && (
          <p className="text-center mt-4 text-sm">{msg}</p>
        )}
      </div>
    </div>
  );
}
