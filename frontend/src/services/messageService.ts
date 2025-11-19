// frontend/src/services/messageService.ts
import api from "./api";
import { ApiResponse } from "./api";
import { MessageListResponse, MessageStats } from "../types/models";

class MessageService {
    /**
     * Get messages with filtering options
     */
    async getMessages(
        page: number = 1,
        pageSize: number = 50,
        filters?: {
            channelId?: number;
            startDate?: string;
            endDate?: string;
            matchedKeywords?: string;
            isForwarded?: boolean;
        }
    ): Promise<MessageListResponse> {
        const params = new URLSearchParams({
            page: page.toString(),
            page_size: pageSize.toString(),
        });

        if (filters) {
            if (filters.channelId) {
                params.append("channel_id", filters.channelId.toString());
            }
            if (filters.startDate) {
                params.append("start_date", filters.startDate);
            }
            if (filters.endDate) {
                params.append("end_date", filters.endDate);
            }
            if (filters.matchedKeywords) {
                params.append("matched_keywords", filters.matchedKeywords);
            }
            if (filters.isForwarded !== undefined) {
                params.append("is_forwarded", filters.isForwarded.toString());
            }
        }

        const response = await api.get<ApiResponse<MessageListResponse>>(`/messages?${params.toString()}`);
        return response.data.data;
    }

    /**
     * Get message statistics
     */
    async getStats(days: number = 7): Promise<MessageStats> {
        const params = new URLSearchParams({
            days: days.toString(),
        });

        const response = await api.get<ApiResponse<MessageStats>>(`/messages/stats?${params.toString()}`);
        return response.data.data;
    }

    /**
     * Delete a message
     */
    async deleteMessage(messageId: number): Promise<void> {
        await api.delete(`/messages/${messageId}`);
    }

    /**
     * Get message by ID
     */
    async getMessageById(messageId: number): Promise<any> {
        // Note: This endpoint might need to be implemented in backend
        const response = await api.get<ApiResponse>(`/messages/${messageId}`);
        return response.data.data;
    }

    /**
     * Get recent messages (last N messages)
     */
    async getRecentMessages(limit: number = 10): Promise<MessageListResponse> {
        return this.getMessages(1, limit);
    }

    /**
     * Get messages by channel
     */
    async getMessagesByChannel(channelId: number, page: number = 1, pageSize: number = 50): Promise<MessageListResponse> {
        return this.getMessages(page, pageSize, { channelId });
    }

    /**
     * Search messages by keyword
     */
    async searchMessages(query: string, limit: number = 50): Promise<MessageListResponse> {
        return this.getMessages(1, limit, { matchedKeywords: query });
    }
}

export default new MessageService();
