import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxy /api to the FastAPI backend so the browser makes same-origin calls
// in dev and we avoid CORS juggling.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // listen on all interfaces so the lab proxy can reach it
    port: 5173,
    // The lab serves this app via a remote hostname; allow it (and any
    // *.labs.decoded.com subdomain) past Vite's host check.
    allowedHosts: [".labs.decoded.com"],
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
