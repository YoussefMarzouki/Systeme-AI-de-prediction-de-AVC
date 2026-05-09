import { Component, DoCheck } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { StateService } from '../../services/state.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
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
          { label: 'Dashboard', icon: 'dashboard', route: `${prefix}/dashboard` },
          { label: 'Patient Management', icon: 'patients', route: `${prefix}/patients` },
          { label: 'User Management', icon: 'admin', route: `${prefix}/users` }
        ];
        return;
      }

      const items = this.state.isCurrentUserSpecialiste
        ? [
            { label: 'Dashboard', icon: 'dashboard', route: `${prefix}/dashboard` },
            { label: 'Registration', icon: 'registration', route: `${prefix}/registration` },
            { label: 'Patient Intake', icon: 'intake', route: `${prefix}/intake` },
            { label: 'Validation Queue', icon: 'validation', route: `${prefix}/validation-queue` }
          ]
        : [
            { label: 'Dashboard', icon: 'dashboard', route: `${prefix}/dashboard` },
            { label: 'Registration', icon: 'registration', route: `${prefix}/registration` }
          ];

      if (this.state.isCurrentUserMedecin) {
        items.push({ label: 'Patient Intake', icon: 'intake', route: `${prefix}/intake` });
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
