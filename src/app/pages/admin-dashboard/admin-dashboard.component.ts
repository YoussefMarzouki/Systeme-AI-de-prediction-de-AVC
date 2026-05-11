import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { SystemHealth, SystemHealthService } from '../../services/system-health.service';

import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslateModule],
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
      titleKey: 'ADMIN_DASHBOARD.PATIENT_MGMT',
      descKey: 'ADMIN_DASHBOARD.PATIENT_DESC',
      route: '/admin/patients',
      icon: 'patients',
      metric: 'Records'
    },
    {
      titleKey: 'ADMIN_DASHBOARD.USER_MGMT',
      descKey: 'ADMIN_DASHBOARD.USER_DESC',
      route: '/admin/users',
      icon: 'users',
      metric: 'Accounts'
    }
  ];

  healthCards = [
    {
      key: 'backend' as const,
      titleKey: 'ADMIN_DASHBOARD.BACKEND',
      descKey: 'ADMIN_DASHBOARD.BACKEND_DESC',
      icon: 'server'
    },
    {
      key: 'prediction' as const,
      titleKey: 'ADMIN_DASHBOARD.PREDICTION',
      descKey: 'ADMIN_DASHBOARD.PREDICTION_DESC',
      icon: 'activity'
    },
    {
      key: 'database' as const,
      titleKey: 'ADMIN_DASHBOARD.DATABASE',
      descKey: 'ADMIN_DASHBOARD.DATABASE_DESC',
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
