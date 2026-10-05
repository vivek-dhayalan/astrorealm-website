// Forwards every request to the AstroRealm Python container. The container sleeps when idle
// (sleepAfter) and wakes on the next request, so you pay only while it runs.
import { Container, getContainer } from "@cloudflare/containers";

// Settings passed from wrangler.jsonc "vars" and secrets into the container's environment.
const PASS_THROUGH = [
  "MATCHAPI_ENV", "SITE_NAME", "SITE_BASE_URL", "SOURCE_URL", "CONTACT_EMAIL",
  "TURNSTILE_SITE_KEY", "TURNSTILE_SECRET_KEY",
  "ADSENSE_CLIENT", "ADSENSE_SLOT_TOP", "ADSENSE_SLOT_SIDE", "ADSENSE_SLOT_BOTTOM",
  "GA_MEASUREMENT_ID", "MAP_STYLE_URL", "RATE_LIMIT_PER_MINUTE",
];

export class AstroRealmApp extends Container {
  defaultPort = 8000;   // uvicorn port in the Dockerfile
  sleepAfter = "10m";   // stop after 10 minutes without requests

  constructor(ctx, env) {
    super(ctx, env);
    const vars = {};
    for (const key of PASS_THROUGH) {
      if (env[key] !== undefined && env[key] !== "") vars[key] = String(env[key]);
    }
    this.envVars = vars;
  }
}

export default {
  async fetch(request, env) {
    // One named instance keeps the in-app rate limiter consistent. Raise max_instances and use
    // getRandom() from @cloudflare/containers if traffic ever needs more than one.
    const app = getContainer(env.APP, "main");
    return app.fetch(request);
  },
};
