import { Component, DoCheck } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { StateService } from '../../services/state.service';
import { AuthService } from '../../services/auth.service';

import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, TranslateModule],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.css'
})
export class SidebarComponent implements DoCheck {
  navItems: any[] = [];
  private lastPrefix = '';

  constructor(public state: StateService, private authService: AuthService) {}

  ngDoCheck() {
    const prefix = this.state.routePrefix;
    if (this.lastPrefix !== prefix || this.navItems.length === 0) {
      this.lastPrefix = prefix;

      if (this.state.isCurrentUserAdmin) {
        this.navItems = [
          { label: 'SIDEBAR.DASHBOARD', icon: 'dashboard', route: `${prefix}/dashboard` },
          { label: 'SIDEBAR.PATIENT_MANAGEMENT', icon: 'patients', route: `${prefix}/patients` },
          { label: 'SIDEBAR.USER_MANAGEMENT', icon: 'admin', route: `${prefix}/users` }
        ];
        return;
      }

      const items = this.state.isCurrentUserSpecialiste
        ? [
            { label: 'SIDEBAR.DASHBOARD', icon: 'dashboard', route: `${prefix}/dashboard` },
            { label: 'SIDEBAR.REGISTRATION', icon: 'registration', route: `${prefix}/registration` },
            { label: 'SIDEBAR.PATIENT_INTAKE', icon: 'intake', route: `${prefix}/intake` },
            { label: 'SIDEBAR.VALIDATION_QUEUE', icon: 'validation', route: `${prefix}/validation-queue` }
          ]
        : [
            { label: 'SIDEBAR.DASHBOARD', icon: 'dashboard', route: `${prefix}/dashboard` },
            { label: 'SIDEBAR.REGISTRATION', icon: 'registration', route: `${prefix}/registration` }
          ];

      if (this.state.isCurrentUserMedecin) {
        items.push({ label: 'SIDEBAR.PATIENT_INTAKE', icon: 'intake', route: `${prefix}/intake` });
      }

      this.navItems = items;
    }
  }

  trackByRoute(index: number, item: any): string {
    return item.route;
  }

  logout(event: Event): void {
    event.preventDefault();
    this.authService.logout();
  }
}
