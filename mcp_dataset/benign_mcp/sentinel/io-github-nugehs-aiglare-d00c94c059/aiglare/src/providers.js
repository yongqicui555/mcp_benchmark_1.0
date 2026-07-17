// Provider registry — the data layer that makes this tool provider-agnostic.
// Adding a provider is a one-line PR. Each entry matches by package import
// and/or by network host (for raw fetch/axios calls to an inference endpoint).

export const PROVIDERS = [
  { id: 'openai', label: 'OpenAI', packages: ['openai'], hosts: ['api.openai.com'] },
  { id: 'deepseek', label: 'DeepSeek', packages: ['deepseek'], hosts: ['api.deepseek.com'] },
  { id: 'anthropic', label: 'Anthropic', packages: ['@anthropic-ai/sdk'], hosts: ['api.anthropic.com'] },
  { id: 'google-genai', label: 'Google Generative AI', packages: ['@google/generative-ai', '@google/genai', '@google-cloud/vertexai'], hosts: ['generativelanguage.googleapis.com', 'aiplatform.googleapis.com'] },
  { id: 'cohere', label: 'Cohere', packages: ['cohere-ai'], hosts: ['api.cohere.ai', 'api.cohere.com'] },
  { id: 'mistral', label: 'Mistral', packages: ['@mistralai/mistralai'], hosts: ['api.mistral.ai'] },
  { id: 'groq', label: 'Groq', packages: ['groq-sdk'], hosts: ['api.groq.com'] },
  { id: 'replicate', label: 'Replicate', packages: ['replicate'], hosts: ['api.replicate.com'] },
  { id: 'vercel-ai', label: 'Vercel AI SDK', packages: ['ai', '@ai-sdk/openai', '@ai-sdk/anthropic', '@ai-sdk/google', '@ai-sdk/mistral', '@ai-sdk/groq', '@ai-sdk/xai', '@ai-sdk/cohere', '@ai-sdk/amazon-bedrock', '@ai-sdk/azure', '@ai-sdk/deepseek', '@ai-sdk/perplexity'], hosts: [] },
  { id: 'langchain', label: 'LangChain', packages: ['langchain', '@langchain/core', '@langchain/openai', 'langgraph', '@langchain/langgraph'], hosts: [] },
  { id: 'ollama', label: 'Ollama', packages: ['ollama'], hosts: ['localhost:11434', '127.0.0.1:11434'] },
  { id: 'bedrock', label: 'AWS Bedrock', packages: ['@aws-sdk/client-bedrock-runtime'], hosts: ['bedrock-runtime'] },
  { id: 'cloudflare-ai', label: 'Cloudflare Workers AI', packages: ['@cloudflare/ai'], hosts: ['api.cloudflare.com'] },
  { id: 'huggingface', label: 'Hugging Face', packages: ['@huggingface/inference'], hosts: ['api-inference.huggingface.co'] },
];

// Method-name hints that indicate an actual inference call (vs. just an import).
export const INFERENCE_CALL_HINTS = [
  'createChatCompletion', 'chat.completions.create', 'completions.create',
  'messages.create', 'generateContent', 'generate', 'invoke', 'stream',
  'embeddings.create', 'run', 'predict', 'createMessage', 'streamText',
  'generateText', 'generateObject', 'chat', 'complete',
];

export function findProviderByPackage(spec) {
  const s = spec.replace(/^['"]|['"]$/g, '');
  return PROVIDERS.find(p => p.packages.some(pkg => s === pkg || s.startsWith(pkg + '/'))) || null;
}

export function findProviderByHost(urlLiteral) {
  return PROVIDERS.find(p => p.hosts.some(h => urlLiteral.includes(h))) || null;
}
