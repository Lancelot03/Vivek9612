import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Constants from 'expo-constants';

const EXPO_PUBLIC_BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

export interface User {
  employeeId: string;
  employeeName: string;
  cadre: string;
  projectName: string;
  role: 'admin' | 'invitee';
  isFirstLogin: boolean;
  mustChangePassword: boolean;
  officeType?: string;
  permissions: string[];
  lastLogin?: string;
}

export interface LoginCredentials {
  employeeCode: string;
  password: string;
}

export interface ChangePasswordData {
  employeeCode: string;
  oldPassword: string;
  newPassword: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

class AuthService {
  private static instance: AuthService;
  private token: string | null = null;
  private user: User | null = null;

  private constructor() {}

  public static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
      }

      const authData: AuthResponse = await response.json();
      
      // Store token and user data
      await this.storeAuthData(authData);
      
      return authData;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  async changePassword(passwordData: ChangePasswordData): Promise<void> {
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/auth/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(passwordData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Password change failed');
      }
    } catch (error) {
      console.error('Password change error:', error);
      throw error;
    }
  }

  async setOfficeType(employeeCode: string, officeType: string): Promise<void> {
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/auth/set-office-type`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          employeeCode,
          officeType,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to set office type');
      }
    } catch (error) {
      console.error('Set office type error:', error);
      throw error;
    }
  }

  async getCurrentUser(): Promise<User | null> {
    try {
      const token = await this.getToken();
      if (!token) {
        return null;
      }

      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        // Token might be invalid, clear stored data
        await this.logout();
        return null;
      }

      const userData: User = await response.json();
      this.user = userData;
      await AsyncStorage.setItem('user', JSON.stringify(userData));
      
      return userData;
    } catch (error) {
      console.error('Get current user error:', error);
      return null;
    }
  }

  async logout(): Promise<void> {
    try {
      const token = await this.getToken();
      
      if (token) {
        // Notify server about logout
        await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local storage regardless of server response
      await this.clearAuthData();
    }
  }

  async getToken(): Promise<string | null> {
    if (this.token) {
      return this.token;
    }

    try {
      this.token = await AsyncStorage.getItem('auth_token');
      return this.token;
    } catch (error) {
      console.error('Get token error:', error);
      return null;
    }
  }

  async getUser(): Promise<User | null> {
    if (this.user) {
      return this.user;
    }

    try {
      const userString = await AsyncStorage.getItem('user');
      if (userString) {
        this.user = JSON.parse(userString);
        return this.user;
      }
    } catch (error) {
      console.error('Get user error:', error);
    }

    return null;
  }

  async isAuthenticated(): Promise<boolean> {
    const token = await this.getToken();
    const user = await this.getUser();
    return !!(token && user);
  }

  async hasPermission(permission: string): Promise<boolean> {
    const user = await this.getUser();
    return user?.permissions.includes(permission) || false;
  }

  async isAdmin(): Promise<boolean> {
    const user = await this.getUser();
    return user?.role === 'admin';
  }

  async isFirstLogin(): Promise<boolean> {
    const user = await this.getUser();
    return user?.isFirstLogin || false;
  }

  async mustChangePassword(): Promise<boolean> {
    const user = await this.getUser();
    return user?.mustChangePassword || false;
  }

  private async storeAuthData(authData: AuthResponse): Promise<void> {
    try {
      await AsyncStorage.setItem('auth_token', authData.access_token);
      await AsyncStorage.setItem('user', JSON.stringify(authData.user));
      
      this.token = authData.access_token;
      this.user = authData.user;
    } catch (error) {
      console.error('Store auth data error:', error);
      throw new Error('Failed to store authentication data');
    }
  }

  private async clearAuthData(): Promise<void> {
    try {
      await AsyncStorage.multiRemove(['auth_token', 'user']);
      this.token = null;
      this.user = null;
    } catch (error) {
      console.error('Clear auth data error:', error);
    }
  }

  async getAuthHeaders(): Promise<Record<string, string>> {
    const token = await this.getToken();
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }

  async makeAuthenticatedRequest(
    url: string, 
    options: RequestInit = {}
  ): Promise<Response> {
    const headers = await this.getAuthHeaders();
    
    const response = await fetch(url, {
      ...options,
      headers: {
        ...headers,
        ...options.headers,
      },
    });

    // If unauthorized, clear auth data and redirect to login
    if (response.status === 401) {
      await this.logout();
      throw new Error('Authentication required');
    }

    return response;
  }
}

export default AuthService;