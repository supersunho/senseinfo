// frontend/src/pages/Dashboard.tsx
import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/common/Card";
import { Button } from "../components/common/Button";
import { Header } from "../components/layout/Header";
import { api } from "../services/api";
import { toast } from "react-hot-toast";
import { Activity, MessageSquare, Users, TrendingUp, Eye, Share2 } from "lucide-react";

interface DashboardStats {
    total_messages: number;
    total_channels: number;
    total_keywords: number;
    forwarded_messages: number;
    period_days: number;
    average_per_day: number;
}

interface RecentMessage {
    id: number;
    text: string;
    channel_title: string;
    message_date: string;
    matched_keywords: string[];
}

export const Dashboard: React.FC = () => {
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [recentMessages, setRecentMessages] = useState<RecentMessage[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadDashboardData();
    }, []);

    const loadDashboardData = async () => {
        try {
            setLoading(true);

            // Get stats
            const statsResponse = await api.get("/messages/stats?days=7");
            setStats(statsResponse.data);

            // Get recent messages
            const messagesResponse = await api.get("/messages?page=1&page_size=5");
            setRecentMessages(messagesResponse.data.messages);
        } catch (error) {
            toast.error("Failed to load dashboard data");
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString();
    };

    const truncateText = (text: string, maxLength: number) => {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + "...";
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="w-12 h-12 border-b-2 rounded-full animate-spin border-primary"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background">
            <Header title="Dashboard" />

            <main className="container px-4 py-8 mx-auto md:px-6">
                {/* Stats Grid */}
                <div className="grid gap-4 mb-8 md:grid-cols-2 lg:grid-cols-4">
                    <Card>
                        <CardContent className="p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-medium text-muted-foreground">Total Messages</p>
                                    <p className="text-2xl font-bold">{stats?.total_messages || 0}</p>
                                </div>
                                <MessageSquare className="w-8 h-8 text-muted-foreground" />
                            </div>
                            <div className="flex items-center mt-2 text-xs text-muted-foreground">
                                <TrendingUp className="w-3 h-3 mr-1 text-green-500" />
                                Last 7 days
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardContent className="p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-medium text-muted-foreground">Active Channels</p>
                                    <p className="text-2xl font-bold">{stats?.total_channels || 0}</p>
                                </div>
                                <Users className="w-8 h-8 text-muted-foreground" />
                            </div>
                            <div className="flex items-center mt-2 text-xs text-muted-foreground">
                                <Activity className="w-3 h-3 mr-1 text-blue-500" />
                                Monitoring
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardContent className="p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-medium text-muted-foreground">Keywords</p>
                                    <p className="text-2xl font-bold">{stats?.total_keywords || 0}</p>
                                </div>
                                <Eye className="w-8 h-8 text-muted-foreground" />
                            </div>
                            <div className="flex items-center mt-2 text-xs text-muted-foreground">Active filters</div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardContent className="p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-medium text-muted-foreground">Forwarded</p>
                                    <p className="text-2xl font-bold">{stats?.forwarded_messages || 0}</p>
                                </div>
                                <Share2 className="w-8 h-8 text-muted-foreground" />
                            </div>
                            <div className="flex items-center mt-2 text-xs text-muted-foreground">Auto-forwarded</div>
                        </CardContent>
                    </Card>
                </div>

                {/* Recent Messages */}
                <Card>
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <div>
                                <CardTitle>Recent Messages</CardTitle>
                                <CardDescription>Latest matched messages from your channels</CardDescription>
                            </div>
                            <Button variant="outline" onClick={() => (window.location.href = "/channels")}>
                                View All
                            </Button>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {recentMessages.length === 0 ? (
                                <div className="py-8 text-center text-muted-foreground">No messages yet. Start monitoring channels to see messages here.</div>
                            ) : (
                                recentMessages.map((message) => (
                                    <div key={message.id} className="pb-4 border-b border-border last:border-0">
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                                <p className="text-sm font-medium">{message.channel_title}</p>
                                                <p className="mt-1 text-xs text-muted-foreground">{formatDate(message.message_date)}</p>
                                                <p className="mt-2 text-sm">{truncateText(message.text || "No text", 150)}</p>
                                                <div className="flex flex-wrap gap-1 mt-2">
                                                    {message.matched_keywords.map((keyword, idx) => (
                                                        <span key={idx} className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-md bg-primary/10 text-primary">
                                                            {keyword}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </CardContent>
                </Card>
            </main>
        </div>
    );
};
