// frontend/src/types/models.ts
/**
 * Data Model Type Definitions
 */

/**
 * User model
 */
export interface User {
    id: number;
    telegram_id: number;
    phone_number: string;
    first_name?: string;
    last_name?: string;
    username?: string;
    is_authenticated: boolean;
    is_active: boolean;
    is_admin: boolean;
    created_at: string;
    updated_at?: string;
    last_auth_date?: string;
    message_count_today: number;
    last_message_date?: string;
}

/**
 * Channel model
 */
export interface Channel {
    id: number;
    username: string;
    title: string;
    description?: string;
    is_active: boolean;
    is_monitoring: boolean;
    joined_at: string;
    last_message_id: number;
    message_count: number;
    total_messages_processed: number;
    user_id: number;
}

/**
 * Channel list response
 */
export interface ChannelListResponse {
    channels: Channel[];
    total: number;
}

/**
 * Channel create request
 */
export interface ChannelCreateRequest {
    username: string;
}

/**
 * Channel statistics
 */
export interface ChannelStats {
    channel_id: number;
    period_days: number;
    total_messages: number;
    total_views: number;
    total_forwards: number;
    unique_senders: number;
    average_views_per_message: number;
    average_forwards_per_message: number;
}

/**
 * Keyword model
 */
export interface Keyword {
    id: number;
    word: string;
    is_inclusion: boolean;
    is_active: boolean;
    created_at: string;
    channel_id: number;
}

/**
 * Keyword list response
 */
export interface KeywordListResponse {
    keywords: Keyword[];
    total: number;
}

/**
 * Keyword create request
 */
export interface KeywordCreateRequest {
    channel_id: number;
    word: string;
    is_inclusion: boolean;
}

/**
 * Message model
 */
export interface Message {
    id: number;
    telegram_message_id: number;
    text?: string;
    raw_text?: string;
    sender_id?: number;
    sender_username?: string;
    sender_first_name?: string;
    sender_last_name?: string;
    media_type?: string;
    file_hash?: string;
    message_date: string;
    edit_date?: string;
    views: number;
    forwards: number;
    is_forwarded: boolean;
    forwarded_at?: string;
    forward_destination?: string;
    matched_keywords?: string[];
    channel_id: number;
}

/**
 * Message list response
 */
export interface MessageListResponse {
    messages: Message[];
    total: number;
    page: number;
    page_size: number;
}

/**
 * Message statistics
 */
export interface MessageStats {
    period_days: number;
    total_messages: number;
    forwarded_messages: number;
    keyword_matches: number;
    channel_breakdown: Record<string, number>;
    average_per_day: number;
}

/**
 * System status
 */
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

/**
 * Auth response
 */
export interface AuthResponse {
    status: "code_sent" | "authenticated" | "2fa_required";
    message: string;
    requires_2fa: boolean;
    user_id?: number;
}

/**
 * Telegram API credentials
 */
export interface TelegramCredentials {
    api_id: string;
    api_hash: string;
}

/**
 * Auth verification request
 */
export interface AuthVerificationRequest {
    phone_number: string;
    phone_code_hash: string;
    code: string;
    api_id?: string;
    api_hash?: string;
}

/**
 * 2FA verification request
 */
export interface TwoFARequest {
    phone_number: string;
    password: string;
}

/**
 * Paginated query result
 */
export interface PaginatedResult<T> {
    items: T[];
    total: number;
    page: number;
    page_size: number;
    has_next: boolean;
    has_prev: boolean;
}

/**
 * Sort order
 */
export type SortOrder = "asc" | "desc";

/**
 * Toast notification types
 */
export type ToastType = "success" | "error" | "warning" | "info";
