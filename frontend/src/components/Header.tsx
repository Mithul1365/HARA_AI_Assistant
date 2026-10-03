import React from 'react';

const Header: React.FC = () => {
  return (
    <header className="h-[57px] bg-gradient-to-r from-[#0b4f91] via-[#1765a8] to-[#0b4f91] flex items-center justify-between px-5 text-white">
      
      <div className="flex items-center h-full">
        <div className="flex items-center justify-center w-[54px] h-[40px]">
          <img
            src="/tata-logo-tata-icon-free-free-vector.jpg"
            alt="Tata"
            className="w-[42px] h-[42px] object-contain"
          />
        </div>

        <div className="h-8 w-px bg-white/30 ml-4 mr-5" />

        <div className="leading-tight">
          <div className="text-[18px] font-semibold">
            HARA AI Assistant
          </div>
          <div className="text-[11px] text-white/90 mt-[1px]">
            AI-powered Automotive Functional Safety Analysis
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="text-right leading-tight">
          <div className="text-[11px] font-semibold">
            Powered by Qwen3 (Local)
          </div>
          <div className="text-[8px] text-white/75">
            Private • Secure • No API Cost
          </div>
        </div>

        <div className="w-8 h-8 rounded-full border border-white/40 flex items-center justify-center text-xs font-semibold">
          AI
        </div>
      </div>

    </header>
  );
};

export default Header;
