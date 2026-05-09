import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { StateService } from '../../services/state.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './header.component.html',
  styleUrl: './header.component.css'
})
export class HeaderComponent {
  constructor(public state: StateService, private authService: AuthService) {}

  get userName(): string {
    return this.authService.currentUser?.nom || 'User';
  }

  get userRole(): string {
    if (this.state.isCurrentUserAdmin) return 'Administrator';
    if (this.state.isCurrentUserSpecialiste) return 'Specialist Doctor';
    if (this.state.currentRole === 'mg') return 'General Practitioner';
    return 'Reception Agent';
  }

  get userInitials(): string {
    return this.userName
      .split(/[,\s]+/)
      .filter(n => n.length > 0)
      .map(n => n[0])
      .join('')
      .substring(0, 2)
      .toUpperCase();
  }

  get prefix(): string {
    return this.state.routePrefix;
  }
}
