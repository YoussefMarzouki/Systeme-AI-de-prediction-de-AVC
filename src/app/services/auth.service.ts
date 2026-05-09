import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { Router } from '@angular/router';
import { StateService, UserRole } from './state.service';

export type AppRole = UserRole | 'unknown';

export interface LoginResponse {
  status: string;
  token: string;
  user: {
    id: string;
    nom: string;
    email: string;
    type: string;
    etat: string;
    specialiste?: boolean;
  };
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = '/api/v1/auth';

  constructor(
    private http: HttpClient,
    private router: Router,
    private state: StateService
  ) {
    const role = this.currentRoleKey;
    if (role !== 'unknown') {
      this.state.setRole(role);
    }
  }

  login(email: string, motDePasse: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.apiUrl}/login`, { email, motDePasse }).pipe(
      tap(res => {
        localStorage.setItem('strokeai_token', res.token);
        localStorage.setItem('strokeai_user', JSON.stringify(res.user));
        const role = this.currentRoleKey;
        if (role !== 'unknown') {
          this.state.setRole(role);
        }
      })
    );
  }

  clearSession(): void {
    localStorage.removeItem('strokeai_token');
    localStorage.removeItem('strokeai_user');
    this.state.setRole('agent');
  }

  logout(): void {
    this.clearSession();
    this.router.navigate(['/login']);
  }

  get isLoggedIn(): boolean {
    return !!localStorage.getItem('strokeai_token') && this.currentRoleKey !== 'unknown';
  }

  get currentUser(): any {
    const raw = localStorage.getItem('strokeai_user');
    if (!raw) return null;

    try {
      return JSON.parse(raw);
    } catch {
      this.clearSession();
      return null;
    }
  }

  get token(): string | null {
    return localStorage.getItem('strokeai_token');
  }

  get userType(): string {
    return this.currentUser?.type || '';
  }

  get currentRoleKey(): AppRole {
    const user = this.currentUser;
    if (!user) return 'unknown';
    if (user.type === 'admin') return 'admin';
    if (user.type === 'agent_accueil') return 'agent';
    if (user.type === 'medecin') return user.specialiste ? 'ms' : 'mg';
    return 'unknown';
  }

  getLandingRoute(): string {
    const role = this.currentRoleKey;
    if (role === 'admin') return '/admin/dashboard';
    if (role === 'ms') return '/ms/validation-queue';
    if (role === 'mg') return '/mg/dashboard';
    if (role === 'agent') return '/agent/dashboard';
    return '/login';
  }

  getRoutePrefix(): string {
    const role = this.currentRoleKey;
    if (role === 'admin') return '/admin';
    if (role === 'ms') return '/ms';
    if (role === 'mg') return '/mg';
    if (role === 'agent') return '/agent';
    return '/login';
  }
}

