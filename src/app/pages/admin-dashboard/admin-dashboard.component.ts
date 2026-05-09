import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { SystemHealth, SystemHealthService } from '../../services/system-health.service';

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './admin-dashboard.component.html',
  styleUrl: './admin-dashboard.component.css'
})
export class AdminDashboardComponent implements OnInit {
  healthLoading = true;
  healthError = '';
  systemHealth: SystemHealth = {
    backend: { ok: false, label: 'Checking', state: 'unknown' },
    prediction: { ok: false, label: 'Checking', state: 'unknown' },
    database: { ok: false, label: 'Checking', state: 'unknown' }
  };

  managementCards = [
    {
      title: 'Patient Management',
      description: 'Review, select, and update patient records and medical dossier information.',
      route: '/admin/patients',
      icon: 'patients',
      metric: 'Records'
    },
    {
      title: 'User Management',
      description: 'Create, update, search, and remove authorized system accounts.',
      route: '/admin/users',
      icon: 'users',
      metric: 'Accounts'
    }
  ];

  healthCards = [
    {
      key: 'backend' as const,
      title: 'Backend',
      description: 'Flask API service',
      icon: 'server'
    },
    {
      key: 'prediction' as const,
      title: 'Prediction Service',
      description: 'AI model microservice',
      icon: 'activity'
    },
    {
      key: 'database' as const,
      title: 'Database',
      description: 'PostgreSQL connection, checked through backend',
      icon: 'database'
    }
  ];

  constructor(private systemHealthService: SystemHealthService) {}

  ngOnInit(): void {
    this.loadHealth();
  }

  loadHealth(): void {
    this.healthLoading = true;
    this.healthError = '';

    this.systemHealthService.getHealth().subscribe({
      next: (health) => {
        this.systemHealth = health;
        this.healthLoading = false;
      }
    });
  }
}
