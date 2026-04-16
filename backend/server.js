require("dotenv").config();
const jwt = require("jsonwebtoken");
const express = require("express");
const multer = require("multer");
const cors = require("cors");
const crypto = require("crypto");
const { createClient } = require("@supabase/supabase-js");
const { ethers } = require("ethers");
const modelClient = require("./services/modelClient");

/* ================= RETRY HELPER ================= */

const retryRequest = async (fn, retries = 3, delay = 1000) => {
  for (let i = 0; i < retries; i++) {
    try {
      return await fn();
    } catch (err) {
      const isNetworkError = 
        err.message.includes("ECONNRESET") || 
        err.message.includes("fetch failed") || 
        err.message.includes("Timeout") ||
        err.message.includes("ConnectTimeoutError");

      if (i === retries - 1 || !isNetworkError) throw err;
      
      console.warn(`⚠️ Request failed (Attempt ${i + 1}/${retries}): ${err.message}. Retrying in ${delay}ms...`);
      await new Promise(r => setTimeout(r, delay));
      delay *= 2; // Exponential backoff
    }
  }
};

const app = express();
app.use(express.json());
app.use(cors());

const nodemailer = require("nodemailer");

const transporter = nodemailer.createTransport({
  service: "gmail",
  auth: {
    user: process.env.EMAIL_USER,
    pass: process.env.EMAIL_PASS,
  },
});

console.log("EMAIL_USER:", process.env.EMAIL_USER);
console.log("EMAIL_PASS exists:", !!process.env.EMAIL_PASS);

/* ================= AUTH MIDDLEWARE ================= */

const authenticateUser = async (req, res, next) => {
  try {
    const token = req.headers.authorization?.split(" ")[1];

    if (!token) {
      return res.status(401).json({ error: "Unauthorized" });
    }

    const decoded = jwt.decode(token);

    if (!decoded?.sub) {
      return res.status(401).json({ error: "Invalid token" });
    }

    req.user = {
      id: decoded.sub,
      email: decoded.email,
    };

    next();
  } catch (err) {
    return res.status(401).json({ error: "Auth failed" });
  }
};

/* ================= SUPABASE ================= */

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE,
);

/* ================= HASH VERIFICATION HELPER ================= */

const verifyContractHash = async (contractId) => {
  console.log(`🔍 Verifying integrity for contract: ${contractId}`);

  // 1. Get contract record
  const { data: contract, error: dbError } = await retryRequest(() => 
    supabase
      .from("contracts")
      .select("file_url, contract_hash")
      .eq("contract_id", contractId)
      .single()
  );

  if (dbError || !contract) throw new Error("Contract record not found");

  // 2. Download file into memory (RAM)
  const res = await fetch(contract.file_url);
  if (!res.ok) throw new Error("Could not fetch file from storage for verification");
  const buffer = await res.arrayBuffer();

  // 3. Recompute SHA-256 hash
  const currentHash = "0x" + crypto
    .createHash("sha256")
    .update(Buffer.from(buffer))
    .digest("hex");

  // 4. Detailed comparison
  if (currentHash !== contract.contract_hash) {
    console.error(`💥 HASH MISMATCH detected! DB: ${contract.contract_hash} vs FILE: ${currentHash}`);
    throw new Error("Contract integrity check failed: The document has been modified since upload.");
  }

  console.log("✅ Integrity verified. Hash matches database.");
  return true;
};

/* ================= FILE UPLOAD ================= */

const upload = multer({ storage: multer.memoryStorage() });

/* ================= UPLOAD CONTRACT ================= */

app.post(
  "/upload-contract",
  authenticateUser,
  upload.single("file"),
  async (req, res) => {
    try {
      console.log("📥 Upload request received");

      const sender_id = req.user.id;
      const { receiver_email, contract_id } = req.body;
      const file = req.file;

      if (!file || !receiver_email) {
        return res.status(400).json({ error: "Missing data" });
      }

      /* =====================================================
         🔒 DUPLICATE CHECK (ONLY for NEW contracts)
      ===================================================== */

      if (!contract_id) {
        const { data: existing } = await supabase
          .from("contracts")
          .select("*")
          .eq("sender_id", sender_id)
          .eq("receiver_email", receiver_email)
          .eq("is_active", true)
          .neq("status", "REJECTED")
          .neq("status", "ON_BLOCKCHAIN");

        if (existing.length > 0) {
          return res.status(400).json({
            error: "Active contract already exists for this email",
          });
        }
      }

      /* =====================================================
         📦 UPLOAD FILE
      ===================================================== */

      const safeName = file.originalname
        .replace(/[^a-zA-Z0-9.\-_]/g, "_")
        .replace(/\s+/g, "_");

      const fileName = `${Date.now()}-${safeName}`;

      const { error: storageError } = await retryRequest(() => 
        supabase.storage
          .from("contracts")
          .upload(fileName, file.buffer, {
            contentType: file.mimetype,
          })
      );

      if (storageError) throw storageError;

      const fileUrl = `${process.env.SUPABASE_URL}/storage/v1/object/public/contracts/${fileName}`;
      const contractHash =
        "0x" + crypto.createHash("sha256").update(file.buffer).digest("hex");
      /* =====================================================
         🔍 CHECK RECEIVER EXISTS
      ===================================================== */

      const { data: receiverUser } = await supabase
        .from("users")
        .select("id")
        .eq("email", receiver_email)
        .maybeSingle();

      let receiver_id = receiverUser ? receiverUser.id : null;

      /* =====================================================
         🔥 REUPLOAD FLOW (UPDATE EXISTING)
      ===================================================== */

      let contract;

      if (contract_id) {
        console.log("🔄 Reupload detected");
        // 🧹 delete old file from storage
        const { data: oldContract } = await supabase
          .from("contracts")
          .select("file_url")
          .eq("contract_id", contract_id)
          .single();

        if (oldContract?.file_url) {
          const oldPath = oldContract.file_url.split("/contracts/")[1];

          if (oldPath) {
            await supabase.storage.from("contracts").remove([oldPath]);
          }
        }

        const { data, error: updateError } = await supabase
          .from("contracts")
          .update({
            file_url: fileUrl,
            contract_hash: contractHash,
            status: "SENT",
            is_active: true,
            blockchain_tx_hash: null,
            updated_at: new Date().toISOString(),
          })
          .eq("contract_id", contract_id)
          .eq("sender_id", sender_id) // 🔐 security check
          .select()
          .single();

        if (updateError) throw updateError;

        contract = data;
      } else {
        /* =====================================================
           🆕 NEW CONTRACT FLOW
        ===================================================== */

        const { data, error: dbError } = await supabase
          .from("contracts")
          .insert({
            sender_id,
            receiver_email,
            receiver_id,
            file_url: fileUrl,
            contract_hash: contractHash,
            status: "SENT",
            is_active: true,
          })
          .select()
          .single();

        if (dbError) throw dbError;

        contract = data;

        /* =====================================================
     📧 INVITE EMAIL (ONLY for NEW USER)
  ===================================================== */

        if (!receiver_id) {
          await supabase.from("email_invites").insert({
            email: receiver_email,
            contract_id: contract.contract_id,
          });

          await transporter.sendMail({
            from: `"Contract Platform" <${process.env.EMAIL_USER}>`,
            to: receiver_email,
            subject: "📄 Contract Shared With You",
            html: `
        <h2>You have received a contract</h2>
        <p>Someone has shared a contract with you.</p>
        <p>Please sign up to review and sign it.</p>
        <a href="http://localhost:3000/signup"
           style="padding:10px 16px;background:#8B5DFF;color:white;text-decoration:none;border-radius:8px;">
           Sign Up
        </a>
      `,
          });
        }
      }

      res.json(contract);
    } catch (err) {
      console.error("❌ Upload error:", err);
      res.status(500).json({ error: "Upload failed", details: err.message });
    }
  },
);

/* ================= STORE SIGNATURE ================= */

app.post("/store-signature", async (req, res) => {
  try {
    const {
      contract_id,
      user_id,
      wallet_address,
      signature,
      role, // "A" or "B"
    } = req.body;

    // 🔍 check if row exists
    const { data: existing } = await supabase
      .from("signatures")
      .select("*")
      .eq("contract_id", contract_id)
      .maybeSingle();

    // 🛡️ INTEGRITY CHECK: Verify hash before storing signature
    await retryRequest(() => verifyContractHash(contract_id));

    /* ================= RECEIVER SIGNS (B) ================= */

    if (role === "B") {
      if (existing) {
        await supabase
          .from("signatures")
          .update({
            signer_b_user_id: user_id,
            signer_b_wallet: wallet_address,
            signature_b: signature,
            signed_b_at: new Date().toISOString(),
          })
          .eq("contract_id", contract_id);
      } else {
        await supabase.from("signatures").insert({
          contract_id,
          signer_b_user_id: user_id,
          signer_b_wallet: wallet_address,
          signature_b: signature,
          signed_b_at: new Date().toISOString(),
        });
      }

      // update contract status
      await supabase
        .from("contracts")
        .update({ status: "AWAITING_SENDER_SIGNATURE" })
        .eq("contract_id", contract_id);
    }

    /* ================= SENDER SIGNS (A) ================= */

    if (role === "A") {
      if (!existing) {
        return res.status(400).json({
          error: "Receiver must sign first",
        });
      }

      await supabase
        .from("signatures")
        .update({
          signer_a_user_id: user_id,
          signer_a_wallet: wallet_address,
          signature_a: signature,
          signed_a_at: new Date().toISOString(),
        })
        .eq("contract_id", contract_id);

      await supabase
        .from("contracts")
        .update({ status: "SIGNED" })
        .eq("contract_id", contract_id);
    }

    res.json({ success: true });
  } catch (err) {
    console.error("❌ Signature store error:", err);
    res.status(500).json({ error: "Signature store failed", details: err.message });
  }
});

/* ================= BLOCKCHAIN STORE ================= */

app.post("/store-onchain", async (req, res) => {
  try {
    const { contractHash, sigA, sigB, walletA, walletB } = req.body;

    const provider = new ethers.JsonRpcProvider(process.env.RPC_URL);
    const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);

    const abi = require("./abi.json");

    const contract = new ethers.Contract(
      process.env.CONTRACT_ADDRESS,
      abi,
      wallet,
    );

    const tx = await contract.storeContractProof(
      contractHash,
      sigA,
      sigB,
      walletA,
      walletB,
    );

    await tx.wait();

    res.json({ txHash: tx.hash });
  } catch (err) {
    console.error("❌ Blockchain error:", err);
    res.status(500).json({ error: "Blockchain failed", details: err.message });
  }
});

/* ================= GET RECEIVED CONTRACTS ================= */

app.get("/contracts/received/:userId", async (req, res) => {
  try {
    const { userId } = req.params;

    const { data, error } = await supabase
      .from("contracts")
      .select("*")
      .eq("receiver_id", userId)
      .order("created_at", { ascending: false });

    if (error) throw error;

    res.json(data);
  } catch (err) {
    console.error("❌ Fetch received contracts error:", err);
    res.status(500).json({ error: "Failed to fetch contracts", details: err.message });
  }
});

/* ================= UPDATE CONTRACT STATUS ================= */

app.patch("/contracts/:id/status", async (req, res) => {
  try {
    const { id } = req.params;
    const { status } = req.body;

    // 🔥 decide update payload
    let updatePayload = { status };

    // ✅ CRITICAL BUSINESS RULE
    if (status === "REJECTED") {
      updatePayload.is_active = false;
    }

    const { data, error } = await supabase
      .from("contracts")
      .update(updatePayload)
      .eq("contract_id", id)
      .select()
      .single();

    if (error) throw error;

    res.json(data);
  } catch (err) {
    console.error("❌ Status update error:", err);
    res.status(500).json({ error: "Failed to update status", details: err.message });
  }
});

/* ================= FINALIZE CONTRACT ================= */

app.post("/contracts/:id/finalize", async (req, res) => {
  try {
    const { id } = req.params;

    // 1️⃣ get contract
    const { data: contract } = await supabase
      .from("contracts")
      .select("*")
      .eq("contract_id", id)
      .single();

    // 2️⃣ get signatures
    const { data: sig } = await supabase
      .from("signatures")
      .select("*")
      .eq("contract_id", id)
      .single();

    if (!sig?.signature_a || !sig?.signature_b) {
      return res.status(400).json({
        error: "Both signatures not present",
      });
    }

    // 3️⃣ recompute hash from file (and verify against DB)
    await verifyContractHash(id);

    const fileRes = await fetch(contract.file_url);
    const buffer = await fileRes.arrayBuffer();

    const crypto = require("crypto");
    const contractHash = crypto
      .createHash("sha256")
      .update(Buffer.from(buffer))
      .digest("hex");

    // 4️⃣ blockchain write
    const provider = new ethers.JsonRpcProvider(process.env.RPC_URL);
    const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
    const abi = require("./abi.json");

    const chainContract = new ethers.Contract(
      process.env.CONTRACT_ADDRESS,
      abi,
      wallet,
    );

    const tx = await chainContract.storeContractProof(
      "0x" + contractHash,
      sig.signature_a,
      sig.signature_b,
      sig.signer_a_wallet,
      sig.signer_b_wallet,
    );

    await tx.wait();

    // 5️⃣ update status
    await retryRequest(() => 
      supabase
        .from("contracts")
        .update({
          status: "ON_BLOCKCHAIN",
          blockchain_tx_hash: tx.hash,
          contract_hash: "0x" + contractHash,
        })
        .eq("contract_id", id)
    );

    // 🔥 SECURITY PROTOCOL: DELETE FILE FROM STORAGE AFTER ON-CHAIN FINALIZATION
    if (contract.file_url) {
      console.log(`🗑️ Deleting file from bucket for privacy after blockchain finalization: ${contract.file_url}`);
      try {
        const oldPath = contract.file_url.split("/contracts/")[1];
        if (oldPath) {
          const { error: deletionError } = await supabase.storage.from("contracts").remove([oldPath]);
          if (deletionError) console.error("Failed to delete from storage:", deletionError);
        }
      } catch (deletionErr) {
        console.error("Error during storage deletion:", deletionErr);
      }
    }

    res.json({ txHash: tx.hash });
  } catch (err) {
    console.error("❌ Finalize error:", err);
    res.status(500).json({ error: "Finalize failed", details: err.message });
  }
});

/* ================= GET SENT CONTRACTS ================= */

app.get("/contracts/sent/:userId", async (req, res) => {
  try {
    const { userId } = req.params;

    const { data, error } = await retryRequest(() => 
      supabase
        .from("contracts")
        .select("*")
        .eq("sender_id", userId)
        .order("created_at", { ascending: false })
    );

    if (error) throw error;

    res.json(data);
  } catch (err) {
    console.error("❌ Fetch sent contracts error:", err);
    res.status(500).json({ error: "Failed to fetch sent contracts", details: err.message });
  }
});

/* ================= GET ALL USER CONTRACTS ================= */

app.get("/contracts/all/:userId", async (req, res) => {
  try {
    const { userId } = req.params;

    const { data, error } = await retryRequest(() => 
      supabase
        .from("contracts")
        .select("*")
        .or(`sender_id.eq.${userId},receiver_id.eq.${userId}`)
        .order("created_at", { ascending: false })
    );

    if (error) throw error;

    res.json(data);
  } catch (err) {
    console.error("❌ Fetch all contracts error:", err);
    res.status(500).json({ error: "Failed to fetch contracts", details: err.message });
  }
});

/* ================= GET SINGLE CONTRACT ================= */

app.get("/contract/:id", async (req, res) => {
  try {
    const { id } = req.params;

    const { data: contract, error } = await retryRequest(() => 
      supabase
        .from("contracts")
        .select("*")
        .eq("contract_id", id)
        .single()
    );

    if (error) throw error;
    res.json(contract);
  } catch (err) {
    console.error("❌ Fetch contract error:", err);
    res.status(500).json({ error: "Failed to fetch contract", details: err.message });
  }
});

/* ================= ANALYZE CONTRACT ================= */

app.post("/contract/:id/analyze", async (req, res) => {
  try {
    const { id } = req.params;

    // 1. Fetch contract
    const { data: contract, error } = await retryRequest(() => 
      supabase
        .from("contracts")
        .select("file_url")
        .eq("contract_id", id)
        .single()
    );

    if (error || !contract || !contract.file_url) {
      throw new Error("Contract not found or no file attached");
    }

    // 2. Download file to buffer
    const fileRes = await fetch(contract.file_url);
    if (!fileRes.ok) throw new Error("Could not fetch file from storage");
    const buffer = Buffer.from(await fileRes.arrayBuffer());

    // Extract extension or assume pdf (or whatever was saved)
    let extension = ".pdf";
    if (contract.file_url.endsWith(".docx")) extension = ".docx";
    else if (contract.file_url.endsWith(".txt")) extension = ".txt";

    // 3. Send to Python gRPC server
    const analysisResponse = await modelClient.analyzeDocument(buffer, extension);

    // 4. Return structured response directly to frontend (no JSON.parse necessary)
    res.json(analysisResponse);
  } catch (err) {
    console.error("❌ Analyze error:", err);
    res.status(500).json({ error: "Analysis failed", details: err.message });
  }
});

/* ================= EPHEMERAL INTELLIGENCE ANALYSIS ================= */

app.post("/analyze-ephemeral", authenticateUser, upload.single("file"), async (req, res) => {
  try {
    console.log("📥 Ephemeral analysis request received (Not storing in DB)");
    const file = req.file;
    if (!file) {
      return res.status(400).json({ error: "Missing document file" });
    }

    let extension = "pdf";
    if (file.originalname.endsWith(".docx")) extension = "docx";
    else if (file.originalname.endsWith(".txt")) extension = "txt";

    const analysisResponse = await modelClient.analyzeDocument(file.buffer, extension);
    res.json(analysisResponse);
  } catch (err) {
    console.error("❌ Ephemeral analyze error:", err);
    res.status(500).json({ error: "Analysis failed", details: err.message });
  }
});

/* ================= LEGAL VERIFIER ================= */

app.post("/verify-contract", authenticateUser, upload.single("file"), async (req, res) => {
  try {
    console.log("🔍 Legal Verifier request received");
    const file = req.file;
    const { txHash } = req.body;

    if (!file || !txHash) {
      return res.status(400).json({ error: "Missing file or transaction hash" });
    }

    // Hash the uploaded file
    const contractHash = "0x" + crypto.createHash("sha256").update(file.buffer).digest("hex");

    // Look up contracts table by blockchain_tx_hash
    const { data: contract, error } = await supabase
      .from("contracts")
      .select("contract_hash, status")
      .eq("blockchain_tx_hash", txHash)
      .single();

    if (error || !contract) {
      return res.json({ 
        success: false, 
        message: "Transaction hash not found in registry or unlinked.",
        isTampered: false 
      });
    }

    if (contract.contract_hash === contractHash) {
      return res.json({ 
        success: true, 
        message: "Document matches the cryptographically signed ledger. Authentic.",
        isTampered: false 
      });
    } else {
      return res.json({ 
        success: false, 
        message: "CRITICAL: Hash mismatch! This document has been tampered with or modified.",
        isTampered: true 
      });
    }

  } catch (err) {
    console.error("❌ Verify error:", err);
    res.status(500).json({ error: "Verification failed", details: err.message });
  }
});

/* ================= LINK CONTRACTS AFTER SIGNUP ================= */

app.post("/link-receiver", authenticateUser, async (req, res) => {
  try {
    const userId = req.user.id;
    const email = req.user.email;

    // ✅ link contracts
    await retryRequest(() => 
      supabase
        .from("contracts")
        .update({ receiver_id: userId })
        .eq("receiver_email", email)
        .is("receiver_id", null)
    );

    // ✅ DELETE invite (CRITICAL FIX)
    await retryRequest(() => 
      supabase.from("email_invites").delete().eq("email", email)
    );

    res.json({ success: true });
  } catch (err) {
    console.error("❌ Link receiver error:", err);
    res.status(500).json({ error: "Link failed", details: err.message });
  }
});

/* ================= START SERVER ================= */

const PORT = 5001;

app.listen(PORT, "0.0.0.0", () => {
  console.log(`🚀 Server running on http://127.0.0.1:${PORT}`);
});
