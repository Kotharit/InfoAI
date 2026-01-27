import { useState, useEffect, createContext, useContext } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useNavigate, Navigate } from "react-router-dom";
import axios from "axios";

// API URL - works for both local development and Vercel deployment
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = BACKEND_URL ? `${BACKEND_URL}/api` : '/api';

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("user");
    return saved ? JSON.parse(saved) : null;
  });

  const login = (userData) => {
    setUser(userData);
    localStorage.setItem("user", JSON.stringify(userData));
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("user");
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => useContext(AuthContext);

// Theme Context
const ThemeContext = createContext();

const ThemeProvider = ({ children }) => {
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem("theme");
    return saved === "dark";
  });

  useEffect(() => {
    localStorage.setItem("theme", isDark ? "dark" : "light");
    document.documentElement.classList.toggle("dark", isDark);
  }, [isDark]);

  const toggleTheme = () => setIsDark(!isDark);

  return (
    <ThemeContext.Provider value={{ isDark, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

const useTheme = () => useContext(ThemeContext);

// Theme Toggle Button
const ThemeToggle = () => {
  const { isDark, toggleTheme } = useTheme();
  
  return (
    <button
      onClick={toggleTheme}
      className="fixed bottom-6 left-6 p-3 rounded-full shadow-lg transition-all duration-300 hover:scale-110 z-50"
      style={{
        background: isDark ? "#374151" : "#ffffff",
        border: `2px solid ${isDark ? "#4b5563" : "#e5e7eb"}`,
      }}
      title={isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
    >
      {isDark ? (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="5"/>
          <line x1="12" y1="1" x2="12" y2="3"/>
          <line x1="12" y1="21" x2="12" y2="23"/>
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
          <line x1="1" y1="12" x2="3" y2="12"/>
          <line x1="21" y1="12" x2="23" y2="12"/>
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
        </svg>
      ) : (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#6366f1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
      )}
    </button>
  );
};

// Login Page
const LoginPage = () => {
  const navigate = useNavigate();
  const { isDark } = useTheme();
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/login`, { username, password });
      if (response.data.ok) {
        login(response.data.user);
        navigate("/app");
      } else {
        setError(response.data.error || "Login failed");
      }
    } catch (err) {
      setError(err.response?.data?.error || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`min-h-screen flex items-center justify-center transition-colors duration-300 ${isDark ? "bg-gray-900" : "bg-gradient-to-br from-teal-50 via-white to-cyan-50"}`}>
      <div className={`w-full max-w-md p-8 rounded-2xl shadow-xl ${isDark ? "bg-gray-800 border border-gray-700" : "bg-white"}`}>
        <div className="text-center mb-8">
          <div className={`inline-flex items-center justify-center w-16 h-16 rounded-xl mb-4 ${isDark ? "bg-teal-600" : "bg-gradient-to-br from-teal-500 to-cyan-500"}`}>
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <line x1="3" y1="9" x2="21" y2="9"/>
              <line x1="9" y1="21" x2="9" y2="9"/>
            </svg>
          </div>
          <h1 className={`text-2xl font-bold ${isDark ? "text-white" : "text-gray-900"}`}>Infographic Studio</h1>
          <p className={`mt-2 ${isDark ? "text-gray-400" : "text-gray-600"}`}>Sign in to continue</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className={`block text-sm font-medium mb-2 ${isDark ? "text-gray-300" : "text-gray-700"}`}>Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className={`w-full p-3 rounded-lg border transition-colors ${
                isDark 
                  ? "bg-gray-700 border-gray-600 text-white focus:border-teal-500" 
                  : "bg-gray-50 border-gray-200 text-gray-900 focus:border-teal-500"
              } focus:outline-none focus:ring-2 focus:ring-teal-500/20`}
              placeholder="Enter username"
              required
            />
          </div>
          <div>
            <label className={`block text-sm font-medium mb-2 ${isDark ? "text-gray-300" : "text-gray-700"}`}>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={`w-full p-3 rounded-lg border transition-colors ${
                isDark 
                  ? "bg-gray-700 border-gray-600 text-white focus:border-teal-500" 
                  : "bg-gray-50 border-gray-200 text-gray-900 focus:border-teal-500"
              } focus:outline-none focus:ring-2 focus:ring-teal-500/20`}
              placeholder="Enter password"
              required
            />
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className={`w-full py-3 px-4 rounded-lg font-semibold transition-all ${
              loading ? "opacity-50 cursor-not-allowed" : "hover:scale-[1.02]"
            } ${isDark ? "bg-teal-600 text-white hover:bg-teal-500" : "bg-teal-500 text-white hover:bg-teal-600"}`}
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <div className={`mt-6 p-4 rounded-lg ${isDark ? "bg-gray-700/50" : "bg-gray-50"}`}>
          <p className={`text-xs ${isDark ? "text-gray-400" : "text-gray-500"}`}>
            <strong>Demo Credentials:</strong><br/>
            Admin: admin / admin123<br/>
            Contributor: contributor / contrib123
          </p>
        </div>
      </div>
    </div>
  );
};

// Protected Route
const ProtectedRoute = ({ children }) => {
  const { user } = useAuth();
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

// Landing Page
const LandingPage = () => {
  const navigate = useNavigate();
  const { isDark } = useTheme();

  return (
    <div className={`min-h-screen transition-colors duration-300 ${isDark ? "bg-gray-900" : "bg-gradient-to-br from-teal-50 via-white to-cyan-50"}`}>
      <div className="container mx-auto px-6 py-16">
        <div className="text-center max-w-4xl mx-auto">
          <div className="mb-8">
            <div className={`inline-flex items-center justify-center w-20 h-20 rounded-2xl shadow-xl mb-6 ${isDark ? "bg-teal-600" : "bg-gradient-to-br from-teal-500 to-cyan-500"}`}>
              <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <line x1="3" y1="9" x2="21" y2="9"/>
                <line x1="9" y1="21" x2="9" y2="9"/>
              </svg>
            </div>
          </div>

          <h1 className={`text-5xl md:text-6xl font-bold mb-6 leading-tight ${isDark ? "text-white" : "text-gray-900"}`}>
            Transform Reports into
            <span className={`block ${isDark ? "text-teal-400" : "text-teal-600"}`}>Stunning Visual Stories</span>
          </h1>

          <p className={`text-xl md:text-2xl mb-10 max-w-2xl mx-auto ${isDark ? "text-gray-300" : "text-gray-600"}`}>
            Upload a PDF report and let AI create beautiful, storytelling-oriented infographics with visual metaphors and executive clarity.
          </p>

          <button
            onClick={() => navigate("/login")}
            className={`group inline-flex items-center gap-3 px-8 py-4 text-lg font-semibold rounded-xl shadow-lg transition-all duration-300 hover:scale-105 hover:shadow-xl ${
              isDark 
                ? "bg-teal-500 text-white hover:bg-teal-400" 
                : "bg-gradient-to-r from-teal-500 to-cyan-500 text-white hover:from-teal-600 hover:to-cyan-600"
            }`}
          >
            Get Started
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="group-hover:translate-x-1 transition-transform">
              <line x1="5" y1="12" x2="19" y2="12"/>
              <polyline points="12 5 19 12 12 19"/>
            </svg>
          </button>
        </div>

        {/* Features Section */}
        <div className="mt-24 grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {[
            {
              icon: (
                <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                </svg>
              ),
              title: "AI-Powered Insight",
              description: "Your reports already contain the truth. Our AI simply listens—extracting meaning, patterns, and intent—then shaping them into a clear visual narrative that speaks without explanation."
            },
            {
              icon: (
                <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="12 2 2 7 12 12 22 7 12 2"/>
                  <polyline points="2 17 12 22 22 17"/>
                  <polyline points="2 12 12 17 22 12"/>
                </svg>
              ),
              title: "Visual Storytelling",
              description: "Numbers persuade. Stories convince. We translate raw data into visual metaphors—before vs after, cause vs effect, signal vs noise—designed to be understood in seconds and remembered for longer."
            },
            {
              icon: (
                <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
              ),
              title: "Presentation-Ready Output",
              description: "No redesigns. No polishing. No back-and-forth. Export high-resolution infographics crafted for boardrooms, decks, reports, and decisive conversations."
            }
          ].map((feature, idx) => (
            <div
              key={idx}
              className={`p-8 rounded-2xl transition-all duration-300 hover:scale-105 ${
                isDark 
                  ? "bg-gray-800 hover:bg-gray-750 border border-gray-700" 
                  : "bg-white hover:shadow-xl shadow-lg border border-gray-100"
              }`}
            >
              <div className={`inline-flex items-center justify-center w-14 h-14 rounded-xl mb-5 ${
                isDark ? "bg-teal-900/50 text-teal-400" : "bg-teal-100 text-teal-600"
              }`}>
                {feature.icon}
              </div>
              <h3 className={`text-xl font-semibold mb-3 ${isDark ? "text-white" : "text-gray-900"}`}>
                {feature.title}
              </h3>
              <p className={isDark ? "text-gray-400" : "text-gray-600"}>
                {feature.description}
              </p>
            </div>
          ))}
        </div>

        {/* How It Works */}
        <div className="mt-24 max-w-4xl mx-auto">
          <h2 className={`text-3xl font-bold text-center mb-12 ${isDark ? "text-white" : "text-gray-900"}`}>
            How It Works
          </h2>
          <div className="grid md:grid-cols-2 gap-8">
            {[
              { step: "1", title: "Share the Thought", desc: "Upload a report, paste text, or describe your idea. A rough input is enough—clarity will follow." },
              { step: "2", title: "Intelligence Finds Structure", desc: "Our AI reads between the lines. It identifies what matters, organizes complexity, and designs a visual blueprint." },
              { step: "3", title: "Intent Becomes Direction", desc: "The blueprint is refined through a deterministic prompt—ensuring consistency, accuracy, and alignment with your message." },
              { step: "4", title: "Meaning Becomes Visual", desc: "The final idea is rendered into a clean, expressive infographic—where insight meets aesthetics." }
            ].map((item, idx) => (
              <div key={idx} className={`flex gap-4 p-6 rounded-xl ${isDark ? "bg-gray-800/50" : "bg-white/80"}`}>
                <div className="flex-shrink-0">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg ${
                    isDark ? "bg-teal-600 text-white" : "bg-teal-500 text-white"
                  }`}>
                    {item.step}
                  </div>
                </div>
                <div>
                  <h4 className={`font-semibold text-lg mb-2 ${isDark ? "text-white" : "text-gray-900"}`}>{item.title}</h4>
                  <p className={`text-sm leading-relaxed ${isDark ? "text-gray-400" : "text-gray-600"}`}>{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <footer className={`py-8 mt-16 border-t ${isDark ? "border-gray-800" : "border-gray-200"}`}>
        <p className={`text-center text-sm ${isDark ? "text-gray-500" : "text-gray-500"}`}>
          Visual Intelligence for Modern Reports
        </p>
      </footer>
    </div>
  );
};

// Loading Steps Component
const LoadingSteps = ({ currentStep }) => {
  const steps = [
    { id: 1, label: "Extracting text from document...", icon: "📄" },
    { id: 2, label: "AI creating visual blueprint...", icon: "🧠" },
    { id: 3, label: "Refining image prompt...", icon: "⚙️" },
    { id: 4, label: "Rendering infographic...", icon: "🎨" }
  ];

  return (
    <div className="space-y-4">
      {steps.map((step) => (
        <div key={step.id} className={`flex items-center gap-4 p-4 rounded-lg transition-all ${
          currentStep === step.id 
            ? "bg-teal-50 dark:bg-teal-900/30 border-2 border-teal-500" 
            : currentStep > step.id 
            ? "bg-green-50 dark:bg-green-900/20 border border-green-300 dark:border-green-700"
            : "bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 opacity-50"
        }`}>
          <span className="text-2xl">{step.icon}</span>
          <span className={`font-medium ${
            currentStep === step.id ? "text-teal-700 dark:text-teal-300" : 
            currentStep > step.id ? "text-green-700 dark:text-green-300" : 
            "text-gray-500"
          }`}>
            {step.label}
          </span>
          {currentStep === step.id && (
            <svg className="animate-spin h-5 w-5 text-teal-500 ml-auto" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
            </svg>
          )}
          {currentStep > step.id && (
            <svg className="h-5 w-5 text-green-500 ml-auto" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 6L9 17l-5-5"/>
            </svg>
          )}
        </div>
      ))}
    </div>
  );
};

// Toggle Option Component
const ToggleOption = ({ label, options, value, onChange, isDark }) => {
  return (
    <div className="mb-4">
      <label className={`block text-sm font-medium mb-2 ${isDark ? "text-gray-300" : "text-gray-700"}`}>
        {label}
      </label>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <button
            key={option.value}
            onClick={() => onChange(option.value)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
              value === option.value
                ? isDark 
                  ? "bg-teal-600 text-white" 
                  : "bg-teal-500 text-white"
                : isDark
                  ? "bg-gray-700 text-gray-300 hover:bg-gray-600"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
};

// Main App Page
const MainApp = () => {
  const navigate = useNavigate();
  const { isDark } = useTheme();
  const { user, logout } = useAuth();
  
  const [prompt, setPrompt] = useState("");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [status, setStatus] = useState({ message: "", type: "" });
  const [generatedImage, setGeneratedImage] = useState(null);
  const [blueprint, setBlueprint] = useState(null);
  const [compiledPromptPreview, setCompiledPromptPreview] = useState("");
  const [showDebug, setShowDebug] = useState(false);
  const [usageCount, setUsageCount] = useState(0);

  // Settings state
  const [settings, setSettings] = useState({
    layout: "before_after_with_recommendations",
    creativity: "moderate",
    palette: "teal",
    textDensity: "balanced",
    tone: "professional"
  });

  // Check usage on mount
  useEffect(() => {
    const checkUsage = async () => {
      if (user) {
        try {
          const response = await axios.get(`${API}/auth/usage/${user.username}`);
          if (response.data.ok) {
            setUsageCount(response.data.usage_count);
          }
        } catch (err) {
          console.error("Failed to check usage:", err);
        }
      }
    };
    checkUsage();
  }, [user]);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === "application/pdf") {
      setFile(selectedFile);
      setStatus({ message: `File selected: ${selectedFile.name}`, type: "info" });
    } else if (selectedFile) {
      setStatus({ message: "Please select a PDF file", type: "error" });
    }
  };

  const handleGenerate = async () => {
    if (!prompt.trim() && !file) {
      setStatus({ message: "Please enter text or upload a PDF file", type: "error" });
      return;
    }

    // Check usage limit for contributors
    if (user?.role === "contributor" && usageCount >= 2) {
      setStatus({ message: "Usage limit reached. Contact admin for more access.", type: "error" });
      return;
    }

    setLoading(true);
    setLoadingStep(1);
    setStatus({ message: "", type: "" });
    setGeneratedImage(null);
    setBlueprint(null);
    setCompiledPromptPreview("");

    const formData = new FormData();
    if (file) formData.append("file", file);
    formData.append("prompt", prompt);
    formData.append("settings", JSON.stringify(settings));
    formData.append("username", user?.username || "");

    try {
      setLoadingStep(1);
      await new Promise(r => setTimeout(r, 500));
      setLoadingStep(2);
      
      const response = await axios.post(`${API}/generate`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 120000
      });

      setLoadingStep(3);
      await new Promise(r => setTimeout(r, 300));
      setLoadingStep(4);
      await new Promise(r => setTimeout(r, 300));

      if (response.data.ok) {
        const { image, blueprint: bp, compiled_prompt_preview } = response.data;
        
        if (image && image.data) {
          const imageDataUrl = `data:${image.mime_type || 'image/png'};base64,${image.data}`;
          setGeneratedImage(imageDataUrl);
        }
        
        setBlueprint(bp);
        setCompiledPromptPreview(compiled_prompt_preview || "");
        setStatus({ message: "Infographic generated successfully!", type: "success" });
        setUsageCount(prev => prev + 1);
      } else {
        setStatus({ message: response.data.error || "Generation failed", type: "error" });
      }
    } catch (error) {
      console.error("Generate error:", error);
      const errorData = error.response?.data;
      setStatus({ 
        message: errorData?.error || error.message || "An error occurred", 
        type: "error" 
      });
    } finally {
      setLoading(false);
      setLoadingStep(0);
    }
  };

  const handleClear = () => {
    setPrompt("");
    setFile(null);
    setStatus({ message: "", type: "" });
    setGeneratedImage(null);
    setBlueprint(null);
    setCompiledPromptPreview("");
    const fileInput = document.getElementById("file-input");
    if (fileInput) fileInput.value = "";
  };

  const handleDownload = () => {
    if (!generatedImage) return;
    const link = document.createElement("a");
    link.download = "infographic.png";
    link.href = generatedImage;
    link.click();
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className={`min-h-screen transition-colors duration-300 ${isDark ? "bg-gray-900" : "bg-gray-50"}`}>
      {/* Header */}
      <header className={`py-4 px-6 border-b ${isDark ? "bg-gray-800 border-gray-700" : "bg-white border-gray-200"}`}>
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <button 
            onClick={() => navigate("/")}
            className={`flex items-center gap-3 hover:opacity-80 transition-opacity`}
          >
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${isDark ? "bg-teal-600" : "bg-gradient-to-br from-teal-500 to-cyan-500"}`}>
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <line x1="3" y1="9" x2="21" y2="9"/>
                <line x1="9" y1="21" x2="9" y2="9"/>
              </svg>
            </div>
            <span className={`font-bold text-xl ${isDark ? "text-white" : "text-gray-900"}`}>Infographic Studio</span>
          </button>
          <div className="flex items-center gap-4">
            <div className={`text-sm ${isDark ? "text-gray-400" : "text-gray-600"}`}>
              <span className="font-medium">{user?.username}</span>
              <span className={`ml-2 px-2 py-0.5 rounded text-xs ${
                user?.role === "admin" 
                  ? "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400" 
                  : "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
              }`}>
                {user?.role}
              </span>
              {user?.role === "contributor" && (
                <span className={`ml-2 text-xs ${isDark ? "text-gray-500" : "text-gray-400"}`}>
                  ({usageCount}/2 used)
                </span>
              )}
            </div>
            <button
              onClick={() => setShowDebug(!showDebug)}
              className={`text-xs px-2 py-1 rounded ${isDark ? "bg-gray-700 text-gray-300" : "bg-gray-200 text-gray-600"}`}
            >
              {showDebug ? "Hide Debug" : "Debug"}
            </button>
            <button
              onClick={handleLogout}
              className={`text-sm px-3 py-1.5 rounded-lg ${isDark ? "bg-gray-700 text-gray-300 hover:bg-gray-600" : "bg-gray-200 text-gray-600 hover:bg-gray-300"}`}
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Input Panel */}
          <div className="space-y-6">
            {/* Text Input */}
            <div className={`p-6 rounded-xl ${isDark ? "bg-gray-800 border border-gray-700" : "bg-white shadow-lg border border-gray-100"}`}>
              <label className={`block font-semibold mb-3 ${isDark ? "text-white" : "text-gray-900"}`}>
                📄 Paste Report Text or Prompt
              </label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={6}
                placeholder="Paste your report content, site visit notes, or describe what infographic you want..."
                className={`w-full p-4 rounded-lg border resize-none transition-colors ${
                  isDark 
                    ? "bg-gray-700 border-gray-600 text-white placeholder-gray-400 focus:border-teal-500" 
                    : "bg-gray-50 border-gray-200 text-gray-900 placeholder-gray-400 focus:border-teal-500"
                } focus:outline-none focus:ring-2 focus:ring-teal-500/20`}
              />
              
              {/* File Upload */}
              <div className="mt-4">
                <label className={`block font-semibold mb-2 ${isDark ? "text-white" : "text-gray-900"}`}>
                  📁 Or Upload PDF Report
                </label>
                <input
                  id="file-input"
                  type="file"
                  accept=".pdf"
                  onChange={handleFileChange}
                  className={`w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:font-medium cursor-pointer ${
                    isDark 
                      ? "text-gray-300 file:bg-teal-600 file:text-white hover:file:bg-teal-500" 
                      : "text-gray-600 file:bg-teal-500 file:text-white hover:file:bg-teal-600"
                  }`}
                />
              </div>
            </div>

            {/* Settings Panel */}
            <div className={`p-6 rounded-xl ${isDark ? "bg-gray-800 border border-gray-700" : "bg-white shadow-lg border border-gray-100"}`}>
              <h3 className={`font-semibold mb-4 ${isDark ? "text-white" : "text-gray-900"}`}>
                ⚙️ Generation Settings
              </h3>
              
              <ToggleOption
                label="Layout"
                options={[
                  { value: "before_after_with_recommendations", label: "Before/After" },
                  { value: "split_two_column", label: "Two Column" },
                  { value: "process_flow", label: "Process Flow" },
                  { value: "summary_grid", label: "Summary Grid" }
                ]}
                value={settings.layout}
                onChange={(v) => setSettings(s => ({ ...s, layout: v }))}
                isDark={isDark}
              />

              <ToggleOption
                label="Creativity"
                options={[
                  { value: "none", label: "None" },
                  { value: "subtle", label: "Subtle" },
                  { value: "moderate", label: "Moderate" },
                  { value: "high", label: "High" }
                ]}
                value={settings.creativity}
                onChange={(v) => setSettings(s => ({ ...s, creativity: v }))}
                isDark={isDark}
              />

              <ToggleOption
                label="Palette"
                options={[
                  { value: "teal", label: "Teal" },
                  { value: "warm", label: "Warm" },
                  { value: "mono", label: "Mono" }
                ]}
                value={settings.palette}
                onChange={(v) => setSettings(s => ({ ...s, palette: v }))}
                isDark={isDark}
              />

              <ToggleOption
                label="Text Density"
                options={[
                  { value: "low", label: "Low (Visual)" },
                  { value: "balanced", label: "Balanced" },
                  { value: "high", label: "High (Detailed)" }
                ]}
                value={settings.textDensity}
                onChange={(v) => setSettings(s => ({ ...s, textDensity: v }))}
                isDark={isDark}
              />

              <ToggleOption
                label="Tone"
                options={[
                  { value: "professional", label: "Professional" },
                  { value: "creative", label: "Creative" }
                ]}
                value={settings.tone}
                onChange={(v) => setSettings(s => ({ ...s, tone: v }))}
                isDark={isDark}
              />

              {/* Generate Button */}
              <div className="mt-6 flex gap-3">
                <button
                  onClick={handleGenerate}
                  disabled={loading || (user?.role === "contributor" && usageCount >= 2)}
                  className={`flex-1 py-3 px-4 rounded-lg font-semibold transition-all ${
                    loading || (user?.role === "contributor" && usageCount >= 2)
                      ? "opacity-50 cursor-not-allowed" 
                      : "hover:scale-[1.02]"
                  } ${isDark ? "bg-teal-600 text-white hover:bg-teal-500" : "bg-teal-500 text-white hover:bg-teal-600"}`}
                >
                  {loading ? "Generating..." : "🎨 Generate Infographic"}
                </button>
                <button
                  onClick={handleClear}
                  className={`py-3 px-4 rounded-lg font-medium border transition-colors ${
                    isDark 
                      ? "border-gray-600 text-gray-300 hover:bg-gray-700" 
                      : "border-gray-300 text-gray-600 hover:bg-gray-100"
                  }`}
                >
                  Clear
                </button>
              </div>

              {/* Status Message */}
              {status.message && (
                <div className={`mt-4 p-3 rounded-lg text-sm ${
                  status.type === "error" 
                    ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400" 
                    : status.type === "success"
                    ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                    : "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                }`}>
                  {status.message}
                </div>
              )}
            </div>

            {/* Loading Steps */}
            {loading && (
              <div className={`p-6 rounded-xl ${isDark ? "bg-gray-800 border border-gray-700" : "bg-white shadow-lg border border-gray-100"}`}>
                <h3 className={`font-semibold mb-4 ${isDark ? "text-white" : "text-gray-900"}`}>
                  🔄 Generation Pipeline
                </h3>
                <LoadingSteps currentStep={loadingStep} />
              </div>
            )}

            {/* Debug Panel */}
            {showDebug && blueprint && (
              <div className={`p-6 rounded-xl ${isDark ? "bg-gray-800 border border-gray-700" : "bg-white shadow-lg border border-gray-100"}`}>
                <h3 className={`font-semibold mb-4 ${isDark ? "text-white" : "text-gray-900"}`}>
                  🔧 Debug Info
                </h3>
                
                <details className="mb-4">
                  <summary className={`cursor-pointer font-medium ${isDark ? "text-teal-400" : "text-teal-600"}`}>
                    Visual Blueprint JSON
                  </summary>
                  <pre className={`mt-2 p-3 rounded-lg text-xs overflow-auto max-h-64 ${
                    isDark ? "bg-gray-700 text-gray-300" : "bg-gray-100 text-gray-700"
                  }`}>
                    {JSON.stringify(blueprint, null, 2)}
                  </pre>
                </details>
                
                {compiledPromptPreview && (
                  <details>
                    <summary className={`cursor-pointer font-medium ${isDark ? "text-teal-400" : "text-teal-600"}`}>
                      Compiled Prompt Preview
                    </summary>
                    <pre className={`mt-2 p-3 rounded-lg text-xs overflow-auto max-h-64 whitespace-pre-wrap ${
                      isDark ? "bg-gray-700 text-gray-300" : "bg-gray-100 text-gray-700"
                    }`}>
                      {compiledPromptPreview}
                    </pre>
                  </details>
                )}
              </div>
            )}
          </div>

          {/* Output Panel */}
          <div className="space-y-6">
            <div className={`p-6 rounded-xl ${isDark ? "bg-gray-800 border border-gray-700" : "bg-white shadow-lg border border-gray-100"}`}>
              <div className="flex items-center justify-between mb-4">
                <h3 className={`font-semibold ${isDark ? "text-white" : "text-gray-900"}`}>
                  🖼️ Generated Infographic
                </h3>
                {generatedImage && (
                  <button
                    onClick={handleDownload}
                    className={`flex items-center gap-2 py-2 px-4 rounded-lg font-medium transition-all hover:scale-105 ${
                      isDark ? "bg-teal-600 text-white hover:bg-teal-500" : "bg-teal-500 text-white hover:bg-teal-600"
                    }`}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                      <polyline points="7 10 12 15 17 10"/>
                      <line x1="12" y1="15" x2="12" y2="3"/>
                    </svg>
                    Download PNG
                  </button>
                )}
              </div>
              
              <div className={`rounded-lg overflow-hidden border ${isDark ? "border-gray-700 bg-gray-900" : "border-gray-200 bg-gray-50"}`}>
                {generatedImage ? (
                  <img 
                    src={generatedImage} 
                    alt="Generated Infographic"
                    className="w-full h-auto"
                    style={{ maxHeight: "80vh" }}
                  />
                ) : (
                  <div className={`flex flex-col items-center justify-center py-24 ${isDark ? "text-gray-500" : "text-gray-400"}`}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" className="mb-4 opacity-50">
                      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                      <circle cx="8.5" cy="8.5" r="1.5"/>
                      <polyline points="21 15 16 10 5 21"/>
                    </svg>
                    <p className="text-lg font-medium">No image generated yet</p>
                    <p className="text-sm mt-2">Configure settings and click Generate</p>
                  </div>
                )}
              </div>

              {blueprint && (
                <div className={`mt-4 p-4 rounded-lg ${isDark ? "bg-gray-700/50" : "bg-gray-50"}`}>
                  <h4 className={`font-semibold mb-2 ${isDark ? "text-white" : "text-gray-900"}`}>
                    {blueprint.title}
                  </h4>
                  <p className={`text-sm ${isDark ? "text-gray-400" : "text-gray-600"}`}>
                    {blueprint.subtitle}
                  </p>
                  <p className={`text-xs mt-2 ${isDark ? "text-gray-500" : "text-gray-500"}`}>
                    Layout: {blueprint.layout} | Creativity: {blueprint.creativity} | Palette: {blueprint.palette}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <div className="App">
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/app" element={
                <ProtectedRoute>
                  <MainApp />
                </ProtectedRoute>
              } />
            </Routes>
          </BrowserRouter>
          <ThemeToggle />
        </div>
      </ThemeProvider>
    </AuthProvider>
  );
}

export default App;
