"use client";

import { useEffect, useState } from "react";
import { signWithMetaMask } from "@/utils/signContract";

export default function ReceiverDashboard() {
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);

  const RECEIVER_ID = "22222222-2222-2222-2222-222222222222";

  useEffect(() => {
    fetchContracts();
  }, []);

  const fetchContracts = async () => {
    try {
      const res = await fetch(
        `https://digital-contract-platform.onrender.com/contracts/received/${RECEIVER_ID}`,
      );
      const data = await res.json();
      setContracts(data);
    } catch (err) {
      console.error("Fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (contractId, newStatus) => {
    try {
      await fetch(`https://digital-contract-platform.onrender.com/contracts/${contractId}/status`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status: newStatus }),
      });

      fetchContracts();
    } catch (err) {
      console.error("Status update failed:", err);
    }
  };

  const handleReceiverSign = async (contract) => {
    try {
      // 🔐 MetaMask sign
      const { signature, wallet } = await signWithMetaMask(contract.file_url);

      // 💾 store signature B
      await fetch("https://digital-contract-platform.onrender.com/store-signature", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          contract_id: contract.contract_id,
          user_id: RECEIVER_ID,
          wallet_address: wallet,
          signature,
          role: "B",
        }),
      });

      fetchContracts();
    } catch (err) {
      console.error("Receiver sign failed:", err);
    }
  };

  return (
    <div className="min-h-screen bg-[#1E201E] p-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-2xl font-bold mb-6 text-center text-[#ECDFCC]">
          📥 Received Contracts
        </h1>

        {loading && <p className="text-center text-[#ECDFCC]">Loading...</p>}

        {!loading && contracts.length === 0 && (
          <p className="text-center text-[#697565]">No contracts received.</p>
        )}

        <div className="space-y-4">
          {contracts.map((contract) => (
            <div
              key={contract.contract_id}
              className="bg-[#3C3D37] border border-[#697565] rounded-xl p-5 shadow"
            >
              <p className="font-semibold mb-3 text-[#ECDFCC]">
                Status: {contract.status}
              </p>
              <p className="text-xs text-red-400">DEBUG: [{contract.status}]</p>

              <div className="flex flex-wrap gap-3">
                {/* VIEW */}
                <a
                  href={contract.file_url}
                  target="_blank"
                  className="bg-[#697565] hover:bg-[#5a6458] text-[#ECDFCC] px-4 py-2 rounded-xl transition"
                >
                  View Contract
                </a>

                {/* ================= STEP 1: ACCEPT / REJECT ================= */}
                {contract.status === "SENT" && (
                  <>
                    <button
                      onClick={() =>
                        updateStatus(
                          contract.contract_id,
                          "PENDING_SIGNATURE_B",
                        )
                      }
                      className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-xl transition"
                    >
                      Accept
                    </button>

                    <button
                      onClick={() =>
                        updateStatus(contract.contract_id, "REJECTED")
                      }
                      className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-xl transition"
                    >
                      Reject
                    </button>
                  </>
                )}

                {/* ================= STEP 2: RECEIVER SIGN ================= */}
                {contract.status?.trim().toUpperCase() === "PENDING_SIGNATURE_B" && (
                  <button
                    onClick={() => handleReceiverSign(contract)}
                    className="bg-[#8B5DFF] hover:bg-[#6A42C2] text-white px-4 py-2 rounded-xl transition"
                  >
                    ✍️ Sign Contract
                  </button>
                )}

                {/* ================= WAITING STATES ================= */}
                {contract.status === "PENDING_SIGNATURE_A" && (
                  <span className="text-yellow-400 text-sm self-center">
                    Waiting for sender signature…
                  </span>
                )}

                {contract.status === "ON_BLOCKCHAIN" && (
                  <span className="text-green-400 text-sm self-center">
                    ✅ Stored on blockchain
                  </span>
                )}

                {contract.status === "REJECTED" && (
                  <span className="text-red-400 text-sm self-center">
                    ❌ Rejected
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
