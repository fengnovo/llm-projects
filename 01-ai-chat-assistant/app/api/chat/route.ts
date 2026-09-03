import OpenAI from "openai";
import { OpenAIStream, StreamingTextResponse } from "ai";

// 创建 OpenAI 客户端（兼容任何 OpenAI 格式的 API，包括 vLLM、one-api 等）
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
  baseURL: process.env.OPENAI_BASE_URL,
});

export const runtime = "edge";

export async function POST(req: Request) {
  try {
    const { messages } = await req.json();

    // 调用 OpenAI 兼容接口，开启流式响应
    const response = await openai.chat.completions.create({
      model: process.env.OPENAI_MODEL || "gpt-3.5-turbo",
      stream: true,
      messages,
      temperature: 0.7,
    });

    // 使用 Vercel AI SDK 将响应转换为流式文本
    const stream = OpenAIStream(response);

    return new StreamingTextResponse(stream);
  } catch (error) {
    console.error("Chat API Error:", error);
    return new Response(
      JSON.stringify({ error: "聊天服务暂时不可用，请稍后重试" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
}
