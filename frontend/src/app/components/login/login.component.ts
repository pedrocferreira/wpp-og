import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { AuthService } from '../../services/auth.service';
import { ToastService } from '../../services/toast.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatIconModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit {
  isSignUp: boolean = false;
  
  // Form fields
  name: string = '';
  email: string = '';
  password: string = '';
  
  hidePassword: boolean = true;
  isLoading: boolean = false;

  constructor(
    private authService: AuthService,
    private router: Router,
    private toastService: ToastService
  ) {}

  ngOnInit(): void {
    // Verificar se já está logado
    if (this.authService.isAuthenticated) {
      this.router.navigate(['/dashboard']);
    }
  }

  onLogin(): void {
    if (!this.email || !this.password) {
      this.toastService.warning('Por favor, preencha e-mail e senha.');
      return;
    }
    this.isLoading = true;
    this.authService.login({ email: this.email, password: this.password }).subscribe({
      next: () => {
        this.toastService.success('Login realizado com sucesso!');
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.isLoading = false;
        this.toastService.error(err?.error?.detail || 'Credenciais inválidas.');
      }
    });
  }

  onSignUp(): void {
    if (!this.name || !this.email || !this.password) {
      this.toastService.warning('Por favor, preencha todos os campos para criar a conta.');
      return;
    }
    this.isLoading = true;
    this.authService.register({ name: this.name, email: this.email, password: this.password }).subscribe({
      next: () => {
        this.toastService.success('Conta criada com sucesso! Bem-vindo(a)!');
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.isLoading = false;
        this.toastService.error(err?.error?.detail || 'Não foi possível criar a conta.');
      }
    });
  }

  togglePasswordVisibility(): void {
    this.hidePassword = !this.hidePassword;
  }
}
