// frontend/src/services/api.ts
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from "axios";
import { toast } from "react-hot-toast";

// API response interface
export interface ApiResponse<T = any> {
    status: string;
    message?: string;
    data: T;
    errors?: Array<{
        field: string;
        message: string;
    }>;
}

// API error interface
export interface ApiError {
    response?: {
        data: {
            detail: string;
            errors?: Array<{
                field: string;
                message: string;
            }>;
        };
        status: number;
    };
    message: string;
}

// Create axios instance with named export
export const api: AxiosInstance = axios.create({
    baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api",
    timeout: 10000,
    headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
    },
});

// Request interceptor
api.interceptors.request.use(
    (config: AxiosRequestConfig): AxiosRequestConfig => {
        // Add auth token if exists
        const token = localStorage.getItem("auth_token");
        if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        // Log request in development
        if (import.meta.env.DEV) {
            console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`);
        }

        return config;
    },
    (error: AxiosError): Promise<AxiosError> => {
        return Promise.reject(error);
    }
);

// Response interceptor
api.interceptors.response.use(
    (response: AxiosResponse): AxiosResponse => {
        // Log response in development
        if (import.meta.env.DEV) {
            console.log(`[API Response] ${response.status} ${response.config.url}`);
        }

        return response;
    },
    (error: AxiosError<ApiError>): Promise<AxiosError> => {
        // Handle error responses
        const { response } = error;

        if (response) {
            const { status, data } = response;

            // Log error in development
            if (import.meta.env.DEV) {
                console.error(`[API Error] ${status} ${error.config?.url}:`, data);
            }

            // Handle specific error cases
            switch (status) {
                case 401:
                    // Unauthorized - clear auth and redirect to login
                    localStorage.removeItem("auth_token");
                    localStorage.removeItem("telegram_api_id");
                    localStorage.removeItem("telegram_api_hash");
                    window.location.href = "/setup";
                    break;

                case 403:
                    toast.error("Access forbidden");
                    break;

                case 404:
                    toast.error("Resource not found");
                    break;

                case 422:
                    // Validation errors
                    if (data.errors) {
                        data.errors.forEach((err) => {
                            toast.error(`${err.field}: ${err.message}`);
                        });
                    } else {
                        toast.error(data.detail || "Validation error");
                    }
                    break;

                case 429:
                    toast.error("Too many requests. Please wait.");
                    break;

                case 500:
                    toast.error("Server error. Please try again later.");
                    break;

                default:
                    toast.error(data.detail || "An unexpected error occurred");
            }
        } else {
            // Network error
            toast.error("Network error. Please check your connection.");
        }

        return Promise.reject(error);
    }
);

// Default export for backward compatibility
export default api;
