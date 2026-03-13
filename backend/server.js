require("dotenv").config();
const jwt = require("jsonwebtoken");
const express = require("express");
const multer = require("multer");
const cors = require("cors");
const crypto = require("crypto");
const { createClient } = require("@supabase/supabase-js");
const { ethers } = require("ethers");

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

      const { error: storageError } = await supabase.storage
        .from("contracts")
        .upload(fileName, file.buffer, {
          contentType: file.mimetype,
        });

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
      res.status(500).send("Upload failed");
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
        .update({ status: "PENDING_SIGNATURE_A" })
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
    res.status(500).send("Signature store failed");
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
    res.status(500).send("Blockchain failed");
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
    res.status(500).send("Failed to fetch contracts");
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
    res.status(500).send("Failed to update status");
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

    // 3️⃣ recompute hash from file
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
    await supabase
      .from("contracts")
      .update({
        status: "ON_BLOCKCHAIN",
        blockchain_tx_hash: tx.hash,
        contract_hash: "0x" + contractHash,
      })
      .eq("contract_id", id);

    res.json({ txHash: tx.hash });
  } catch (err) {
    console.error("❌ Finalize error:", err);
    res.status(500).send("Finalize failed");
  }
});

/* ================= GET SENT CONTRACTS ================= */

app.get("/contracts/sent/:userId", async (req, res) => {
  try {
    const { userId } = req.params;

    const { data, error } = await supabase
      .from("contracts")
      .select("*")
      .eq("sender_id", userId)
      .order("created_at", { ascending: false });

    if (error) throw error;

    res.json(data);
  } catch (err) {
    console.error("❌ Fetch sent contracts error:", err);
    res.status(500).send("Failed to fetch sent contracts");
  }
});

/* ================= GET ALL USER CONTRACTS ================= */

app.get("/contracts/all/:userId", async (req, res) => {
  try {
    const { userId } = req.params;

    const { data, error } = await supabase
      .from("contracts")
      .select("*")
      .or(`sender_id.eq.${userId},receiver_id.eq.${userId}`)
      .order("created_at", { ascending: false });

    if (error) throw error;

    res.json(data);
  } catch (err) {
    console.error("❌ Fetch all contracts error:", err);
    res.status(500).send("Failed to fetch contracts");
  }
});

/* ================= LINK CONTRACTS AFTER SIGNUP ================= */

app.post("/link-receiver", authenticateUser, async (req, res) => {
  try {
    const userId = req.user.id;
    const email = req.user.email;

    // ✅ link contracts
    await supabase
      .from("contracts")
      .update({ receiver_id: userId })
      .eq("receiver_email", email)
      .is("receiver_id", null);

    // ✅ DELETE invite (CRITICAL FIX)
    await supabase.from("email_invites").delete().eq("email", email);

    res.json({ success: true });
  } catch (err) {
    console.error("❌ Link receiver error:", err);
    res.status(500).send("Link failed");
  }
});

/* ================= START SERVER ================= */

const PORT = 5001;

app.listen(PORT, "0.0.0.0", () => {
  console.log(`🚀 Server running on http://127.0.0.1:${PORT}`);
});
