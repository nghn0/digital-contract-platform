"use client";

import { useEffect, useState } from "react";
import { getCurrentUser, signOutUser } from "@/lib/auth";
import { signWithMetaMask } from "@/utils/signContract";
import { useRouter } from "next/navigation";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export default function Dashboard() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [recentContracts, setRecentContracts] = useState([]);
  const [signingId, setSigningId] = useState(null);

  useEffect(() => {
    init();

    // 🔥 auto refresh every 8 seconds
    const interval = setInterval(() => {
      if (user?.id) fetchRecent(user.id);
    }, 8000);

    return () => clearInterval(interval);
  }, [user?.id]);

  const init = async () => {
    const u = await getCurrentUser();
    if (!u) return router.push("/login");

    setUser(u);
    fetchRecent(u.id);
  };

  /* ================= FETCH BOTH SENT + RECEIVED ================= */

  const fetchRecent = async (userId) => {
    try {
      const res = await fetch(`${API_BASE_URL}/contracts/all/${userId}`);
      const data = await res.json();

      // 🔥 newest first
      const sorted = data.sort(
        (a, b) => new Date(b.created_at) - new Date(a.created_at),
      );

      setRecentContracts(sorted.slice(0, 5));
    } catch (err) {
      console.error(err);
    }
  };

  const handleLogout = async () => {
    await signOutUser();
    router.push("/login");
  };

  /* ================= SENDER SIGN & FINALIZE ================= */

  const handleSenderSign = async (contract) => {
    try {
      setSigningId(contract.contract_id);

      // 🔐 MetaMask sign
      const { signature, wallet } = await signWithMetaMask(contract.file_url);

      // 💾 store signature A
      await fetch("http://localhost:5001/store-signature", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          contract_id: contract.contract_id,
          user_id: user.id,
          wallet_address: wallet,
          signature,
          role: "A",
        }),
      });

      // ⛓ finalize on chain
      await fetch(
        `http://localhost:5001/contracts/${contract.contract_id}/finalize`,
        { method: "POST" },
      );

      fetchRecent(user.id);
    } catch (err) {
      console.error("Sender finalize failed:", err);
    } finally {
      setSigningId(null);
    }
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-[#FFF7D1] p-8">
      <div className="max-w-6xl mx-auto">
        {/* HEADER */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-[#563A9C]">
            Contract Dashboard
          </h1>

          <button
            onClick={handleLogout}
            className="bg-[#563A9C] text-white px-4 py-2 rounded-xl"
          >
            Logout
          </button>
        </div>

        {/* ACTION CARDS */}
        <div className="grid md:grid-cols-2 gap-6 mb-10">
          <div
            onClick={() => router.push("/upload")}
            className="cursor-pointer bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition border border-[#E8DDB5]"
          >
            <h2 className="text-xl font-bold text-[#563A9C] mb-2">
              📤 Send Contract
            </h2>
            <p className="text-gray-600">
              Upload and send a new contract for signature.
            </p>
          </div>

          <div
            onClick={() => router.push("/contracts")}
            className="cursor-pointer bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition border border-[#E8DDB5]"
          >
            <h2 className="text-xl font-bold text-[#563A9C] mb-2">
              📥 View Contracts
            </h2>
            <p className="text-gray-600">
              See all sent and received contracts.
            </p>
          </div>
        </div>

        {/* 🔥 RECENT ACTIVITY */}
        <div className="bg-white rounded-2xl p-6 shadow-lg border border-[#E8DDB5]">
          <h3 className="text-xl font-bold text-[#563A9C] mb-4">
            🕒 Recent Activity
          </h3>

          {recentContracts.length === 0 ? (
            <p className="text-gray-500">No recent contracts.</p>
          ) : (
            <div className="space-y-3">
              {recentContracts.map((c) => {
                const isSender = c.sender_id === user.id;
                const needsSenderSign =
                  isSender && c.status === "PENDING_SIGNATURE_A";
                const isRejected = isSender && c.status === "REJECTED";

                return (
                  <div
                    key={c.contract_id}
                    className="flex flex-col md:flex-row md:justify-between md:items-center gap-3 p-4 bg-[#FFF7D1] rounded-xl"
                  >
                    {/* LEFT */}
                    <div>
                      <p className="font-medium text-[#563A9C]">
                        {isSender ? "📤 Sent → " : "📥 Received ← "}
                        {c.receiver_email}
                      </p>

                      <span className="px-3 py-1 rounded-full text-xs bg-[#8B5DFF] text-white">
                        {c.status}
                      </span>
                    </div>

                    {/* RIGHT ACTIONS */}

                    {/* ✅ SIGN (ONLY SENDER) */}
                    {needsSenderSign && (
                      <button
                        onClick={() => handleSenderSign(c)}
                        disabled={signingId === c.contract_id}
                        className="bg-[#8B5DFF] hover:bg-[#6A42C2] text-white px-4 py-2 rounded-xl font-semibold"
                      >
                        {signingId === c.contract_id
                          ? "Finalizing..."
                          : "✍️ Sign & Finalize"}
                      </button>
                    )}

                    {/* ✅ REUPLOAD (ONLY SENDER) */}
                    {isRejected && (
                      <button
                        onClick={() =>
                          router.push(
                            `/upload?email=${encodeURIComponent(c.receiver_email)}&contractId=${c.contract_id}`,
                          )
                        }
                        className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-xl font-semibold"
                      >
                        🔄 Reupload
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
