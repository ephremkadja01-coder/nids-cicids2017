import { useState, useRef } from "react";
import { BentoGridShowcase } from "@/components/ui/bento-product-features";
import { AILoader } from "@/components/ui/ai-loader";
import { Shield, Activity, TerminalSquare, Mic, Send, Gauge, Zap, ShieldAlert, Square, Volume2 } from "lucide-react";
import ReactMarkdown from 'react-markdown';

function App() {
  const [status, setStatus] = useState<'idle' | 'listening' | 'analyzing' | 'result'>('idle');
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<any>(null);
  
  // Refs pour l'enregistrement audio
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startListening = async () => {
    try {
      // Demander l'accès au micro
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        // Quand on arrête, on crée le fichier audio et on l'envoie
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await transcribeAudio(audioBlob);
        
        // Couper le micro
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setStatus('listening');
    } catch (error) {
      alert("Impossible d'accéder au micro. Vérifie les permissions.");
      setStatus('idle');
    }
  };

  const stopListening = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
      setStatus('analyzing'); // On passe en mode réflexion pendant la transcription
    }
  };

  const transcribeAudio = async (audioBlob: Blob) => {
    const formData = new FormData();
    formData.append("file", audioBlob, "audio.webm");

    try {
      // 1. Envoyer l'audio au backend pour transcription (Groq Whisper)
      const transcribeRes = await fetch("http://127.0.0.1:8000/api/v1/transcribe", {
        method: "POST",
        body: formData,
      });
      const transcribeData = await transcribeRes.json();
      
      const text = transcribeData.text;
      setQuery(text);

      // 2. Une fois transcrit, on lance l'analyse IA
      await analyzeThreat(text);

    } catch (error) {
      alert("Erreur de transcription.");
      setStatus('idle');
    }
  };

  const analyzeThreat = async (text: string) => {
    if (!text.trim()) return;
    setStatus('analyzing');
    setResult(null);
    
    try {
      const response = await fetch("http://127.0.0.1:8000/api/v1/agent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: text,
          features: { "Destination Port": 80, "Flow Duration": 100, "Total Fwd Packets": 5 }
        })
      });
      const data = await response.json();
      setResult(data);
      setStatus('result');
      
      if (data.agent_response) {
        speakResponse(data.agent_response);
      }
    } catch (error) {
      alert("Erreur : Le backend est-il allumé ?");
      setStatus('idle');
    }
  };

  const speakResponse = (text: string) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.onvoiceschanged = () => {
        const voices = window.speechSynthesis.getVoices();
        const frenchVoices = voices.filter(v => v.lang.startsWith('fr'));
        let selectedVoice = frenchVoices.find(v => v.name.includes('Google') || v.name.includes('Natural')) || frenchVoices[0];

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'fr-FR';
        if (selectedVoice) utterance.voice = selectedVoice;
        utterance.rate = 1.0;
        window.speechSynthesis.speak(utterance);
      };
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    analyzeThreat(query);
  };

  const ProCard = ({ title, icon, children, className = "" }: { title: string, icon: React.ReactNode, children: React.ReactNode, className?: string }) => (
    <div className={`relative flex flex-col justify-between h-full p-6 bg-[#0c0c0e] border border-zinc-800/80 rounded-2xl overflow-hidden hover:border-zinc-700 transition-all duration-300 ${className}`}>
      <div className="flex items-center gap-2 mb-4">
        {icon}
        <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">{title}</h3>
      </div>
      {children}
    </div>
  );

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto">
        
        {/* Header */}
        <div className="mb-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div className="flex items-center gap-4">
            <div className="p-2.5 bg-blue-500/10 rounded-xl border border-blue-500/20">
              <Shield className="w-7 h-7 text-blue-500" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">NIDS <span className="text-blue-500">SOC</span></h1>
              <p className="text-sm text-zinc-400 mt-1">Détection d'Intrusion Réseau par l'IA</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2 w-full md:w-auto">
            <form onSubmit={handleSubmit} className="relative flex-1 md:w-80">
              <input 
                type="text" value={query} onChange={(e) => setQuery(e.target.value)}
                placeholder="Interroger l'Agent..."
                className="w-full bg-[#0c0c0e] border border-zinc-800 text-sm text-white px-4 py-2.5 rounded-lg focus:outline-none focus:border-blue-500"
                disabled={status === 'analyzing' || status === 'listening'}
              />
              <button type="submit" className="absolute right-2 top-2.5 text-zinc-500 hover:text-blue-500">
                <Send className="w-4 h-4" />
              </button>
            </form>
            
            <button 
              onClick={status === 'listening' ? stopListening : startListening} 
              disabled={status === 'analyzing'}
              className={`px-4 py-2.5 rounded-lg flex items-center gap-2 text-sm font-medium transition-all ${
                status === 'listening' ? "bg-red-600 text-white animate-pulse" : "bg-blue-600 hover:bg-blue-500 text-white"
              }`}
            >
              {status === 'listening' ? <Square className="w-4 h-4 fill-white" /> : <Mic className="w-4 h-4" />}
              {status === 'listening' ? "Arrêter" : "Vocal"}
            </button>
          </div>
        </div>

        {/* Bento Grid */}
        <BentoGridShowcase
          integration={
            <ProCard title="Analyse de l'Agent IA" icon={<Activity className="w-4 h-4 text-blue-500" />} className="bg-gradient-to-br from-[#0c0c0e] to-[#121216]">
              <div className="flex-1 flex flex-col mt-2">
                {status === 'listening' || status === 'analyzing' ? (
                  <div className="flex-1 flex flex-col items-center justify-center">
                    <AILoader text={status === 'listening' ? "Écoute" : "Réflexion"} />
                  </div>
                ) : status === 'result' && result ? (
                   <div className="w-full">
                      <div className="mb-4 p-3 bg-zinc-900 rounded-lg border border-zinc-800 text-sm italic text-zinc-400">"{query}"</div>
                      <div className={`p-4 rounded-lg border text-sm leading-relaxed ${result.is_attack ? 'bg-red-500/10 border-red-500/20 text-red-200' : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-200'}`}>
                        <div className="flex justify-between items-start">
                          <strong>Agent :</strong>
                          <button onClick={() => speakResponse(result.agent_response)} className="text-zinc-500 hover:text-white">
                            <Volume2 className="w-4 h-4" />
                          </button>
                        </div>
                        <div className="mt-2 prose prose-invert prose-sm">
                          <ReactMarkdown>{result.agent_response}</ReactMarkdown>
                        </div>
                      </div>
                   </div>
                ) : (
                  <div className="flex-1 flex flex-col items-center justify-center opacity-40">
                    <Mic className="w-8 h-8 text-zinc-500 mb-4" />
                    <p className="text-xs font-mono">Clique sur "Vocal" pour parler</p>
                  </div>
                )}
              </div>
            </ProCard>
          }
          trackers={
            <ProCard title="Alertes Actives" icon={<ShieldAlert className="w-4 h-4 text-zinc-400" />}>
              <div>
                <div className="flex items-baseline gap-2">
                  <p className={`text-4xl font-bold tracking-tighter ${result?.is_attack ? 'text-red-500' : 'text-zinc-200'}`}>
                    {result ? result.active_alerts : "--"}
                  </p>
                  <span className="text-sm text-zinc-500">menace(s)</span>
                </div>
                <p className="text-xs text-zinc-500 font-mono mt-2">{result?.is_attack ? "Investigation requise" : "Système sain"}</p>
              </div>
            </ProCard>
          }
          statistic={
            <ProCard title="Temps d'Inférence" icon={<Zap className="w-4 h-4 text-zinc-400" />}>
              <div>
                <div className="flex items-baseline gap-2">
                  <p className="text-4xl font-bold text-white tracking-tighter">{result ? result.inference_time_ms : "--"}</p>
                  <span className="text-sm text-zinc-500">ms</span>
                </div>
                <p className="text-xs text-zinc-500 font-mono mt-2">Modèle XGBoost</p>
              </div>
            </ProCard>
          }
          focus={
            <ProCard title="Indice de Risque" icon={<Gauge className="w-4 h-4 text-zinc-400" />}>
              <div>
                <div className="flex items-baseline gap-2">
                  <p className={`text-3xl font-bold tracking-tighter ${result?.is_attack ? 'text-orange-500' : 'text-emerald-500'}`}>
                    {result ? result.risk_score : "--"}
                  </p>
                  <span className="text-sm text-zinc-500">/ 100</span>
                </div>
                <div className="w-full bg-zinc-800 rounded-full h-1.5 mt-3">
                  <div className={`h-1.5 rounded-full transition-all duration-1000 ${result?.is_attack ? 'bg-orange-500' : 'bg-emerald-500'}`} 
                       style={{ width: result ? `${result.risk_score}%` : '0%' }}></div>
                </div>
              </div>
            </ProCard>
          }
          productivity={
            <ProCard title="Flux Analysés" icon={<Activity className="w-4 h-4 text-zinc-400" />}>
              <div>
                <div className="flex items-baseline gap-2">
                  <p className="text-4xl font-bold text-white tracking-tighter">{result ? "1" : "--"}</p>
                  <span className="text-sm text-zinc-500">flux</span>
                </div>
                <p className="text-xs text-zinc-500 font-mono mt-2">Traité lors de cette requête</p>
              </div>
            </ProCard>
          }
          shortcuts={
            <ProCard title="Traçabilité (Preuves d'exécution)" icon={<TerminalSquare className="w-4 h-4 text-zinc-400" />} className="bg-[#0c0c0e] border-zinc-800">
              <div className="font-mono text-xs overflow-y-auto max-h-[120px] mt-2 text-zinc-400 space-y-2">
                {status === 'idle' && <p className="text-zinc-600">$ En attente...</p>}
                {status === 'result' && result && (
                  <>
                    <div className="p-2 bg-zinc-900 rounded border border-zinc-800">
                      <span className="text-blue-400">[1] Entrée Utilisateur :</span> <br />
                      "{query}"
                    </div>
                    <div className="p-2 bg-zinc-900 rounded border border-zinc-800">
                      <span className="text-purple-400">[2] Analyse XGBoost :</span> <br />
                      Verdict : {result.trace?.ml_verdict} <br />
                      Confiance : {result.trace?.ml_probability}
                    </div>
                    <div className="p-2 bg-zinc-900 rounded border border-zinc-800">
                      <span className="text-emerald-400">[3] LLM utilisé :</span> <br />
                      {result.trace?.model_used}
                    </div>
                  </>
                )}
                {status === 'listening' && <p className="text-red-400">$ [MIC] Enregistrement en cours...</p>}
                {status === 'analyzing' && <p className="text-purple-400">$ Transcription et analyse en cours...</p>}
                {status === 'result' && !result?.trace && (
                  <p className="text-zinc-600">Les données de traçabilité ne sont pas disponibles.</p>
                )}
                {status !== 'idle' && status !== 'result' && (
                  <div className="flex items-center mt-2 text-zinc-500">
                    <span>$</span><span className="w-2 h-4 bg-zinc-500 ml-2 animate-pulse"></span>
                  </div>
                )}
              </div>
            </ProCard>
          }
        />
      </div>
    </div>
  );
}

export default App;