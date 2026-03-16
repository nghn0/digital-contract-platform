"use client";

export const dynamic = "force-dynamic";

import { Suspense, useState, useEffect } from "react";
import { supabase } from "@/lib/supabaseClient";
import { useSearchParams, useRouter } from "next/navigation";
import { FileUp, Mail, ArrowLeft, ShieldCheck, FileText, X } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

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

  /* ================= THEME SYNC START ================= */
  const [darkMode, setDarkMode] = useState(true);

  useEffect(() => {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme !== null) {
      setDarkMode(savedTheme === "true");
    }
  }, []);
  /* ================= THEME SYNC END ================== */

  useEffect(() => {
    if (emailFromQuery) {
      setReceiverEmail(emailFromQuery);
    }
  }, [emailFromQuery]);

  const handleUpload = async () => {
    if (!file || !receiverEmail) {
      setMessage("⚠️ Please select a file and enter receiver email");
      return;
    }

    try {
      setLoading(true);
      setMessage("");

      const { data: { session } } = await supabase.auth.getSession();

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

      const res = await fetch(`${API_BASE_URL}/upload-contract`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
        body: formData,
      });

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
    <div className={`min-h-screen transition-colors duration-500 p-6 md:p-12 ${
      darkMode 
        ? "bg-[radial-gradient(ellipse_at_top_left,_var(--tw-gradient-stops))] from-[#3E2C23] via-[#150D0A] to-[#0D0D0D] text-[#F5E6D8]" 
        : "bg-[#FDFCF9] text-[#2C1810]"
    }`}>
      <div className="max-w-2xl mx-auto">
        
        {/* BACK NAVIGATION */}
        <button 
          onClick={() => router.push('/dashboard')}
          className={`flex items-center gap-2 transition-colors mb-8 group uppercase tracking-widest text-sm font-semibold ${
            darkMode ? "text-[#A39284] hover:text-[#D4AF37]" : "text-gray-500 hover:text-[#D4AF37]"
          }`}
        >
          <ArrowLeft size={18} className="group-hover:-translate-x-1 transition-transform" />
          <span> Dashboard</span>
        </button>

        {/* HEADER SECTION */}
        <div className="text-center mb-10">
          <div className={`inline-block p-4 rounded-2xl mb-4 border ${
            darkMode ? "bg-[#D4AF37]/10 border-[#D4AF37]/20" : "bg-[#D4AF37]/5 border-[#D4AF37]/30"
          }`}>
            <ShieldCheck size={40} className="text-[#D4AF37]" />
          </div>
          <h1 className="text-4xl font-serif font-bold mb-2">
            {contractIdFromQuery ? "Reissue Instrument" : "Execute New Contract"}
          </h1>
          <p className={`${darkMode ? "text-[#A39284]" : "text-gray-600"} font-medium tracking-wide`}>
            Securely upload and dispatch your legal documents for cryptographic signature.
          </p>
        </div>

        {/* UPLOAD FORM CONTAINER */}
        <div className={`rounded-3xl p-8 shadow-2xl border transition-all ${
          darkMode ? "bg-[#1A110D] border-[#2B1D16]" : "bg-white border-gray-200"
        }`}>
          
          {/* FILE UPLOAD ZONE */}
          <div className="mb-8">
            <label className={`block text-xs font-bold uppercase tracking-[0.2em] mb-3 ml-1 ${
              darkMode ? "text-[#A39284]" : "text-gray-500"
            }`}>
              Document Attachment
            </label>
            {!file ? (
              <div className="relative group transition-all">
                <input
                  type="file"
                  onChange={(e) => setFile(e.target.files[0])}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                />
                <div className={`border-2 border-dashed rounded-2xl p-10 text-center transition-all ${
                  darkMode 
                    ? "border-[#2B1D16] group-hover:border-[#D4AF37]/40 bg-black/20" 
                    : "border-gray-200 group-hover:border-[#D4AF37] bg-gray-50"
                }`}>
                  <FileUp size={32} className={`mx-auto mb-4 transition-colors ${
                    darkMode ? "text-[#A39284] group-hover:text-[#D4AF37]" : "text-gray-400 group-hover:text-[#D4AF37]"
                  }`} />
                  <p className={`font-medium ${darkMode ? "text-[#F5E6D8]" : "text-gray-800"}`}>Click to select or drag and drop</p>
                  <p className="text-[#A39284] text-xs mt-2">PDF, DOCX (Max 10MB)</p>
                </div>
              </div>
            ) : (
              <div className={`flex items-center justify-between border p-4 rounded-xl ${
                darkMode ? "bg-[#D4AF37]/10 border-[#D4AF37]/30" : "bg-[#D4AF37]/5 border-[#D4AF37]/40"
              }`}>
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-[#D4AF37] rounded-lg">
                    <FileText size={20} className="text-[#1A110D]" />
                  </div>
                  <div>
                    <p className={`text-sm font-bold truncate max-w-[200px] ${darkMode ? "text-[#F5E6D8]" : "text-gray-900"}`}>{file.name}</p>
                    <p className={`text-[10px] uppercase font-mono ${darkMode ? "text-[#A39284]" : "text-gray-500"}`}>Ready for dispatch</p>
                  </div>
                </div>
                <button 
                  onClick={() => setFile(null)}
                  className={`p-2 rounded-full transition-colors ${
                    darkMode ? "hover:bg-white/5 text-[#A39284] hover:text-red-400" : "hover:bg-black/5 text-gray-400 hover:text-red-600"
                  }`}
                >
                  <X size={18} />
                </button>
              </div>
            )}
          </div>

          {/* EMAIL INPUT */}
          <div className="mb-8">
            <label className={`block text-xs font-bold uppercase tracking-[0.2em] mb-3 ml-1 ${
              darkMode ? "text-[#A39284]" : "text-gray-500"
            }`}>
              Recipient Party
            </label>
            <div className="relative">
              <Mail className={`absolute left-4 top-1/2 -translate-y-1/2 ${darkMode ? "text-[#A39284]" : "text-gray-400"}`} size={18} />
              <input
                type="email"
                placeholder="receiver@legalvault.com"
                value={receiverEmail}
                onChange={(e) => setReceiverEmail(e.target.value)}
                disabled={!!emailFromQuery}
                className={`w-full pl-12 pr-4 py-4 rounded-2xl border transition-all outline-none font-medium ${
                  darkMode
                    ? (emailFromQuery ? "bg-black/40 border-[#2B1D16] text-[#A39284]" : "bg-black/20 border-[#2B1D16] focus:border-[#D4AF37]/50 text-[#F5E6D8]")
                    : (emailFromQuery ? "bg-gray-100 border-gray-200 text-gray-400" : "bg-white border-gray-200 focus:border-[#D4AF37] text-gray-900")
                } ${emailFromQuery ? "cursor-not-allowed" : ""}`}
              />
            </div>
            {emailFromQuery && (
              <p className="text-[10px] text-[#D4AF37] uppercase tracking-wider mt-2 ml-1">
                Recipient fixed for reissue protocol
              </p>
            )}
          </div>

          {/* DISPATCH BUTTON */}
          <button
            onClick={handleUpload}
            disabled={loading}
            className={`w-full py-4 rounded-2xl font-bold text-sm uppercase tracking-[0.2em] transition-all shadow-lg active:scale-[0.98] ${
              loading 
                ? "bg-white/5 text-[#A39284] cursor-wait" 
                : "bg-[#D4AF37] hover:bg-[#B8962E] text-[#1A110D]"
            }`}
          >
            {loading
              ? "Verifying & Sending..."
              : contractIdFromQuery
              ? "Reissue Instrument"
              : "Dispatch Contract"}
          </button>

          {/* STATUS MESSAGE */}
          {message && (
            <div className={`mt-6 p-4 rounded-xl text-center text-sm font-medium border ${
              message.includes('✅') 
                ? 'bg-green-500/10 border-green-500/20 text-green-400' 
                : 'bg-red-500/10 border-red-500/20 text-red-400'
            }`}>
              {message}
            </div>
          )}
        </div>

        {/* FOOTER SECURITY INFO */}
        <p className={`mt-8 text-center text-[10px] font-mono tracking-tighter uppercase italic ${
          darkMode ? "text-[#A39284]/40" : "text-gray-400"
        }`}>
          Files are encrypted before transit • 256-bit AES End-to-End
        </p>
      </div>
    </div>
  );
}

/* ================= PAGE WRAPPER ================= */

export default function UploadPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#0D0D0D] flex items-center justify-center">
        <div className="text-[#D4AF37] font-serif italic text-xl animate-pulse">Initializing Secure Uplink...</div>
      </div>
    }>
      <UploadContent />
    </Suspense>
  );
}
