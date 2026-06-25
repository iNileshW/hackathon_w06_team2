import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxy /api to the FastAPI backend so the browser makes same-origin calls
// in dev and we avoid CORS juggling.
export default defineConfig({
  // Relative asset URLs so the app works under any proxy path prefix
  // (the lab serves it behind a remote host, not necessarily at root).
  base: "./",
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
  // `vite preview` serves the production build (no dev module/HMR paths that
  // a remote proxy 404s on). Same host allowance + API proxy as dev.
  preview: {
    host: true,
    port: 5173,
    allowedHosts: [".labs.decoded.com"],
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
