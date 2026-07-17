import axios from 'axios';

export const getUsers = () => axios.get('/api/users');
export const createUser = (body: unknown) => axios.post('/api/users', body);
export const getUser = (id: string) => axios.get(`/api/users/${id}`);
export const removeUser = (id: string) => axios({ url: `/api/users/${id}`, method: 'delete' });
export const ping = () => fetch('/api/ping', { method: 'GET' });
export const updateUser = (id: string) => fetch(`/api/users/${id}`, { method: 'PUT' });
