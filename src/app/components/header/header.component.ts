import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './header.component.html',
  styleUrl: './header.component.css'
})
export class HeaderComponent {
  userName = 'Dr. Ahmed Ben Ali';
  userRole = 'Médecin Généraliste';

  get userInitials(): string {
    return this.userName
      .split(' ')
      .filter(n => n.length > 2)
      .map(n => n[0])
      .join('')
      .substring(0, 2)
      .toUpperCase();
  }
}
