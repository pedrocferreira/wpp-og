import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  action?: {
    label: string;
    callback: () => void;
  };
}

@Injectable({
  providedIn: 'root'
})
export class ToastService {
  private toastsSubject = new BehaviorSubject<Toast[]>([]);
  public toasts$ = this.toastsSubject.asObservable();

  private generateId(): string {
    return Math.random().toString(36).substr(2, 9);
  }

  success(title: string, message?: string, duration: number = 5000): void {
    this.show({
      type: 'success',
      title,
      message,
      duration
    });
  }

  error(title: string, message?: string, duration: number = 7000): void {
    this.show({
      type: 'error',
      title,
      message,
      duration
    });
  }

  warning(title: string, message?: string, duration: number = 6000): void {
    this.show({
      type: 'warning',
      title,
      message,
      duration
    });
  }

  info(title: string, message?: string, duration: number = 5000): void {
    this.show({
      type: 'info',
      title,
      message,
      duration
    });
  }

  show(toast: Omit<Toast, 'id'>): void {
    const newToast: Toast = {
      ...toast,
      id: this.generateId()
    };

    const currentToasts = this.toastsSubject.value;
    this.toastsSubject.next([...currentToasts, newToast]);

    if (toast.duration && toast.duration > 0) {
      setTimeout(() => {
        this.remove(newToast.id);
      }, toast.duration);
    }
  }

  remove(id: string): void {
    const currentToasts = this.toastsSubject.value;
    const updatedToasts = currentToasts.filter(toast => toast.id !== id);
    this.toastsSubject.next(updatedToasts);
  }

  clear(): void {
    this.toastsSubject.next([]);
  }
} 