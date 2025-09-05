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
      // Create new checkpoint
      const { version, storage_key, url, epoch, avg_reward, is_active } =
        await req.json();

      if (!version || !storage_key) {
        return new Response(
          JSON.stringify({
            success: false,
            error: "Missing required fields: version, storage_key",
          }),
          {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          }
        );
      }

      // If this is being marked as active, deactivate all other checkpoints
      if (is_active) {
        await supabaseClient
          .from("checkpoints")
          .update({ is_active: false })
          .neq("version", version);
      }

      const { data, error } = await supabaseClient
        .from("checkpoints")
        .insert({
          version,
          storage_key,
          url: url || null,
          epoch: epoch || 0,
          avg_reward: avg_reward || 0,
          is_active: is_active || false,
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
      // Get checkpoints with optional filtering
      const url = new URL(req.url);
      const version = url.searchParams.get("version");
      const active_only = url.searchParams.get("active_only") === "true";
      const limit = parseInt(url.searchParams.get("limit") || "50");
      const offset = parseInt(url.searchParams.get("offset") || "0");

      let query = supabaseClient
        .from("checkpoints")
        .select("*")
        .order("created_at", { ascending: false })
        .range(offset, offset + limit - 1);

      if (version) {
        query = query.eq("version", version);
      }
      if (active_only) {
        query = query.eq("is_active", true);
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

      // Get statistics
      const stats = {
        total_checkpoints: data.length,
        active_checkpoints: data.filter((c) => c.is_active).length,
        latest_epoch:
          data.length > 0 ? Math.max(...data.map((c) => c.epoch || 0)) : 0,
        best_avg_reward:
          data.length > 0 ? Math.max(...data.map((c) => c.avg_reward || 0)) : 0,
        versions: [...new Set(data.map((c) => c.version))],
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
      // Update checkpoint (typically to activate/deactivate)
      const url = new URL(req.url);
      const checkpointId = url.searchParams.get("id");
      const updates = await req.json();

      if (!checkpointId) {
        return new Response(
          JSON.stringify({ success: false, error: "Checkpoint ID required" }),
          {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          }
        );
      }

      // If setting as active, deactivate all others
      if (updates.is_active === true) {
        await supabaseClient
          .from("checkpoints")
          .update({ is_active: false })
          .neq("id", checkpointId);
      }

      const { data, error } = await supabaseClient
        .from("checkpoints")
        .update(updates)
        .eq("id", checkpointId)
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
      // Delete checkpoint (admin operation)
      const url = new URL(req.url);
      const checkpointId = url.searchParams.get("id");

      if (!checkpointId) {
        return new Response(
          JSON.stringify({ success: false, error: "Checkpoint ID required" }),
          {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          }
        );
      }

      // Don't allow deletion of active checkpoint
      const { data: checkpoint } = await supabaseClient
        .from("checkpoints")
        .select("is_active")
        .eq("id", checkpointId)
        .single();

      if (checkpoint?.is_active) {
        return new Response(
          JSON.stringify({
            success: false,
            error: "Cannot delete active checkpoint. Deactivate first.",
          }),
          {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          }
        );
      }

      const { error } = await supabaseClient
        .from("checkpoints")
        .delete()
        .eq("id", checkpointId);

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
          message: "Checkpoint deleted successfully",
        }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }
  } catch (error) {
    console.error("RFT Checkpoints error:", error);
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
