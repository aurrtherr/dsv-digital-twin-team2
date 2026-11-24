// Demo log-in screen: name + password; the backend says which role that person has.
import { useState } from 'react';
import type { FormEvent } from 'react';
import { api } from '../api';

export interface User { name: string; role: string }

const CSS = `
.lg{min-height:100vh;display:grid;place-items:center;background:var(--bg);color:var(--ink);font-family:var(--font-body);padding:24px 16px}
.lg-card{width:min(380px,100%);background:var(--surface);border:1px solid var(--line);border-radius:var(--r-lg);box-shadow:var(--shadow);padding:28px 24px}
.lg-brand{display:flex;align-items:center;gap:10px;margin-bottom:20px}
.lg-logo{width:36px;height:36px;border-radius:var(--r-sm);background:var(--navy);display:grid;place-items:center}
.lg-logo i{width:16px;height:13px;background:var(--gold);border-radius:2px;position:relative}
.lg-logo i::before{content:"";position:absolute;left:50%;top:0;bottom:0;width:4px;margin-left:-2px;background:rgba(0,38,100,.25)}
.lg h1{font-family:var(--font-head);font-size:var(--fs-lg);margin:0;line-height:1.2}
.lg-brand span{display:block;color:var(--muted);font-size:var(--fs-xs)}
.lg label{display:block;font-size:var(--fs-sm);font-weight:600;margin:14px 0 6px}
.lg input{width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:var(--r-sm);background:var(--surface-2);font-size:var(--fs-base)}
.lg input:focus{outline:2px solid var(--accent);outline-offset:1px;border-color:transparent}
.lg-btn{width:100%;margin-top:20px;padding:11px;border:0;border-radius:var(--r-sm);background:var(--accent);color:var(--on-accent);font-weight:600;font-size:var(--fs-base)}
.lg-btn:disabled{opacity:.7;cursor:progress}
.lg-err{color:var(--late);background:var(--late-soft);border-radius:var(--r-sm);padding:8px 10px;font-size:var(--fs-sm);margin:14px 0 0}
.lg-wait{color:var(--muted);font-size:var(--fs-xs);margin:10px 0 0;text-align:center}
.lg-foot{color:var(--muted);font-size:var(--fs-xs);margin:18px 0 0;text-align:center}
`;

export function Login({ onLogin }: { onLogin: (u: User) => void }) {
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !password) { setErr('Enter your name and password.'); return; }
    setBusy(true); setErr('');
    api.login(name, password)
      .then(onLogin)
      .catch(x => { setErr(String(x.message || x)); setBusy(false); });
  };

  return (
    <div className="lg">
      <style>{CSS}</style>
      <form className="lg-card" onSubmit={submit} noValidate>
        <div className="lg-brand">
          <div className="lg-logo" aria-hidden="true"><i /></div>
          <div><h1>Warehouse Twin</h1><span>DSV · Singapore</span></div>
        </div>
        <label htmlFor="lg-name">Name</label>
        <input id="lg-name" autoComplete="username" autoFocus value={name} onChange={e => setName(e.target.value)} />
        <label htmlFor="lg-pw">Password</label>
        <input id="lg-pw" type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} />
        {err && <p className="lg-err" role="alert">{err}</p>}
        <button className="lg-btn" type="submit" disabled={busy}>{busy ? 'Logging in…' : 'Log in'}</button>
        {busy && <p className="lg-wait">If the server was asleep, this can take up to a minute.</p>}
        <p className="lg-foot">Prototype log-in · you see the screens for your role</p>
      </form>
    </div>
  );
}
