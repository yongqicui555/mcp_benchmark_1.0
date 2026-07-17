import OpenAI from 'openai';
import { z } from 'zod';
const Result = z.object({ species: z.string(), confidence: z.number() });
export async function identify(input) {
  try {
    const client = new OpenAI();
    const r = await client.chat.completions.create({ model: 'gpt-4', messages: input.messages });
    const parsed = Result.safeParse(JSON.parse(r.choices[0].message.content));
    if (!parsed.success) return { status: 'uncertain', species: null };
    if (parsed.data.confidence < 0.7) return { status: 'low_confidence', candidates: [] };
    return { status: 'ok', ...parsed.data };
  } catch {
    return { status: 'uncertain', species: null };
  }
}
