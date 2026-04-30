import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { StateService } from './state.service';
import type {
  CaseDetail,
  QueueCase,
  RapportValidationStatus,
  RejectRapportPayload,
  ValidateRapportPayload
} from '../models/rapport-validation.model';

export type {
  CaseDetail,
  QueueCase,
  RapportValidationStatus,
  RejectRapportPayload,
  ValidateRapportPayload
} from '../models/rapport-validation.model';

@Injectable({
  providedIn: 'root'
})
export class RapportService {
  private apiUrl = '/api/v1/rapports';

  constructor(private http: HttpClient, private state: StateService) {}

  getValidationQueue(status: RapportValidationStatus = 'PENDING_VALIDATION'): Observable<{ status: string; queue: QueueCase[] }> {
    return this.http.get<{ status: string; queue: QueueCase[] }>(
      `${this.apiUrl}/validation-queue?status=${encodeURIComponent(status)}`,
      { headers: this.state.getAuthHeaders() }
    );
  }

  getCaseDetail(dossierId: string): Observable<{ status: string; case: CaseDetail }> {
    return this.http.get<{ status: string; case: CaseDetail }>(
      `${this.apiUrl}/dossier/${dossierId}`,
      { headers: this.state.getAuthHeaders() }
    );
  }

  validateRapport(rapportId: string, payload: ValidateRapportPayload): Observable<any> {
    return this.http.patch(
      `${this.apiUrl}/${rapportId}/validate`,
      payload,
      { headers: this.state.getAuthHeaders() }
    );
  }

  rejectRapport(rapportId: string, payload: RejectRapportPayload): Observable<any> {
    return this.http.patch(
      `${this.apiUrl}/${rapportId}/reject`,
      payload,
      { headers: this.state.getAuthHeaders() }
    );
  }
}
