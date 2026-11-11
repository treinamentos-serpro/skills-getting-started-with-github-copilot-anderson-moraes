import { defineConfig } from "vite";

export default defineConfig({
  root: "src/static",
  base: "/static/",
  build: {
    outDir: "../../dist",
    emptyOutDir: true,
  },
});