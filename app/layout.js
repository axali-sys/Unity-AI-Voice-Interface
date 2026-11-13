import { getPublicAppUrl } from "../lib/public-app-url.mjs";

const appOrigin = getPublicAppUrl();

export const metadata = {
  metadataBase: new URL(appOrigin),
  title: "Axaliai Assistant",
  description: "Lovable-style AI assistant interface for the Axaliai XParallel project",
  alternates: {
    canonical: "/",
  },
  openGraph: {
    title: "Axaliai Assistant",
    description: "AI assistant interface for the Axaliai XParallel project",
    url: "/",
    siteName: "Axaliai Assistant",
    type: "website",
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
