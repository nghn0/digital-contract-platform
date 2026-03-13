"use client";

import { useEffect, useState } from "react";
import { signWithMetaMask } from "@/utils/signContract";

export default function SenderDashboard() {
  const [contracts, setContracts] = useState([]);

  const SENDER_ID = "11111111-1111-1111-1111-111111111111";

  useEffect(() => {
    fetchContracts();
  }, []);

  const fetchContracts = async () => {
    const res = await fetch(
      `https://digital-contract-platform.onrender.com/contracts/sent/${SENDER_ID}`,
    );
    const data = await res.json();
    setContracts(data);
  };

  const handleSign = async (contract) => {
    try {
      // sign
      const { signature, wallet } = await signWithMetaMask(contract.file_url);

      // store signature A
      await fetch("https://digital-contract-platform.onrender.com/store-signature", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contract_id: contract.contract_id,
          user_id: SENDER_ID,
          wallet_address: wallet,
          signature,
          role: "A",
        }),
      });

      // finalize on chain
      await fetch(
        `https://digital-contract-platform.onrender.com/contracts/${contract.contract_id}/finalize`,
        { method: "POST" },
      );

      fetchContracts();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-[#1E201E] p-8">
      <div className="max-w-3xl mx-auto space-y-4">
        <h1 className="text-2xl text-[#ECDFCC] font-bold text-center">
          📤 Sent Contracts
        </h1>

        {contracts.map((c) => (
          <div key={c.contract_id} className="bg-[#3C3D37] p-5 rounded-xl">
            <p className="text-[#ECDFCC] mb-3">Status: {c.status}</p>

            {(c.status === "PENDING_SIGNATURE_A" || c.status === "SIGNED") &&
              !c.blockchain_tx_hash && (
                <button
                  onClick={() => handleSign(c)}
                  className="bg-[#697565] text-[#ECDFCC] px-4 py-2 rounded-xl"
                >
                  Sign & Finalize
                </button>
              )}

            {c.blockchain_tx_hash && (
              <p className="text-green-400 mt-2">TX: {c.blockchain_tx_hash}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
