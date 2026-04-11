import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { StateService } from './state.service';

@Injectable({
  providedIn: 'root'
})
export class DonneesCliniquesService {
  private apiUrl = '/api/v1/dossiers';

  constructor(private http: HttpClient, private state: StateService) {}

  /**
   * Adds 'Donnees Cliniques' (symptoms) to a dossier
   */
  addDonneesCliniques(fastData: { symptoms: string[], tension?: number | string }, additionalNotes: string): Observable<any> {
    const payload = {
      fast: fastData.symptoms.join(', '), // Convert list to string for DB String(100)
      tension: fastData.tension ? fastData.tension.toString() : null,
      notes: additionalNotes
    };
    return this.http.post(`${this.apiUrl}/${this.state.dossierId}/donnees-cliniques`, payload, { headers: this.state.getAuthHeaders() });
  }
}
