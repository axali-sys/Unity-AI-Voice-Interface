import "./globals.css";

export const metadata = {
  title: "Axaliai — General AI Infrastructure",
  description: "An evolving AI infrastructure ecosystem for connected intelligence, orchestration and interoperability.",
  metadataBase: new URL("https://axaliai.com"),
  openGraph: { title: "Axaliai — General AI Infrastructure", description: "Build beyond one intelligence.", type: "website" },
};

export default function RootLayout({ children }) {
  return <html lang="en"><body>{children}</body></html>;
}
