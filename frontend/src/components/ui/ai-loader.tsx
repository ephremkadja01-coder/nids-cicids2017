import * as React from "react";

interface LoaderProps {
  size?: number; 
  text?: string;
}

export const AILoader: React.FC<LoaderProps> = ({ size = 150, text = "Listening" }) => {
  const letters = text.split("");

  return (
    <div className="relative flex items-center justify-center font-sans select-none w-full h-full">
      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        {letters.map((letter, index) => (
          <span
            key={index}
            className="inline-block text-white opacity-40 animate-loaderLetter font-bold text-xl tracking-wider"
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            {letter}
          </span>
        ))}
        <div className="absolute inset-0 rounded-full animate-loaderCircle"></div>
      </div>

      <style>{`
        @keyframes loaderCircle {
          0% { transform: rotate(90deg); box-shadow: 0 6px 12px 0 #38bdf8 inset, 0 12px 18px 0 #005dff inset, 0 36px 36px 0 #1e40af inset, 0 0 3px 1.2px rgba(56, 189, 248, 0.3), 0 0 6px 1.8px rgba(0, 93, 255, 0.2); }
          50% { transform: rotate(270deg); box-shadow: 0 6px 12px 0 #60a5fa inset, 0 12px 6px 0 #0284c7 inset, 0 24px 36px 0 #005dff inset, 0 0 3px 1.2px rgba(56, 189, 248, 0.3), 0 0 6px 1.8px rgba(0, 93, 255, 0.2); }
          100% { transform: rotate(450deg); box-shadow: 0 6px 12px 0 #4dc8fd inset, 0 12px 18px 0 #005dff inset, 0 36px 36px 0 #1e40af inset, 0 0 3px 1.2px rgba(56, 189, 248, 0.3), 0 0 6px 1.8px rgba(0, 93, 255, 0.2); }
        }
        @keyframes loaderLetter {
          0%, 100% { opacity: 0.4; transform: translateY(0); }
          20% { opacity: 1; transform: scale(1.15); }
          40% { opacity: 0.7; transform: translateY(0); }
        }
        .animate-loaderCircle { animation: loaderCircle 3s linear infinite; }
        .animate-loaderLetter { animation: loaderLetter 1.5s infinite; }
      `}</style>
    </div>
  );
};