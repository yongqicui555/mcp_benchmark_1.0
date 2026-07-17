import Anthropic from '@anthropic-ai/sdk';
export async function POST(request) {
  const a = new Anthropic();
  const msg = await a.messages.create({ model: 'claude-3', max_tokens: 500, messages: [] });
  return NextResponse.json({ reply: msg.content[0].text });
}
