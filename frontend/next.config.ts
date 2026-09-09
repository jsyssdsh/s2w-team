import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  images: {
    unoptimized: true,
  },
  // Without this, export writes "farm.html" as a *sibling* of the "farm/"
  // directory Next also creates (for the route's RSC payload files), and
  // FastAPI's StaticFiles(html=True) mount only resolves "index.html"
  // inside a directory -- it never tries "<path>.html". A direct request
  // for /farm then matches the (index-less) directory and 404s, even
  // though client-side <Link> navigation works. trailingSlash makes export
  // write "farm/index.html" instead, which that directory-index fallback
  // already serves correctly with no backend change.
  trailingSlash: true,
};

export default nextConfig;
