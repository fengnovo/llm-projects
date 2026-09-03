import Chat from "@/components/chat";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4">
      <div className="w-full max-w-3xl h-[85vh] flex flex-col bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100">
        <header className="px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-blue-50 to-purple-50">
          <h1 className="text-xl font-bold text-gray-800">AI 聊天助手</h1>
          <p className="text-sm text-gray-500 mt-1">基于 Next.js + Vercel AI SDK 构建</p>
        </header>
        <Chat />
      </div>
    </main>
  );
}
