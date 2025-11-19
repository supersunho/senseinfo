// frontend/src/types/api.ts
/**
 * API Response Type Definitions
 */

/**
 * Base API response interface
 */
export interface ApiResponse<T = any> {
    status: string;
    message: string;
    data: T;
    errors?: Array<{
        field: string;
        message: string;
    }>;
    meta?: {
        total: number;
        page: number;
        page_size: number;
        has_next: boolean;
        has_prev: boolean;
    };
}

/**
 * Paginated response interface
 */
export interface PaginatedResponse<T> extends ApiResponse<T> {
    meta: {
        total: number;
        page: number;
        page_size: number;
        has_next: boolean;
        has_prev: boolean;
    };
}

/**
 * Error response interface
 */
export interface ApiErrorResponse {
    detail: string;
    errors?: Array<{
        field: string;
        message: string;
    }>;
    status_code?: number;
}

/**
 * Validation error interface
 */
export interface ValidationError {
    field: string;
    message: string;
    type: string;
}

/**
 * Query parameters interface for list endpoints
 */
export interface ListQueryParams {
    skip?: number;
    limit?: number;
    include_inactive?: boolean;
    start_date?: string;
    end_date?: string;
    page?: number;
    page_size?: number;
}

/**
 * Sorting parameters interface
 */
export interface SortParams {
    sort_by?: string;
    sort_order?: "asc" | "desc";
}

/**
 * Filter parameters interface for messages
 */
export interface MessageFilterParams extends ListQueryParams {
    channel_id?: number;
    matched_keywords?: string;
    is_forwarded?: boolean;
}

/**
 * Filter parameters interface for channels
 */
export interface ChannelFilterParams extends ListQueryParams {
    is_active?: boolean;
    is_monitoring?: boolean;
}

/**
 * Filter parameters interface for keywords
 */
export interface KeywordFilterParams extends ListQueryParams {
    channel_id?: number;
    is_inclusion?: boolean;
    is_active?: boolean;
}

/**
 * Statistics query parameters
 */
export interface StatsQueryParams {
    days: number;
    channel_id?: number;
    group_by?: string;
}
