// frontend/src/services/keywordService.ts
import api from "./api";
import { ApiResponse } from "./api";
import { Keyword, KeywordListResponse, KeywordCreateRequest } from "../types/models";

class KeywordService {
    /**
     * Get all keywords for user's channels
     */
    async getAll(channelId?: number, includeInactive: boolean = false, skip: number = 0, limit: number = 100): Promise<KeywordListResponse> {
        const params = new URLSearchParams({
            include_inactive: includeInactive.toString(),
            skip: skip.toString(),
            limit: limit.toString(),
        });

        if (channelId) {
            params.append("channel_id", channelId.toString());
        }

        const response = await api.get<ApiResponse<KeywordListResponse>>(`/keywords?${params.toString()}`);
        return response.data.data;
    }

    /**
     * Get keywords for a specific channel
     */
    async getByChannelId(channelId: number): Promise<KeywordListResponse> {
        return this.getAll(channelId);
    }

    /**
     * Add a new keyword
     */
    async addKeyword(data: KeywordCreateRequest): Promise<Keyword> {
        const response = await api.post<ApiResponse<Keyword>>("/keywords", data);
        return response.data.data;
    }

    /**
     * Delete (deactivate) a keyword
     */
    async deleteKeyword(keywordId: number): Promise<void> {
        await api.delete(`/keywords/${keywordId}`);
    }

    /**
     * Toggle keyword active status
     */
    async toggleKeyword(keywordId: number): Promise<Keyword> {
        const response = await api.put<ApiResponse<Keyword>>(`/keywords/${keywordId}/toggle`);
        return response.data.data;
    }

    /**
     * Update keyword (partial update)
     */
    async updateKeyword(keywordId: number, updates: Partial<KeywordCreateRequest>): Promise<Keyword> {
        const response = await api.patch<ApiResponse<Keyword>>(`/keywords/${keywordId}`, updates);
        return response.data.data;
    }
}

export default new KeywordService();
