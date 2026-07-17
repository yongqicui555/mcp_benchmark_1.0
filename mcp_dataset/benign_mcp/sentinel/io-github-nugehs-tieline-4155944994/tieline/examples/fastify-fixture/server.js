const fastify = require('fastify')();

fastify.get('/health', async () => ({ ok: true }));
fastify.post('/users', async (req) => req.body);
fastify.get('/users/:id', async (req) => ({ id: req.params.id }));
fastify.route({ method: 'DELETE', url: '/users/:id', handler: async () => ({}) });
fastify.route({ method: ['PUT', 'PATCH'], url: '/users/:id', handler: async () => ({}) });

module.exports = fastify;
