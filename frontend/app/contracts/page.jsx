"use client";

import { useEffect, useState } from "react";
import { getCurrentUser } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { signWithMetaMask } from "@/utils/signContract";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export default function ContractsPage() {
  const router = useRouter();
  const [contracts, setContracts] = useState([]);
  const [user, setUser] = useState(null);
  const [loadingId, setLoadingId] = useState(null);

  /* ================= INIT ================= */

  useEffect(() => {
    init();
  }, []);

  const init = async () => {
    const u = await getCurrentUser();
    if (!u) return router.push("/login");

    setUser(u);
    fetchContracts(u.id);
  };

  /* ================= AUTO REFRESH 🔥 ================= */

  useEffect(() => {
    if (!user?.id) return;

    const interval = setInterval(() => {
      fetchContracts(user.id);
    }, 6000); // refresh every 6 sec

    return () => clearInterval(interval); // prevent memory leak
  }, [user?.id]);

  /* ================= FETCH ================= */

  const fetchContracts = async (userId) => {
    try {
      const res = await fetch(
        `${API_BASE_URL}/contracts/all/${userId}`
      );
      const data = await res.json();
      setContracts(data);
    } catch (err) {
      // If local server fails, try the deployed server as fallback
      try {
        const res = await fetch(
          `${API_BASE_URL}/contracts/all/${userId}`
        );
        const data = await res.json();
        setContracts(data);
      } catch (fallbackErr) {
        console.error("Both local and remote fetch failed:", fallbackErr);
      }
      console.error(err);
    }
  };

  /* ================= RECEIVER ACCEPT ================= */

  const handleAccept = async (contractId) => {
    try {
      setLoadingId(contractId);

      await fetch(`${API_BASE_URL}/contracts/${contractId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "PENDING_SIGNATURE_B" }),
      });

      fetchContracts(user.id);
    } catch (err) {
      console.error("Accept failed:", err);
    } finally {
      setLoadingId(null);
    }
  };

  /* ================= RECEIVER REJECT ================= */

  const handleReject = async (contractId) => {
    try {
      setLoadingId(contractId);

      await fetch(`${API_BASE_URL}/contracts/${contractId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "REJECTED" }),
      });

      fetchContracts(user.id);
    } catch (err) {
      console.error("Reject failed:", err);
    } finally {
      setLoadingId(null);
    }
  };

  /* ================= RECEIVER SIGN ================= */

  const handleReceiverSign = async (contract) => {
    try {
      setLoadingId(contract.contract_id);

      const { signature, wallet } = await signWithMetaMask(
        contract.file_url
      );

      await fetch("${API_BASE_URL}/store-signature", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          contract_id: contract.contract_id,
          user_id: user.id,
          wallet_address: wallet,
          signature,
          role: "B",
        }),
      });

      fetchContracts(user.id);
    } catch (err) {
      console.error("Receiver sign failed:", err);
    } finally {
      setLoadingId(null);
    }
  };

  /* ================= SENDER SIGN & FINALIZE ================= */

  const handleSenderSign = async (contract) => {
    try {
      setLoadingId(contract.contract_id);

      const { signature, wallet } = await signWithMetaMask(
        contract.file_url
      );

      await fetch("${API_BASE_URL}/store-signature", {
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

      await fetch(
        `${API_BASE_URL}/contracts/${contract.contract_id}/finalize`,
        { method: "POST" }
      );

      fetchContracts(user.id);
    } catch (err) {
      console.error("Sender finalize failed:", err);
    } finally {
      setLoadingId(null);
    }
  };

  /* ================= COPY TX ================= */

  const copyTx = (tx) => {
    navigator.clipboard.writeText(tx);
    alert("✅ TX copied");
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-[#FFF7D1] p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-[#563A9C] mb-6">
          📄 All Contracts
        </h1>

        {contracts.length === 0 ? (
          <p className="text-gray-500">No contracts found.</p>
        ) : (
          <div className="space-y-4">
            {contracts.map((c) => {
              const isSender = c.sender_id === user.id;
              const status = c.status?.trim().toUpperCase();

              return (
                <div
                  key={c.contract_id}
                  className="bg-white rounded-2xl p-6 shadow-lg border border-[#E8DDB5]"
                >
                  <div className="flex justify-between items-center mb-3">
                    <span className="font-semibold text-[#563A9C]">
                      {isSender ? "📤 Sent" : "📥 Received"} —{" "}
                      {c.receiver_email}
                    </span>

                    <span className="px-3 py-1 rounded-full text-sm bg-[#8B5DFF] text-white">
                      {status}
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-3">
                    <a
                      href={c.file_url}
                      target="_blank"
                      className="bg-[#563A9C] text-white px-4 py-2 rounded-xl"
                    >
                      View
                    </a>

                    {c.blockchain_tx_hash && (
                      <button
                        onClick={() => copyTx(c.blockchain_tx_hash)}
                        className="bg-[#8B5DFF] text-white px-4 py-2 rounded-xl"
                      >
                        Copy TX
                      </button>
                    )}

                    {!isSender && status === "SENT" && (
                      <>
                        <button
                          disabled={loadingId === c.contract_id}
                          onClick={() => handleAccept(c.contract_id)}
                          className="bg-green-600 text-white px-4 py-2 rounded-xl"
                        >
                          Accept
                        </button>

                        <button
                          disabled={loadingId === c.contract_id}
                          onClick={() => handleReject(c.contract_id)}
                          className="bg-red-600 text-white px-4 py-2 rounded-xl"
                        >
                          Reject
                        </button>
                      </>
                    )}

                    {!isSender && status === "PENDING_SIGNATURE_B" && (
                      <button
                        disabled={loadingId === c.contract_id}
                        onClick={() => handleReceiverSign(c)}
                        className="bg-[#6A42C2] text-white px-4 py-2 rounded-xl"
                      >
                        ✍️ Sign Contract
                      </button>
                    )}

                    {isSender && status === "PENDING_SIGNATURE_A" && (
                      <button
                        disabled={loadingId === c.contract_id}
                        onClick={() => handleSenderSign(c)}
                        className="bg-[#563A9C] text-white px-4 py-2 rounded-xl"
                      >
                        🚀 Sign & Finalize
                      </button>
                    )}

                    {isSender && status === "REJECTED" && (
                      <button
                        onClick={() => router.push("/upload")}
                        className="bg-[#8B5DFF] text-white px-4 py-2 rounded-xl"
                      >
                        Reupload
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
