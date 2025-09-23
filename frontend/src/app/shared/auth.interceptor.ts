import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, switchMap, throwError } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const http = inject(HttpClient);
  const token = localStorage.getItem('accessToken');

  // Adiciona o token se disponível
  if (token) {
    const cloned = req.clone({
      headers: req.headers.set('Authorization', `Bearer ${token}`)
    });
    
    return next(cloned).pipe(
      catchError((error: HttpErrorResponse) => {
        // Se o token expirou (401), tenta renovar
        if (error.status === 401 && !req.url.includes('/auth/login/')) {
          return handleTokenRefresh(http, router).pipe(
            switchMap((newToken: string) => {
              // Retry da requisição original com o novo token
              const retryReq = req.clone({
                headers: req.headers.set('Authorization', `Bearer ${newToken}`)
              });
              return next(retryReq);
            }),
            catchError(() => {
              // Se o refresh falhou, redireciona para login
              localStorage.removeItem('accessToken');
              localStorage.removeItem('refreshToken');
              router.navigate(['/login']);
              return throwError(() => error);
            })
          );
        }
        return throwError(() => error);
      })
    );
  }

  return next(req);
};

function handleTokenRefresh(http: HttpClient, router: Router) {
  const refreshToken = localStorage.getItem('refreshToken');
  
  if (!refreshToken) {
    router.navigate(['/login']);
    return throwError(() => new Error('No refresh token'));
  }

  return http.post<any>(`${environment.apiUrl}/token/refresh/`, {
    refresh: refreshToken
  }).pipe(
    switchMap((response) => {
      localStorage.setItem('accessToken', response.access);
      return [response.access];
    }),
    catchError((error) => {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      router.navigate(['/login']);
      return throwError(() => error);
    })
  );
} 