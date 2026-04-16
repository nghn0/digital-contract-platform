"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, ShieldCheck, UploadCloud, Info, AlertOctagon, CheckCircle2 } from "lucide-react";
import { supabase } from "@/lib/supabaseClient";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5001";

export default function VerifierPage() {
  const router = useRouter();
  
  const [file, setFile] = useState(null);
  const [txHash, setTxHash] = useState("");
  const [isVerifying, setIsVerifying] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileUpload = (e) => {
    const selectedFile = e.target.files ? e.target.files[0] : e;
    if (!selectedFile) return;
    setFile(selectedFile);
    setResult(null);
    setError(null);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragover") setIsDragging(true);
    else if (e.type === "dragleave") setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleVerify = async () => {
    if (!file || !txHash.trim()) {
      setError("Please provide both a transaction hash and a document.");
      return;
    }
    
    try {
      setIsVerifying(true);
      setError(null);
      setResult(null);

      const formData = new FormData();
      formData.append("file", file);
      formData.append("txHash", txHash.trim());

      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token || "";

      const res = await fetch(`${API_BASE_URL}/verify-contract`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
        body: formData,
      });

      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.error || d.details || "Verification request failed");
      }

      const data = await res.json();
      setResult({
        success: data.success,
        message: data.message,
        isTampered: data.isTampered
      });
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-[#150D0A] to-[#0D0D0D] text-[#F5E6D8] flex flex-col items-center py-20 px-6">
      <button 
        onClick={() => router.push('/dashboard')}
        className="absolute top-8 left-8 flex items-center gap-2 text-stone-400 hover:text-[#D4AF37] transition-colors"
      >
        <ArrowLeft size={16} /> <span className="text-sm font-semibold tracking-widest uppercase">Dashboard</span>
      </button>

      <div className="w-full max-w-2xl bg-[#1A110D] border border-[#2B1D16] rounded-3xl p-8 shadow-2xl relative overflow-hidden">
        
        {/* Background glow */}
        <div className="absolute -top-32 -right-32 w-64 h-64 bg-[#D4AF37]/10 blur-3xl rounded-full"></div>

        <div className="flex flex-col items-center mb-10 relative z-10">
          <div className="w-20 h-20 mb-6 rounded-2xl bg-gradient-to-br from-[#1A110D] to-[#2C1810] border border-[#2B1D16] flex items-center justify-center shadow-[0_0_20px_rgba(212,175,55,0.05)]">
            <ShieldCheck size={40} className="text-[#A39284]" />
          </div>
          <h1 className="text-3xl font-serif text-center mb-3">Cryptographic Verifier</h1>
          <p className="text-[#A39284] text-center max-w-md">
            Upload an offline document and its associated blockchain transaction hash to mathematically prove it has not been forged or altered.
          </p>
        </div>

        <div className="space-y-6 relative z-10">
          {/* TX Hash Input */}
          <div>
            <label className="block text-xs font-bold tracking-widest uppercase text-stone-500 mb-2 ml-1">
              Blockchain Transaction Hash
            </label>
            <input 
              type="text" 
              value={txHash}
              onChange={(e) => {
                setTxHash(e.target.value);
                setResult(null);
              }}
              placeholder="0x..."
              className="w-full bg-black/40 border border-[#2B1D16] focus:border-[#D4AF37]/50 rounded-xl px-5 py-4 text-stone-300 font-mono text-sm outline-none transition-colors"
            />
          </div>

          {/* File Upload */}
          <div>
            <label className="block text-xs font-bold tracking-widest uppercase text-stone-500 mb-2 ml-1">
              Document Object
            </label>
            <label 
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              className={`cursor-pointer group flex flex-col items-center justify-center w-full h-32 border-2 border-dashed transition-all rounded-xl ${
                file || isDragging 
                  ? 'border-[#D4AF37] bg-[#D4AF37]/10' 
                  : 'border-[#2B1D16] bg-black/40 hover:border-[#D4AF37]/50'
              }`}
            >
              <UploadCloud size={32} className={`${file || isDragging ? 'text-[#D4AF37]' : 'text-[#A39284] group-hover:text-[#D4AF37]'} mb-2 transition-colors`} />
              <span className={`text-sm ${file || isDragging ? 'text-[#D4AF37] font-semibold' : 'text-[#A39284]'}`}>
                {isDragging ? "Drop document here" : file ? file.name : "Click to select or drag and drop"}
              </span>
              <input 
                type="file" 
                className="hidden" 
                onChange={handleFileUpload} 
              />
            </label>
          </div>

          {/* Actions */}
          <div className="pt-4">
            <button 
              onClick={handleVerify}
              disabled={isVerifying || !file || !txHash.trim()}
              className="w-full h-14 bg-[#D4AF37] hover:bg-[#B8962E] disabled:bg-[#D4AF37]/20 disabled:text-[#F5E6D8]/30 disabled:cursor-not-allowed text-[#1A110D] font-bold tracking-widest uppercase text-sm rounded-xl shadow-[0_0_20px_rgba(212,175,55,0.2)] transition-all flex items-center justify-center gap-2"
            >
              {isVerifying ? (
                <>
                  <div className="w-5 h-5 border-2 border-[#1A110D]/30 border-t-[#1A110D] rounded-full animate-spin"></div>
                  Computing Hashes...
                </>
              ) : (
                "Verify Authenticity"
              )}
            </button>
          </div>

          {/* Results/Errors */}
          {error && (
            <div className="p-4 bg-red-950/30 border border-red-900/50 rounded-xl flex items-start gap-3">
              <Info className="text-red-400 shrink-0 mt-0.5" size={18} />
              <p className="text-sm text-red-200">{error}</p>
            </div>
          )}

          {result && (
            <div className={`p-6 rounded-xl border flex gap-4 ${
              result.success 
                ? 'bg-green-950/20 border-green-900/40' 
                : 'bg-red-950/20 border-red-900/40'
            }`}>
              {result.success ? (
                <CheckCircle2 className="text-green-500 shrink-0" size={28} />
              ) : (
                <AlertOctagon className="text-red-500 shrink-0" size={28} />
              )}
              
              <div>
                <h3 className={`text-lg font-serif font-bold mb-1 ${result.success ? 'text-green-400' : 'text-red-400'}`}>
                  {result.success ? "Verification Successful" : "Verification Failed"}
                </h3>
                <p className={`text-sm ${result.success ? 'text-green-200/80' : 'text-red-200/80'}`}>
                  {result.message}
                </p>
                {!result.success && result.isTampered && (
                  <div className="mt-3 text-xs bg-red-950/60 p-3 rounded font-mono text-red-300 border border-red-900/50">
                    The cryptographic hash of the provided file does not match the ledger. The document has been edited since it was signed.
                  </div>
                )}
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
