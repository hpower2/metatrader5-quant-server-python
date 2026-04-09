import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "standalone",
  typedRoutes: true,
  eslint: {
    dirs: ["app", "components", "features", "hooks", "lib", "schemas", "stores", "tests", "types"]
  }
};

export default nextConfig;
