require("dotenv").config();
const express = require("express");
const { createClient } = require("@supabase/supabase-js");

const app = express();

/* ================= SUPABASE CLIENT ================= */

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE
);

/* ================= HEALTH CHECK ================= */

app.get("/test-supabase", async (req, res) => {
  try {
    console.log("🔍 Testing Supabase connection...");

    // simple query (change table if needed)
    const { data, error } = await supabase
      .from("users")
      .select("*")
      .limit(1);

    if (error) {
      console.error("❌ Supabase error:", error);
      return res.status(500).json({
        success: false,
        error: error.message,
      });
    }

    console.log("✅ Supabase connected!");

    res.json({
      success: true,
      message: "Supabase connected successfully",
      sample: data,
    });
  } catch (err) {
    console.error("❌ Server error:", err);
    res.status(500).json({
      success: false,
      error: err.message,
    });
  }
});

/* ================= START SERVER ================= */

const PORT = 5050;

app.listen(PORT, () => {
  console.log(`🚀 Test server running on http://localhost:${PORT}`);
});