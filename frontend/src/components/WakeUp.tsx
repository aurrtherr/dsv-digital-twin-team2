// Loading screen shown until the first data arrives. On the online demo the free
// backend sleeps when idle and can take up to a minute to wake, so this keeps
// people company: boxes ride a conveyor into the dock while messages rotate.
import { useEffect, useState } from 'react';

const MESSAGES = [
  'Waking up the warehouse…',
  'Forklift warming up…',
  'Opening the dock doors…',
  'Counting cartons…',
  'Scanning LPNs…',
  'Lining up the Milkrun…',
  'Checking planned dates…',
  'Almost there, stacking pallets…',
];

const CSS = `
.wk{min-height:100vh;display:grid;place-items:center;background:var(--bg);color:var(--ink);font-family:var(--font-body);
  padding:24px 16px;opacity:0;animation:wk-in .4s ease .25s forwards}
.wk-box{width:min(440px,100%);text-align:center}
.wk h1{font-family:var(--font-head);font-size:var(--fs-xl);margin:0 0 4px;color:var(--ink)}
.wk .wk-sub{color:var(--muted);font-size:var(--fs-sm);margin:0 0 28px}
.wk-scene{position:relative;height:104px;margin:0 auto 22px;overflow:hidden}
.wk-dock{position:absolute;right:0;bottom:22px;width:62px;height:76px;background:var(--navy);border-radius:var(--r-sm) var(--r-sm) 0 0;
  color:var(--on-navy);font:600 10px/1 var(--font-head);letter-spacing:.08em;display:flex;align-items:flex-start;justify-content:center;padding-top:8px;z-index:2}
.wk-dock::after{content:"";position:absolute;left:9px;right:9px;bottom:0;height:44px;background:var(--navy-2);border-radius:3px 3px 0 0;
  background-image:repeating-linear-gradient(to bottom,transparent 0 6px,rgba(255,255,255,.12) 6px 7px)}
.wk-belt{position:absolute;left:0;right:30px;bottom:14px;height:8px;border-radius:var(--r-pill);background:var(--line);
  background-image:repeating-linear-gradient(90deg,var(--muted) 0 10px,transparent 10px 20px);background-size:20px 100%;opacity:.7;
  animation:wk-belt .6s linear infinite}
.wk-rollers{position:absolute;left:8px;right:40px;bottom:0;display:flex;justify-content:space-between}
.wk-rollers i{width:12px;height:12px;border-radius:50%;border:2px solid var(--muted);border-top-color:transparent;animation:wk-spin .8s linear infinite}
.wk-parcel{position:absolute;bottom:22px;left:-40px;width:30px;height:24px;border-radius:3px;background:#C8955A;
  box-shadow:inset 0 -3px 0 rgba(0,0,0,.12);animation:wk-ride 4s linear infinite}
.wk-parcel::before{content:"";position:absolute;left:50%;top:0;bottom:0;width:6px;margin-left:-3px;background:#E9C893}
.wk-parcel.tall{height:32px;width:26px}
.wk-parcel.gold{background:var(--gold)}
.wk-parcel.gold::before{background:rgba(255,255,255,.55)}
.wk-msg{font-family:var(--font-head);font-size:var(--fs-md);min-height:1.5em;margin:0 0 6px;animation:wk-fade 3s ease infinite}
.wk-time{color:var(--muted);font-size:var(--fs-sm);font-variant-numeric:tabular-nums;margin:0}
.wk-note{color:var(--muted);font-size:var(--fs-xs);margin:14px auto 0;max-width:34ch;line-height:1.5}
@keyframes wk-in{to{opacity:1}}
@keyframes wk-belt{to{background-position:20px 0}}
@keyframes wk-spin{to{transform:rotate(360deg)}}
@keyframes wk-ride{0%{transform:translateX(0)}85%{transform:translateX(min(380px,calc(100vw - 110px)));opacity:1}100%{transform:translateX(min(400px,calc(100vw - 90px)));opacity:0}}
@keyframes wk-fade{0%,100%{opacity:.35}15%,85%{opacity:1}}
@media (prefers-reduced-motion:reduce){.wk-belt,.wk-rollers i,.wk-parcel,.wk-msg{animation:none}.wk-parcel{display:none}}
`;

export function WakeUp() {
  const [secs, setSecs] = useState(0);
  useEffect(() => {
    const start = Date.now();
    const id = window.setInterval(() => setSecs(Math.floor((Date.now() - start) / 1000)), 1000);
    return () => window.clearInterval(id);
  }, []);
  const msg = MESSAGES[Math.floor(secs / 3) % MESSAGES.length];

  return (
    <div className="wk" role="status" aria-live="polite">
      <style>{CSS}</style>
      <div className="wk-box">
        <h1>Warehouse Twin</h1>
        <p className="wk-sub">DSV · one week of operations, replayed</p>
        <div className="wk-scene" aria-hidden="true">
          <div className="wk-parcel" style={{ animationDelay: '0s' }} />
          <div className="wk-parcel tall" style={{ animationDelay: '-1s' }} />
          <div className="wk-parcel gold" style={{ animationDelay: '-2s' }} />
          <div className="wk-parcel" style={{ animationDelay: '-3s' }} />
          <div className="wk-belt" />
          <div className="wk-rollers">{Array.from({ length: 7 }, (_, i) => <i key={i} />)}</div>
          <div className="wk-dock">DOCK</div>
        </div>
        <p className="wk-msg" key={msg}>{msg}</p>
        <p className="wk-time">{secs} s</p>
        {secs >= 5 && (
          <p className="wk-note">The free server naps when nobody is using it. Waking it usually takes under a minute, and then the app is quick.</p>
        )}
      </div>
    </div>
  );
}
