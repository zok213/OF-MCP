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
  if (req.method === "OPTIONS") {
    return new Response("ok", {
      headers: { ...corsHeaders, ...securityHeaders },
    });
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_ANON_KEY") ?? ""
    );

    if (req.method === "POST") {
      // Create new response
      const { user_id, prompt, response_text, model_id, metadata } =
        await req.json();

      if (!user_id || !prompt || !response_text) {
        return new Response(
          JSON.stringify({
            success: false,
            error: "Missing required fields: user_id, prompt, response_text",
          }),
          {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          }
        );
      }

      const { data, error } = await supabaseClient
        .from("responses")
        .insert({
          user_id,
          prompt,
          response_text,
          model_id: model_id || "default",
          metadata: metadata || {},
          created_at: new Date().toISOString(),
        })
        .select()
        .single();

      if (error) {
        return new Response(
          JSON.stringify({ success: false, error: error.message }),
          {
            status: 500,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          }
        );
      }

      return new Response(JSON.stringify({ success: true, data }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    } else if (req.method === "GET") {
      // Get responses with optional filtering
      const url = new URL(req.url);
      const user_id = url.searchParams.get("user_id");
      const model_id = url.searchParams.get("model_id");
      const limit = parseInt(url.searchParams.get("limit") || "50");
      const offset = parseInt(url.searchParams.get("offset") || "0");

      let query = supabaseClient
        .from("responses")
        .select("*")
        .order("created_at", { ascending: false })
        .range(offset, offset + limit - 1);

      if (user_id) {
        query = query.eq("user_id", user_id);
      }
      if (model_id) {
        query = query.eq("model_id", model_id);
      }

      const { data, error } = await query;

      if (error) {
        return new Response(
          JSON.stringify({ success: false, error: error.message }),
          {
            status: 500,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          }
        );
      }

      return new Response(
        JSON.stringify({ success: true, data, count: data.length }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    } else if (req.method === "PUT") {
      // Update response
      const url = new URL(req.url);
      const responseId = url.searchParams.get("id");
      const updates = await req.json();

      if (!responseId) {
        return new Response(
          JSON.stringify({ success: false, error: "Response ID required" }),
          {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          }
        );
      }

      const { data, error } = await supabaseClient
        .from("responses")
        .update(updates)
        .eq("id", responseId)
        .select()
        .single();

      if (error) {
        return new Response(
          JSON.stringify({ success: false, error: error.message }),
          {
            status: 500,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          }
        );
      }

      return new Response(JSON.stringify({ success: true, data }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }
  } catch (error) {
    console.error("RFT Responses error:", error);
    return new Response(
      JSON.stringify({
        success: false,
        error: `Processing failed: ${error.message}`,
      }),
      {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  }
});
