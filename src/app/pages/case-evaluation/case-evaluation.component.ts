import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, ActivatedRoute, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { RapportService, CaseDetail } from '../../services/rapport.service';

@Component({
  selector: 'app-case-evaluation',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  templateUrl: './case-evaluation.component.html',
  styleUrl: './case-evaluation.component.css'
})
export class CaseEvaluationComponent implements OnInit {
  dossierId: string | null = null;
  caseDetail: CaseDetail | null = null;
  loading = true;
  error: string | null = null;
  saving = false;

  specialistNotes = '';
  predictedClass = '';
  aiAssessment = '';
  
  currentSlice = 1;
  totalSlices = 1;
  
  zoomLevel = 1;
  isFullscreen = false;

  constructor(
    private route: ActivatedRoute, 
    private router: Router,
    private rapportService: RapportService
  ) {}

  ngOnInit() {
    this.route.paramMap.subscribe(params => {
      this.dossierId = params.get('id');
      if (this.dossierId) {
        this.loadCaseDetail();
      } else {
        this.error = "Aucun ID de dossier fourni.";
        this.loading = false;
      }
    });
  }

  loadCaseDetail() {
    this.loading = true;
    this.rapportService.getCaseDetail(this.dossierId!).subscribe({
      next: (res) => {
        this.caseDetail = res.case;
        
        // Robust stroke type matching
        const rawType = res.case.predicted_class || '';
        console.log('Received stroke type:', rawType);
        
        if (rawType.includes('Hemorrhagic')) {
          this.predictedClass = 'Hemorrhagic';
        } else if (rawType.includes('Ischemic')) {
          this.predictedClass = 'Ischemic';
        } else if (rawType.includes('Normal')) {
          this.predictedClass = 'Normal';
        } else {
          this.predictedClass = rawType;
        }

        this.aiAssessment = res.case.ai_assessment || '';
        this.totalSlices = res.case.total_slices > 0 ? res.case.total_slices : 1;
        this.loading = false;
      },
      error: (err) => {
        console.error(err);
        this.error = "Erreur lors du chargement du dossier.";
        this.loading = false;
      }
    });
  }

  prevSlice() {
    if (this.currentSlice > 1) this.currentSlice--;
  }

  nextSlice() {
    if (this.currentSlice < this.totalSlices) this.currentSlice++;
  }

  zoomIn() {
    if (this.zoomLevel < 3) this.zoomLevel += 0.25;
  }

  zoomOut() {
    if (this.zoomLevel > 0.5) this.zoomLevel -= 0.25;
  }

  toggleFullscreen() {
    this.isFullscreen = !this.isFullscreen;
  }

  validate() {
    if (!this.caseDetail || !this.caseDetail.rapport_id) return;
    this.saving = true;
    this.rapportService.validateRapport(this.caseDetail.rapport_id, {
      notes: this.specialistNotes,
      predicted_class: this.predictedClass,
      ai_assessment: this.aiAssessment
    }).subscribe({
      next: () => {
        this.router.navigate(['/ms/validation-queue']);
      },
      error: (err) => {
        console.error(err);
        this.saving = false;
      }
    });
  }

  reject() {
    if (!this.caseDetail || !this.caseDetail.rapport_id) return;
    this.saving = true;
    this.rapportService.rejectRapport(this.caseDetail.rapport_id, {
      notes: this.specialistNotes
    }).subscribe({
      next: () => {
        this.router.navigate(['/ms/validation-queue']);
      },
      error: (err) => {
        console.error(err);
        this.saving = false;
      }
    });
  }
}

