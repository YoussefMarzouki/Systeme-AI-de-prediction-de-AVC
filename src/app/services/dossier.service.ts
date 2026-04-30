import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { StateService } from './state.service';

@Injectable({
  providedIn: 'root'
})
export class DossierService {
  private apiUrl = '/api/v1/dossiers';

  constructor(private http: HttpClient, private state: StateService) {}

  /**
   * Creates a dossier for the patient. 
   */
  createDossier(isMedecin: boolean = this.state.isCurrentUserDoctor): Observable<any> {
    const payload = {
      patient_id: this.state.patientId,
      is_medecin: isMedecin
    };
    return this.http.post(this.apiUrl, payload, { headers: this.state.getAuthHeaders() });
  }

  /**
   * Get all evaluated dossiers for Medecin dashboard
   */
  getEvaluatedDossiers(): Observable<any> {
    return this.http.get(`${this.apiUrl}/evaluated`, { headers: this.state.getAuthHeaders() });
  }
}
