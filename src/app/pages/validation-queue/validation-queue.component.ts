import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { RapportService, QueueCase } from '../../services/rapport.service';

@Component({
  selector: 'app-validation-queue',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './validation-queue.component.html',
  styleUrl: './validation-queue.component.css'
})
export class ValidationQueueComponent implements OnInit {
  cases: QueueCase[] = [];
  expandedCaseId: string | null = null;
  loading = true;
  error: string | null = null;
  currentTab: 'PENDING_VALIDATION' | 'VALIDATED' | 'REJECTED' = 'PENDING_VALIDATION';

  constructor(private rapportService: RapportService) {}

  ngOnInit() {
    this.loadQueue();
  }

  loadQueue() {
    this.loading = true;
    this.error = null;
    this.rapportService.getValidationQueue(this.currentTab).subscribe({
      next: (res) => {
        this.cases = res.queue || [];
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Impossible de charger la file d\'attente.';
        this.loading = false;
        console.error(err);
      }
    });
  }

  setTab(tab: 'PENDING_VALIDATION' | 'VALIDATED' | 'REJECTED') {
    this.currentTab = tab;
    this.loadQueue();
  }

  toggleExpand(caseId: string) {
    this.expandedCaseId = this.expandedCaseId === caseId ? null : caseId;
  }

  getAiScore(c: QueueCase): number | null {
    return c.ai_irm_score ?? c.ai_symptom_score ?? c.ai_probability_score ?? null;
  }
}
