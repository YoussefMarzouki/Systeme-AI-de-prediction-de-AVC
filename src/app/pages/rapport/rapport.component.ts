import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';

@Component({
  selector: 'app-rapport',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './rapport.component.html',
  styleUrl: './rapport.component.css'
})
export class RapportComponent implements OnInit, OnDestroy {
  private readonly storageKey = 'strokeai:lastRapport';
  predictionData: any;
  patientDetails: any;
  imageUrl: string | null = null;
  currentDate = new Date();
  exportError = '';
  exportLoading = false;

  currentSliceIndex = 0;
  totalSlices = 0;

  constructor(private router: Router) {
    const navigation = this.router.getCurrentNavigation();
    if (navigation?.extras.state) {
      this.predictionData = navigation.extras.state['prediction'];
      this.patientDetails = navigation.extras.state['patientDetails'];
      this.imageUrl = navigation.extras.state['imageUrl'];
      this.normalizePredictionData();
      this.saveReportState();
    } else {
      this.restoreReportState();
    }
  }

  ngOnInit(): void {
    if (!this.predictionData) {
      console.warn("No prediction data provided.");
    } else {
      this.initializeSliceViewer();
    }
  }

  initializeSliceViewer(): void {
    const slices = this.predictionData.all_slices || [];
    this.totalSlices = slices.length;
    
    // Set starting slice index to the representative one matching this.imageUrl
    if (this.totalSlices > 0 && this.imageUrl) {
      const idx = slices.findIndex((s: any) => s.imageUrl === this.imageUrl);
      if (idx !== -1) {
        this.currentSliceIndex = idx;
      }
    }
  }

  prevSlice(): void {
    if (this.currentSliceIndex > 0) {
      this.currentSliceIndex--;
    }
  }

  nextSlice(): void {
    if (this.currentSliceIndex < this.totalSlices - 1) {
      this.currentSliceIndex++;
    }
  }

  ngOnDestroy(): void {
    document.body.classList.remove('printing-rapport');
  }

  private normalizePredictionData(): void {
    if (!this.predictionData) return;

    // Detect modifications by specialist
    this.predictionData.is_modified =
      this.predictionData.validation_status === 'VALIDATED' ||
      this.predictionData.validation_status === 'REJECTED';
    this.predictionData.version_label =
      this.predictionData.version_label ||
      (this.predictionData.version_type === 'ORIGINAL_AI' ? 'Original AI report' : null) ||
      (this.predictionData.version_type === 'SPECIALIST_REVIEW' ? 'Specialist-reviewed report' : null);

    // Unify notes field
    this.predictionData.display_notes = this.predictionData.specialist_notes || this.predictionData.rejection_notes;

    this.predictionData.symptom_probability =
      this.predictionData.symptom_probability ?? this.predictionData.probability ?? null;
    
    this.predictionData.symptom_urgency =
      this.predictionData.symptom_urgency ?? this.predictionData.urgency ?? null;
    
    // Prioritize Specialist Assessment if validated or rejected (expert feedback), otherwise use AI response
    this.predictionData.final_assessment = 
      ((this.predictionData.validation_status === 'VALIDATED' || this.predictionData.validation_status === 'REJECTED') ? this.predictionData.ai_assessment : null) || 
      this.predictionData.symptom_response ||
      this.predictionData.response ||
      this.predictionData.ai_assessment ||
      "N/A: Symptom analysis incomplete.";
  }

  private saveReportState(): void {
    try {
      sessionStorage.setItem(this.storageKey, JSON.stringify({
        predictionData: this.predictionData,
        patientDetails: this.patientDetails,
        imageUrl: this.imageUrl
      }));
    } catch (err) {
      console.warn('Unable to save report state.', err);
    }
  }

  private restoreReportState(): void {
    try {
      const raw = sessionStorage.getItem(this.storageKey);
      if (!raw) return;
      const saved = JSON.parse(raw);
      this.predictionData = saved.predictionData;
      this.patientDetails = saved.patientDetails;
      this.imageUrl = saved.imageUrl;
      this.normalizePredictionData();
    } catch (err) {
      console.warn('Unable to restore report state.', err);
    }
  }

  getRiskCardClass(): string {
    const level = this.predictionData?.risk_level;
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

  getSliceRiskColorClass(prob: number): string {
    if (prob == null) return 'risk-text-unknown';
    if (prob >= 0.6) return 'risk-text-high';
    if (prob >= 0.2) return 'risk-text-medium';
    return 'risk-text-low';
  }

  exportPdf() {
    this.exportError = '';
    document.body.classList.add('printing-rapport');
    setTimeout(() => window.print(), 50);
    window.addEventListener(
      'afterprint',
      () => document.body.classList.remove('printing-rapport'),
      { once: true }
    );
  }
}
