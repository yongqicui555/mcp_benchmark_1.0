// A mock RTK Query slice that calls the Express fixture backend.
// Five endpoints should MATCH; two are deliberate drift to prove detection.
import { createApi } from '@reduxjs/toolkit/query/react';

export const usersApi = createApi({
  reducerPath: 'usersApi',
  baseQuery: () => ({ data: null }),
  endpoints: (builder) => ({
    // --- should match the Express routes ---
    getUsers: builder.query({ query: () => 'users' }), // GET /api/v1/users
    getUser: builder.query({ query: (id) => `users/${id}` }), // GET /api/v1/users/:id
    ping: builder.query({ query: () => 'ping' }), // GET /api/v1/ping
    createUser: builder.mutation({ query: (b) => ({ url: 'users', method: 'POST', body: b }) }),
    deleteUser: builder.mutation({ query: (id) => ({ url: `users/${id}`, method: 'DELETE' }) }),

    // --- deliberate drift ---
    getStats: builder.query({ query: () => 'stats' }), // BE serves /status, not /stats
    updateUser: builder.mutation({ query: (id) => ({ url: `users/${id}`, method: 'PUT' }) }), // no PUT on BE
  }),
});
