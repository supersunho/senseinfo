// frontend/src/pages/Setup.tsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/common/Card";
import { Button } from "../components/common/Button";
import { Input } from "../components/common/Input";
import { api } from "../services/api";
import { toast } from "react-hot-toast";

interface SetupFormData {
    apiId: string;
    apiHash: string;
    phoneNumber: string;
    code: string;
    password: string;
}

export const Setup: React.FC = () => {
    const navigate = useNavigate();
    const [step, setStep] = useState<"api" | "phone" | "code" | "password" | "complete">("api");
    const [formData, setFormData] = useState<SetupFormData>({
        apiId: "",
        apiHash: "",
        phoneNumber: "",
        code: "",
        password: "",
    });
    const [loading, setLoading] = useState(false);
    const [phoneCodeHash, setPhoneCodeHash] = useState("");

    const handleApiSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            // Store API credentials temporarily
            localStorage.setItem("telegram_api_id", formData.apiId);
            localStorage.setItem("telegram_api_hash", formData.apiHash);

            setStep("phone");
            toast.success("API credentials saved");
        } catch (error) {
            toast.error("Failed to save API credentials");
        } finally {
            setLoading(false);
        }
    };

    const handlePhoneSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            const response = await api.post("/auth/telegram/start", {
                phone_number: `+${formData.phoneNumber}`,
            });

            if (response.data.status === "code_sent") {
                setPhoneCodeHash(response.data.phone_code_hash);
                setStep("code");
                toast.success("Verification code sent");
            } else if (response.data.requires_2fa) {
                setStep("password");
                toast.info("2FA required");
            }
        } catch (error: any) {
            toast.error(error.response?.data?.detail || "Failed to send code");
        } finally {
            setLoading(false);
        }
    };

    const handleCodeSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            const apiId = localStorage.getItem("telegram_api_id");
            const apiHash = localStorage.getItem("telegram_api_hash");

            const response = await api.post("/auth/telegram/verify", {
                phone_number: `+${formData.phoneNumber}`,
                phone_code_hash: phoneCodeHash,
                code: formData.code,
                api_id: apiId,
                api_hash: apiHash,
            });

            if (response.data.status === "authenticated") {
                setStep("complete");
                toast.success("Authentication successful");
                setTimeout(() => navigate("/dashboard"), 2000);
            } else if (response.data.requires_2fa) {
                setStep("password");
                toast.info("2FA password required");
            }
        } catch (error: any) {
            toast.error(error.response?.data?.detail || "Invalid code");
        } finally {
            setLoading(false);
        }
    };

    const handlePasswordSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            const response = await api.post("/auth/telegram/2fa", {
                phone_number: `+${formData.phoneNumber}`,
                password: formData.password,
            });

            if (response.data.status === "authenticated") {
                setStep("complete");
                toast.success("2FA authentication successful");
                setTimeout(() => navigate("/dashboard"), 2000);
            }
        } catch (error: any) {
            toast.error(error.response?.data?.detail || "Invalid password");
        } finally {
            setLoading(false);
        }
    };

    const renderStep = () => {
        switch (step) {
            case "api":
                return (
                    <form onSubmit={handleApiSubmit} className="space-y-4">
                        <Input
                            label="Telegram API ID"
                            type="number"
                            value={formData.apiId}
                            onChange={(e) => setFormData({ ...formData, apiId: e.target.value })}
                            placeholder="12345678"
                            required
                            helperText="Get from https://my.telegram.org/apps"
                        />
                        <Input
                            label="Telegram API Hash"
                            type="password"
                            value={formData.apiHash}
                            onChange={(e) => setFormData({ ...formData, apiHash: e.target.value })}
                            placeholder="your_api_hash_here"
                            required
                            helperText="Keep this secret!"
                        />
                        <Button type="submit" className="w-full" loading={loading}>
                            Next
                        </Button>
                    </form>
                );

            case "phone":
                return (
                    <form onSubmit={handlePhoneSubmit} className="space-y-4">
                        <Input
                            label="Phone Number"
                            type="tel"
                            value={formData.phoneNumber}
                            onChange={(e) => setFormData({ ...formData, phoneNumber: e.target.value })}
                            placeholder="821012345678"
                            required
                            helperText="Include country code (e.g., 82 for Korea)"
                        />
                        <Button type="submit" className="w-full" loading={loading}>
                            Send Code
                        </Button>
                    </form>
                );

            case "code":
                return (
                    <form onSubmit={handleCodeSubmit} className="space-y-4">
                        <Input
                            label="Verification Code"
                            type="text"
                            value={formData.code}
                            onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                            placeholder="12345"
                            required
                            helperText="Check your Telegram app"
                        />
                        <Button type="submit" className="w-full" loading={loading}>
                            Verify
                        </Button>
                    </form>
                );

            case "password":
                return (
                    <form onSubmit={handlePasswordSubmit} className="space-y-4">
                        <Input
                            label="2FA Password"
                            type="password"
                            value={formData.password}
                            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                            placeholder="Your 2FA password"
                            required
                        />
                        <Button type="submit" className="w-full" loading={loading}>
                            Submit
                        </Button>
                    </form>
                );

            case "complete":
                return (
                    <div className="space-y-4 text-center">
                        <div className="flex items-center justify-center">
                            <div className="flex items-center justify-center w-16 h-16 text-white bg-green-500 rounded-full">✓</div>
                        </div>
                        <h2 className="text-2xl font-bold">Setup Complete!</h2>
                        <p className="text-muted-foreground">Redirecting to dashboard...</p>
                    </div>
                );
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen p-4 bg-background">
            <Card className="w-full max-w-md">
                <CardHeader>
                    <CardTitle>InfoSense Setup</CardTitle>
                    <CardDescription>Configure your Telegram surveillance system</CardDescription>
                </CardHeader>
                <CardContent>{renderStep()}</CardContent>
            </Card>
        </div>
    );
};
