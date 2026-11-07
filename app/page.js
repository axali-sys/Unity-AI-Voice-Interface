const systems = [
  { name: "AI Core", tag: "INTELLIGENCE", text: "Reasoning, model access and cognitive services form the intelligence layer." },
  { name: "Omni", tag: "ORCHESTRATION", text: "Coordinates tasks, tools and workflows across connected systems." },
  { name: "Parallel Intelligence", tag: "COLLABORATION", text: "Brings multiple AI systems into a reviewable, comparative workflow." },
  { name: "XParallel", tag: "INTEROPERABILITY", text: "Connects services, agents and execution environments through governed interfaces." },
  { name: "OmniMemory + Knowledge Genome", tag: "KNOWLEDGE", text: "A planned knowledge fabric for context, provenance, retrieval and traceability." },
  { name: "Engineering Fabric", tag: "BUILD + REPAIR", text: "Developer tools, Build Studio and AI Repair Shop concepts for engineering workflows." },
];
const pages = [
  ["about","About","An infrastructure-first approach to connected intelligence."],
  ["infrastructure","Infrastructure","A layered foundation for intelligence, orchestration, knowledge and execution."],
  ["technologies","Technologies","Composable systems, open interfaces and verifiable workflows."],
  ["systems","AI Systems","Distinct AI products can share infrastructure without losing their identities."],
  ["solutions","Solutions","Practical building blocks for teams, developers and organizations."],
  ["developers","Developer Platform","A future-facing developer entry point with clear integration boundaries."],
  ["apis","API Services","API capabilities are published only when endpoints and access are verified."],
  ["docs","Documentation","Architecture notes, integration guidance and service status."],
  ["research","Research & Innovation","Exploring collaborative intelligence, knowledge systems and roaming agents."],
  ["security","Security","Human approval, least privilege and server-side secrets are foundational principles."],
  ["contact","Contact","Start a conversation about infrastructure, integration or collaboration."],
];
export default function Home() {
  return <main className="ax-site">
    <header className="ax-nav"><a className="ax-brand" href="#"><span className="ax-mark">A</span><span>AXALIAI<small>GENERAL AI INFRASTRUCTURE</small></span></a><nav>{pages.slice(0,5).map(([id,label])=><a key={id} href={`#${id}`}>{label}</a>)}</nav><a className="ax-nav-cta" href="#contact">Connect <span>↗</span></a></header>
    <section className="ax-hero">
      <div className="ax-orbit ax-orbit-one"></div><div className="ax-orbit ax-orbit-two"></div>
      <div className="ax-hero-copy"><p className="ax-kicker"><i></i> THE INFRASTRUCTURE BEHIND CONNECTED AI</p><h1>Build beyond<br/><em>one intelligence.</em></h1><p className="ax-lead">Axaliai is an evolving AI infrastructure ecosystem designed to connect intelligence, orchestrate work and make systems interoperable.</p><div className="ax-actions"><a className="ax-button primary" href="#infrastructure">Explore the infrastructure <span>↗</span></a><a className="ax-text-link" href="/assistant">Open AI assistant →</a></div><div className="ax-proof"><span>01 / INTELLIGENCE</span><span>02 / ORCHESTRATION</span><span>03 / INTEROPERABILITY</span></div></div>
      <div className="ax-hero-visual"><div className="ax-core"><div className="ax-core-inner">A<span>×</span></div><small>AXALIAI CORE</small></div><div className="ax-node node-a">AI CORE</div><div className="ax-node node-b">OMNI</div><div className="ax-node node-c">PARALLEL</div><div className="ax-node node-d">XPARALLEL</div><div className="ax-connection"></div></div>
      <div className="ax-scroll">SCROLL TO EXPLORE <span>↓</span></div>
    </section>
    <section className="ax-statement"><p className="ax-kicker">A CONNECTED SYSTEM, NOT A CLOSED PLATFORM</p><h2>One infrastructure.<br/><em>Many independent systems.</em></h2><p>Axaliai provides an architectural direction for AI systems to work together while retaining their own purpose, identity and control boundaries.</p></section>
    <section className="ax-section" id="infrastructure"><div className="ax-section-head"><div><p className="ax-kicker">THE SYSTEM LANDSCAPE / 01</p><h2>Infrastructure, <em>layer by layer.</em></h2></div><p>Composable foundations for building, connecting and coordinating AI capabilities.</p></div><div className="ax-system-grid">{systems.map((s,i)=><article className="ax-system-card" key={s.name}><div className="ax-card-top"><span>0{i+1}</span><span>{s.tag}</span></div><div className="ax-glyph">{["◈","◎","⫶","⌘","⌬","⌁"][i]}</div><h3>{s.name}</h3><p>{s.text}</p><a href="#technologies">Explore layer <span>↗</span></a></article>)}</div></section>
    <section className="ax-section ax-dark-band" id="technologies"><p className="ax-kicker">TECHNOLOGY PRINCIPLES / 02</p><h2>Open by design.<br/><em>Governed by default.</em></h2><div className="ax-principles"><article><b>01</b><h3>Interoperability</h3><p>Connect through documented contracts rather than locking every capability into one runtime.</p></article><article><b>02</b><h3>Human control</h3><p>Meaningful execution, deployment and sensitive actions require explicit authorization.</p></article><article><b>03</b><h3>Evidence first</h3><p>Separate a proposed capability from a tested integration and a verified live service.</p></article></div></section>
    <section className="ax-section" id="systems"><div className="ax-section-head"><div><p className="ax-kicker">INDEPENDENT PRODUCTS / 03</p><h2>Different systems.<br/><em>Shared foundations.</em></h2></div><p>Products keep their own names, roadmaps and user experiences while connecting to common infrastructure where useful.</p></div><div className="ax-product-list"><div><span>01</span><b>Axaliai</b><small>Umbrella infrastructure ecosystem</small></div><div><span>02</span><b>ƎllE</b><small>AI assistant identity</small></div><div><span>03</span><b>NexAI</b><small>Independent AI assistant product</small></div><div><span>04</span><b>XParallel</b><small>Execution and interoperability infrastructure</small></div><div><span>05</span><b>IDEAS</b><small>Separate global ideas marketplace</small></div></div></section>
    <section className="ax-section ax-capabilities" id="solutions"><p className="ax-kicker">SOLUTIONS / 04</p><h2>Infrastructure for<br/><em>real-world workflows.</em></h2><div className="ax-solution-grid"><article><span>↗</span><h3>Connect systems</h3><p>Bridge AI providers, applications and services through controlled integration points.</p></article><article><span>⌘</span><h3>Coordinate work</h3><p>Structure multi-step tasks across agents, tools and human decision-makers.</p></article><article><span>◌</span><h3>Build with evidence</h3><p>Track lifecycle, approvals and verifiable outcomes through the engineering process.</p></article></div></section>
    <section className="ax-developer" id="developers"><div><p className="ax-kicker">DEVELOPER PLATFORM / 05</p><h2>Build on a system<br/><em>that connects.</em></h2><p>Developer documentation, integration contracts and API access information are being organized around verified service capabilities.</p><a className="ax-button light" href="#docs">Explore developer resources ↗</a></div><div className="ax-code-card"><div className="ax-code-head"><i></i><i></i><i></i><span>integration.contract</span></div><pre><code>{`{
  "ecosystem": "Axaliai",
  "principles": [
    "interoperability",
    "human-approval",
    "evidence-first"
  ],
  "execution": "authorization-required"
}`}</code></pre><small>Illustrative architecture contract — not a live API response.</small></div></section>
    <section className="ax-section ax-api" id="apis"><p className="ax-kicker">API SERVICES / 06</p><h2>Clear contracts.<br/><em>No fictional endpoints.</em></h2><p>Public API documentation and developer access will be published after each service contract, authentication model and operational status have been validated.</p><div className="ax-api-status"><span className="status-dot"></span><div><b>Service directory</b><small>Documentation foundation in progress · live availability not asserted</small></div><a href="#contact">Request integration details ↗</a></div></section>
    <section className="ax-section ax-docs" id="docs"><p className="ax-kicker">DOCUMENTATION / 07</p><h2>Understand the architecture.</h2><div className="ax-doc-links"><a href="#infrastructure">Infrastructure overview <span>↗</span></a><a href="#security">Security principles <span>↗</span></a><a href="#research">Research direction <span>↗</span></a><a href="#apis">API publication policy <span>↗</span></a></div></section>
    <section className="ax-research" id="research"><p className="ax-kicker">RESEARCH & INNOVATION / 08</p><h2>Explore what<br/><em>connected intelligence can become.</em></h2><p>Research themes include collaborative reasoning, knowledge provenance, roaming agent networks, multimodal runtimes and resilient orchestration. These are areas of exploration, not claims of completed products.</p></section>
    <section className="ax-section ax-security" id="security"><div><p className="ax-kicker">SECURITY / 09</p><h2>Trust is an<br/><em>engineering property.</em></h2></div><div className="ax-security-grid"><article><b>Credentials</b><p>Secrets stay server-side and are never embedded in public browser code.</p></article><article><b>Authorization</b><p>Execution boundaries are explicit, scoped and approval-gated.</p></article><article><b>Verification</b><p>Operational claims require test evidence and an identified environment.</p></article></div></section>
    <section className="ax-contact" id="contact"><p className="ax-kicker">START A CONVERSATION</p><h2>Let’s connect<br/><em>the next layer.</em></h2><p>For infrastructure discussions, developer collaboration or partnership enquiries.</p><a className="ax-button light" href="mailto:contact@axaliai.com">Contact Axaliai ↗</a><small>Replace this contact route with a verified business inbox before public launch.</small></section>
    <footer className="ax-footer"><a className="ax-brand" href="#"><span className="ax-mark">A</span><span>AXALIAI<small>GENERAL AI INFRASTRUCTURE</small></span></a><span>© {new Date().getFullYear()} Axaliai. Built for connected intelligence.</span><div><a href="#security">Security</a><a href="#docs">Documentation</a><a href="/assistant">Assistant</a></div></footer>
  </main>;
}
