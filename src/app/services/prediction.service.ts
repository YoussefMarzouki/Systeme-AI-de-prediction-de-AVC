import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { StateService } from './state.service';
import { LanguageService } from './language.service';

@Injectable({
  providedIn: 'root'
})
export class PredictionService {
  private apiUrl = '/api/v1/dossiers';

  constructor(
    private http: HttpClient, 
    private state: StateService,
    private languageService: LanguageService
  ) {}

  /**
   * Request fused (image + symptoms) prediction from backend
   */
  predictFused(imageUrl: string | null, symptomsText: string | null): Observable<any> {
    const lang = this.languageService.getCurrentLanguage();
    const payload = {
      image_url: imageUrl,
      symptoms_text: symptomsText ? `${symptomsText}\n\nconvert the answer to ${lang}` : symptomsText,
      language: lang
    };
    return this.http.post(`${this.apiUrl}/${this.state.dossierId}/predict`, payload, { headers: this.state.getAuthHeaders() });
  }

  /**
   * Request symptoms-only prediction (no image, no duplicate LLM call)
   */
  predictSymptoms(symptomsText: string): Observable<any> {
    const lang = this.languageService.getCurrentLanguage();
    const payload = {
      image_url: null,
      symptoms_text: symptomsText ? `${symptomsText}\n\nconvert the answer to ${lang}` : symptomsText,
      language: lang
    };
    return this.http.post(`${this.apiUrl}/${this.state.dossierId}/predict`, payload, { headers: this.state.getAuthHeaders() });
  }

  /**
   * Request image-only prediction (no symptom analysis)
   */
  predictImage(imageUrl: string): Observable<any> {
    const payload = {
      image_url: imageUrl,
      symptoms_text: null
    };
    return this.http.post(`${this.apiUrl}/${this.state.dossierId}/predict`, payload, { headers: this.state.getAuthHeaders() });
  }

  /**
   * Finalize batch predictions by saving the merged prediction to the backend.
   */
  finalizePrediction(prediction: any): Observable<any> {
    const payload = {
      prediction: prediction
    };
    return this.http.post(`${this.apiUrl}/${this.state.dossierId}/predict/finalize`, payload, { headers: this.state.getAuthHeaders() });
  }
}
