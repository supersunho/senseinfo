// frontend/src/App.tsx
import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { Setup } from "./pages/Setup";
import { Dashboard } from "./pages/Dashboard";
import { Channels } from "./pages/Channels";
import { Keywords } from "./pages/Keywords";
import { Sidebar, MobileMenuButton } from "./components/layout/Sidebar";

function App() {
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [isAuthenticated, setIsAuthenticated] = useState(false);

    useEffect(() => {
        // Check authentication status
        const checkAuth = async () => {
            try {
                const token = localStorage.getItem("auth_token");
                if (token) {
                    setIsAuthenticated(true);
                } else {
                    // Try to verify session with backend
                    const response = await fetch("/api/system/status");
                    if (response.ok) {
                        setIsAuthenticated(true);
                    }
                }
            } catch (error) {
                setIsAuthenticated(false);
            }
        };
        checkAuth();
    }, []);

    const toggleSidebar = () => {
        setIsSidebarOpen(!isSidebarOpen);
    };

    const closeSidebar = () => {
        setIsSidebarOpen(false);
    };

    return (
        <BrowserRouter>
            <div className="min-h-screen bg-background">
                <Toaster
                    position="top-right"
                    toastOptions={{
                        duration: 4000,
                        style: {
                            background: "hsl(var(--background))",
                            color: "hsl(var(--foreground))",
                            border: "1px solid hsl(var(--border))",
                        },
                    }}
                />

                <Routes>
                    <Route path="/setup" element={!isAuthenticated ? <Setup /> : <Navigate to="/dashboard" />} />
                    <Route path="/dashboard" element={isAuthenticated ? <Dashboard /> : <Navigate to="/setup" />} />
                    <Route path="/channels" element={isAuthenticated ? <Channels /> : <Navigate to="/setup" />} />
                    <Route path="/keywords" element={isAuthenticated ? <Keywords /> : <Navigate to="/setup" />} />
                    <Route path="/" element={<Navigate to={isAuthenticated ? "/dashboard" : "/setup"} />} />
                </Routes>

                {isAuthenticated && (
                    <>
                        <MobileMenuButton onClick={toggleSidebar} />
                        <Sidebar isOpen={isSidebarOpen} onClose={closeSidebar} />
                    </>
                )}
            </div>
        </BrowserRouter>
    );
}

export default App;
