import OpenAI from 'openai';
export class ChatService {
  async reply(input) {
    const client = new OpenAI();
    const r = await client.chat.completions.create({ model: 'gpt-4', messages: input.messages });
    return r.choices[0].message.content;
  }
}
