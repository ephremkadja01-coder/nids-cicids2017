import { useState, useRef, useEffect } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { BentoGridShowcase } from "@/components/ui/bento-product-features";
import { AILoader } from "@/components/ui/ai-loader";
import { Shield, Activity, TerminalSquare, Mic, Send, Gauge, Zap, ShieldAlert, Square, Volume2, Wifi, Upload } from "lucide-react";
import ReactMarkdown from 'react-markdown';

gsap.registerPlugin(useGSAP);

// --- ANIMATION 2 : Composant Compteur Animé ---
const AnimatedNumber = ({ value, decimals = 0 }: { value: number | string, decimals?: number }) => {
  const ref = useRef<HTMLSpanElement>(null);
  
  useGSAP(() => {
    if (!ref.current || typeof value !== 'number') return;
    const obj = { val: 0 };
    gsap.to(obj, {
      val: value,
      duration: 1.5,
      ease: "power3.out",
      onUpdate: () => {
        if (ref.current) ref.current.textContent = obj.val.toFixed(decimals);
      }
    });
  }, [value]);

  if (typeof value !== 'number') return <span>{value}</span>;
  return <span ref={ref}>0</span>;
};

function App() {
  const [status, setStatus] = useState<'idle' | 'listening' | 'analyzing' | 'result'>('idle');
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<any>(null);
  
  // --- ÉTATS WEBSOCKET ---
  const [liveFeed, setLiveFeed] = useState<any[]>([]);
  const [liveAlerts, setLiveAlerts] = useState(0);
  const [wsConnected, setWsConnected] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);
  
  // --- REFS POUR ANIMATIONS 3 & 4 ---
  const alertCardRef = useRef<HTMLDivElement>(null);
  const liveFeedCardRef = useRef<HTMLDivElement>(null);

  // --- ANIMATION 1 : Stagger des cartes (Apparition en cascade) ---
  useGSAP(() => {
    gsap.from(".dashboard-header", { opacity: 0, y: 18, duration: 0.7, ease: "power2.out" });
    gsap.from(".gsap-stagger", {
      y: 30, opacity: 0, duration: 0.8, stagger: 0.1, ease: "power3.out", delay: 0.2
    });
  }, { scope: containerRef });

  // --- ANIMATION 3 : Pulsation rouge sur alerte ---
  useGSAP(() => {
    if ((liveAlerts > 0 || result?.active_alerts > 0) && alertCardRef.current) {
      gsap.fromTo(alertCardRef.current,
        { boxShadow: "0 0 0 0 rgba(239, 68, 68, 0.7)" },
        { boxShadow: "0 0 0 20px rgba(239, 68, 68, 0)", duration: 1, ease: "power2.out" }
      );
    }
  }, [liveAlerts, result]);

  // --- ANIMATION 4 : Flash bleu sur le flux Scapy ---
  useGSAP(() => {
    if (liveFeed.length > 0 && liveFeedCardRef.current) {
      gsap.fromTo(liveFeedCardRef.current,
        { backgroundColor: "rgba(59, 130, 246, 0.2)" },
        { backgroundColor: "transparent", duration: 0.4, ease: "power1.out" }
      );
    }
  }, [liveFeed]);

  // --- CONNEXION WEBSOCKET ---
  useEffect(() => {
    let ws: WebSocket;
    let reconnectTimeout: any;

    const connectWebSocket = () => {
      ws = new WebSocket("ws://127.0.0.1:8000/api/v1/ws/alerts");
      
      ws.onopen = () => {
        console.log("✅ WebSocket connecté !");
        setWsConnected(true);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setLiveFeed(prev => [{ ...data, id: Date.now() }, ...prev].slice(0, 4));
        if (data.is_attack) {
          setLiveAlerts(prev => prev + 1);
        }
      };

      ws.onclose = () => {
        console.log("❌ WebSocket déconnecté. Reconnexion...");
        setWsConnected(false);
        reconnectTimeout = setTimeout(connectWebSocket, 3000);
      };
    };

    connectWebSocket();
    return () => { if (ws) ws.close(); clearTimeout(reconnectTimeout); };
  }, []);

  const startListening = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await transcribeAudio(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setStatus('listening');
    } catch (error) {
      alert("Impossible d'accéder au micro.");
      setStatus('idle');
    }
  };

  const stopListening = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
      setStatus('analyzing');
    }
  };

  const transcribeAudio = async (audioBlob: Blob) => {
    const formData = new FormData();
    formData.append("file", audioBlob, "audio.webm");

    try {
      const transcribeRes = await fetch("http://127.0.0.1:8000/api/v1/transcribe", {
        method: "POST",
        body: formData,
      });
      
      if (!transcribeRes.ok) throw new Error("Erreur serveur transcription");
      
      const transcribeData = await transcribeRes.json();
      
      // ✅ CORRECTION 1 : On s'assure que le texte n'est pas undefined
      const text = transcribeData.text || "";
      setQuery(text);
      
      if (text.trim()) {
        await analyzeThreat(text);
      } else {
        setStatus('idle');
      }
    } catch (error) {
      console.error("Erreur transcription:", error);
      alert("Erreur de transcription. Vérifie le terminal backend.");
      setStatus('idle');
    }
  };

  const analyzeThreat = async (text: string) => {
    if (!text.trim()) return;
    setStatus('analyzing');
    setResult(null);

    const featuresToSend = liveFeed.length > 0
      ? { "Destination Port": liveFeed[0].port || 80 }
      : { "Destination Port": 80, "Flow Duration": 100, "Total Fwd Packets": 5 };
    
    try {
      const response = await fetch("http://127.0.0.1:8000/api/v1/agent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: text,
          features: featuresToSend,
          live_alerts: liveAlerts 
        })
      });
      const data = await response.json();
      setResult(data);
      setStatus('result');
      if (data.agent_response) speakResponse(data.agent_response);
    } catch (error) {
      alert("Erreur : Le backend est-il allumé ?");
      setStatus('idle');
    }
  };

  // ✅ CORRECTION 2 : Meilleure gestion de la voix et nettoyage du texte
  const speakResponse = (text: string) => {
    if (!('speechSynthesis' in window) || !text.trim()) return;

    // 1. Nettoyer le texte (enlever le Markdown comme ** ou #)
    const cleanText = text.replace(/[*#_]/g, '').replace(/\n/g, ' ');

    const synthesis = window.speechSynthesis;
    synthesis.cancel(); // Annuler toute lecture en cours

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = 'fr-FR';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    // 2. Chercher la meilleure voix française disponible
    const setVoiceAndSpeak = () => {
      const voices = synthesis.getVoices();
      const frenchVoices = voices.filter(voice => voice.lang.startsWith('fr'));
      
      // On privilégie les voix Google, Natural ou Microsoft
      const bestVoice = frenchVoices.find(voice => 
        /google|natural|microsoft/i.test(voice.name)
      ) || frenchVoices[0];

      if (bestVoice) {
        utterance.voice = bestVoice;
      }
      synthesis.speak(utterance);
    };

    // Parfois, les voix mettent du temps à charger
    if (synthesis.getVoices().length === 0) {
      synthesis.onvoiceschanged = setVoiceAndSpeak;
    } else {
      setVoiceAndSpeak();
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    analyzeThreat(query);
  };

  const ProCard = ({ title, icon, children, className = "" }: { title: string, icon: React.ReactNode, children: React.ReactNode, className?: string }) => (
    <div className={`gsap-stagger relative flex flex-col justify-between h-full p-6 bg-[#0c0c0e] border border-zinc-800/80 rounded-2xl overflow-hidden hover:border-zinc-700 transition-all duration-300 ${className}`}>
      <div className="flex items-center gap-2 mb-4">
        {icon}
        <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">{title}</h3>
      </div>
      {children}
    </div>
  );

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setQuery(`Analyse du fichier : ${file.name}`);
    setStatus('analyzing');
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/upload-csv", { method: "POST", body: formData });
      const data = await res.json();
      
      if (data.data && data.data.length > 0) {
        const attacks = data.attacks_found;
        const total = data.total_analyzed;
        const agentText = `Analyse du fichier ${file.name} terminée. J'ai analysé un échantillon aléatoire de ${total} flux. Attention : ${attacks} attaques ont été détectées. ${attacks > 0 ? "Une investigation immédiate est requise pour identifier la source de ces menaces." : "Le trafic semble sain."}`;

        setResult({
          is_attack: attacks > 0,
          risk_score: attacks > 0 ? Math.min(100, Math.round((attacks / total) * 100 * 2)) : 0,
          active_alerts: attacks,
          inference_time_ms: 0,
          agent_response: agentText,
          trace: { 
            ml_verdict: attacks > 0 ? "ATTACK DETECTED" : "BENIGN", 
            ml_probability: `${attacks} attaques / ${total} flux`, 
            model_used: "XGBoost (Batch CSV)", 
            live_alerts_seen: attacks 
          }
        });
        speakResponse(agentText);
      }
      setStatus('result');
    } catch (error) {
      alert("Erreur upload CSV");
      setStatus('idle');
    }
  };

  return (
    <div ref={containerRef} className="min-h-screen bg-[#09090b] text-zinc-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto">
        
        {/* Header */}
        <div className="dashboard-header mb-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div className="flex items-center gap-4">
            <div className="p-2.5 bg-blue-500/10 rounded-xl border border-blue-500/20">
              <Shield className="w-7 h-7 text-blue-500" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
                NIDS <span className="text-blue-500">SOC</span>
                <div className={`flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono border ${wsConnected ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-red-500/10 border-red-500/30 text-red-400'}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${wsConnected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`}></span>
                  {wsConnected ? "LIVE" : "OFFLINE"}
                </div>
              </h1>
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

            <label className="cursor-pointer px-4 py-2.5 rounded-lg flex items-center gap-2 text-sm font-medium bg-zinc-800 hover:bg-zinc-700 text-white transition-all">
              <Upload className="w-4 h-4" />
              <span className="hidden md:inline">CSV</span>
              <input type="file" accept=".csv" className="hidden" onChange={handleFileUpload} />
            </label>
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
            <div ref={alertCardRef} className="h-full rounded-2xl">
              <ProCard title="Alertes Actives" icon={<ShieldAlert className="w-4 h-4 text-zinc-400" />}>
                <div>
                  <div className="flex items-baseline gap-2">
                    <p className={`text-4xl font-bold tracking-tighter ${liveAlerts > 0 || result?.is_attack ? 'text-red-500' : 'text-zinc-200'}`}>
                      <AnimatedNumber value={liveAlerts > 0 ? liveAlerts : (result ? result.active_alerts : 0)} decimals={0} />
                    </p>
                    <span className="text-sm text-zinc-500">menace(s)</span>
                  </div>
                  <p className="text-xs text-zinc-500 font-mono mt-2">
                    {liveAlerts > 0 || result?.is_attack ? "Investigation requise" : "Système sain"}
                  </p>
                </div>
              </ProCard>
            </div>
          }
          statistic={
            <ProCard title="Temps d'Inférence" icon={<Zap className="w-4 h-4 text-zinc-400" />}>
              <div>
                <div className="flex items-baseline gap-2">
                  <p className="text-4xl font-bold text-white tracking-tighter">
                    {result && result.inference_time_ms ? <AnimatedNumber value={result.inference_time_ms} decimals={2} /> : "--"}
                  </p>
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
                    {result ? <AnimatedNumber value={result.risk_score} decimals={0} /> : "--"}
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
            <div ref={liveFeedCardRef} className="h-full rounded-2xl">
              <ProCard title="Flux en direct (Scapy)" icon={<Wifi className="w-4 h-4 text-blue-400" />}>
                <div className="font-mono text-xs mt-2 space-y-2">
                  {liveFeed.length === 0 ? (
                    <p className="text-zinc-600">En attente de paquets...</p>
                  ) : (
                    liveFeed.map((item, idx) => (
                      <div key={idx} className={`flex justify-between border-b border-zinc-800/50 pb-1 ${item.is_attack ? 'text-red-400' : 'text-emerald-400'}`}>
                        <span>Port: {item.port || "N/A"}</span>
                        <span>{item.verdict}</span>
                      </div>
                    ))
                  )}
                </div>
              </ProCard>
            </div>
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
                      <span className="text-orange-400">[3] Alertes Scapy vues :</span> <br />
                      {result.trace?.live_alerts_seen} paquet(s) suspect(s)
                    </div>
                    <div className="p-2 bg-zinc-900 rounded border border-zinc-800">
                      <span className="text-emerald-400">[4] LLM utilisé :</span> <br />
                      {result.trace?.model_used}
                    </div>
                  </>
                )}
                {status === 'listening' && <p className="text-red-400">$ [MIC] Enregistrement en cours...</p>}
                {status === 'analyzing' && <p className="text-purple-400">$ Transcription et analyse en cours...</p>}
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