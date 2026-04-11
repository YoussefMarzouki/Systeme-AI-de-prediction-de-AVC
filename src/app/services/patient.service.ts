import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { StateService } from './state.service';
import { Patient } from '../models/patient.model';

@Injectable({
  providedIn: 'root'
})
export class PatientService {
  private apiUrl = '/api/v1/patients';

  constructor(private http: HttpClient, private state: StateService) {}

  /**
   * Registers a new patient.
   */
  createPatient(patient: Patient): Observable<any> {
    return this.http.post(this.apiUrl, patient, { headers: this.state.getAuthHeaders() });
  }

  /**
   * Search for patients by name or CIN
   */
  searchPatients(query: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/search?q=${query}`, { headers: this.state.getAuthHeaders() });
  }

  /**
   * Get consultation history for a specific patient
   */
  getPatientHistory(patientId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/${patientId}/history`, { headers: this.state.getAuthHeaders() });
  }
}
