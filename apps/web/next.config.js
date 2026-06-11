const path = require("path");
const fs = require("fs");

const workspaceRoot = path.resolve(__dirname, "../..");
const outputFileTracingRoot = fs.existsSync(path.join(workspaceRoot, "apps/web/package.json"))
  ? workspaceRoot
  : path.resolve(__dirname);

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  outputFileTracingRoot,
  reactStrictMode: true
};

module.exports = nextConfig;
