// scripts/upload_to_edge.js
import fs from "fs";
import path from "path";
import fetch from "node-fetch";
import FormData from "form-data";

async function uploadImage(filePath) {
  // Sanitize and validate the file path
  const absolutePath = path.resolve(filePath);
  const workingDir = process.cwd();

  // Ensure the file path is within the working directory to prevent path traversal
  if (!absolutePath.startsWith(workingDir)) {
    throw new Error(
      "Security Error: Attempted path traversal - file must be within working directory"
    );
  }

  // Validate file exists
  if (!fs.existsSync(absolutePath)) {
    throw new Error(`File not found: ${filePath}`);
  }

  // Extract filename safely using path module
  const fileName = path.basename(absolutePath);

  // Ensure it's an image file
  const allowedExtensions = [".jpg", ".jpeg", ".png", ".webp", ".gif"];
  const fileExtension = path.extname(fileName).toLowerCase();
  if (!allowedExtensions.includes(fileExtension)) {
    throw new Error(
      `Invalid file type. Allowed types: ${allowedExtensions.join(", ")}`
    );
  }

  // Stream the file to the edge upload function using multipart/form-data
  // This avoids loading the whole file into memory as a base64 string.
  const form = new FormData();
  form.append("file", fs.createReadStream(absolutePath), {
    filename: fileName,
    contentType: mimeTypeFromExtension(fileExtension),
  });
  // include filename explicitly as metadata as well
  form.append("fileName", fileName);

  // Upload to Wasabi through Edge Function
  const res = await fetch(
    "https://xewniavplpocctogfgnc.supabase.co/functions/v1/upload",
    {
      method: "POST",
      headers: form.getHeaders(),
      body: form,
    }
  );

  // helper to map extensions to mime types
  function mimeTypeFromExtension(ext) {
    switch (ext) {
      case ".jpg":
      case ".jpeg":
        return "image/jpeg";
      case ".png":
        return "image/png";
      case ".webp":
        return "image/webp";
      case ".gif":
        return "image/gif";
      default:
        return "application/octet-stream";
    }
  }

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
