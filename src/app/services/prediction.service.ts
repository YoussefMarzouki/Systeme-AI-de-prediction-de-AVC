import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { StateService } from './state.service';

@Injectable({
  providedIn: 'root'
})
export class PredictionService {
  private apiUrl = '/api/v1/dossiers';

  constructor(private http: HttpClient, private state: StateService) {}

  /**
   * Request prediction from backend
   */
  predictFused(imageUrl: string | null, symptomsText: string | null): Observable<any> {
    const payload = {
      image_url: imageUrl,
      symptoms_text: symptomsText
    };
    return this.http.post(`${this.apiUrl}/${this.state.dossierId}/predict`, payload, { headers: this.state.getAuthHeaders() });
  }
}
