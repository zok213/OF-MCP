// scripts/upload_to_edge.js
import fs from "fs";
import fetch from "node-fetch";

async function uploadImage(filePath) {
  const fileName = filePath.split("/").pop();
  const fileContent = fs.readFileSync(filePath, { encoding: "base64" });

  // Upload to Wasabi through Edge Function
  const res = await fetch(
    "https://xewniavplpocctogfgnc.supabase.co/functions/v1/upload",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        // Add Authorization header if you want to track user_id
        // "Authorization": `Bearer ${userToken}`
      },
      body: JSON.stringify({
        fileName,
        fileContent,
      }),
    }
  );

  if (!res.ok) {
    throw new Error(`❌ Upload failed: ${res.status} ${res.statusText}`);
  }

  const data = await res.json();

  if (data.success) {
    console.log(`✅ Uploaded ${fileName} → ${data.url}`);
    if (data.dbStatus === "success") {
      console.log("✅ Image metadata saved to database");
    } else {
      console.warn("⚠️ Image uploaded but metadata not saved to database");
    }
    return data.url;
  } else {
    throw new Error("Upload failed: " + (data.error || "Unknown error"));
  }
}

// Example usage
(async () => {
  try {
    const testFile = "./example.jpg"; // image after crawling
    await uploadImage(testFile);
  } catch (err) {
    console.error("Error:", err);
  }
})();
