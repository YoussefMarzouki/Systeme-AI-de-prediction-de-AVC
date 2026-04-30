import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { Router } from '@angular/router';

import { PatientService } from '../../services/patient.service';
import { DossierService } from '../../services/dossier.service';
import { StateService } from '../../services/state.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {
  records: any[] = [];
  filteredRecords: any[] = [];
  loading = true;
  activeFilter = 'all';

  // History panel state
  historyOpen = false;
  historyLoading = false;
  historyData: any = null;

  constructor(
    private router: Router,
    private patientService: PatientService,
    private dossierService: DossierService,
    public stateService: StateService
  ) {
    // We let StateService handle the role instead of hardcoding it.
  }

  ngOnInit(): void {
    this.fetchDossiers();
  }

  get highRiskCount(): number {
    return this.records.filter(r => r.risk_level === 'HIGH' || r.risk_level === 'VERY_HIGH').length;
  }

  get mediumRiskCount(): number {
    return this.records.filter(r => r.risk_level === 'MEDIUM').length;
  }

  get lowRiskCount(): number {
    return this.records.filter(r =>
      r.risk_level === 'LOW' ||
      r.risk_level === 'UNKNOWN' ||
      r.risk_level === 'UNCERTAIN'
    ).length;
  }

  fetchDossiers() {
    this.loading = true;
    this.dossierService.getEvaluatedDossiers().subscribe({
      next: (res) => {
        if (res.status === 'success') {
          this.records = res.records;
          this.applyFilter();
        }
        this.loading = false;
      },
      error: (err) => {
        console.error('Error fetching evaluated dossiers', err);
        this.loading = false;
      }
    });
  }

  setFilter(filter: string) {
    this.activeFilter = filter;
    this.applyFilter();
  }

  private applyFilter() {
    switch (this.activeFilter) {
      case 'high':
        this.filteredRecords = this.records.filter(r => r.risk_level === 'HIGH' || r.risk_level === 'VERY_HIGH');
        break;
      case 'medium':
        this.filteredRecords = this.records.filter(r => r.risk_level === 'MEDIUM');
        break;
      case 'low':
        this.filteredRecords = this.records.filter(r => r.risk_level === 'LOW' || r.risk_level === 'UNKNOWN' || r.risk_level === 'UNCERTAIN');
        break;
      default:
        this.filteredRecords = [...this.records];
    }
  }

  getAvatarGradient(name: string): string {
    const gradients = [
      'linear-gradient(135deg, #3b82f6, #8b5cf6)',
      'linear-gradient(135deg, #0d9488, #06b6d4)',
      'linear-gradient(135deg, #f59e0b, #ef4444)',
      'linear-gradient(135deg, #8b5cf6, #ec4899)',
      'linear-gradient(135deg, #10b981, #3b82f6)',
    ];
    const index = (name?.charCodeAt(0) || 0) % gradients.length;
    return gradients[index];
  }

  getRiskClass(level: string): string {
    switch (level) {
      case 'HIGH':
      case 'VERY_HIGH':
        return 'risk-high';
      case 'MEDIUM':
        return 'risk-medium';
      case 'LOW':
        return 'risk-low';
      default:
        return 'risk-unknown';
    }
  }

  // ── History panel ─────────────────────────────────
  openHistory(record: any) {
    if (!record.patient_id) {
      console.warn('No patient_id available for history');
      return;
    }
    this.historyOpen = true;
    this.historyLoading = true;
    this.historyData = null;

    this.patientService.getPatientHistory(record.patient_id).subscribe({
      next: (res) => {
        if (res.status === 'success') {
          this.historyData = res.history;
        }
        this.historyLoading = false;
      },
      error: (err) => {
        console.error('Error fetching patient history', err);
        this.historyLoading = false;
      }
    });
  }

  closeHistory() {
    this.historyOpen = false;
    this.historyData = null;
  }

  viewHistoryReport(consultation: any) {
    this.closeHistory();

    const reportContent = consultation.rapport?.contenu;

    if (reportContent) {
      // Use actual report data if available
      let parsedPrediction = reportContent;
      if (typeof parsedPrediction === 'string') {
        try { parsedPrediction = JSON.parse(parsedPrediction); } catch(e) {}
      }

      this.router.navigate([`${this.stateService.routePrefix}/rapport`], {
        state: {
          prediction: parsedPrediction,
          patientDetails: {
            nom: this.historyData?.patient_name || 'Unknown',
            tension: consultation.clinical_data?.[0]?.tension || null,
            symptoms: consultation.clinical_data?.map((c: any) => c.notes).filter((n: any) => n) || ['Loaded from Patient DB']
          },
          imageUrl: consultation.image_urls?.[0] || parsedPrediction?.imageUrl || null
        }
      });
    } else {
      // Fallback back to historical summary if report data doesn't exist
      this.router.navigate([`${this.stateService.routePrefix}/rapport`], {
        state: {
          prediction: {
            risk_level: consultation.risk_level || 'UNKNOWN',
            fused_probability: consultation.fused_probability || 0,
            confidence: 0.99,
            predicted_class: 'Historical Record',
            symptom_urgency: 'N/A',
            symptom_probability: null,
            image_probability: null,
            symptom_response: 'Loaded from consultation history.'
          },
          patientDetails: {
            nom: this.historyData?.patient_name || 'Unknown',
            tension: consultation.clinical_data?.[0]?.tension || null,
            symptoms: consultation.clinical_data?.map((c: any) => c.notes).filter((n: any) => n) || []
          },
          imageUrl: consultation.image_urls?.[0] || null
        }
      });
    }
  }

  viewReport(record: any) {
    if (record.prediction_data) {
      let parsedPrediction = record.prediction_data;
      if (typeof parsedPrediction === 'string') {
        try { parsedPrediction = JSON.parse(parsedPrediction); } catch(e) {}
      }

      this.router.navigate([`${this.stateService.routePrefix}/rapport`], {
        state: {
          prediction: parsedPrediction,
          patientDetails: {
            nom: record.patient_name,
            symptoms: ['Loaded from Patient DB']
          },
          imageUrl: record.imageUrl || parsedPrediction?.imageUrl || null
        }
      });
    } else {
      const risk_level = record.risk_level === 'UNKNOWN' ? 'UNCERTAIN' : record.risk_level;

      this.router.navigate([`${this.stateService.routePrefix}/rapport`], {
        state: {
          prediction: {
            risk_level: risk_level,
            fused_probability: record.fused_probability,
            confidence: 0.99,
            predicted_class: 'N/A: Historical Fetch',
            symptom_urgency: 'N/A: Historical Fetch',
            symptom_probability: null,
            image_probability: null,
            symptom_response: 'Detailed Symptom RAG breakdown was previously attached to this record.'
          },
          patientDetails: {
            tension: record.tension || null,
            symptoms: record.symptoms || ['Historically Logged Assessment']
          },
          imageUrl: record.imageUrl || null
        }
      });
    }
  }

  onTableRowClick(record: any) {
    if (this.stateService.isCurrentUserDoctor) {
      if (record.dossier_status === 'PENDING_MRI') {
        this.goToMriUpload(record);
      } else {
        this.goToIntake(record);
      }
    }
  }

  goToMriUpload(record: any) {
    if (record && record.patient_id) {
      // Need to resume context to Mri Upload for the dossier
      this.stateService.setPatientId(record.patient_id);
      this.stateService.setDossierId(record.dossier_id);
      this.router.navigate([`${this.stateService.routePrefix}/mri-upload`], {
        state: { 
          patientDetails: { 
            name: record.patient_name, 
            cin: record.patient_cin 
          },
          symptomsData: {
            symptomsText: record.symptoms && record.symptoms.length > 0 ? record.symptoms[0] : 'General Assessment',
            tensionValue: record.tension
          }
        }
      });
    }
  }

  goToIntake(record: any) {
    if (record && record.patient_id) {
      // Set the selected patient ID in StateService so Intake component can pick it up
      this.stateService.setPatientId(record.patient_id);
      this.router.navigate([`${this.stateService.routePrefix}/intake`], {
        state: { 
          patientDetails: { 
            name: record.patient_name, 
            cin: record.patient_cin 
          } 
        }
      });
    }
  }
}
