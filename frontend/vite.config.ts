import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  base: "/ui-react/",
  root: "frontend",
  plugins: [react(), tailwindcss()],
  build: {
    outDir: "../src/nfi_engine/ui/react_dist",
    emptyOutDir: true,
    manifest: true,
    sourcemap: false,
    target: "es2022",
    cssCodeSplit: true,
    rollupOptions: {
      input: "index.html",
    },
  },
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: false,
    proxy: {
      "/api": "http://127.0.0.1:18180",
      "/settings": "http://127.0.0.1:18180",
      "/logs": "http://127.0.0.1:18180",
    },
  },
});
