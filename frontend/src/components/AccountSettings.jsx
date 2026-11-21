import { useState } from 'react';
import toast from 'react-hot-toast';
import { KeyRound, Save } from 'lucide-react';
import { Input } from './form';
import { Spinner } from './ui';
import { useAuth } from '../context/AuthContext';
import api, { errorMessage, fieldErrors, tokenStore } from '../services/api';
import { roleLabel } from '../utils/roles';

/** Profile + change-password panel used by both the admin dashboard and the student portal. */
export default function AccountSettings({ allowNameEdit = true }) {
  const { user, setUser } = useAuth();
  const [profile, setProfile] = useState({ name: user.name, phone: user.phone || '' });
  const [pw, setPw] = useState({ currentPassword: '', newPassword: '', confirm: '' });
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState('');

  const saveProfile = async (e) => {
    e.preventDefault();
    setBusy('profile');
    try {
      const { data } = await api.put('/auth/profile', allowNameEdit ? profile : { phone: profile.phone });
      setUser((u) => ({ ...u, ...data.data }));
      toast.success('Profile updated');
    } catch (ex) {
      toast.error(errorMessage(ex));
    } finally {
      setBusy('');
    }
  };

  const changePassword = async (e) => {
    e.preventDefault();
    const errs = {};
    if (!pw.currentPassword) errs.currentPassword = 'Required';
    if (pw.newPassword.length < 8 || !/[A-Za-z]/.test(pw.newPassword) || !/\d/.test(pw.newPassword)) errs.newPassword = 'At least 8 characters with letters and numbers';
    if (pw.newPassword !== pw.confirm) errs.confirm = 'Passwords do not match';
    setErrors(errs);
    if (Object.keys(errs).length) return;
    setBusy('pw');
    try {
      const { data } = await api.put('/auth/password', { currentPassword: pw.currentPassword, newPassword: pw.newPassword });
      tokenStore.set(data.data.token);
      setPw({ currentPassword: '', newPassword: '', confirm: '' });
      toast.success('Password changed');
    } catch (ex) {
      setErrors(fieldErrors(ex));
      toast.error(errorMessage(ex));
    } finally {
      setBusy('');
    }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <form onSubmit={saveProfile} className="card space-y-5 p-6 sm:p-8">
        <div>
          <h3 className="font-sans text-lg font-semibold">Profile</h3>
          <p className="text-sm text-slate-500">{user.email} · {roleLabel(user.role)}</p>
        </div>
        <Input label="Full name" value={profile.name} disabled={!allowNameEdit} onChange={(e) => setProfile((p) => ({ ...p, name: e.target.value }))} />
        <Input label="Phone" value={profile.phone} onChange={(e) => setProfile((p) => ({ ...p, phone: e.target.value }))} />
        <button type="submit" className="btn-primary" disabled={busy === 'profile'}>{busy === 'profile' ? <Spinner className="h-4 w-4" /> : <Save className="h-4 w-4" />}Save profile</button>
      </form>
      <form onSubmit={changePassword} className="card space-y-5 p-6 sm:p-8" noValidate>
        <div><h3 className="font-sans text-lg font-semibold">Change password</h3><p className="text-sm text-slate-500">Use at least 8 characters with letters and numbers.</p></div>
        <Input label="Current password" type="password" autoComplete="current-password" value={pw.currentPassword} error={errors.currentPassword} onChange={(e) => setPw((p) => ({ ...p, currentPassword: e.target.value }))} />
        <Input label="New password" type="password" autoComplete="new-password" value={pw.newPassword} error={errors.newPassword} onChange={(e) => setPw((p) => ({ ...p, newPassword: e.target.value }))} />
        <Input label="Confirm new password" type="password" autoComplete="new-password" value={pw.confirm} error={errors.confirm} onChange={(e) => setPw((p) => ({ ...p, confirm: e.target.value }))} />
        <button type="submit" className="btn-primary" disabled={busy === 'pw'}>{busy === 'pw' ? <Spinner className="h-4 w-4" /> : <KeyRound className="h-4 w-4" />}Update password</button>
      </form>
    </div>
  );
}
