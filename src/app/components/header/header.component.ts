import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { StateService } from '../../services/state.service';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './header.component.html',
  styleUrl: './header.component.css'
})
export class HeaderComponent {
  constructor(public state: StateService, private router: Router) {}

  get userName(): string {
    if (this.state.isCurrentUserSpecialiste) return 'Dr. Khemiri Youssef';
    if (this.state.isCurrentUserMedecin) return 'Dr. Mansour Leila';
    return 'Agent Yassin';
  }

  get userRole(): string {
    if (this.state.isCurrentUserSpecialiste) return 'Medecin Specialiste';
    if (this.state.isCurrentUserMedecin) return 'Medecin Generaliste';
    return 'Agent d\'accueil';
  }

  get userInitials(): string {
    return this.userName
      .split(' ')
      .filter(n => n.length > 0)
      .map(n => n[0])
      .join('')
      .substring(0, 2)
      .toUpperCase();
  }

  get prefix(): string {
    return this.state.routePrefix;
  }

  toggleRole() {
    if (this.state.currentRole === 'agent') {
      this.router.navigateByUrl('/mg/dashboard');
    } else if (this.state.currentRole === 'mg') {
      this.router.navigateByUrl('/ms/validation-queue');
    } else {
      this.router.navigateByUrl('/agent/dashboard');
    }
  }
}
