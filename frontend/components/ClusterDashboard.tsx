"use client";

import { useEffect, useState } from 'react';

interface AgentStatus {
  id: string;
  type: string;
  status: string;
  tasks_completed: number;
  errors: number;
  pid: number | null;
  uptime: string;
}

interface SystemHealth {
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
}

interface ClusterSummary {
  total: number;
  healthy: number;
  unhealthy: number;
}

export default function ClusterDashboard() {
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [summary, setSummary] = useState<ClusterSummary | null>(null);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    const fetchAgentStatus = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/cluster/agents/live');
        const data = await res.json();
        setAgents(data.agents);
        setSummary(data.summary);
        setLastUpdate(new Date());
      } catch (error) {
        console.error('Failed to fetch agent status:', error);
      }
    };

    const fetchSystemHealth = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/cluster/status');
        const data = await res.json();
        setSystemHealth(data.system);
        setIsLoading(false);
      } catch (error) {
        console.error('Failed to fetch system health:', error);
      }
    };

    // Initial fetch
    fetchAgentStatus();
    fetchSystemHealth();

    // Poll every 2 seconds
    const interval = setInterval(() => {
      fetchAgentStatus();
      fetchSystemHealth();
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const handleManualHeal = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/cluster/heal', {
        method: 'POST'
      });
      const data = await res.json();
      alert(`♻️ ${data.message}\nHealed: ${data.healed_workers.join(', ') || 'None'}`);
    } catch (error) {
      alert('Failed to trigger heal: ' + error);
    }
  };

  const getHealthColor = (percent: number) => {
    if (percent > 80) return 'text-red-500';
    if (percent > 60) return 'text-yellow-500';
    return 'text-green-500';
  };

  const getHealthBg = (percent: number) => {
    if (percent > 80) return 'bg-red-500';
    if (percent > 60) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-2xl">Loading cluster status...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">🤖 Agent Foundry Cluster</h1>
        <p className="text-gray-400">
          Live monitoring • Last update: {lastUpdate.toLocaleTimeString()}
        </p>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-slate-800 rounded-lg p-6">
            <div className="text-sm text-gray-400 mb-2">Total Agents</div>
            <div className="text-4xl font-bold">{summary.total}</div>
          </div>
          <div className="bg-green-900 bg-opacity-20 rounded-lg p-6">
            <div className="text-sm text-green-400 mb-2">Healthy</div>
            <div className="text-4xl font-bold text-green-500">
              {summary.healthy}
            </div>
          </div>
          <div className="bg-red-900 bg-opacity-20 rounded-lg p-6">
            <div className="text-sm text-red-400 mb-2">Unhealthy</div>
            <div className="text-4xl font-bold text-red-500">
              {summary.unhealthy}
            </div>
          </div>
        </div>
      )}

      {/* System Health */}
      {systemHealth && (
        <div className="bg-slate-800 rounded-lg p-6 mb-8">
          <h2 className="text-2xl font-bold mb-4">System Health</h2>
          <div className="grid grid-cols-3 gap-6">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-gray-400">CPU Usage</span>
                <span className={`font-bold ${getHealthColor(systemHealth.cpu_percent)}`}>
                  {systemHealth.cpu_percent.toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${getHealthBg(systemHealth.cpu_percent)}`}
                  style={{ width: `${systemHealth.cpu_percent}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-2">
                <span className="text-gray-400">Memory Usage</span>
                <span className={`font-bold ${getHealthColor(systemHealth.memory_percent)}`}>
                  {systemHealth.memory_percent.toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${getHealthBg(systemHealth.memory_percent)}`}
                  style={{ width: `${systemHealth.memory_percent}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-2">
                <span className="text-gray-400">Disk Usage</span>
                <span className={`font-bold ${getHealthColor(systemHealth.disk_percent)}`}>
                  {systemHealth.disk_percent.toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${getHealthBg(systemHealth.disk_percent)}`}
                  style={{ width: `${systemHealth.disk_percent}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Agent Table */}
      <div className="bg-slate-800 rounded-lg p-6 mb-8">
        <h2 className="text-2xl font-bold mb-4">Live Agent Workers</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left border-b border-slate-700">
                <th className="pb-3 px-4">Status</th>
                <th className="pb-3 px-4">Agent Type</th>
                <th className="pb-3 px-4">PID</th>
                <th className="pb-3 px-4">Tasks</th>
                <th className="pb-3 px-4">Errors</th>
                <th className="pb-3 px-4">Uptime</th>
              </tr>
            </thead>
            <tbody>
              {agents.map((agent) => (
                <tr key={agent.id} className="border-b border-slate-700 hover:bg-slate-750">
                  <td className="py-4 px-4">
                    <span className="text-2xl">{agent.status.split(' ')[0]}</span>
                  </td>
                  <td className="py-4 px-4">
                    <span className="font-mono font-semibold">{agent.type}</span>
                  </td>
                  <td className="py-4 px-4">
                    <span className="font-mono text-sm text-gray-400">
                      {agent.pid || 'N/A'}
                    </span>
                  </td>
                  <td className="py-4 px-4">
                    <span className="text-green-400 font-bold">
                      {agent.tasks_completed}
                    </span>
                  </td>
                  <td className="py-4 px-4">
                    <span className={agent.errors > 0 ? 'text-red-400 font-bold' : 'text-gray-500'}>
                      {agent.errors}
                    </span>
                  </td>
                  <td className="py-4 px-4">
                    <span className="text-sm text-gray-400">{agent.uptime}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-4">
        <button
          onClick={handleManualHeal}
          className="bg-red-600 hover:bg-red-700 px-6 py-3 rounded-lg font-bold transition"
        >
          🔧 Trigger Manual Self-Heal
        </button>
        <button
          onClick={() => window.location.reload()}
          className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-bold transition"
        >
          🔄 Refresh
        </button>
      </div>
    </div>
  );
}
