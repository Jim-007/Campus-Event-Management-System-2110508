import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';

export const DashboardPage: React.FC = () => {
  const { user, apiFetch, refreshUser } = useAuth();
  const [tab, setTab] = useState<'events' | 'groups' | 'profile'>('events');
  const [events, setEvents] = useState<any[]>([]);
  const [groups, setGroups] = useState<any[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [message, setMessage] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);

  // Event Form
  const [editingId, setEditingId] = useState<number | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('Workshop');
  const [venue, setVenue] = useState('');
  const [startTime, setStartTime] = useState('2026-12-10T10:00');
  const [endTime, setEndTime] = useState('2026-12-10T12:00');
  const [capacity, setCapacity] = useState(50);
  const [groupId, setGroupId] = useState<string>('');
  const [assignedTo, setAssignedTo] = useState<string>('');

  // Group Form
  const [groupName, setGroupName] = useState('');
  const [groupDesc, setGroupDesc] = useState('');
  const [memberEmail, setMemberEmail] = useState('');
  const [permCreate, setPermCreate] = useState(true);
  const [permEdit, setPermEdit] = useState(false);
  const [permAssign, setPermAssign] = useState(false);
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);

  // Profile Form
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');

  const loadAll = async () => {
    const [evRes, grRes, seRes] = await Promise.all([
      apiFetch('/api/events'),
      apiFetch('/api/groups'),
      apiFetch('/api/auth/sessions'),
    ]);
    if (evRes.ok) setEvents(await evRes.json());
    if (grRes.ok) setGroups(await grRes.json());
    if (seRes.ok) setSessions(await seRes.json());
  };

  useEffect(() => {
    loadAll();
  }, []);

  const resetEventForm = () => {
    setEditingId(null);
    setTitle('');
    setDescription('');
    setVenue('');
    setGroupId('');
    setAssignedTo('');
  };

  const handleSaveEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);
    const payload: any = {
      title,
      description,
      category,
      venue,
      start_time: startTime,
      end_time: endTime,
      capacity: Number(capacity),
      group_id: groupId ? Number(groupId) : null,
      assigned_to: assignedTo ? Number(assignedTo) : null,
    };

    const url = editingId ? `/api/events/${editingId}` : '/api/events';
    const method = editingId ? 'PATCH' : 'POST';
    const res = await apiFetch(url, { method, body: JSON.stringify(payload) });
    const data = await res.json();
    if (!res.ok) {
      setMessage({ type: 'err', text: `RBAC / Server Error (${res.status}): ${data.detail}` });
      return;
    }
    setMessage({ type: 'ok', text: editingId ? 'Event updated' : 'Event created' });
    resetEventForm();
    loadAll();
  };

  const handleDeleteEvent = async (id: number) => {
    setMessage(null);
    const res = await apiFetch(`/api/events/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (!res.ok) {
      setMessage({ type: 'err', text: `Denied (${res.status}): ${data.detail}` });
      return;
    }
    setMessage({ type: 'ok', text: 'Event deleted' });
    loadAll();
  };

  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await apiFetch('/api/groups', {
      method: 'POST',
      body: JSON.stringify({ name: groupName, description: groupDesc }),
    });
    if (res.ok) {
      setGroupName('');
      setGroupDesc('');
      setMessage({ type: 'ok', text: 'Group created' });
      loadAll();
    }
  };

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedGroupId) return;
    const res = await apiFetch(`/api/groups/${selectedGroupId}/members`, {
      method: 'POST',
      body: JSON.stringify({
        email: memberEmail,
        can_create: permCreate,
        can_edit: permEdit,
        can_assign: permAssign,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      setMessage({ type: 'err', text: data.detail });
      return;
    }
    setMemberEmail('');
    setMessage({ type: 'ok', text: data.message });
    loadAll();
  };

  const handleRenameGroup = async (gid: number, oldName: string) => {
    const newName = prompt('Enter new group name:', oldName);
    if (!newName || newName === oldName) return;
    const res = await apiFetch(`/api/groups/${gid}`, {
      method: 'PATCH',
      body: JSON.stringify({ name: newName }),
    });
    const data = await res.json();
    if (!res.ok) setMessage({ type: 'err', text: `Denied (${res.status}): ${data.detail}` });
    else loadAll();
  };

  const handleDeleteGroup = async (gid: number) => {
    const res = await apiFetch(`/api/groups/${gid}`, { method: 'DELETE' });
    const data = await res.json();
    if (!res.ok) setMessage({ type: 'err', text: `Denied (${res.status}): ${data.detail}` });
    else loadAll();
  };

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await apiFetch('/api/auth/me', {
      method: 'PATCH',
      body: JSON.stringify({ full_name: fullName }),
    });
    if (res.ok) {
      const updated = await res.json();
      refreshUser(updated);
      setMessage({ type: 'ok', text: 'Profile updated' });
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await apiFetch('/api/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    });
    const data = await res.json();
    if (!res.ok) setMessage({ type: 'err', text: data.detail });
    else {
      setCurrentPassword('');
      setNewPassword('');
      setMessage({ type: 'ok', text: data.message });
    }
  };

  const handleRevokeSession = async (sessionId: number) => {
    const res = await apiFetch(`/api/auth/sessions/${sessionId}`, { method: 'DELETE' });
    if (res.ok) {
      setMessage({ type: 'ok', text: `Session #${sessionId} revoked` });
      loadAll();
    }
  };

  return (
    <div className="container">
      <div className="tabs">
        <button className={tab === 'events' ? 'active' : ''} onClick={() => setTab('events')}>
          My &amp; Group Events ({events.length})
        </button>
        <button className={tab === 'groups' ? 'active' : ''} onClick={() => setTab('groups')}>
          Shared Groups ({groups.length})
        </button>
        <button className={tab === 'profile' ? 'active' : ''} onClick={() => setTab('profile')}>
          Profile &amp; Sessions
        </button>
      </div>

      {message && <div className={`alert ${message.type === 'err' ? 'error' : 'success'}`}>{message.text}</div>}

      {tab === 'events' && (
        <div className="grid-2">
          <div className="card">
            <h3>{editingId ? `Edit Event #${editingId}` : 'Create New Event'}</h3>
            <form onSubmit={handleSaveEvent} className="stack">
              <input placeholder="Event Title" value={title} onChange={(e) => setTitle(e.target.value)} required />
              <textarea placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} required />
              <div className="row">
                <select value={category} onChange={(e) => setCategory(e.target.value)}>
                  <option>Workshop</option>
                  <option>Seminar</option>
                  <option>Exhibition</option>
                  <option>Cultural</option>
                </select>
                <input placeholder="Venue" value={venue} onChange={(e) => setVenue(e.target.value)} required />
              </div>
              <div className="row">
                <input type="datetime-local" value={startTime} onChange={(e) => setStartTime(e.target.value)} required />
                <input type="datetime-local" value={endTime} onChange={(e) => setEndTime(e.target.value)} required />
              </div>
              <div className="row">
                <input
                  type="number"
                  min={1}
                  placeholder="Capacity"
                  value={capacity}
                  onChange={(e) => setCapacity(Number(e.target.value))}
                  required
                />
                <select value={groupId} onChange={(e) => setGroupId(e.target.value)}>
                  <option value="">Personal Event (No Group)</option>
                  {groups.map((g) => (
                    <option key={g.id} value={g.id}>
                      Group: {g.name}
                    </option>
                  ))}
                </select>
              </div>
              <input
                type="number"
                placeholder="Assign to User ID (optional)"
                value={assignedTo}
                onChange={(e) => setAssignedTo(e.target.value)}
              />
              <div className="row">
                <button type="submit" className="btn primary">
                  {editingId ? 'Save Changes' : 'Create Event'}
                </button>
                {editingId && (
                  <button type="button" className="btn" onClick={resetEventForm}>
                    Cancel
                  </button>
                )}
              </div>
            </form>
          </div>

          <div className="stack">
            {events.length === 0 ? (
              <div className="card muted">No events visible to your account yet.</div>
            ) : (
              events.map((ev) => (
                <div key={ev.id} className="card">
                  <div className="space-between">
                    <strong>{ev.title}</strong>
                    <span className="badge">{ev.category}</span>
                  </div>
                  <p className="muted">{ev.description}</p>
                  <small>
                    Venue: {ev.venue} | Cap: {ev.capacity} | Owner ID: #{ev.owner_id}
                    {ev.group_id ? ` | Group #${ev.group_id}` : ' | Private'}
                    {ev.assigned_to ? ` | Assigned: #${ev.assigned_to}` : ''}
                  </small>
                  <div className="row" style={{ marginTop: '0.75rem' }}>
                    <button
                      className="btn small"
                      onClick={() => {
                        setEditingId(ev.id);
                        setTitle(ev.title);
                        setDescription(ev.description);
                        setCategory(ev.category);
                        setVenue(ev.venue);
                        setStartTime(ev.start_time);
                        setEndTime(ev.end_time);
                        setCapacity(ev.capacity);
                        setGroupId(ev.group_id ? String(ev.group_id) : '');
                        setAssignedTo(ev.assigned_to ? String(ev.assigned_to) : '');
                      }}
                    >
                      Edit / Assign
                    </button>
                    <button className="btn small danger" onClick={() => handleDeleteEvent(ev.id)}>
                      Delete
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {tab === 'groups' && (
        <div className="grid-2">
          <div className="stack">
            <div className="card">
              <h3>Create Organizing Group</h3>
              <form onSubmit={handleCreateGroup} className="stack">
                <input placeholder="Group Name" value={groupName} onChange={(e) => setGroupName(e.target.value)} required />
                <input placeholder="Description" value={groupDesc} onChange={(e) => setGroupDesc(e.target.value)} />
                <button type="submit" className="btn primary">Create Group</button>
              </form>
            </div>

            <div className="card">
              <h3>Manage Group Member Permissions</h3>
              <form onSubmit={handleAddMember} className="stack">
                <select
                  value={selectedGroupId || ''}
                  onChange={(e) => setSelectedGroupId(Number(e.target.value))}
                  required
                >
                  <option value="">Select a group...</option>
                  {groups.map((g) => (
                    <option key={g.id} value={g.id}>{g.name}</option>
                  ))}
                </select>
                <input
                  type="email"
                  placeholder="Member Email (e.g. bob@campus.edu)"
                  value={memberEmail}
                  onChange={(e) => setMemberEmail(e.target.value)}
                  required
                />
                <div className="row">
                  <label><input type="checkbox" checked={permCreate} onChange={(e) => setPermCreate(e.target.checked)} /> Can Create</label>
                  <label><input type="checkbox" checked={permEdit} onChange={(e) => setPermEdit(e.target.checked)} /> Can Edit</label>
                  <label><input type="checkbox" checked={permAssign} onChange={(e) => setPermAssign(e.target.checked)} /> Can Assign</label>
                </div>
                <button type="submit" className="btn primary">Add / Update Member</button>
              </form>
            </div>
          </div>

          <div className="stack">
            {groups.map((g) => (
              <div key={g.id} className="card">
                <div className="space-between">
                  <h4>{g.name} (ID #{g.id})</h4>
                  <span className="badge">{g.is_owner ? 'Owner' : 'Member'}</span>
                </div>
                <p className="muted">{g.description}</p>
                <div className="row" style={{ marginBottom: '0.75rem' }}>
                  <button className="btn small" onClick={() => handleRenameGroup(g.id, g.name)}>Rename</button>
                  <button className="btn small danger" onClick={() => handleDeleteGroup(g.id)}>Delete Group</button>
                </div>
                <strong>Members &amp; Permissions:</strong>
                <ul>
                  {g.members.map((m: any) => (
                    <li key={m.id}>
                      {m.full_name} ({m.email}) — Create: {m.can_create ? 'Yes' : 'No'}, Edit: {m.can_edit ? 'Yes' : 'No'}, Assign: {m.can_assign ? 'Yes' : 'No'}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'profile' && (
        <div className="grid-2">
          <div className="stack">
            <div className="card">
              <h3>Update Profile</h3>
              <form onSubmit={handleUpdateProfile} className="stack">
                <input value={user?.email || ''} disabled />
                <input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
                <button type="submit" className="btn primary">Save Profile</button>
              </form>
            </div>
            <div className="card">
              <h3>Change Password</h3>
              <form onSubmit={handleChangePassword} className="stack">
                <input
                  type="password"
                  placeholder="Current Password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                />
                <input
                  type="password"
                  placeholder="New Password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                />
                <button type="submit" className="btn primary">Update Password</button>
              </form>
            </div>
          </div>

          <div className="card">
            <h3>Active &amp; Recent Login Sessions</h3>
            <div className="stack">
              {sessions.map((s) => (
                <div key={s.id} className="session-item space-between">
                  <div>
                    <strong>Session #{s.id}</strong> — IP: {s.ip_address}
                    <br />
                    <small className="muted">{s.user_agent}</small>
                  </div>
                  {s.is_revoked ? (
                    <span className="badge danger">Revoked</span>
                  ) : (
                    <button className="btn small danger" onClick={() => handleRevokeSession(s.id)}>
                      Revoke
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};