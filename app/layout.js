export const metadata = {
  title: "Axaliai Assistant",
  description: "Lovable-style AI assistant interface for the Axaliai XParallel project",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
