"use client";

import { useChat } from "ai/react";
import { Send, Trash2, Bot, User, Loader2 } from "lucide-react";
import { useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";

export default function Chat() {
  const { messages, input, handleInputChange, handleSubmit, isLoading, setMessages } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 清空对话
  const handleClear = () => {
    setMessages([]);
  };

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <Bot size={48} className="mb-4 opacity-50" />
            <p className="text-lg">开始一段对话吧</p>
            <p className="text-sm mt-2">输入你的问题，AI 会为你解答</p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 ${
              message.role === "user" ? "flex-row-reverse" : "flex-row"
            }`}
          >
            {/* 头像 */}
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                message.role === "user"
                  ? "bg-blue-500 text-white"
                  : "bg-purple-100 text-purple-600"
              }`}
            >
              {message.role === "user" ? <User size={16} /> : <Bot size={16} />}
            </div>

            {/* 消息内容 */}
            <div
              className={`max-w-[80%] px-4 py-2 rounded-2xl ${
                message.role === "user"
                  ? "bg-blue-500 text-white rounded-tr-sm"
                  : "bg-gray-100 text-gray-800 rounded-tl-sm"
              }`}
            >
              <ReactMarkdown className="prose prose-sm max-w-none">
                {message.content}
              </ReactMarkdown>
            </div>
          </div>
        ))}

        {/* 加载中提示 */}
        {isLoading && messages[messages.length - 1]?.role !== "assistant" && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center flex-shrink-0">
              <Bot size={16} />
            </div>
            <div className="bg-gray-100 px-4 py-3 rounded-2xl rounded-tl-sm">
              <Loader2 size={18} className="animate-spin text-gray-400" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <div className="border-t border-gray-100 p-4 bg-white">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <button
            type="button"
            onClick={handleClear}
            className="px-3 py-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            title="清空对话"
          >
            <Trash2 size={20} />
          </button>

          <input
            value={input}
            onChange={handleInputChange}
            placeholder="输入消息..."
            className="flex-1 px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />

          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-4 py-2 bg-blue-500 text-white rounded-xl hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
          </button>
        </form>
      </div>
    </div>
  );
}
