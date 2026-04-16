const { createClient } = require("@supabase/supabase-js");
require("dotenv").config();

async function testConnection() {
  console.log("🔍 Starting connectivity test...");
  console.log("URL:", process.env.SUPABASE_URL);

  const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE
  );

  console.log("⏳ Attempting to fetch a single row from 'contracts'...");
  
  const start = Date.now();
  try {
    const { data, error } = await supabase
      .from("contracts")
      .select("count")
      .limit(1);

    const duration = Date.now() - start;

    if (error) {
      console.error("❌ Supabase returned an error:");
      console.error(JSON.stringify(error, null, 2));
    } else {
      console.log(`✅ Connection successful! (Took ${duration}ms)`);
      console.log("Data sample:", data);
    }
  } catch (err) {
    const duration = Date.now() - start;
    console.error(`💥 CRITICAL FETCH ERROR after ${duration}ms:`);
    console.error(err);
    
    if (err.message.includes("fetch failed")) {
      console.log("\n💡 DIAGNOSIS: This is a network-level timeout.");
      console.log("Please check if:");
      console.log("1. Your internet is working.");
      console.log("2. You are on a VPN or network that blocks port 443 for Node.js.");
      console.log("3. The Supabase URL in your .env is correct and reachable via browser.");
    }
  }
}

testConnection();