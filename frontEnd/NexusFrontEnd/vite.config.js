import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import envCompatible from "vite-plugin-env-compatible";


// https://vitejs.dev/config/
export default defineConfig({
  envPrefix: "REACT_APP_",
  plugins: [react(), envCompatible()],
  server: {
    host: '0.0.0.0', // Allow access from network devices
    port: 5173, // Default port, you can change it if needed
  },
});
