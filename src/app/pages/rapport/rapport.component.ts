import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';

@Component({
  selector: 'app-rapport',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './rapport.component.html',
  styleUrl: './rapport.component.css'
})
export class RapportComponent implements OnInit {
  private readonly storageKey = 'strokeai:lastRapport';
  predictionData: any;
  patientDetails: any;
  imageUrl: string | null = null;
  currentDate = new Date();

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
    }
  }

  private normalizePredictionData(): void {
    if (!this.predictionData) return;

    // Detect modifications by specialist
    this.predictionData.is_modified = !!(this.predictionData.validation_status && this.predictionData.validation_status !== 'GENERATED');

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

  printRapport() {
    window.print();
  }
}
