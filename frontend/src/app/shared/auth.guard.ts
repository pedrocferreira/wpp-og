import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';

export const authGuard: CanActivateFn = (route, state) => {
  const router = inject(Router);

  const token = localStorage.getItem('accessToken');

  if (token) {
    // Aqui poderíamos adicionar uma lógica para validar o token com o backend
    return true;
  } else {
    // Redireciona para a página de login se não houver token
    router.navigate(['/login']);
    return false;
  }
}; 