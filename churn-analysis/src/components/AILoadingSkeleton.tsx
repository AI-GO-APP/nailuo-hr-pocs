import React from "react";

/**
 * AI 生成中骨架動畫
 */
export default function AILoadingSkeleton() {
  return (
    <div className="ai-loading-skeleton">
      <div className="ai-loading-header">
        <div className="ai-loading-dot-container">
          <span className="ai-loading-dot"></span>
          <span className="ai-loading-dot"></span>
          <span className="ai-loading-dot"></span>
        </div>
        <span className="ai-loading-label">AI 正在分析資料並生成洞察...</span>
      </div>
      <div className="ai-loading-lines">
        <div className="shimmer-line" style={{width: "92%"}}></div>
        <div className="shimmer-line" style={{width: "78%"}}></div>
        <div className="shimmer-line" style={{width: "85%"}}></div>
        <div className="shimmer-line" style={{width: "60%"}}></div>
      </div>
    </div>
  );
}
