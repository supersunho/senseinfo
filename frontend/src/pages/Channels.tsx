// frontend/src/pages/Channels.tsx
import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/common/Card";
import { Button } from "../components/common/Button";
import { Input } from "../components/common/Input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "../components/common/Dialog";
import { Header } from "../components/layout/Header";
import { api } from "../services/api";
import { toast } from "react-hot-toast";
import { Plus, Trash2, Edit, UserPlus, UserMinus } from "lucide-react";
import { cn } from "../utils/cn";

interface Channel {
    id: number;
    username: string;
    title: string;
    is_active: boolean;
    is_monitoring: boolean;
    joined_at: string;
    message_count: number;
}

export const Channels: React.FC = () => {
    const [channels, setChannels] = useState<Channel[]>([]);
    const [loading, setLoading] = useState(true);
    const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
    const [newChannelUsername, setNewChannelUsername] = useState("");
    const [addingChannel, setAddingChannel] = useState(false);

    useEffect(() => {
        loadChannels();
    }, []);

    const loadChannels = async () => {
        try {
            setLoading(true);
            const response = await api.get("/channels");
            setChannels(response.data.channels);
        } catch (error) {
            toast.error("Failed to load channels");
        } finally {
            setLoading(false);
        }
    };

    const handleAddChannel = async () => {
        if (!newChannelUsername.startsWith("@")) {
            toast.error("Channel username must start with @");
            return;
        }

        try {
            setAddingChannel(true);
            await api.post("/channels", { username: newChannelUsername });
            toast.success(`Joined channel ${newChannelUsername}`);
            setNewChannelUsername("");
            setIsAddDialogOpen(false);
            loadChannels();
        } catch (error: any) {
            toast.error(error.response?.data?.detail || "Failed to join channel");
        } finally {
            setAddingChannel(false);
        }
    };

    const handleToggleMonitoring = async (channelId: number, currentStatus: boolean) => {
        try {
            await api.put(`/channels/${channelId}/toggle`);
            toast.success(`Monitoring ${currentStatus ? "disabled" : "enabled"}`);
            loadChannels();
        } catch (error) {
            toast.error("Failed to toggle monitoring");
        }
    };

    const handleRemoveChannel = async (channelId: number) => {
        if (!window.confirm("Are you sure you want to remove this channel?")) {
            return;
        }

        try {
            await api.delete(`/channels/${channelId}`);
            toast.success("Channel removed successfully");
            loadChannels();
        } catch (error) {
            toast.error("Failed to remove channel");
        }
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
            <Header title="Channel Management" />

            <main className="container px-4 py-8 mx-auto md:px-6">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h2 className="text-3xl font-bold tracking-tight">Channels</h2>
                        <p className="text-muted-foreground">Manage your monitored Telegram channels</p>
                    </div>
                    <Button onClick={() => setIsAddDialogOpen(true)}>
                        <Plus className="w-4 h-4 mr-2" />
                        Add Channel
                    </Button>
                </div>

                <Card>
                    <CardContent className="p-0">
                        <div className="divide-y divide-border">
                            {channels.length === 0 ? (
                                <div className="py-12 text-center">
                                    <UserPlus className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                                    <h3 className="mb-2 text-lg font-semibold">No channels yet</h3>
                                    <p className="mb-4 text-muted-foreground">Start monitoring Telegram channels by adding your first one</p>
                                    <Button onClick={() => setIsAddDialogOpen(true)}>Add Channel</Button>
                                </div>
                            ) : (
                                channels.map((channel) => (
                                    <div key={channel.id} className="flex items-center justify-between p-6 transition-colors hover:bg-accent/50">
                                        <div className="flex items-center space-x-4">
                                            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10">
                                                <span className="text-lg font-bold text-primary">{channel.title.charAt(0).toUpperCase()}</span>
                                            </div>
                                            <div>
                                                <p className="font-medium">{channel.title}</p>
                                                <p className="text-sm text-muted-foreground">
                                                    @{channel.username} • {channel.message_count} messages
                                                </p>
                                            </div>
                                        </div>

                                        <div className="flex items-center space-x-2">
                                            <span className={cn("px-2 py-1 text-xs rounded-full", channel.is_monitoring ? "bg-green-500/10 text-green-500" : "bg-gray-500/10 text-gray-500")}>
                                                {channel.is_monitoring ? "Active" : "Paused"}
                                            </span>

                                            <Button variant="ghost" size="sm" onClick={() => handleToggleMonitoring(channel.id, channel.is_monitoring)}>
                                                {channel.is_monitoring ? <UserMinus className="w-4 h-4" /> : <UserPlus className="w-4 h-4" />}
                                            </Button>

                                            <Button variant="ghost" size="sm" onClick={() => handleRemoveChannel(channel.id)}>
                                                <Trash2 className="w-4 h-4 text-destructive" />
                                            </Button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </CardContent>
                </Card>

                {/* Add Channel Dialog */}
                <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Add New Channel</DialogTitle>
                            <DialogDescription>Enter the channel username to start monitoring</DialogDescription>
                        </DialogHeader>

                        <div className="py-4 space-y-4">
                            <Input
                                label="Channel Username"
                                placeholder="@channelusername"
                                value={newChannelUsername}
                                onChange={(e) => setNewChannelUsername(e.target.value)}
                                helperText="Include @ symbol (e.g., @telegram)"
                            />
                        </div>

                        <DialogFooter>
                            <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                                Cancel
                            </Button>
                            <Button onClick={handleAddChannel} loading={addingChannel} disabled={!newChannelUsername}>
                                Add Channel
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </main>
        </div>
    );
};
