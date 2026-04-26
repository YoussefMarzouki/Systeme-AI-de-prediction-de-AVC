import { Component, DoCheck } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { StateService } from '../../services/state.service';

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

  constructor(public state: StateService) {}

  ngDoCheck() {
    const prefix = this.state.isCurrentUserMedecin ? '/mg' : '/agent';
    if (this.lastPrefix !== prefix || this.navItems.length === 0) {
      this.lastPrefix = prefix;
      const items = [
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
}
