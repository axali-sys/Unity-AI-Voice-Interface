export default async function handler(req,res){
  if(req.method!=="POST") return res.status(405).json({error:"method_not_allowed"});
  const base=(process.env.XP_GATEWAY_URL||"https://api.axaliai.com").replace(/\/$/,"");
  const r=await fetch(base+"/public/solution",{method:"POST",headers:{"Content-Type":"application/json",Origin:req.headers.origin||"https://xparallel-ui.vercel.app"},body:JSON.stringify(req.body||{})});
  const body=await r.text(); res.status(r.status).setHeader("Content-Type","application/json").send(body);
}
