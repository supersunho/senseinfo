// frontend/src/components/layout/Sidebar.tsx
import React from "react";
import { NavLink } from "react-router-dom";
import { LayoutDashboard, Settings, MessageSquare, Key, LogOut, Menu, X } from "lucide-react";
import { Button } from "../common/Button";
import { cn } from "../../utils/cn";

export interface SidebarProps {
    isOpen: boolean;
    onClose: () => void;
}

const navItems = [
    {
        title: "Dashboard",
        href: "/dashboard",
        icon: LayoutDashboard,
    },
    {
        title: "Channels",
        href: "/channels",
        icon: MessageSquare,
    },
    {
        title: "Keywords",
        href: "/keywords",
        icon: Key,
    },
    {
        title: "Settings",
        href: "/settings",
        icon: Settings,
    },
];

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
    const handleLogout = () => {
        localStorage.removeItem("auth_token");
        window.location.href = "/setup";
    };

    return (
        <>
            {/* Mobile overlay */}
            {isOpen && <div className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden" onClick={onClose} />}

            {/* Sidebar */}
            <aside
                className={cn(
                    "fixed left-0 top-0 z-50 h-screen w-64 border-r border-border bg-background transition-transform duration-300 ease-in-out lg:translate-x-0",
                    isOpen ? "translate-x-0" : "-translate-x-full"
                )}
            >
                <div className="flex flex-col h-full">
                    {/* Header */}
                    <div className="flex items-center justify-between h-16 px-6 border-b border-border">
                        <div className="flex items-center space-x-2">
                            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary text-primary-foreground">IS</div>
                            <span className="text-lg font-bold">InfoSense</span>
                        </div>
                        <Button variant="ghost" size="icon" className="lg:hidden" onClick={onClose}>
                            <X className="w-4 h-4" />
                        </Button>
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 px-4 py-4 overflow-y-auto">
                        <div className="space-y-1">
                            {navItems.map((item) => {
                                const Icon = item.icon;
                                return (
                                    <NavLink
                                        key={item.href}
                                        to={item.href}
                                        className={({ isActive }) =>
                                            cn(
                                                "flex items-center space-x-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                                                isActive ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                                            )
                                        }
                                        onClick={onClose}
                                    >
                                        <Icon className="w-4 h-4" />
                                        <span>{item.title}</span>
                                    </NavLink>
                                );
                            })}
                        </div>
                    </nav>

                    {/* Footer */}
                    <div className="p-4 border-t border-border">
                        <Button variant="ghost" className="justify-start w-full text-destructive" onClick={handleLogout}>
                            <LogOut className="w-4 h-4 mr-2" />
                            Logout
                        </Button>
                    </div>
                </div>
            </aside>
        </>
    );
};

export const MobileMenuButton: React.FC<{ onClick: () => void }> = ({ onClick }) => {
    return (
        <Button variant="ghost" size="icon" className="lg:hidden" onClick={onClick}>
            <Menu className="w-4 h-4" />
        </Button>
    );
};
