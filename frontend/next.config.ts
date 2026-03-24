import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* reactCompiler disabled — causes Turbopack panic: "Next.js package not found" in get_next_server_import_map */
  // @ts-ignore
  allowedDevOrigins: [
    "localhost",
    "localhost:3000",
    "127.0.0.1",
    "127.0.0.1:3000",
    "192.168.100.22", 
    "192.168.100.22:3000"
  ]
};

export default nextConfig;
