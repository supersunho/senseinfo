// frontend/src/services/authService.ts
import api from "./api";
import { ApiResponse } from "./api";
import { User } from "../types/models";

export interface AuthStartRequest {
    phone_number: string;
}

export interface AuthVerifyRequest {
    phone_number: string;
    phone_code_hash: string;
    code: string;
    api_id?: string;
    api_hash?: string;
}

export interface AuthPasswordRequest {
    phone_number: string;
    password: string;
}

export interface AuthResponse {
    status: "code_sent" | "authenticated" | "2fa_required";
    message: string;
    requires_2fa: boolean;
    user_id?: number;
}

export interface SystemStatus {
    database: {
        status: string;
        latency_ms?: number;
        error?: string;
    };
    redis: {
        status: string;
        error?: string;
        info?: any;
    };
    telegram: {
        status: string;
        api_id_configured: boolean;
        api_hash_configured: boolean;
    };
    clients: {
        active_count: number;
        status: string;
    };
    overall: {
        status: string;
        healthy_components: number;
        total_components: number;
    };
}

class AuthService {
    /**
     * Start Telegram authentication by sending verification code
     */
    async startAuth(phoneNumber: string): Promise<AuthResponse> {
        const response = await api.post<ApiResponse<AuthResponse>>("/auth/telegram/start", {
            phone_number: phoneNumber,
        });
        return response.data.data;
    }

    /**
     * Verify Telegram code and complete authentication
     */
    async verifyCode(data: AuthVerifyRequest): Promise<AuthResponse> {
        const response = await api.post<ApiResponse<AuthResponse>>("/auth/telegram/verify", data);

        if (response.data.data.status === "authenticated" && response.data.data.user_id) {
            // Store auth token if provided
            const token = response.headers["authorization"];
            if (token) {
                localStorage.setItem("auth_token", token.replace("Bearer ", ""));
            }
        }

        return response.data.data;
    }

    /**
     * Verify 2FA password
     */
    async verify2FA(data: AuthPasswordRequest): Promise<AuthResponse> {
        const response = await api.post<ApiResponse<AuthResponse>>("/auth/telegram/2fa", data);

        if (response.data.data.status === "authenticated") {
            // Store auth token if provided
            const token = response.headers["authorization"];
            if (token) {
                localStorage.setItem("auth_token", token.replace("Bearer ", ""));
            }
        }

        return response.data.data;
    }

    /**
     * Logout user
     */
    async logout(): Promise<void> {
        await api.post("/auth/logout");
        this.clearAuthData();
    }

    /**
     * Clear all authentication data
     */
    clearAuthData(): void {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("telegram_api_id");
        localStorage.removeItem("telegram_api_hash");
        localStorage.removeItem("user_data");
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated(): boolean {
        return !!localStorage.getItem("auth_token");
    }

    /**
     * Get stored API credentials
     */
    getApiCredentials(): { apiId: string | null; apiHash: string | null } {
        return {
            apiId: localStorage.getItem("telegram_api_id"),
            apiHash: localStorage.getItem("telegram_api_hash"),
        };
    }

    /**
     * Store API credentials
     */
    storeApiCredentials(apiId: string, apiHash: string): void {
        localStorage.setItem("telegram_api_id", apiId);
        localStorage.setItem("telegram_api_hash", apiHash);
    }

    /**
     * Get system status
     */
    async getSystemStatus(): Promise<SystemStatus> {
        const response = await api.get<ApiResponse<SystemStatus>>("/system/status");
        return response.data.data;
    }

    /**
     * Initialize database
     */
    async initDatabase(): Promise<{ status: string; message: string }> {
        const response = await api.post<ApiResponse>("/system/init-db");
        return response.data;
    }
}

export default new AuthService();
