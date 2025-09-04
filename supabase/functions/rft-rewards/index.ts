import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_ANON_KEY") ?? ""
    );

    if (req.method === "POST") {
      // Create new reward record
      const { response_id, score, detail, created_at } = await req.json();

      if (!response_id || typeof score !== "number") {
        return new Response(
          JSON.stringify({
            success: false,
            error: "Missing required fields: response_id, score (number)",
          }),
          {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          }
        );
      }

      // Validate score range (typically -1 to 1 for RFT)
      if (score < -1 || score > 1) {
        return new Response(
          JSON.stringify({
            success: false,
            error: "Score must be between -1 and 1",
          }),
          {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          }
        );
      }

      const { data, error } = await supabaseClient
        .from("rewards")
        .insert({
          response_id,
          score,
          detail: detail || null,
          created_at: created_at || new Date().toISOString(),
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
      // Get rewards with optional filtering
      const url = new URL(req.url);
      const response_id = url.searchParams.get("response_id");
      const min_score = url.searchParams.get("min_score");
      const max_score = url.searchParams.get("max_score");
      const limit = parseInt(url.searchParams.get("limit") || "100");
      const offset = parseInt(url.searchParams.get("offset") || "0");

      let query = supabaseClient
        .from("rewards")
        .select(
          `
          *,
          responses:response_id (
            id,
            user_id,
            prompt,
            response_text,
            model_id,
            created_at
          )
        `
        )
        .order("created_at", { ascending: false })
        .range(offset, offset + limit - 1);

      if (response_id) {
        query = query.eq("response_id", response_id);
      }
      if (min_score !== null) {
        query = query.gte("score", parseFloat(min_score));
      }
      if (max_score !== null) {
        query = query.lte("score", parseFloat(max_score));
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

      // Calculate statistics
      const stats = {
        total_rewards: data.length,
        avg_score:
          data.length > 0
            ? data.reduce((sum, r) => sum + r.score, 0) / data.length
            : 0,
        max_score: data.length > 0 ? Math.max(...data.map((r) => r.score)) : 0,
        min_score: data.length > 0 ? Math.min(...data.map((r) => r.score)) : 0,
        score_distribution: {
          positive: data.filter((r) => r.score > 0).length,
          negative: data.filter((r) => r.score < 0).length,
          neutral: data.filter((r) => r.score === 0).length,
        },
      };

      return new Response(
        JSON.stringify({
          success: true,
          data,
          count: data.length,
          stats,
        }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    } else if (req.method === "PUT") {
      // Update reward score
      const url = new URL(req.url);
      const rewardId = url.searchParams.get("id");
      const { score, detail } = await req.json();

      if (!rewardId) {
        return new Response(
          JSON.stringify({ success: false, error: "Reward ID required" }),
          {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          }
        );
      }

      const updates = {};
      if (typeof score === "number") {
        if (score < -1 || score > 1) {
          return new Response(
            JSON.stringify({
              success: false,
              error: "Score must be between -1 and 1",
            }),
            {
              status: 400,
              headers: { ...corsHeaders, "Content-Type": "application/json" },
            }
          );
        }
        updates.score = score;
      }
      if (detail !== undefined) {
        updates.detail = detail;
      }

      const { data, error } = await supabaseClient
        .from("rewards")
        .update(updates)
        .eq("id", rewardId)
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
    } else if (req.method === "DELETE") {
      // Delete reward (admin operation)
      const url = new URL(req.url);
      const rewardId = url.searchParams.get("id");

      if (!rewardId) {
        return new Response(
          JSON.stringify({ success: false, error: "Reward ID required" }),
          {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          }
        );
      }

      const { error } = await supabaseClient
        .from("rewards")
        .delete()
        .eq("id", rewardId);

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
        JSON.stringify({
          success: true,
          message: "Reward deleted successfully",
        }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }
  } catch (error) {
    console.error("RFT Rewards error:", error);
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
