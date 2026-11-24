import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';

export const AdminPage: React.FC = () => {
  const { apiFetch } = useAuth();
  const [subTab, setSubTab] = useState<'overview' | 'users' | 'content' | 'logs' | 'security'>('overview');
  const [msg, setMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);

  // Overview
  const [stats, setStats] = useState<any>(null);

  // Users
  const [usersData, setUsersData] = useState<any>({ items: [], total: 0, page: 1 });
  const [userSearch, setUserSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedUserIds, setSelectedUserIds] = useState<number[]>([]);
  const [userDetail, setUserDetail] = useState<any>(null);

  // Content Moderation
  const [allEvents, setAllEvents] = useState<any[]>([]);
  const [allGroups, setAllGroups] = useState<any[]>([]);
  const [selectedEventIds, setSelectedEventIds] = useState<number[]>([]);
  const [selectedGroupIds, setSelectedGroupIds] = useState<number[]>([]);

  // Logs & Security
  const [logs, setLogs] = useState<any[]>([]);
  const [logAction, setLogAction] = useState('');
  const [logSearch, setLogSearch] = useState('');
  const [security, setSecurity] = useState<any>(null);

  const loadStats = async () => {
    const res = await apiFetch('/api/admin/stats');
    if (res.ok) setStats(await res.json());
  };

  const loadUsers = async (page = 1) => {
    const params = new URLSearchParams({ page: String(page), limit: '10' });
    if (userSearch) params.set('search', userSearch);
    if (roleFilter) params.set('role', roleFilter);
    if (statusFilter) params.set('status', statusFilter);
    const res = await apiFetch(`/api/admin/users?${params.toString()}`);
    if (res.ok) setUsersData(await res.json());
  };

  const loadContent = async () => {
    const [evRes, grRes] = await Promise.all([apiFetch('/api/admin/events'), apiFetch('/api/admin/groups')]);
    if (evRes.ok) setAllEvents(await evRes.json());
    if (grRes.ok) setAllGroups(await grRes.json());
  };

  const loadLogs = async () => {
    const params = new URLSearchParams();
    if (logAction) params.set('action', logAction);
    if (logSearch) params.set('search', logSearch);
    const res = await apiFetch(`/api/admin/logs?${params.toString()}`);
    if (res.ok) setLogs(await res.json());
  };

  const loadSecurity = async () => {
    const res = await apiFetch('/api/admin/security');
    if (res.ok) setSecurity(await res.json());
  };

  useEffect(() => {
    loadStats();
    loadUsers();
    loadContent();
    loadLogs();
    loadSecurity();
  }, []);

  const downloadCsv = async (resource: 'users' | 'events' | 'logs') => {
    const params = new URLSearchParams();
    if (resource === 'users') {
      if (userSearch) params.set('search', userSearch);
      if (roleFilter) params.set('role', roleFilter);
      if (statusFilter) params.set('status', statusFilter);
    } else if (resource === 'logs') {
      if (logAction) params.set('action', logAction);
      if (logSearch) params.set('search', logSearch);
    }
    const res = await apiFetch(`/api/admin/export/${resource}?${params.toString()}`);
    if (res.ok) {
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${resource}_export.csv`;
      a.click();
      loadLogs();
    }
  };

  const handleBan = async (uid: number) => {
    const reason = prompt('Enter ban reason:', 'Policy violation');
    if (!reason) return;
    const res = await apiFetch(`/api/admin/users/${uid}/ban`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
    const data = await res.json();
    setMsg({ type: res.ok ? 'ok' : 'err', text: data.detail || data.message });
    loadUsers(usersData.page);
    loadStats();
  };

  const handleUnban = async (uid: number) => {
    const res = await apiFetch(`/api/admin/users/${uid}/unban`, { method: 'POST' });
    const data = await res.json();
    setMsg({ type: res.ok ? 'ok' : 'err', text: data.detail || data.message });
    loadUsers(usersData.page);
    loadStats();
  };

  const handleBulkBan = async (ban: boolean) => {
    if (selectedUserIds.length === 0) return;
    const endpoint = ban ? '/api/admin/users/bulk-ban' : '/api/admin/users/bulk-unban';
    const res = await apiFetch(endpoint, {
      method: 'POST',
      body: JSON.stringify({ user_ids: selectedUserIds, reason: 'Bulk admin moderation' }),
    });
    const data = await res.json();
    setMsg({ type: 'ok', text: data.message });
    setSelectedUserIds([]);
    loadUsers(usersData.page);
    loadStats();
  };

  const handleRoleChange = async (uid: number, newRole: string) => {
    const res = await apiFetch(`/api/admin/users/${uid}/role`, {
      method: 'PATCH',
      body: JSON.stringify({ role: newRole }),
    });
    const data = await res.json();
    setMsg({ type: res.ok ? 'ok' : 'err', text: data.detail || data.message });
    loadUsers(usersData.page);
  };

  const handleRevokeAll = async (uid: number) => {
    const res = await apiFetch(`/api/admin/users/${uid}/revoke-sessions`, { method: 'POST' });
    const data = await res.json();
    setMsg({ type: 'ok', text: data.message });
  };

  const viewUserDetail = async (uid: number) => {
    const res = await apiFetch(`/api/admin/users/${uid}`);
    if (res.ok) setUserDetail(await res.json());
  };

  return (
    <div className="container">
      <h2>Admin Security &amp; Governance Dashboard</h2>
      <div className="tabs">
        <button className={subTab === 'overview' ? 'active' : ''} onClick={() => setSubTab('overview')}>Overview</button>
        <button className={subTab === 'users' ? 'active' : ''} onClick={() => setSubTab('users')}>Users</button>
        <button className={subTab === 'content' ? 'active' : ''} onClick={() => setSubTab('content')}>Content Moderation</button>
        <button className={subTab === 'logs' ? 'active' : ''} onClick={() => { setSubTab('logs'); loadLogs(); }}>Activity Logs</button>
        <button className={subTab === 'security' ? 'active' : ''} onClick={() => { setSubTab('security'); loadSecurity(); }}>Security View</button>
      </div>

      {msg && <div className={`alert ${msg.type === 'err' ? 'error' : 'success'}`}>{msg.text}</div>}

      {subTab === 'overview' && stats && (
        <div className="stats-grid">
          <div className="card"><h4>Total Users</h4><p className="stat-num">{stats.total_users}</p><small>+{stats.new_last_7_days.users} last 7d</small></div>
          <div className="card"><h4>Banned Users</h4><p className="stat-num danger-text">{stats.banned_users}</p></div>
          <div className="card"><h4>Total Events</h4><p className="stat-num">{stats.total_events}</p><small>+{stats.new_last_7_days.events} last 7d</small></div>
          <div className="card"><h4>Total Groups</h4><p className="stat-num">{stats.total_groups}</p><small>+{stats.new_last_7_days.groups} last 7d</small></div>
        </div>
      )}

      {subTab === 'users' && (
        <div className="stack">
          <div className="card row wrap">
            <input placeholder="Search email or name..." value={userSearch} onChange={(e) => setUserSearch(e.target.value)} />
            <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
              <option value="">All Roles</option>
              <option value="user">User</option>
              <option value="admin">Admin</option>
            </select>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="">All Status</option>
              <option value="active">Active</option>
              <option value="banned">Banned</option>
            </select>
            <button className="btn primary" onClick={() => loadUsers(1)}>Filter</button>
            <button className="btn" onClick={() => downloadCsv('users')}>Export Filtered CSV</button>
            {selectedUserIds.length > 0 && (
              <>
                <button className="btn danger" onClick={() => handleBulkBan(true)}>Bulk Ban ({selectedUserIds.length})</button>
                <button className="btn" onClick={() => handleBulkBan(false)}>Bulk Unban</button>
              </>
            )}
          </div>

          <div className="card table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Select</th>
                  <th>ID</th>
                  <th>User</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {usersData.items.map((u: any) => (
                  <tr key={u.id}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selectedUserIds.includes(u.id)}
                        onChange={(e) =>
                          setSelectedUserIds(
                            e.target.checked ? [...selectedUserIds, u.id] : selectedUserIds.filter((id) => id !== u.id)
                          )
                        }
                      />
                    </td>
                    <td>#{u.id}</td>
                    <td><strong>{u.full_name}</strong><br /><small>{u.email}</small></td>
                    <td>
                      <select value={u.role} onChange={(e) => handleRoleChange(u.id, e.target.value)}>
                        <option value="user">user</option>
                        <option value="admin">admin</option>
                      </select>
                    </td>
                    <td>{u.is_banned ? <span className="badge danger">Banned: {u.ban_reason}</span> : <span className="badge">Active</span>}</td>
                    <td className="row wrap">
                      <button className="btn small" onClick={() => viewUserDetail(u.id)}>Details</button>
                      {u.is_banned ? (
                        <button className="btn small" onClick={() => handleUnban(u.id)}>Unban</button>
                      ) : (
                        <button className="btn small danger" onClick={() => handleBan(u.id)}>Ban</button>
                      )}
                      <button className="btn small" onClick={() => handleRevokeAll(u.id)}>Revoke Sessions</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {userDetail && (
            <div className="card">
              <div className="space-between">
                <h3>User Detail: {userDetail.user.full_name} ({userDetail.user.email})</h3>
                <button className="btn small" onClick={() => setUserDetail(null)}>Close</button>
              </div>
              <p>
                Events Owned: {userDetail.events.length} | Groups Owned: {userDetail.owned_groups.length} | Active Sessions:{' '}
                {userDetail.sessions.filter((s: any) => !s.is_revoked).length}
              </p>
              <strong>Recent Activity:</strong>
              <ul>
                {userDetail.recent_activity.map((l: any) => (
                  <li key={l.id}>[{l.action}] {l.details} ({l.ip_address})</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {subTab === 'content' && (
        <div className="grid-2">
          <div className="card">
            <div className="space-between">
              <h3>All Events ({allEvents.length})</h3>
              <div className="row">
                <button className="btn small" onClick={() => downloadCsv('events')}>Export CSV</button>
                {selectedEventIds.length > 0 && (
                  <button
                    className="btn small danger"
                    onClick={async () => {
                      await apiFetch('/api/admin/events/bulk-delete', {
                        method: 'POST',
                        body: JSON.stringify({ ids: selectedEventIds }),
                      });
                      setSelectedEventIds([]);
                      loadContent();
                    }}
                  >
                    Delete Selected ({selectedEventIds.length})
                  </button>
                )}
              </div>
            </div>
            {allEvents.map((ev) => (
              <div key={ev.id} className="session-item row">
                <input
                  type="checkbox"
                  checked={selectedEventIds.includes(ev.id)}
                  onChange={(e) =>
                    setSelectedEventIds(e.target.checked ? [...selectedEventIds, ev.id] : selectedEventIds.filter((i) => i !== ev.id))
                  }
                />
                <span>#{ev.id} — {ev.title} (Owner #{ev.owner_id})</span>
              </div>
            ))}
          </div>

          <div className="card">
            <div className="space-between">
              <h3>All Groups ({allGroups.length})</h3>
              {selectedGroupIds.length > 0 && (
                <button
                  className="btn small danger"
                  onClick={async () => {
                    await apiFetch('/api/admin/groups/bulk-delete', {
                      method: 'POST',
                      body: JSON.stringify({ ids: selectedGroupIds }),
                    });
                    setSelectedGroupIds([]);
                    loadContent();
                  }}
                >
                  Delete Selected ({selectedGroupIds.length})
                </button>
              )}
            </div>
            {allGroups.map((g) => (
              <div key={g.id} className="session-item row">
                <input
                  type="checkbox"
                  checked={selectedGroupIds.includes(g.id)}
                  onChange={(e) =>
                    setSelectedGroupIds(e.target.checked ? [...selectedGroupIds, g.id] : selectedGroupIds.filter((i) => i !== g.id))
                  }
                />
                <span>#{g.id} — {g.name} (Owner #{g.owner_id})</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {subTab === 'logs' && (
        <div className="stack">
          <div className="card row wrap">
            <select value={logAction} onChange={(e) => setLogAction(e.target.value)}>
              <option value="">All Actions</option>
              <option value="LOGIN">LOGIN</option>
              <option value="FAILED_LOGIN">FAILED_LOGIN</option>
              <option value="LOGOUT">LOGOUT</option>
              <option value="PASSWORD_CHANGE">PASSWORD_CHANGE</option>
              <option value="ROLE_CHANGE">ROLE_CHANGE</option>
              <option value="BAN">BAN</option>
              <option value="DELETE">DELETE</option>
              <option value="EXPORT">EXPORT</option>
            </select>
            <input placeholder="Search email, IP, or details..." value={logSearch} onChange={(e) => setLogSearch(e.target.value)} />
            <button className="btn primary" onClick={loadLogs}>Filter Logs</button>
            <button className="btn" onClick={() => downloadCsv('logs')}>Export Filtered Logs CSV</button>
          </div>

          <div className="card table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Time (UTC)</th>
                  <th>Action</th>
                  <th>User</th>
                  <th>Details</th>
                  <th>IP &amp; Browser</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((l) => (
                  <tr key={l.id}>
                    <td><small>{new Date(l.created_at).toLocaleString()}</small></td>
                    <td><span className="badge">{l.action}</span></td>
                    <td>{l.actor_email}</td>
                    <td>{l.details}</td>
                    <td><small>{l.ip_address}<br />{l.user_agent}</small></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {subTab === 'security' && security && (
        <div className="grid-2">
          <div className="card">
            <h3>Failed Logins by IP Address</h3>
            <table>
              <thead><tr><th>IP Address</th><th>Attempts</th></tr></thead>
              <tbody>
                {security.by_ip.map((row: any) => (
                  <tr key={row.ip_address}><td>{row.ip_address}</td><td>{row.count}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="card">
            <h3>Failed Logins by Account</h3>
            <table>
              <thead><tr><th>Email</th><th>Attempts</th></tr></thead>
              <tbody>
                {security.by_account.map((row: any) => (
                  <tr key={row.email}><td>{row.email}</td><td>{row.count}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};