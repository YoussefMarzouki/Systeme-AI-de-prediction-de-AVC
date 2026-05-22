import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { UtilisateurService } from '../../services/utilisateur.service';
import { Utilisateur } from '../../models/utilisateur.model';
import { AuthService } from '../../services/auth.service';

import { TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-admin',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslateModule],
  templateUrl: './admin.component.html',
  styleUrl: './admin.component.css'
})
export class AdminComponent implements OnInit {
  users: Utilisateur[] = [];
  filteredUsers: Utilisateur[] = [];
  searchQuery = '';
  activeFilter = 'all';
  isLoading = true;

  showModal = false;
  showDeleteConfirm = false;
  isEditing = false;
  deleteTargetId = '';
  deleteTargetName = '';

  formData = {
    nom: '',
    email: '',
    motDePasse: '',
    type: 'medecin',
    etat: 'actif',
    specialiste: false
  };
  editingId = '';
  formError = '';

  constructor(
    private utilisateurService: UtilisateurService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.loadUsers();
  }

  loadUsers(): void {
    this.isLoading = true;
    this.utilisateurService.list().subscribe({
      next: (res) => {
        this.users = res.utilisateurs;
        this.applyFilters();
        this.isLoading = false;
      },
      error: () => {
        this.isLoading = false;
      }
    });
  }

  applyFilters(): void {
    let result = this.users;
    if (this.activeFilter !== 'all') {
      result = result.filter(u => u.type === this.activeFilter);
    }
    if (this.searchQuery.trim()) {
      const q = this.searchQuery.toLowerCase();
      result = result.filter(u =>
        u.nom.toLowerCase().includes(q) || u.email.toLowerCase().includes(q)
      );
    }
    this.filteredUsers = result;
  }

  onSearchChange(): void {
    this.applyFilters();
  }

  setFilter(filter: string): void {
    this.activeFilter = filter;
    this.applyFilters();
  }

  getRoleBadgeClass(type: string): string {
    switch (type) {
      case 'medecin': return 'badge-medecin';
      case 'agent_accueil': return 'badge-agent';
      case 'admin': return 'badge-admin';
      default: return 'badge-default';
    }
  }

  getRoleLabel(type: string): string {
    switch (type) {
      case 'medecin': return 'USER_MANAGEMENT.DOCTOR';
      case 'agent_accueil': return 'USER_MANAGEMENT.RECEPTION_AGENT';
      case 'admin': return 'USER_MANAGEMENT.ADMINISTRATOR';
      default: return type;
    }
  }

  openAddModal(): void {
    this.isEditing = false;
    this.editingId = '';
    this.formData = { nom: '', email: '', motDePasse: '', type: 'medecin', etat: 'actif', specialiste: false };
    this.formError = '';
    this.showModal = true;
  }

  openEditModal(user: Utilisateur): void {
    this.isEditing = true;
    this.editingId = user.id || '';
    this.formData = {
      nom: user.nom,
      email: user.email,
      motDePasse: '',
      type: user.type,
      etat: user.etat,
      specialiste: (user as any).specialiste || false
    };
    this.formError = '';
    this.showModal = true;
  }

  closeModal(): void {
    this.showModal = false;
  }

  submitForm(): void {
    this.formError = '';
    if (!this.formData.nom || !this.formData.email) {
      this.formError = 'Name and email are required.';
      return;
    }
    if (!this.isEditing && !this.formData.motDePasse) {
      this.formError = 'Password is required for new users.';
      return;
    }

    const payload: any = { ...this.formData };
    if (this.isEditing && !payload.motDePasse) {
      delete payload.motDePasse;
    }

    if (this.isEditing) {
      this.utilisateurService.update(this.editingId, payload).subscribe({
        next: () => { this.closeModal(); this.loadUsers(); },
        error: (err) => { this.formError = err.error?.error || 'Update failed.'; }
      });
    } else {
      this.utilisateurService.create(payload).subscribe({
        next: () => { this.closeModal(); this.loadUsers(); },
        error: (err) => { this.formError = err.error?.error || 'Creation failed.'; }
      });
    }
  }

  isCurrentUser(user: Utilisateur): boolean {
    return !!user.id && user.id === this.authService.currentUser?.id;
  }

  confirmDelete(user: Utilisateur): void {
    if (this.isCurrentUser(user)) {
      return;
    }
    this.deleteTargetId = user.id || '';
    this.deleteTargetName = user.nom;
    this.showDeleteConfirm = true;
  }

  cancelDelete(): void {
    this.showDeleteConfirm = false;
  }

  executeDelete(): void {
    this.utilisateurService.delete(this.deleteTargetId).subscribe({
      next: () => { this.showDeleteConfirm = false; this.loadUsers(); },
      error: () => { this.showDeleteConfirm = false; }
    });
  }
}

