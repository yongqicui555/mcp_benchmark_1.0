import OpenAI from 'openai';
export class TripSuggestService {
  async suggest(input) {
    try {
      const client = new OpenAI();
      const r = await client.chat.completions.create({ model: 'gpt-4', messages: input.messages });
      // never actions anything directly — returns a draft pending human approval
      return { status: 'pending_approval', requiresApproval: true, text: r.choices[0].message.content };
    } catch {
      return { status: 'unavailable', text: null };
    }
  }
}
