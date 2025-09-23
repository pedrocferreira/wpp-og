import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable } from 'rxjs';
import { environment } from '../../environments/environment';

interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  is_online: boolean;
}

interface LoginResponse {
  user: User;
  token: string;
  refresh: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser$ = this.currentUserSubject.asObservable();

  constructor(
    private http: HttpClient,
    private router: Router
  ) {
    // Verifica se há um usuário logado ao inicializar
    this.checkCurrentUser();
  }

  get currentUser(): User | null {
    return this.currentUserSubject.value;
  }

  get isAuthenticated(): boolean {
    const token = localStorage.getItem('accessToken');
    if (!token) return false;

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Math.floor(Date.now() / 1000);
      const isValid = payload.exp > currentTime;
      
      // Se o token não é válido, limpa o localStorage
      if (!isValid) {
        this.clearSession();
      }
      
      return isValid;
    } catch {
      // Se há erro ao decodificar o token, limpa o localStorage
      this.clearSession();
      return false;
    }
  }

  login(credentials: { email: string; password: string }): Observable<LoginResponse> {
    return new Observable(observer => {
      this.http.post<LoginResponse>(`${environment.apiUrl}/auth/login/`, credentials)
        .subscribe({
          next: (response) => {
            this.setSession(response);
            observer.next(response);
            observer.complete();
          },
          error: (error) => {
            observer.error(error);
          }
        });
    });
  }

  register(userData: { name: string; email: string; password: string }): Observable<LoginResponse> {
    const { name, email, password } = userData;
    const [first_name, ...last_name_parts] = name.split(' ');
    const last_name = last_name_parts.join(' ');

    const registrationData = {
      email,
      password,
      first_name,
      last_name
    };

    return new Observable(observer => {
      this.http.post<LoginResponse>(`${environment.apiUrl}/auth/register/`, registrationData)
        .subscribe({
          next: (response) => {
            this.setSession(response);
            observer.next(response);
            observer.complete();
          },
          error: (error) => {
            observer.error(error);
          }
        });
    });
  }

  setupAdmin(): Observable<LoginResponse> {
    return new Observable(observer => {
      this.http.post<LoginResponse>(`${environment.apiUrl}/auth/setup_admin/`, {})
        .subscribe({
          next: (response) => {
            this.setSession(response);
            observer.next(response);
            observer.complete();
          },
          error: (error) => {
            observer.error(error);
          }
        });
    });
  }

  logout(): void {
    const refreshToken = localStorage.getItem('refreshToken');
    
    // Tenta fazer logout no backend
    if (refreshToken) {
      this.http.post(`${environment.apiUrl}/auth/logout/`, { refresh: refreshToken })
        .subscribe({
          complete: () => this.clearSession()
        });
    } else {
      this.clearSession();
    }
  }

  private setSession(response: LoginResponse): void {
    localStorage.setItem('accessToken', response.token);
    localStorage.setItem('refreshToken', response.refresh);
    this.currentUserSubject.next(response.user);
  }

  private clearSession(): void {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    this.currentUserSubject.next(null);
    this.router.navigate(['/login']);
  }

  private checkCurrentUser(): void {
    if (this.isAuthenticated) {
      // Busca dados do usuário atual
      this.http.get<User>(`${environment.apiUrl}/auth/me/`)
        .subscribe({
          next: (user) => {
            this.currentUserSubject.next(user);
          },
          error: () => {
            this.clearSession();
          }
        });
    }
  }
} 