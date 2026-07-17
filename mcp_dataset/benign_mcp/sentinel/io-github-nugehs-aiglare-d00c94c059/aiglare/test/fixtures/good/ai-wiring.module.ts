import OpenAI from 'openai';

// DI wiring only: constructs the client in a factory and re-exports it.
// It imports the provider but never calls the model, so it is not a surface.
export const aiClientFactory = (config) => new OpenAI(config.options);

export const providers = [
  { provide: OpenAI, useFactory: aiClientFactory },
  { provide: 'AI_MODEL', useFactory: (config) => config.model },
];
