'use client'
import { useState, useRef, useEffect, FC } from 'react';
import { 
  MessageSquare, Send, Loader2, Bot, User, TrendingUp, BarChart3, 
  ShieldCheck, Briefcase, ChevronDown, Copy, Check, Sparkles, Activity, Database,
  Sun, Cloud, CloudRain, CloudSnow, Wind, Droplets, MapPin, Globe
} from 'lucide-react';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend, Filler
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend, Filler);

// --- INTERFACES & COMPONENTS ---
interface Message {
  sender: 'user' | 'bot';
  content: any;
  type: 'summary' | 'data_chart' | 'prediction_chart' | 'live_weather' | 'text' | 'error';
  summary?: string;
  sql_query?: string;
  unit?: string;
  timestamp?: Date;
}

const SingleValueDisplay: FC<{ value: any; label: string; unit: string }> = ({ value, label, unit }) => {
  const formattedValue = typeof value === 'number' ? new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 2 }).format(value) : String(value);
  return (
    <div className="bg-gray-800 p-4 rounded-lg text-center"><p className="text-sm text-gray-400 uppercase tracking-wider">{label.replace(/_/g, ' ')}</p><p className="text-4xl font-bold text-teal-400 mt-1">{formattedValue}</p>{unit && <p className="text-sm text-gray-400 mt-1">{unit}</p>}</div>
  );
};

const WeatherDisplay: FC<{ data: any }> = ({ data }) => {
  const getWeatherIcon = (condition: string) => {
    const lowerCaseCondition = condition.toLowerCase();
    if (lowerCaseCondition.includes('clear')) return <Sun className="w-12 h-12 text-yellow-400" />;
    if (lowerCaseCondition.includes('rain')) return <CloudRain className="w-12 h-12 text-blue-400" />;
    if (lowerCaseCondition.includes('snow')) return <CloudSnow className="w-12 h-12 text-white" />;
    return <Cloud className="w-12 h-12 text-gray-400" />;
  };
  return (
    <div className="bg-gradient-to-br from-blue-900/30 via-gray-900/30 to-gray-900/30 p-6 rounded-2xl border border-blue-500/20">
      <div className="flex justify-between items-start"><div><h3 className="text-2xl font-bold">{data.city}, {data.country}</h3><p className="text-gray-400 capitalize">{data.description}</p></div>{getWeatherIcon(data.condition)}</div>
      <div className="mt-4 flex items-end justify-between"><p className="text-7xl font-black text-white">{Math.round(data.temperature)}<span className="text-3xl text-gray-400 align-super">°C</span></p><div className="text-right"><p className="text-sm text-gray-300">H: {Math.round(data.temp_max)}° / L: {Math.round(data.temp_min)}°</p></div></div>
      <div className="mt-6 pt-4 border-t border-gray-700/50 grid grid-cols-2 gap-4 text-sm"><div className="flex items-center space-x-2"><Droplets className="w-5 h-5 text-blue-300" /><p>Humidity: {data.humidity}%</p></div><div className="flex items-center space-x-2"><Wind className="w-5 h-5 text-gray-300" /><p>Wind: {data.wind_speed} m/s</p></div></div>
    </div>
  );
};

const QuickActions: FC<{ onActionClick: (action: string) => void }> = ({ onActionClick }) => {
  const actions = [
    { icon: TrendingUp, label: "National CO2 Trends", query: "Show the CO2 trend for Germany since 2000" },
    { icon: Briefcase, label: "Corporate Emissions", query: "What were the scope 1 emissions for TechCorp in 2022?" },
    { icon: Globe, label: "GDP Forecast", query: "Forecast GDP for India" },
    { icon: MapPin, label: "Live Weather", query: "What's the weather in Tokyo?" }
  ];
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      {actions.map((action, index) => (<button key={index} onClick={() => onActionClick(action.query)} className="group relative p-4 bg-gray-800/50 rounded-xl border border-gray-700/50 hover:border-teal-500/30 transition-all duration-300 hover:scale-105"><div className="relative flex flex-col items-center space-y-2"><action.icon className="w-6 h-6 text-teal-400 group-hover:text-teal-300 transition-colors" /><span className="text-xs text-gray-300 group-hover:text-white text-center font-medium">{action.label}</span></div></button>))}
    </div>
  );
};

const SqlQueryDisplay: FC<{ query: string }> = ({ query }) => {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => { navigator.clipboard.writeText(query); setCopied(true); setTimeout(() => setCopied(false), 2000); };
  return (<details className="mt-4 group"><summary className="flex items-center justify-between cursor-pointer text-sm text-gray-400 hover:text-teal-400 p-3 bg-gray-900/50 rounded-t-lg border border-gray-700/30"><div className="flex items-center space-x-2"><Database className="w-4 h-4" /><span>Generated SQL Query</span></div><ChevronDown className="w-4 h-4 transition-transform duration-200 group-open:rotate-180" /></summary><div className="relative"><button onClick={handleCopy} className="absolute top-2 right-2 p-1.5 bg-gray-700/50 hover:bg-gray-600/50 rounded-md">{copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4 text-gray-400" />}</button><pre className="bg-gray-950/80 p-4 pt-8 rounded-b-lg border-x border-b border-gray-700/50 text-sm text-teal-300 overflow-x-auto"><code>{query}</code></pre></div></details>);
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([{ sender: 'bot', type: 'text', content: "Welcome to ClimateLens Pro! 🌍 I'm your AI-powered climate data analyst. Ask me anything about climate trends, emissions data, or request forecasts. Try one of the quick actions below to get started!", timestamp: new Date() }]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const handleSendMessage = async (messageContent?: string) => {
    const query = (typeof messageContent === 'string' ? messageContent : input).trim();
    if (query === '' || isLoading) return;
    setMessages(prev => [...prev, { sender: 'user', content: query, type: 'text', timestamp: new Date() }]);
    setInput('');
    setIsLoading(true);
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);
      const response = await fetch('http://localhost:5001/api/ask', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query }), signal: controller.signal });
      clearTimeout(timeoutId);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'An unknown server error occurred.');
      
      const botMessage: Message = {
        sender: 'bot',
        type: data.answer_type,
        content: data.data,
        summary: data.summary,
        sql_query: data.sql_query,
        unit: data.unit,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botMessage]);

    } catch (error: any) {
      let errorMessage = "Sorry, an error occurred while processing your request.";
      if (error.name === 'AbortError') errorMessage = "The request took too long and timed out.";
      else if (error.message) errorMessage = error.message;
      setMessages(prev => [...prev, { sender: 'bot', content: `Sorry, ${errorMessage.toLowerCase()}`, type: 'error', timestamp: new Date() }]);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleQuickAction = (query: string) => {
    handleSendMessage(query);
  };
  
  const renderMessageContent = (msg: Message) => {
    if (msg.sender === 'user' || !['summary', 'data_chart', 'prediction_chart', 'live_weather'].includes(msg.type)) {
      return <p className={msg.type === 'error' ? 'text-red-400' : 'text-gray-100'}>{msg.content}</p>;
    }
    const { unit = "", sql_query, summary, content } = msg;
    const commonChartContainer = (chartComponent: React.ReactNode) => (
      <div className="space-y-4">{summary && (<div className="p-4 bg-gray-900/50 rounded-xl border border-gray-700/30"><div className="flex items-start space-x-3"><Sparkles className="w-5 h-5 text-teal-400 mt-0.5" /><p className="text-gray-200 leading-relaxed">{summary}</p></div></div>)}<div className="bg-gray-800/50 p-4 rounded-xl border border-gray-700/30 min-h-[300px]">{chartComponent}</div>{sql_query && <SqlQueryDisplay query={sql_query} />}</div>
    );
    const chartOptions = (axis: 'x' | 'y' = 'x') => ({
      indexAxis: axis, plugins: { tooltip: { callbacks: { label: (c: any) => `${c.dataset.label}: ${new Intl.NumberFormat('en-US',{maximumFractionDigits: 3}).format(c.raw)} ${unit}` } }, legend: { labels: { color: '#e5e7eb' } } },
      scales: { x: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255, 255, 255, 0.1)' } }, y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255, 255, 255, 0.1)' }, title: { display: true, text: unit, color: '#9ca3af' } } }
    });
    switch (msg.type) {
      case 'summary': return <p>{content}</p>;
      case 'live_weather': return commonChartContainer(<WeatherDisplay data={content} />);
      case 'data_chart':
        if (!Array.isArray(content) || content.length === 0) return commonChartContainer(<p>Sorry, no data was found for this query.</p>);
        if (content.length === 1 && Object.keys(content[0]).length === 1) { const key = Object.keys(content[0])[0]; return commonChartContainer(<SingleValueDisplay value={content[0][key]} label={key} unit={unit} />); }
        const keys = Object.keys(content[0]);
        const isTimeSeries = keys.includes('year');
        const labelKey = isTimeSeries ? 'year' : (keys.find(k => typeof content[0][k] === 'string') || keys[0]);
        const dataKey = keys.find(k => typeof content[0][k] === 'number') || keys[1];
        if (!dataKey) return <p>Could not determine data series to plot.</p>;
        const chartData = { labels: content.map((item: any) => item[labelKey]), datasets: [{ label: dataKey.replace(/_/g, ' ').toUpperCase(), data: content.map((item: any) => item[dataKey]), backgroundColor: 'rgba(29, 209, 161, 0.7)', borderColor: 'rgba(29, 209, 161, 1)', borderWidth: 1 }] };
        return commonChartContainer(<div className="h-[300px]">{isTimeSeries ? <Line data={chartData} options={chartOptions('x')} /> : <Bar data={chartData} options={chartOptions('y')} />}</div>);
      case 'prediction_chart':
        const { historical, predicted, metric } = content;
        const predChartData = { labels: [...historical.map((i: any) => i.year), ...predicted.map((i: any) => i.year)], datasets: [ { label: `Historical ${metric.toUpperCase()}`, data: historical.map((i: any) => i[metric]), borderColor: 'rgba(29, 209, 161, 1)', tension: 0.1 }, { label: `Predicted ${metric.toUpperCase()}`, data: [...Array(historical.length - 1).fill(null), historical[historical.length - 1][metric], ...predicted.map((i: any) => i.value)], borderColor: 'rgba(255, 99, 132, 1)', borderDash: [5, 5], tension: 0.1 } ] };
        return commonChartContainer(<div className="h-[300px]"><Line data={predChartData} options={chartOptions('x')} /></div>);
      default: return <p>Unsupported message type.</p>;
    }
  };
  const formatTime = (date?: Date) => { if (!date) return ''; return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true }); };
  
  return (
    <div className="flex flex-col h-screen bg-gray-900 text-gray-100 font-sans">
      <header className="relative bg-gray-900/80 backdrop-blur-xl p-4 shadow-md border-b border-gray-700/50">
        <div className="max-w-7xl mx-auto flex items-center space-x-4"><div className="relative"><div className="absolute -inset-1 bg-gradient-to-r from-teal-500 to-blue-500 rounded-lg blur opacity-75"></div><div className="relative p-2 bg-gray-800 rounded-lg"><MessageSquare className="text-white" size={24}/></div></div><h1 className="text-xl font-bold">ClimateLens Pro</h1></div>
      </header>
      <main className="flex-1 overflow-y-auto p-6 space-y-8">
        <div className="max-w-4xl mx-auto">{messages.length === 1 && <QuickActions onActionClick={handleQuickAction} />}{messages.map((msg, index) => (<div key={index} className={`flex items-start gap-4 ${msg.sender === 'user' ? 'justify-end' : ''} mb-6`}>{msg.sender === 'bot' && <div className="p-2 bg-gray-700 rounded-full"><Bot className="text-teal-400" /></div>}<div className={`p-4 rounded-xl shadow-lg max-w-3xl ${msg.sender === 'user' ? 'bg-teal-700' : 'bg-gray-800/50'}`}>{renderMessageContent(msg)}</div>{msg.sender === 'user' && <div className="p-2 bg-gray-700 rounded-full"><User /></div>}</div>))}{isLoading && (<div className="flex items-start gap-4"><div className="p-2 bg-gray-700 rounded-full"><Bot className="text-teal-400" /></div><div className="p-4 rounded-lg bg-gray-700 flex items-center space-x-2"><Loader2 className="animate-spin text-teal-400" /><span>Analyzing...</span></div></div>)}<div ref={messagesEndRef} /></div>
      </main>
      <footer className="p-4 bg-gray-900/80 backdrop-blur-sm border-t border-gray-700/50">
        <div className="max-w-4xl mx-auto flex items-center gap-2"><input type="text" value={input} onChange={(e) => setInput(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()} placeholder="Ask for summaries, data, or predictions..." className="w-full p-3 bg-gray-700 rounded-lg border border-gray-600 focus:outline-none focus:ring-2 focus:ring-teal-500" disabled={isLoading} /><button onClick={() => handleSendMessage()} className="bg-teal-600 p-3 rounded-lg hover:bg-teal-500 disabled:bg-gray-600" disabled={isLoading}><Send /></button></div>
      </footer>
    </div>
  );
}