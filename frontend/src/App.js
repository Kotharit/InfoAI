import { useState, useRef, useEffect, createContext, useContext } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import axios from "axios";
import * as htmlToImage from "html-to-image";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

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

// Icon Map for Infographic Blocks - Comprehensive mapping
const ICON_MAP = {
  // Industry & Environment
  factory: "🏭", thermometer: "🌡️", leaf: "🌱", sun: "☀️", chart: "📊", clock: "⏱️",
  "polar-bear": "🐻‍❄️", car: "🚗", user: "👤", lightbulb: "💡", phone: "📱", document: "📄",
  rocket: "🚀", star: "⭐", heart: "❤️", globe: "🌍", money: "💰", book: "📚",
  target: "🎯", tools: "🔧", shield: "🛡️", brain: "🧠", idea: "💡", growth: "📈",
  team: "👥", computer: "💻", email: "📧", calendar: "📅", check: "✅", warning: "⚠️",
  innovation: "🔬", strategy: "♟️", success: "🏆", data: "📊", network: "🌐", security: "🔒",
  
  // Healthcare & Medical
  scan: "🔬", flask: "🧪", patient: "👨‍⚕️", doctor: "👩‍⚕️", medicine: "💊", pill: "💊",
  hospital: "🏥", ambulance: "🚑", health: "❤️‍🩹", dna: "🧬", virus: "🦠", microscope: "🔬",
  stethoscope: "🩺", syringe: "💉", bandage: "🩹", wheelchair: "♿", treatment: "💉",
  diagnosis: "🔍", diagnose: "🔍", research: "🔬", lab: "🧪", analytics: "📈", prediction: "🔮",
  medical: "⚕️", personalize: "👤", personalized: "👤", admin: "📋", administrative: "📋",
  automate: "⚙️", automation: "⚙️", automated: "⚙️", predict: "🔮", predictive: "🔮",
  
  // Technology & AI
  ai: "🤖", robot: "🤖", machine: "🖥️", algorithm: "🧮", code: "💻",
  chip: "🔌", database: "🗄️", cloud: "☁️", server: "🖥️", digital: "📱", tech: "💻",
  
  // Business & Finance
  business: "💼", finance: "💵", investment: "📈", profit: "💰", sales: "📊", 
  marketing: "📢", customer: "👥", partnership: "🤝", contract: "📝", office: "🏢",
  
  // Education & Learning
  education: "🎓", learn: "📖", study: "📚", school: "🏫", knowledge: "🧠", training: "🏋️",
  
  // Communication
  communication: "💬", message: "✉️", social: "🌐", media: "📺", broadcast: "📡",
  
  // Nature & Sustainability
  nature: "🌿", tree: "🌳", water: "💧", ocean: "🌊", mountain: "⛰️", animal: "🐾",
  recycle: "♻️", green: "🌿", solar: "☀️", wind: "💨", energy: "⚡", eco: "🌱",
  
  // General Purpose
  key: "🔑", lock: "🔐", search: "🔍", settings: "⚙️", home: "🏠", location: "📍",
  time: "⏰", speed: "⚡", quality: "✨", premium: "👑", award: "🏅", gift: "🎁",
  task: "📋", tasks: "📋", process: "⚙️", step: "👣", steps: "👣", workflow: "🔄"
};

// Smart icon lookup with fallbacks
const getIconEmoji = (key) => {
  if (!key) return "📌";
  const lowerKey = key.toLowerCase().trim();
  
  // Direct match
  if (ICON_MAP[lowerKey]) return ICON_MAP[lowerKey];
  
  // Try removing common suffixes
  const baseName = lowerKey.replace(/s$/, '').replace(/ing$/, '').replace(/ed$/, '').replace(/tion$/, '');
  if (ICON_MAP[baseName]) return ICON_MAP[baseName];
  
  // Try first word if hyphenated or underscored
  const firstPart = lowerKey.split(/[-_ ]/)[0];
  if (ICON_MAP[firstPart]) return ICON_MAP[firstPart];
  
  // Try to find partial match
  const keys = Object.keys(ICON_MAP);
  for (const iconKey of keys) {
    if (lowerKey.includes(iconKey) || iconKey.includes(lowerKey)) {
      return ICON_MAP[iconKey];
    }
  }
  
  // Default fallback based on common categories
  if (lowerKey.includes('health') || lowerKey.includes('medic') || lowerKey.includes('care')) return "⚕️";
  if (lowerKey.includes('tech') || lowerKey.includes('digital') || lowerKey.includes('ai')) return "🤖";
  if (lowerKey.includes('business') || lowerKey.includes('work')) return "💼";
  if (lowerKey.includes('learn') || lowerKey.includes('edu')) return "📚";
  
  return "📌";
};

const getPaletteColors = (palette, isDark) => {
  const palettes = {
    teal: isDark 
      ? ["#134e4a", "#115e59", "#0f766e", "#14b8a6"]
      : ["#ccfbf1", "#99f6e4", "#5eead4", "#2dd4bf"],
    warm: isDark 
      ? ["#7c2d12", "#9a3412", "#c2410c", "#ea580c"]
      : ["#fff7ed", "#ffedd5", "#fed7aa", "#fdba74"],
    mono: isDark 
      ? ["#27272a", "#3f3f46", "#52525b", "#71717a"]
      : ["#f4f4f5", "#e4e4e7", "#d4d4d8", "#a1a1aa"]
  };
  return palettes[palette] || palettes.teal;
};

// Landing Page
const LandingPage = () => {
  const navigate = useNavigate();
  const { isDark } = useTheme();

  return (
    <div className={`min-h-screen transition-colors duration-300 ${isDark ? "bg-gray-900" : "bg-gradient-to-br from-teal-50 via-white to-cyan-50"}`}>
      {/* Hero Section */}
      <div className="container mx-auto px-6 py-16">
        <div className="text-center max-w-4xl mx-auto">
          {/* Logo/Brand */}
          <div className="mb-8">
            <div className={`inline-flex items-center justify-center w-20 h-20 rounded-2xl shadow-xl mb-6 ${isDark ? "bg-teal-600" : "bg-gradient-to-br from-teal-500 to-cyan-500"}`}>
              <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <line x1="3" y1="9" x2="21" y2="9"/>
                <line x1="9" y1="21" x2="9" y2="9"/>
              </svg>
            </div>
          </div>

          {/* Headline */}
          <h1 className={`text-5xl md:text-6xl font-bold mb-6 leading-tight ${isDark ? "text-white" : "text-gray-900"}`}>
            Transform Content into
            <span className={`block ${isDark ? "text-teal-400" : "text-teal-600"}`}>Beautiful Infographics</span>
          </h1>

          {/* Subtitle */}
          <p className={`text-xl md:text-2xl mb-10 max-w-2xl mx-auto ${isDark ? "text-gray-300" : "text-gray-600"}`}>
            Upload a PDF or paste text, and let AI create stunning visual summaries in seconds. No design skills needed.
          </p>

          {/* CTA Button */}
          <button
            onClick={() => navigate("/app")}
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
                  <polyline points="10 9 9 9 8 9"/>
                </svg>
              ),
              title: "PDF & Text Input",
              description: "Upload PDF documents or paste text directly. Our AI extracts and processes your content automatically."
            },
            {
              icon: (
                <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="12 2 2 7 12 12 22 7 12 2"/>
                  <polyline points="2 17 12 22 22 17"/>
                  <polyline points="2 12 12 17 22 12"/>
                </svg>
              ),
              title: "AI-Powered Design",
              description: "Google Gemini analyzes your content and creates structured infographic layouts with perfect information hierarchy."
            },
            {
              icon: (
                <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
              ),
              title: "Export as PNG",
              description: "Download your infographic as a high-quality PNG image, ready to share or include in presentations."
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

        {/* How it Works */}
        <div className="mt-24 max-w-4xl mx-auto">
          <h2 className={`text-3xl font-bold text-center mb-12 ${isDark ? "text-white" : "text-gray-900"}`}>
            How It Works
          </h2>
          <div className="flex flex-col md:flex-row items-center justify-between gap-8">
            {[
              { step: "1", title: "Upload", desc: "Add your PDF or paste text" },
              { step: "2", title: "Generate", desc: "AI creates your infographic" },
              { step: "3", title: "Export", desc: "Download as PNG" }
            ].map((item, idx) => (
              <div key={idx} className="flex items-center gap-4">
                <div className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center font-bold text-xl ${
                  isDark ? "bg-teal-600 text-white" : "bg-teal-500 text-white"
                }`}>
                  {item.step}
                </div>
                <div>
                  <h4 className={`font-semibold ${isDark ? "text-white" : "text-gray-900"}`}>{item.title}</h4>
                  <p className={`text-sm ${isDark ? "text-gray-400" : "text-gray-600"}`}>{item.desc}</p>
                </div>
                {idx < 2 && (
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={isDark ? "#6b7280" : "#9ca3af"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="hidden md:block ml-4">
                    <line x1="5" y1="12" x2="19" y2="12"/>
                    <polyline points="12 5 19 12 12 19"/>
                  </svg>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className={`py-8 mt-16 border-t ${isDark ? "border-gray-800" : "border-gray-200"}`}>
        <p className={`text-center text-sm ${isDark ? "text-gray-500" : "text-gray-500"}`}>
          Infographic MVP — Powered by Google Gemini AI
        </p>
      </footer>
    </div>
  );
};

// Main App Page
const MainApp = () => {
  const navigate = useNavigate();
  const { isDark } = useTheme();
  const infographicRef = useRef(null);
  
  const [prompt, setPrompt] = useState("");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState({ message: "", type: "" });
  const [layout, setLayout] = useState("vertical_steps");
  const [palette, setPalette] = useState("teal");
  const [rawOutput, setRawOutput] = useState("");
  
  const [infographic, setInfographic] = useState({
    title: "Understanding Climate Change",
    subtitle: "Causes, impacts, and action in one page",
    layout: "vertical_steps",
    style: { palette: "teal" },
    blocks: [
      { id: 1, icon: "factory", heading: "Main Causes", bullets: ["Greenhouse gas emissions", "Deforestation & pollution"] },
      { id: 2, icon: "thermometer", heading: "Key Impacts", bullets: ["Rising temperatures", "Extreme weather events"] },
      { id: 3, icon: "leaf", heading: "How to Act", bullets: ["Reduce carbon footprint", "Use renewable energy"] }
    ]
  });

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

    setLoading(true);
    setStatus({ message: "Generating infographic...", type: "info" });
    setRawOutput("");

    const formData = new FormData();
    if (file) formData.append("file", file);
    formData.append("prompt", prompt);

    try {
      const response = await axios.post(`${API}/generate`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      if (response.data.ok && response.data.infographic) {
        const data = response.data.infographic;
        setInfographic(data);
        if (data.layout) setLayout(data.layout);
        if (data.style?.palette) setPalette(data.style.palette);
        setStatus({ message: "Infographic generated successfully!", type: "success" });
      } else {
        setStatus({ message: response.data.error || "Generation failed", type: "error" });
        if (response.data.raw) setRawOutput(response.data.raw);
      }
    } catch (error) {
      console.error("Generate error:", error);
      const errorData = error.response?.data;
      setStatus({ 
        message: errorData?.error || error.message || "An error occurred", 
        type: "error" 
      });
      if (errorData?.raw) setRawOutput(errorData.raw);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setPrompt("");
    setFile(null);
    setStatus({ message: "", type: "" });
    setRawOutput("");
    // Reset file input
    const fileInput = document.getElementById("file-input");
    if (fileInput) fileInput.value = "";
  };

  const handleExport = async () => {
    if (!infographicRef.current) return;
    
    try {
      setStatus({ message: "Exporting PNG...", type: "info" });
      const dataUrl = await htmlToImage.toPng(infographicRef.current, {
        backgroundColor: isDark ? "#1f2937" : "#ffffff",
        quality: 1,
        pixelRatio: 2
      });
      
      const link = document.createElement("a");
      link.download = "infographic.png";
      link.href = dataUrl;
      link.click();
      setStatus({ message: "PNG exported successfully!", type: "success" });
    } catch (error) {
      console.error("Export error:", error);
      setStatus({ message: "Export failed: " + error.message, type: "error" });
    }
  };

  // Update infographic when layout/palette changes
  useEffect(() => {
    setInfographic(prev => ({
      ...prev,
      layout,
      style: { palette }
    }));
  }, [layout, palette]);

  const paletteColors = getPaletteColors(palette, isDark);

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
            <span className={`font-bold text-xl ${isDark ? "text-white" : "text-gray-900"}`}>Infographic MVP</span>
          </button>
          <p className={`text-sm ${isDark ? "text-gray-400" : "text-gray-500"}`}>
            Upload → Generate → Export
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Input Panel */}
          <div className={`lg:col-span-1 space-y-6`}>
            {/* Text Input */}
            <div className={`p-6 rounded-xl ${isDark ? "bg-gray-800 border border-gray-700" : "bg-white shadow-lg border border-gray-100"}`}>
              <label className={`block font-semibold mb-3 ${isDark ? "text-white" : "text-gray-900"}`}>
                Paste Text or Prompt
              </label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={8}
                placeholder="Paste article, document summary, or describe what you want..."
                className={`w-full p-4 rounded-lg border resize-none transition-colors ${
                  isDark 
                    ? "bg-gray-700 border-gray-600 text-white placeholder-gray-400 focus:border-teal-500" 
                    : "bg-gray-50 border-gray-200 text-gray-900 placeholder-gray-400 focus:border-teal-500"
                } focus:outline-none focus:ring-2 focus:ring-teal-500/20`}
              />
              
              {/* File Upload */}
              <div className="mt-4">
                <label className={`block font-semibold mb-2 ${isDark ? "text-white" : "text-gray-900"}`}>
                  Or Upload PDF
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

              {/* Action Buttons */}
              <div className="mt-6 flex gap-3">
                <button
                  onClick={handleGenerate}
                  disabled={loading}
                  className={`flex-1 py-3 px-4 rounded-lg font-semibold transition-all ${
                    loading 
                      ? "opacity-50 cursor-not-allowed" 
                      : "hover:scale-[1.02]"
                  } ${isDark ? "bg-teal-600 text-white hover:bg-teal-500" : "bg-teal-500 text-white hover:bg-teal-600"}`}
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                      </svg>
                      Generating...
                    </span>
                  ) : "Generate"}
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

              <p className={`mt-4 text-xs ${isDark ? "text-gray-500" : "text-gray-400"}`}>
                Tip: Keep input under 15,000 characters for best results.
              </p>
            </div>

            {/* Preview Controls */}
            <div className={`p-6 rounded-xl ${isDark ? "bg-gray-800 border border-gray-700" : "bg-white shadow-lg border border-gray-100"}`}>
              <h3 className={`font-semibold mb-4 ${isDark ? "text-white" : "text-gray-900"}`}>
                Preview Controls
              </h3>
              
              <button
                onClick={handleExport}
                className={`w-full py-3 px-4 rounded-lg font-semibold transition-all hover:scale-[1.02] ${
                  isDark ? "bg-teal-600 text-white hover:bg-teal-500" : "bg-teal-500 text-white hover:bg-teal-600"
                }`}
              >
                <span className="flex items-center justify-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                  </svg>
                  Export PNG
                </span>
              </button>

              {/* Layout Selector */}
              <div className="mt-5">
                <label className={`block font-medium mb-2 ${isDark ? "text-gray-300" : "text-gray-700"}`}>
                  Layout
                </label>
                <select
                  value={layout}
                  onChange={(e) => setLayout(e.target.value)}
                  className={`w-full p-3 rounded-lg border transition-colors ${
                    isDark 
                      ? "bg-gray-700 border-gray-600 text-white" 
                      : "bg-gray-50 border-gray-200 text-gray-900"
                  } focus:outline-none focus:ring-2 focus:ring-teal-500/20`}
                >
                  <option value="vertical_steps">Vertical Steps</option>
                  <option value="timeline">Timeline</option>
                  <option value="grid">Grid</option>
                </select>
              </div>

              {/* Palette Selector */}
              <div className="mt-4">
                <label className={`block font-medium mb-2 ${isDark ? "text-gray-300" : "text-gray-700"}`}>
                  Palette
                </label>
                <select
                  value={palette}
                  onChange={(e) => setPalette(e.target.value)}
                  className={`w-full p-3 rounded-lg border transition-colors ${
                    isDark 
                      ? "bg-gray-700 border-gray-600 text-white" 
                      : "bg-gray-50 border-gray-200 text-gray-900"
                  } focus:outline-none focus:ring-2 focus:ring-teal-500/20`}
                >
                  <option value="teal">Teal</option>
                  <option value="warm">Warm</option>
                  <option value="mono">Mono</option>
                </select>
              </div>

              {/* Raw Output Debug */}
              {rawOutput && (
                <details className="mt-4">
                  <summary className={`cursor-pointer text-sm ${isDark ? "text-gray-400" : "text-gray-500"}`}>
                    Show raw model output (debug)
                  </summary>
                  <pre className={`mt-2 p-3 rounded-lg text-xs overflow-auto max-h-48 ${
                    isDark ? "bg-gray-700 text-gray-300" : "bg-gray-100 text-gray-700"
                  }`}>
                    {rawOutput}
                  </pre>
                </details>
              )}
            </div>
          </div>

          {/* Infographic Preview */}
          <div className="lg:col-span-2">
            <div
              ref={infographicRef}
              className={`rounded-2xl overflow-hidden shadow-xl ${isDark ? "bg-gray-800" : "bg-white"}`}
            >
              {/* Header */}
              <div className={`p-8 text-center border-b ${isDark ? "border-gray-700" : "border-gray-100"}`}>
                <h1 className={`text-3xl font-bold ${isDark ? "text-white" : "text-gray-900"}`}>
                  {infographic.title}
                </h1>
                <p className={`mt-2 ${isDark ? "text-gray-400" : "text-gray-500"}`}>
                  {infographic.subtitle}
                </p>
              </div>

              {/* Blocks */}
              <div className={`p-8 ${
                layout === "grid" 
                  ? "grid grid-cols-1 md:grid-cols-2 gap-6" 
                  : "flex flex-col gap-5"
              }`}>
                {infographic.blocks.map((block, idx) => (
                  <div
                    key={block.id}
                    className={`flex gap-5 p-5 rounded-xl transition-all ${
                      layout === "timeline" ? "relative pl-16" : ""
                    } ${isDark ? "bg-gray-700/50" : "bg-gray-50"}`}
                  >
                    {/* Timeline connector */}
                    {layout === "timeline" && (
                      <>
                        <div className={`absolute left-6 top-0 bottom-0 w-0.5 ${
                          isDark ? "bg-gray-600" : "bg-gray-200"
                        } ${idx === 0 ? "top-1/2" : ""} ${idx === infographic.blocks.length - 1 ? "bottom-1/2" : ""}`} />
                        <div 
                          className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 rounded-full border-2 flex items-center justify-center"
                          style={{ 
                            borderColor: paletteColors[idx % paletteColors.length],
                            backgroundColor: isDark ? "#374151" : "#ffffff"
                          }}
                        >
                          <div 
                            className="w-2 h-2 rounded-full"
                            style={{ backgroundColor: paletteColors[idx % paletteColors.length] }}
                          />
                        </div>
                      </>
                    )}

                    {/* Icon */}
                    <div
                      className="flex-shrink-0 w-16 h-16 rounded-xl flex items-center justify-center text-3xl shadow-md"
                      style={{ backgroundColor: paletteColors[idx % paletteColors.length] }}
                    >
                      {getIconEmoji(block.icon)}
                    </div>

                    {/* Content */}
                    <div className="flex-1">
                      <h3 className={`font-bold text-lg mb-2 ${isDark ? "text-white" : "text-gray-900"}`}>
                        {block.heading}
                      </h3>
                      <ul className={`space-y-1 ${isDark ? "text-gray-300" : "text-gray-600"}`}>
                        {block.bullets.map((bullet, bIdx) => (
                          <li key={bIdx} className="flex items-start gap-2">
                            <span className={isDark ? "text-teal-400" : "text-teal-500"}>•</span>
                            {bullet}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <p className={`mt-4 text-center text-sm ${isDark ? "text-gray-500" : "text-gray-400"}`}>
              Preview your infographic above. Use Export to save as PNG.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

function App() {
  return (
    <ThemeProvider>
      <div className="App">
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/app" element={<MainApp />} />
          </Routes>
        </BrowserRouter>
        <ThemeToggle />
      </div>
    </ThemeProvider>
  );
}

export default App;
