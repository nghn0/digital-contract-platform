"use client";

import { Suspense, useState, useEffect } from "react";
import { supabase } from "@/lib/supabaseClient";
import { useSearchParams, useRouter } from "next/navigation";

/* ================= MAIN CONTENT ================= */

function UploadContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const emailFromQuery = searchParams.get("email");
  const contractIdFromQuery = searchParams.get("contractId");

  const [file, setFile] = useState(null);
  const [receiverEmail, setReceiverEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  /* ================= PREFILL EMAIL ================= */

  useEffect(() => {
    if (emailFromQuery) {
      setReceiverEmail(emailFromQuery);
    }
  }, [emailFromQuery]);

  /* ================= UPLOAD ================= */

  const handleUpload = async () => {
    if (!file || !receiverEmail) {
      setMessage("⚠️ Please select a file and enter receiver email");
      return;
    }

    try {
      setLoading(true);
      setMessage("");

      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        setMessage("❌ Please login again");
        return;
      }

      const formData = new FormData();
      formData.append("file", file);
      formData.append("receiver_email", receiverEmail);

      if (contractIdFromQuery) {
        formData.append("contract_id", contractIdFromQuery);
      }

      const res = await fetch(
        "https://digital-contract-platform.onrender.com/upload-contract",
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
          body: formData,
        }
      );

      const text = await res.text();

      if (!res.ok) {
        throw new Error(text || "Upload failed");
      }

      setMessage("✅ Contract sent successfully!");
      setFile(null);

      setTimeout(() => {
        router.push("/dashboard");
      }, 1000);
    } catch (err) {
      console.error(err);
      setMessage("❌ " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FFF7D1] flex items-center justify-center p-6">
      <div className="w-full max-w-xl bg-white rounded-2xl shadow-xl p-8 border border-[#E6DBB5]">
        <h1 className="text-2xl font-bold mb-6 text-center text-[#563A9C]">
          📄 {contractIdFromQuery ? "Reupload Contract" : "Send Contract"}
        </h1>

        {/* FILE */}
        <input
          type="file"
          onChange={(e) => setFile(e.target.files[0])}
          className="mb-4 w-full rounded-lg border border-gray-300 bg-white text-gray-800 p-2"
        />

        {/* EMAIL */}
        <input
          type="email"
          placeholder="Receiver email"
          value={receiverEmail}
          onChange={(e) => setReceiverEmail(e.target.value)}
          disabled={!!emailFromQuery}
          className={`w-full mb-4 rounded-lg border border-gray-300 p-3 ${
            emailFromQuery
              ? "bg-gray-100 text-gray-500 cursor-not-allowed"
              : "bg-white text-gray-800"
          }`}
        />

        {/* BUTTON */}
        <button
          onClick={handleUpload}
          disabled={loading}
          className="w-full bg-[#8B5DFF] hover:bg-[#6A42C2] text-white py-3 rounded-xl font-semibold transition"
        >
          {loading
            ? "Sending..."
            : contractIdFromQuery
            ? "Reupload"
            : "Send Contract"}
        </button>

        {/* MESSAGE */}
        {message && (
          <p className="mt-4 text-center font-medium text-gray-700">
            {message}
          </p>
        )}
      </div>
    </div>
  );
}

/* ================= PAGE WRAPPER ================= */

export default function UploadPage() {
  return (
    <Suspense fallback={<div className="p-10 text-center">Loading...</div>}>
      <UploadContent />
    </Suspense>
  );
}