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

      if (this.predictionData && !this.predictionData.symptom_response) {
        this.predictionData.symptom_response = "N/A: Symptom analysis incomplete.";
      }
    }
  }

  ngOnInit(): void {
    if (!this.predictionData) {
      console.warn("No prediction data provided.");
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
