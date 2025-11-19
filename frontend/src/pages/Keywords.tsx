// frontend/src/pages/Keywords.tsx
import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/common/Card";
import { Button } from "../components/common/Button";
import { Input } from "../components/common/Input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "../components/common/Dialog";
import { Header } from "../components/layout/Header";
import { api } from "../services/api";
import { toast } from "react-hot-toast";
import { Plus, Trash2, Filter, Ban, Check } from "lucide-react";
import { cn } from "../utils/cn";

interface Channel {
    id: number;
    title: string;
    username: string;
}

interface Keyword {
    id: number;
    word: string;
    is_inclusion: boolean;
    is_active: boolean;
    created_at: string;
}

export const Keywords: React.FC = () => {
    const [channels, setChannels] = useState<Channel[]>([]);
    const [selectedChannel, setSelectedChannel] = useState<string>("");
    const [keywords, setKeywords] = useState<Keyword[]>([]);
    const [loading, setLoading] = useState(true);
    const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
    const [newKeyword, setNewKeyword] = useState("");
    const [isInclusion, setIsInclusion] = useState(true);
    const [addingKeyword, setAddingKeyword] = useState(false);

    useEffect(() => {
        loadChannels();
    }, []);

    useEffect(() => {
        if (selectedChannel) {
            loadKeywords();
        }
    }, [selectedChannel]);

    const loadChannels = async () => {
        try {
            setLoading(true);
            const response = await api.get("/channels");
            setChannels(response.data.channels);
            if (response.data.channels.length > 0) {
                setSelectedChannel(response.data.channels[0].id.toString());
            }
        } catch (error) {
            toast.error("Failed to load channels");
        } finally {
            setLoading(false);
        }
    };

    const loadKeywords = async () => {
        try {
            const response = await api.get(`/keywords?channel_id=${selectedChannel}`);
            setKeywords(response.data.keywords);
        } catch (error) {
            toast.error("Failed to load keywords");
        }
    };

    const handleAddKeyword = async () => {
        if (!newKeyword.trim()) {
            toast.error("Keyword cannot be empty");
            return;
        }

        try {
            setAddingKeyword(true);
            await api.post("/keywords", {
                channel_id: parseInt(selectedChannel),
                word: newKeyword,
                is_inclusion: isInclusion,
            });
            toast.success(`Keyword "${newKeyword}" added`);
            setNewKeyword("");
            setIsAddDialogOpen(false);
            loadKeywords();
        } catch (error: any) {
            toast.error(error.response?.data?.detail || "Failed to add keyword");
        } finally {
            setAddingKeyword(false);
        }
    };

    const handleToggleKeyword = async (keywordId: number, currentStatus: boolean) => {
        try {
            await api.put(`/keywords/${keywordId}/toggle`);
            toast.success(`Keyword ${currentStatus ? "disabled" : "enabled"}`);
            loadKeywords();
        } catch (error) {
            toast.error("Failed to toggle keyword");
        }
    };

    const handleDeleteKeyword = async (keywordId: number) => {
        if (!window.confirm("Are you sure you want to delete this keyword?")) {
            return;
        }

        try {
            await api.delete(`/keywords/${keywordId}`);
            toast.success("Keyword deleted successfully");
            loadKeywords();
        } catch (error) {
            toast.error("Failed to delete keyword");
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
            <Header title="Keyword Management" />

            <main className="container px-4 py-8 mx-auto md:px-6">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h2 className="text-3xl font-bold tracking-tight">Keywords</h2>
                        <p className="text-muted-foreground">Manage filter keywords for your channels</p>
                    </div>
                    <Button onClick={() => setIsAddDialogOpen(true)}>
                        <Plus className="w-4 h-4 mr-2" />
                        Add Keyword
                    </Button>
                </div>

                <div className="mb-6">
                    <label className="block mb-2 text-sm font-medium">Select Channel</label>
                    <select
                        value={selectedChannel}
                        onChange={(e) => setSelectedChannel(e.target.value)}
                        className="w-full px-3 py-2 border rounded-md md:w-64 bg-background border-input focus:outline-none focus:ring-2 focus:ring-ring"
                    >
                        {channels.map((channel) => (
                            <option key={channel.id} value={channel.id}>
                                {channel.title} (@{channel.username})
                            </option>
                        ))}
                    </select>
                </div>

                <Card>
                    <CardContent className="p-0">
                        <div className="divide-y divide-border">
                            {keywords.length === 0 ? (
                                <div className="py-12 text-center">
                                    <Filter className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                                    <h3 className="mb-2 text-lg font-semibold">No keywords yet</h3>
                                    <p className="mb-4 text-muted-foreground">Add keywords to filter messages from this channel</p>
                                    <Button onClick={() => setIsAddDialogOpen(true)}>Add Keyword</Button>
                                </div>
                            ) : (
                                keywords.map((keyword) => (
                                    <div key={keyword.id} className="flex items-center justify-between p-6 transition-colors hover:bg-accent/50">
                                        <div className="flex items-center space-x-4">
                                            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10">
                                                {keyword.is_inclusion ? <Check className="w-5 h-5 text-primary" /> : <Ban className="w-5 h-5 text-destructive" />}
                                            </div>
                                            <div>
                                                <p className="font-medium">{keyword.word}</p>
                                                <p className="text-sm text-muted-foreground">
                                                    {keyword.is_inclusion ? "Inclusion" : "Exclusion"} • Added {new Date(keyword.created_at).toLocaleDateString()}
                                                </p>
                                            </div>
                                        </div>

                                        <div className="flex items-center space-x-2">
                                            <span className={cn("px-2 py-1 text-xs rounded-full", keyword.is_active ? "bg-green-500/10 text-green-500" : "bg-gray-500/10 text-gray-500")}>
                                                {keyword.is_active ? "Active" : "Inactive"}
                                            </span>

                                            <Button variant="ghost" size="sm" onClick={() => handleToggleKeyword(keyword.id, keyword.is_active)}>
                                                {keyword.is_active ? <Ban className="w-4 h-4" /> : <Check className="w-4 h-4" />}
                                            </Button>

                                            <Button variant="ghost" size="sm" onClick={() => handleDeleteKeyword(keyword.id)}>
                                                <Trash2 className="w-4 h-4 text-destructive" />
                                            </Button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </CardContent>
                </Card>

                {/* Add Keyword Dialog */}
                <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Add New Keyword</DialogTitle>
                            <DialogDescription>Create a filter keyword for the selected channel</DialogDescription>
                        </DialogHeader>

                        <div className="py-4 space-y-4">
                            <Input label="Keyword" placeholder="Enter keyword" value={newKeyword} onChange={(e) => setNewKeyword(e.target.value)} />

                            <div className="space-y-2">
                                <label className="text-sm font-medium">Keyword Type</label>
                                <div className="flex space-x-4">
                                    <label className="flex items-center">
                                        <input type="radio" value="inclusion" checked={isInclusion} onChange={() => setIsInclusion(true)} className="mr-2" />
                                        <span>Inclusion (match this word)</span>
                                    </label>
                                    <label className="flex items-center">
                                        <input type="radio" value="exclusion" checked={!isInclusion} onChange={() => setIsInclusion(false)} className="mr-2" />
                                        <span>Exclusion (ignore this word)</span>
                                    </label>
                                </div>
                            </div>
                        </div>

                        <DialogFooter>
                            <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                                Cancel
                            </Button>
                            <Button onClick={handleAddKeyword} loading={addingKeyword} disabled={!newKeyword.trim()}>
                                Add Keyword
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </main>
        </div>
    );
};
