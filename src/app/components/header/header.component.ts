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
    return this.state.isCurrentUserMedecin ? 'Dr. Ahmed Ben Ali' : 'Agent Yassin';
  }

  get userRole(): string {
    return this.state.isCurrentUserMedecin ? 'Médecin Généraliste' : 'Agent d\'accueil';
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
    return this.state.isCurrentUserMedecin ? '/mg' : '/agent';
  }

  toggleRole() {
    const newPrefix = this.state.isCurrentUserMedecin ? '/agent/dashboard' : '/mg/dashboard';
    this.router.navigateByUrl(newPrefix);
  }
}
