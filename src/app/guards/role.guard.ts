import { inject } from '@angular/core';
import { CanActivateChildFn, CanActivateFn, Router } from '@angular/router';
import { AuthService, type AppRole } from '../services/auth.service';

function checkRole(allowedRoles: AppRole[]) {
  const authService = inject(AuthService);
  const router = inject(Router);
  const currentRole = authService.currentRoleKey;

  if (allowedRoles.includes(currentRole)) {
    return true;
  }

  return router.createUrlTree([authService.getLandingRoute()]);
}

export const roleGuard: CanActivateFn = (route) => {
  const allowedRoles = (route.data?.['roles'] || []) as AppRole[];
  return checkRole(allowedRoles);
};

export const roleChildGuard: CanActivateChildFn = (route) => {
  const allowedRoles = (route.parent?.data?.['roles'] || route.data?.['roles'] || []) as AppRole[];
  return checkRole(allowedRoles);
};
