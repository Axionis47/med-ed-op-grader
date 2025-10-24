import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Instructor Portal - Medical Education Grading System",
  description: "Manage rubrics and review student presentations",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-gray-50 min-h-screen">
        <nav className="bg-primary-600 text-white shadow-lg">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16 items-center">
              <div className="flex items-center">
                <h1 className="text-2xl font-bold">Instructor Portal</h1>
              </div>
              <div className="flex space-x-4">
                <a href="/" className="hover:bg-primary-700 px-3 py-2 rounded-md">Dashboard</a>
                <a href="/rubrics" className="hover:bg-primary-700 px-3 py-2 rounded-md">Rubrics</a>
                <a href="/submissions" className="hover:bg-primary-700 px-3 py-2 rounded-md">Submissions</a>
                <a href="/results" className="hover:bg-primary-700 px-3 py-2 rounded-md">Results</a>
              </div>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}

