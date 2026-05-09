import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { catchError, forkJoin, map, of, timeout } from 'rxjs';
import { StateService } from './state.service';

export interface HealthItem {
  ok: boolean;
  label: string;
  state?: 'online' | 'offline' | 'unknown';
}

export interface SystemHealth {
  backend: HealthItem;
  prediction: HealthItem;
  database: HealthItem;
}

interface BackendHealthResponse {
  status: string;
  health: {
    backend: HealthItem;
    database: HealthItem;
  };
}

@Injectable({
  providedIn: 'root'
})
export class SystemHealthService {
  private apiUrl = '/api/v1/system/health';

  constructor(private http: HttpClient, private state: StateService) {}

  getHealth(): Observable<SystemHealth> {
    return forkJoin({
      backend: this.getBackendAndDatabaseHealth(),
      prediction: this.getPredictionHealth()
    }).pipe(
      map(({ backend, prediction }) => ({
        backend: backend.backend,
        database: backend.database,
        prediction
      }))
    );
  }

  private getBackendAndDatabaseHealth(): Observable<{ backend: HealthItem; database: HealthItem }> {
    return this.http.get<BackendHealthResponse>(
      this.apiUrl,
      { headers: this.state.getAuthHeaders() }
    ).pipe(
      timeout(2500),
      map(res => res.health),
      catchError(() => of({
        backend: { ok: false, label: 'Offline', state: 'offline' as const },
        database: { ok: false, label: 'Unknown', state: 'unknown' as const }
      }))
    );
  }

  private getPredictionHealth(): Observable<HealthItem> {
    const predictionUrl = this.getPredictionHealthUrl();
    return this.http.get<any>(predictionUrl).pipe(
      timeout(2500),
      map(res => ({
        ok: res?.status === 'healthy',
        label: res?.status === 'healthy' ? 'Online' : 'Unavailable',
        state: res?.status === 'healthy' ? 'online' as const : 'offline' as const
      })),
      catchError(() => of({ ok: false, label: 'Unavailable', state: 'offline' as const }))
    );
  }

  private getPredictionHealthUrl(): string {
    const protocol = window.location.protocol;
    const hostname = window.location.hostname || 'localhost';
    return `${protocol}//${hostname}:8000/health`;
  }
}
