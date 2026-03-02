(function () {
  function byId(id) { return document.getElementById(id); }

  function setEnabled(btn, enabled) {
    if (!btn) return;
    btn.disabled = !enabled;
    btn.classList.toggle('disabled', !enabled);
  }

  // Login page
  const loginBtn = byId('loginBtn');
  if (loginBtn) {
    const email = byId('email');
    const password = byId('password');
    const tick = () => setEnabled(loginBtn, (email?.value || '').trim() && (password?.value || '').trim());
    email?.addEventListener('input', tick);
    password?.addEventListener('input', tick);
    tick();
  }

  // Signup page
  const signupBtn = byId('signupBtn');
  if (signupBtn) {
    const username = byId('username');
    const email = byId('email');
    const password = byId('password');
    const tick = () => {
      const u = (username?.value || '').trim();
      const e = (email?.value || '').trim();
      const p = (password?.value || '').trim();
      setEnabled(signupBtn, u.length > 0 && e.length > 0 && p.length >= 8);
    };
    username?.addEventListener('input', tick);
    email?.addEventListener('input', tick);
    password?.addEventListener('input', tick);
    tick();
  }

  // Forgot password
  const forgotBtn = byId('forgotBtn');
  if (forgotBtn) {
    const email = byId('email');
    const tick = () => setEnabled(forgotBtn, (email?.value || '').trim());
    email?.addEventListener('input', tick);
    tick();
  }

  // Reset password
  const resetBtn = byId('resetBtn');
  if (resetBtn) {
    const p1 = byId('password');
    const p2 = byId('confirm_password');
    const tick = () => {
      const a = (p1?.value || '');
      const b = (p2?.value || '');
      setEnabled(resetBtn, a.length >= 8 && b.length >= 8 && a === b);
    };
    p1?.addEventListener('input', tick);
    p2?.addEventListener('input', tick);
    tick();
  }
})();
