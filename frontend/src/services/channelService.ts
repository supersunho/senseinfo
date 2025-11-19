// frontend/src/services/channelService.ts
import api from "./api";
import { ApiResponse } from "./api";
import { Channel, ChannelListResponse, ChannelCreateRequest } from "../types/models";

class ChannelService {
    /**
     * Get all channels for the authenticated user
     */
    async getAll(skip: number = 0, limit: number = 100, includeInactive: boolean = false): Promise<ChannelListResponse> {
        const params = new URLSearchParams({
            skip: skip.toString(),
            limit: limit.toString(),
            include_inactive: includeInactive.toString(),
        });

        const response = await api.get<ApiResponse<ChannelListResponse>>(`/channels?${params.toString()}`);
        return response.data.data;
    }

    /**
     * Get a specific channel by ID
     */
    async getById(channelId: number): Promise<Channel> {
        const response = await api.get<ApiResponse<Channel>>(`/channels/${channelId}`);
        return response.data.data;
    }

    /**
     * Add a new channel
     */
    async addChannel(username: string): Promise<Channel> {
        const response = await api.post<ApiResponse<Channel>>("/channels", {
            username: username,
        });
        return response.data.data;
    }

    /**
     * Remove (leave) a channel
     */
    async removeChannel(channelId: number): Promise<void> {
        await api.delete(`/channels/${channelId}`);
    }

    /**
     * Toggle channel monitoring status
     */
    async toggleMonitoring(channelId: number): Promise<Channel> {
        const response = await api.put<ApiResponse<Channel>>(`/channels/${channelId}/toggle`);
        return response.data.data;
    }

    /**
     * Get channel statistics
     */
    async getStats(channelId: number, days: number = 7): Promise<any> {
        const params = new URLSearchParams({
            days: days.toString(),
        });

        const response = await api.get<ApiResponse>(`/channels/${channelId}/stats?${params.toString()}`);
        return response.data.data;
    }
}

export default new ChannelService();
