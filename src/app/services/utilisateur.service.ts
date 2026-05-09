import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { StateService } from './state.service';
import { Utilisateur } from '../models/utilisateur.model';

@Injectable({
  providedIn: 'root'
})
export class UtilisateurService {
  private apiUrl = '/api/v1/utilisateurs';

  constructor(private http: HttpClient, private state: StateService) {}

  list(): Observable<{ status: string; utilisateurs: Utilisateur[] }> {
    return this.http.get<{ status: string; utilisateurs: Utilisateur[] }>(
      this.apiUrl,
      { headers: this.state.getAuthHeaders() }
    );
  }

  get(id: string): Observable<{ status: string; utilisateur: Utilisateur }> {
    return this.http.get<{ status: string; utilisateur: Utilisateur }>(
      `${this.apiUrl}/${id}`,
      { headers: this.state.getAuthHeaders() }
    );
  }

  create(data: any): Observable<{ status: string; id: string }> {
    return this.http.post<{ status: string; id: string }>(
      this.apiUrl,
      data,
      { headers: this.state.getAuthHeaders() }
    );
  }

  update(id: string, data: any): Observable<{ status: string; utilisateur: Utilisateur }> {
    return this.http.put<{ status: string; utilisateur: Utilisateur }>(
      `${this.apiUrl}/${id}`,
      data,
      { headers: this.state.getAuthHeaders() }
    );
  }

  delete(id: string): Observable<any> {
    return this.http.delete(
      `${this.apiUrl}/${id}`,
      { headers: this.state.getAuthHeaders() }
    );
  }

  search(query: string): Observable<{ status: string; utilisateurs: Utilisateur[] }> {
    return this.http.get<{ status: string; utilisateurs: Utilisateur[] }>(
      `${this.apiUrl}/search?q=${encodeURIComponent(query)}`,
      { headers: this.state.getAuthHeaders() }
    );
  }
}
