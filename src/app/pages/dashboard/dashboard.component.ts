import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, RouterModule } from '@angular/router';
import { Router } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { forkJoin, of } from 'rxjs';

import { PatientService } from '../../services/patient.service';
import { DossierService } from '../../services/dossier.service';
import { StateService } from '../../services/state.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule, RouterModule, TranslateModule],
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

  editOpen = false;
  editLoading = false;
  editSaving = false;
  editError = '';
  editRecord: any = null;
  deleteOpen = false;
  deleteSaving = false;
  deleteError = '';
  deleteRecord: any = null;
  editForm = {
    nom: '',
    prenom: '',
    cin: '',
    dateNaissance: '',
    sexe: 'M',
    email: '',
    telephone: '',
    adresse: '',
    statut: 'OUVERT'
  };

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

  get roleLabel(): string {
    if (this.stateService.isCurrentUserAdmin) return 'ROLES.ADMIN';
    if (this.stateService.isCurrentUserSpecialiste) return 'ROLES.SPECIALIST';
    return 'ROLES.GENERALIST';
  }

  get shouldHideClinicalRisk(): boolean {
    return this.stateService.isCurrentUserAdmin || this.stateService.currentRole === 'agent';
  }

  get highRiskCount(): number {
    return this.records.filter(r => ['HIGH', 'VERY_HIGH'].includes(this.normalizeRiskLevel(r.risk_level))).length;
  }

  get mediumRiskCount(): number {
    return this.records.filter(r => this.normalizeRiskLevel(r.risk_level) === 'MEDIUM').length;
  }

  get lowRiskCount(): number {
    return this.records.filter(r => ['LOW', 'UNKNOWN', 'UNCERTAIN'].includes(this.normalizeRiskLevel(r.risk_level))).length;
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
        this.filteredRecords = this.records.filter(r => ['HIGH', 'VERY_HIGH'].includes(this.normalizeRiskLevel(r.risk_level)));
        break;
      case 'medium':
        this.filteredRecords = this.records.filter(r => this.normalizeRiskLevel(r.risk_level) === 'MEDIUM');
        break;
      case 'low':
        this.filteredRecords = this.records.filter(r => ['LOW', 'UNKNOWN', 'UNCERTAIN'].includes(this.normalizeRiskLevel(r.risk_level)));
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
    switch (this.normalizeRiskLevel(level)) {
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

  getRiskLabel(level: string): string {
    const normalized = this.normalizeRiskLevel(level);
    if (normalized === 'VERY_HIGH') return 'RISK.VERY_HIGH';
    if (normalized === 'HIGH') return 'RISK.HIGH';
    if (normalized === 'MEDIUM') return 'RISK.MEDIUM';
    if (normalized === 'LOW') return 'RISK.LOW';
    if (normalized === 'UNCERTAIN') return 'RISK.UNCERTAIN';
    return 'RISK.UNKNOWN';
  }

  getStatusClass(status: string): string {
    const normalized = this.normalizeStatus(status);
    if (['OUVERT', 'OPEN'].includes(normalized)) return 'open';
    if (['CLOSED', 'FERME'].includes(normalized)) return 'closed';
    if (normalized === 'PENDING_MRI') return 'pending';
    if (normalized === 'NO_DOSSIER') return 'new';
    if (normalized === 'VALIDATED') return 'validated';
    if (normalized === 'REJECTED') return 'rejected';
    return 'unknown';
  }

  getStatusLabel(status: string): string {
    const normalized = this.normalizeStatus(status);
    switch (normalized) {
      case 'OUVERT':
      case 'OPEN':
        return 'STATUS.OPEN';
      case 'CLOSED':
      case 'FERME':
        return 'STATUS.CLOSED';
      case 'PENDING_MRI':
        return 'STATUS.PENDING_MRI';
      case 'NO_DOSSIER':
        return 'STATUS.NO_DOSSIER';
      case 'VALIDATED':
        return 'STATUS.VALIDATED';
      case 'REJECTED':
        return 'STATUS.REJECTED';
      default:
        return 'STATUS.UNKNOWN';
    }
  }

  private normalizeRiskLevel(level: any): string {
    return String(level || 'UNKNOWN').trim().toUpperCase().replace(/[\s-]+/g, '_');
  }

  private normalizeStatus(status: any): string {
    return String(status || 'UNKNOWN').trim().toUpperCase().replace(/[\s-]+/g, '_');
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

  getReportVersionLabel(version: any): string {
    if (!version) return 'Report version';
    if (version.version_type === 'ORIGINAL_AI' || version.statut === 'UNVALIDATED') {
      return 'Original AI report';
    }
    if (version.version_type === 'SPECIALIST_REVIEW') {
      return version.statut === 'REJECTED' ? 'Specialist rejection' : 'Specialist review';
    }
    return version.version_type || 'Report version';
  }

  getReportVersionClass(version: any): string {
    const status = version?.statut;
    if (status === 'VALIDATED') return 'version-validated';
    if (status === 'REJECTED') return 'version-rejected';
    if (status === 'UNVALIDATED') return 'version-original';
    return 'version-generated';
  }

  viewHistoryReport(consultation: any, version?: any) {
    this.closeHistory();

    const selectedReport = version || consultation.rapport;
    const reportContent = selectedReport?.contenu;

    if (reportContent) {
      // Use actual report data if available
      let parsedPrediction = reportContent;
      if (typeof parsedPrediction === 'string') {
        try { parsedPrediction = JSON.parse(parsedPrediction); } catch(e) {}
      }

      parsedPrediction = {
        ...parsedPrediction,
        rapport_id: selectedReport.id,
        rapport_status: selectedReport.statut,
        version_number: selectedReport.version_number ?? parsedPrediction.version_number,
        version_type: selectedReport.version_type ?? parsedPrediction.version_type,
        previous_rapport_id: selectedReport.previous_rapport_id ?? parsedPrediction.previous_rapport_id,
        version_label: version ? this.getReportVersionLabel(version) : undefined
      };

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

  openEdit(record: any, event?: Event) {
    event?.stopPropagation();
    if (!record?.patient_id) {
      this.editError = 'No patient was found for this record.';
      return;
    }

    this.editOpen = true;
    this.editLoading = true;
    this.editSaving = false;
    this.editError = '';
    this.editRecord = record;

    forkJoin({
      patient: this.patientService.getPatient(record.patient_id),
      dossier: record.dossier_id ? this.dossierService.getDossier(record.dossier_id) : of(null)
    }).subscribe({
      next: ({ patient, dossier }) => {
        const patientData = patient?.patient || {};
        const dossierData = dossier?.dossier || {};

        this.editForm = {
          nom: patientData.nom || '',
          prenom: patientData.prenom || '',
          cin: patientData.cin || '',
          dateNaissance: this.toDateInputValue(patientData.dateNaissance),
          sexe: patientData.sexe || 'M',
          email: patientData.email || '',
          telephone: patientData.telephone || '',
          adresse: patientData.adresse || '',
          statut: dossierData.statut || record.dossier_status || 'OUVERT'
        };
        this.editLoading = false;
      },
      error: (err) => {
        this.editError = err.error?.error || 'Unable to load the record for editing.';
        this.editLoading = false;
      }
    });
  }

  closeEdit() {
    if (this.editSaving) return;
    this.editOpen = false;
    this.editRecord = null;
    this.editError = '';
  }

  openDelete(record: any, event?: Event) {
    event?.stopPropagation();
    if (!this.stateService.isCurrentUserAdmin || !record?.patient_id) return;

    this.deleteRecord = record;
    this.deleteOpen = true;
    this.deleteSaving = false;
    this.deleteError = '';
  }

  closeDelete() {
    if (this.deleteSaving) return;
    this.deleteOpen = false;
    this.deleteRecord = null;
    this.deleteError = '';
  }

  deletePatient() {
    if (!this.deleteRecord?.patient_id) return;

    this.deleteSaving = true;
    this.deleteError = '';

    this.patientService.deletePatient(this.deleteRecord.patient_id).subscribe({
      next: () => {
        this.deleteSaving = false;
        this.closeDelete();
        this.fetchDossiers();
      },
      error: (err) => {
        this.deleteSaving = false;
        this.deleteError = err.error?.error || 'Patient deletion failed.';
      }
    });
  }

  saveEdit() {
    if (!this.editRecord?.patient_id) return;
    if (!this.editForm.nom.trim() || !this.editForm.prenom.trim() || !this.editForm.dateNaissance || !this.editForm.sexe) {
      this.editError = 'Please fill in all required fields.';
      return;
    }

    this.editSaving = true;
    this.editError = '';

    const patientPayload = {
      nom: this.editForm.nom.trim(),
      prenom: this.editForm.prenom.trim(),
      cin: this.editForm.cin.trim(),
      dateNaissance: this.editForm.dateNaissance,
      sexe: this.editForm.sexe,
      email: this.editForm.email.trim(),
      telephone: this.editForm.telephone.trim(),
      adresse: this.editForm.adresse.trim()
    };

    const requests: any = {
      patient: this.patientService.updatePatient(this.editRecord.patient_id, patientPayload)
    };

    if (this.editRecord.dossier_id) {
      requests.dossier = this.dossierService.updateDossier(this.editRecord.dossier_id, {
        statut: this.editForm.statut
      });
    }

    forkJoin(requests).subscribe({
      next: () => {
        this.editSaving = false;
        this.closeEdit();
        this.fetchDossiers();
      },
      error: (err) => {
        this.editSaving = false;
        this.editError = err.error?.error || 'Record update failed.';
      }
    });
  }

  private toDateInputValue(value: any): string {
    if (!value) return '';
    return String(value).slice(0, 10);
  }
}
