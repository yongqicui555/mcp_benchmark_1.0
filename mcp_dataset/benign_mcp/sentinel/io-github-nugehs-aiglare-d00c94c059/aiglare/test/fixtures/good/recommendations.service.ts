import OpenAI from 'openai';
@Controller('recommendations')
export class RecommendationsService {
  async getVendorMatches(dto) {
    try {
      const client = new OpenAI();
      const r = await client.chat.completions.create({ model: 'gpt-4', messages: dto.messages });
      return r.choices[0].message.content;
    } catch (e) {
      return []; // fallback to empty
    }
  }
}
