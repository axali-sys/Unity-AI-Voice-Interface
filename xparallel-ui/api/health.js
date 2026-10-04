export default async function handler(req,res){
  const base=(process.env.XP_GATEWAY_URL||"https://api.axaliai.com").replace(/\/$/,"");
  const r=await fetch(base+"/public/health",{headers:{Origin:req.headers.origin||"https://xparallel-ui.vercel.app"}});
  const body=await r.text(); res.status(r.status).setHeader("Content-Type","application/json").send(body);
}
