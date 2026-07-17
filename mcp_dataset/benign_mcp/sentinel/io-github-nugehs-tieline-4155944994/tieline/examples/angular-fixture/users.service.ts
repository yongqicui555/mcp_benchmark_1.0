import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({ providedIn: 'root' })
export class UsersService {
  constructor(private http: HttpClient) {}

  list() {
    return this.http.get<User[]>('/api/users');
  }
  create(u: User) {
    return this.http.post('/api/users', u);
  }
  get(id: string) {
    return this.http.get(`/api/users/${id}`);
  }
  remove(id: string) {
    return this.http.delete(`/api/users/${id}`);
  }
}

interface User {
  id: string;
}
