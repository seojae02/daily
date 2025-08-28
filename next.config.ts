const path = require("path")

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  trailingSlash: true,
  images: {
    unoptimized: true,
  },

  compiler: {
    styledComponents: true,
  },

  webpack: (config: any) => {
    config.resolve.alias["@/"] = path.resolve(__dirname, "src")
    config.resolve.alias["@/components"] = path.resolve(
      __dirname,
      "src/components"
    )
    return config
  },
}

module.exports = nextConfig
