import { useNavigate } from "react-router-dom";
import { Home } from "lucide-react";

export default function NotFoundPage() {
  const nav = useNavigate();
  return (
    <div className="page" style={{textAlign:"center",padding:"80px 0"}}>
      <h1 style={{fontSize:64,fontWeight:700,color:"#E2E8F0",marginBottom:8}}>404</h1>
      <p style={{color:"#64748B",marginBottom:24}}>頁面不存在</p>
      <button className="btn btn-primary" onClick={() => nav("/")}><Home size={14} /> 回首頁</button>
    </div>
  );
}
