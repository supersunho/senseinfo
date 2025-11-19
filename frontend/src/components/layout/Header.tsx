// frontend/src/components/layout/Header.tsx
import React from "react";
import { Bell, Settings, User, LogOut } from "lucide-react";
import { Button } from "../common/Button";
import { useNavigate } from "react-router-dom";

export interface HeaderProps {
    title: string;
    onLogout?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ title, onLogout }) => {
    const navigate = useNavigate();

    const handleLogout = () => {
        if (onLogout) {
            onLogout();
        } else {
            // Default logout behavior
            localStorage.removeItem("auth_token");
            navigate("/setup");
        }
    };

    return (
        <header className="sticky top-0 z-40 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="flex items-center h-16 px-4 md:px-6">
                <div className="flex items-center justify-between flex-1">
                    <div className="flex items-center space-x-4">
                        <h1 className="text-xl font-bold tracking-tight">{title}</h1>
                    </div>

                    <div className="flex items-center space-x-4">
                        <Button variant="ghost" size="icon" className="relative" onClick={() => console.log("Notifications")}>
                            <Bell className="w-4 h-4" />
                            <span className="absolute flex items-center justify-center w-5 h-5 text-xs rounded-full -top-1 -right-1 bg-destructive text-destructive-foreground">3</span>
                        </Button>

                        <Button variant="ghost" size="icon" onClick={() => navigate("/settings")}>
                            <Settings className="w-4 h-4" />
                        </Button>

                        <div className="flex items-center space-x-2">
                            <Button variant="ghost" size="icon" onClick={() => navigate("/profile")}>
                                <User className="w-4 h-4" />
                            </Button>

                            <Button variant="ghost" size="icon" onClick={handleLogout}>
                                <LogOut className="w-4 h-4" />
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </header>
    );
};
