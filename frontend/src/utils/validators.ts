// frontend/src/utils/validators.ts
/**
 * Validation utilities for forms and data
 */

import { toast } from "react-hot-toast";

/**
 * Validate phone number format
 */
export const validatePhoneNumber = (phone: string): boolean => {
    const phoneRegex = /^\+[1-9]\d{10,14}$/;
    return phoneRegex.test(phone);
};

/**
 * Format phone number for display
 */
export const formatPhoneNumber = (phone: string): string => {
    if (!phone.startsWith("+")) {
        return `+${phone}`;
    }
    return phone;
};

/**
 * Validate channel username format
 */
export const validateChannelUsername = (username: string): boolean => {
    const usernameRegex = /^@[a-zA-Z0-9_]{5,32}$/;
    return usernameRegex.test(username);
};

/**
 * Validate keyword format
 */
export const validateKeyword = (keyword: string): boolean => {
    return keyword.trim().length >= 1 && keyword.trim().length <= 100;
};

/**
 * Validate API credentials format
 */
export const validateApiCredentials = (apiId: string, apiHash: string): boolean => {
    const apiIdRegex = /^\d+$/;
    const apiHashRegex = /^[a-f0-9]{32}$/;

    return apiIdRegex.test(apiId) && apiHashRegex.test(apiHash);
};

/**
 * Sanitize input to prevent XSS
 */
export const sanitizeInput = (input: string): string => {
    const div = document.createElement("div");
    div.textContent = input;
    return div.innerHTML;
};

/**
 * Validate email format
 */
export const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
};

/**
 * Validate password strength
 */
export const validatePasswordStrength = (
    password: string
): {
    isValid: boolean;
    errors: string[];
} => {
    const errors: string[] = [];

    if (password.length < 8) {
        errors.push("Password must be at least 8 characters long");
    }

    if (!/[A-Z]/.test(password)) {
        errors.push("Password must contain at least one uppercase letter");
    }

    if (!/[a-z]/.test(password)) {
        errors.push("Password must contain at least one lowercase letter");
    }

    if (!/\d/.test(password)) {
        errors.push("Password must contain at least one number");
    }

    if (!/[!@#$%^&*]/.test(password)) {
        errors.push("Password must contain at least one special character");
    }

    return {
        isValid: errors.length === 0,
        errors,
    };
};

/**
 * Validate date range
 */
export const validateDateRange = (startDate: string, endDate: string): boolean => {
    const start = new Date(startDate);
    const end = new Date(endDate);

    return start <= end;
};

/**
 * Format validation error for display
 */
export const formatValidationError = (error: any): string => {
    if (error.response?.data?.errors) {
        return error.response.data.errors.map((err: any) => `${err.field}: ${err.message}`).join(", ");
    }

    if (error.response?.data?.detail) {
        return error.response.data.detail;
    }

    return "Validation failed";
};

/**
 * Show validation errors as toast notifications
 */
export const showValidationErrors = (errors: string[] | string): void => {
    if (Array.isArray(errors)) {
        errors.forEach((error) => {
            toast.error(error);
        });
    } else {
        toast.error(errors);
    }
};

/**
 * Validate file size
 */
export const validateFileSize = (file: File, maxSizeMB: number): boolean => {
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    return file.size <= maxSizeBytes;
};

/**
 * Validate file type
 */
export const validateFileType = (file: File, allowedTypes: string[]): boolean => {
    return allowedTypes.includes(file.type);
};

/**
 * Check if value is empty
 */
export const isEmpty = (value: any): boolean => {
    if (value === null || value === undefined) {
        return true;
    }

    if (typeof value === "string") {
        return value.trim().length === 0;
    }

    if (Array.isArray(value)) {
        return value.length === 0;
    }

    if (typeof value === "object") {
        return Object.keys(value).length === 0;
    }

    return false;
};

/**
 * Validate number range
 */
export const validateNumberRange = (value: number, min: number, max: number): { isValid: boolean; error?: string } => {
    if (isNaN(value)) {
        return { isValid: false, error: "Value must be a number" };
    }

    if (value < min) {
        return { isValid: false, error: `Value must be at least ${min}` };
    }

    if (value > max) {
        return { isValid: false, error: `Value must be at most ${max}` };
    }

    return { isValid: true };
};

/**
 * Debounce function for validating input
 */
export const debounceValidation = <T extends (...args: any[]) => any>(func: T, wait: number): ((...args: Parameters<T>) => void) => {
    let timeout: NodeJS.Timeout;

    return (...args: Parameters<T>) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), wait);
    };
};
