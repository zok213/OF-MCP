import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
};

const securityHeaders = {
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "X-XSS-Protection": "1; mode=block",
  "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
  "Content-Security-Policy": "default-src 'self'",
};

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === "OPTIONS") {
    return new Response("ok", {
      headers: { ...corsHeaders, ...securityHeaders },
    });
  }

  try {
    // Initialize Supabase client
    const supabaseClient = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_ANON_KEY") ?? ""
    );

    const formData = await req.formData();
    const file = formData.get("file") as File;
    const fileName = formData.get("fileName") as string;
    const userId = (formData.get("user_id") as string) || "anonymous";
    const category = (formData.get("category") as string) || "general";
    const metadata = formData.get("metadata") as string;

    if (!file) {
      return new Response(
        JSON.stringify({ success: false, error: "No file provided" }),
        {
          status: 400,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // Validate file type
    const allowedTypes = [
      "image/jpeg",
      "image/jpg",
      "image/png",
      "image/webp",
      "image/gif",
    ];
    if (!allowedTypes.includes(file.type)) {
      return new Response(
        JSON.stringify({
          success: false,
          error: `Invalid file type. Allowed types: ${allowedTypes.join(", ")}`,
        }),
        {
          status: 400,
          headers: {
            ...corsHeaders,
            ...securityHeaders,
            "Content-Type": "application/json",
          },
        }
      );
    }

    // Validate file size (10MB limit)
    const maxFileSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxFileSize) {
      return new Response(
        JSON.stringify({
          success: false,
          error: `File too large. Maximum size: ${maxFileSize / 1024 / 1024}MB`,
        }),
        {
          status: 400,
          headers: {
            ...corsHeaders,
            ...securityHeaders,
            "Content-Type": "application/json",
          },
        }
      );
    }

    // Validate filename for security
    if (
      fileName &&
      (fileName.includes("..") ||
        fileName.includes("/") ||
        fileName.includes("\\"))
    ) {
      return new Response(
        JSON.stringify({
          success: false,
          error: "Invalid filename. No path traversal allowed.",
        }),
        {
          status: 400,
          headers: {
            ...corsHeaders,
            ...securityHeaders,
            "Content-Type": "application/json",
          },
        }
      );
    }

    // Generate unique filename
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    const fileExtension = file.name.split(".").pop();
    const uniqueFileName = `${category}/${timestamp}-${fileName || file.name}`;

    try {
      // Upload to Supabase Storage (Wasabi compatible)
      const { data: uploadData, error: uploadError } =
        await supabaseClient.storage
          .from("scraped-images")
          .upload(uniqueFileName, file, {
            contentType: file.type,
            upsert: false,
          });

      if (uploadError) {
        console.error("Upload error:", uploadError);
        return new Response(
          JSON.stringify({
            success: false,
            error: `Upload failed: ${uploadError.message}`,
          }),
          {
            status: 500,
            headers: {
              ...corsHeaders,
              ...securityHeaders,
              "Content-Type": "application/json",
            },
          }
        );
      }

      // Get public URL
      const { data: urlData } = supabaseClient.storage
        .from("scraped-images")
        .getPublicUrl(uniqueFileName);

      // Save metadata to database
      let dbStatus = "pending";
      let imageId = null;

      try {
        const imageMetadata = {
          user_id: userId,
          bucket: "scraped-images",
          object_path: uniqueFileName,
          filename: fileName || file.name,
          content_type: file.type,
          size_bytes: file.size,
          uploaded_at: new Date().toISOString(),
          ...(metadata ? JSON.parse(metadata) : {}),
        };

        const { data: dbData, error: dbError } = await supabaseClient
          .from("images")
          .insert(imageMetadata)
          .select("id")
          .single();

        if (dbError) {
          console.error("Database error:", dbError);
          dbStatus = "failed";
        } else {
          dbStatus = "success";
          imageId = dbData.id;
        }
      } catch (dbErr) {
        console.error("Database insertion error:", dbErr);
        dbStatus = "failed";
      }

      return new Response(
        JSON.stringify({
          success: true,
          url: urlData.publicUrl,
          path: uniqueFileName,
          imageId: imageId,
          dbStatus: dbStatus,
          size: file.size,
          contentType: file.type,
        }),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    } catch (error) {
      console.error("Storage operation failed:", error);
      return new Response(
        JSON.stringify({
          success: false,
          error: `Storage operation failed: ${error.message}`,
        }),
        {
          status: 500,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }
  } catch (error) {
    console.error("Request processing error:", error);
    return new Response(
      JSON.stringify({
        success: false,
        error: `Request processing failed: ${error.message}`,
      }),
      {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  }
});
