<script>
  import { onMount, onDestroy } from 'svelte';

  let stats = {
    live_agents: 0,
    running_agents: 0,
    revenue: 0,
    deploys: 0,
    lines_changed: 0,
    tasks_in_queue: 0
  };

  let agents = [];
  let tasks = [];
  let pipelines = { running: [], queued: [], completed: [] };
  let logs = [];
  
  let interval;

  const API_URL = "http://localhost:8000";

  async def fetchData() {
    try {
      const [statsRes, agentsRes, tasksRes, pipesRes, logsRes] = await Promise.all([
        fetch(`${API_URL}/stats`),
        fetch(`${API_URL}/agents`),
        fetch(`${API_URL}/tasks`),
        fetch(`${API_URL}/pipelines`),
        fetch(`${API_URL}/logs`)
      ]);

      if (statsRes.ok) stats = await statsRes.json();
      if (agentsRes.ok) agents = await agentsRes.json();
      if (tasksRes.ok) tasks = await tasksRes.json();
      if (pipesRes.ok) pipelines = await pipesRes.json();
      if (logsRes.ok) logs = await logsRes.json();

    } catch (e) {
      console.error("Failed to fetch dashboard data:", e);
    }
  }

  onMount(() => {
    fetchData();
    interval = setInterval(fetchData, 2000); // Poll every 2s
  });

  onDestroy(() => {
    clearInterval(interval);
  });
</script>

<div class="min-h-screen bg-dark-950 p-6 text-slate-200">
  
  <!-- Header -->
  <header class="flex justify-between items-center mb-8 border-b border-white/10 pb-4">
    <div class="flex items-center gap-2">
      <div class="w-3 h-8 bg-green-500 rounded-sm"></div>
      <h1 class="text-2xl font-bold tracking-tight text-white">Agent Command</h1>
    </div>
    <div class="flex gap-4 text-sm font-mono text-slate-400">
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
        {stats.live_agents.toLocaleString()} agents live
      </div>
      <div>{stats.running_agents} running</div>
    </div>
  </header>

  <!-- Top Stats Grid -->
  <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
    <!-- Live Agents -->
    <div class="bg-dark-900 border border-white/5 rounded-lg p-6 relative overflow-hidden group">
      <div class="relative z-10">
        <h3 class="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-1">Live Agents</h3>
        <div class="text-4xl font-bold text-green-400">{stats.live_agents.toLocaleString()}</div>
        <div class="text-xs text-red-400 mt-2 flex items-center gap-1">
          <span>-12</span> of 2,350 capacity
        </div>
      </div>
      <div class="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-green-500/10 to-transparent"></div>
    </div>

    <!-- Revenue -->
    <div class="bg-dark-900 border border-white/5 rounded-lg p-6">
      <h3 class="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-1">Revenue Today</h3>
      <div class="text-4xl font-bold text-white">${stats.revenue.toLocaleString()}</div>
      <div class="text-xs text-green-400 mt-2">Live tracking</div>
    </div>

    <!-- Deploys -->
    <div class="bg-dark-900 border border-white/5 rounded-lg p-6">
      <h3 class="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-1">Deploys Today</h3>
      <div class="text-4xl font-bold text-white">{stats.deploys}</div>
      <div class="text-xs text-slate-400 mt-2">Automated releases</div>
    </div>

    <!-- Lines Changed -->
    <div class="bg-dark-900 border border-white/5 rounded-lg p-6">
      <h3 class="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-1">Lines Changed</h3>
      <div class="text-4xl font-bold text-white">{stats.lines_changed.toLocaleString()}</div>
      <div class="text-xs text-green-400 mt-2">+62,635 -26,843</div>
    </div>
  </div>

  <!-- Main Content Grid -->
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    
    <!-- Active Initiatives (Left Col) -->
    <div class="lg:col-span-1 space-y-4">
      <div class="flex justify-between items-center mb-2">
        <h2 class="text-lg font-semibold text-white">Active Initiatives</h2>
        <span class="text-xs text-slate-500">{stats.running_agents} running</span>
      </div>
      
      {#each pipelines.running as task}
        <div class="bg-dark-900 border border-white/5 rounded-lg p-4 hover:border-white/10 transition-colors">
          <div class="flex justify-between items-start mb-2">
            <div class="flex items-center gap-2">
              <span class="w-8 h-8 rounded-full bg-blue-600/20 text-blue-400 flex items-center justify-center text-xs font-bold">
                {task.title.substring(0, 2).toUpperCase()}
              </span>
              <div>
                <h4 class="font-medium text-slate-200 text-sm">{task.title}</h4>
                <div class="text-xs text-slate-500">{task.assigned_to_id || 'Unassigned'}</div>
              </div>
            </div>
            <span class="px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 text-[10px] font-bold uppercase tracking-wider">Scalar</span>
          </div>
          
          <div class="w-full bg-dark-800 h-1 rounded-full overflow-hidden mt-3">
             <div class="bg-blue-500 h-full w-1/3 animate-pulse"></div>
          </div>
          <div class="flex justify-between text-[10px] text-slate-500 mt-2">
             <span>35% of 400 max</span>
             <span>861 completed</span>
          </div>
        </div>
      {/each}

      {#if pipelines.running.length === 0}
        <div class="text-slate-500 text-sm p-4 bg-dark-900 rounded-lg">No active initiatives.</div>
      {/if}
    </div>

    <!-- Task Pipeline (Center Col) -->
    <div class="lg:col-span-1">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-lg font-semibold text-white">Task Pipeline</h2>
        <span class="text-xs text-slate-500">{pipelines.queued.length} queued</span>
      </div>

      <div class="space-y-3">
        {#each pipelines.queued as task}
        <div class="bg-dark-900 border border-white/5 rounded-lg p-3 border-l-2 border-l-yellow-500">
          <h4 class="text-sm font-medium text-slate-200">{task.title}</h4>
          <div class="flex justify-between items-center mt-2">
             <span class="text-xs text-slate-500">Queue pos #{task.priority}</span>
             <span class="text-[10px] px-1.5 py-0.5 bg-yellow-500/10 text-yellow-400 rounded">QUEUED</span>
          </div>
        </div>
        {/each}
        
        {#each pipelines.completed as task}
        <div class="bg-dark-900 border border-white/5 rounded-lg p-3 opacity-60">
          <h4 class="text-sm font-medium text-slate-400 line-through">{task.title}</h4>
          <div class="flex justify-between items-center mt-2">
             <span class="text-xs text-slate-600">Completed</span>
             <span class="text-[10px] px-1.5 py-0.5 bg-green-500/10 text-green-400 rounded">DONE</span>
          </div>
        </div>
        {/each}
      </div>
    </div>

    <!-- Agent Messages / Logs (Right Col) -->
    <div class="lg:col-span-1">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-lg font-semibold text-white">Agent Messages</h2>
        <span class="text-xs text-slate-500">{logs.length} recent</span>
      </div>

      <div class="space-y-4">
        {#each logs as log}
        <div class="flex gap-3 text-sm">
          <div class="flex-shrink-0">
            <span class="w-8 h-8 rounded bg-purple-500/10 text-purple-400 flex items-center justify-center font-bold text-xs ring-1 ring-purple-500/20">
              {log.agent.substring(0, 2).toUpperCase()}
            </span>
          </div>
          <div>
            <div class="flex items-center gap-2 mb-0.5">
              <span class="font-bold text-slate-300">{log.agent}</span>
              <span class="text-[10px] text-slate-600">→</span>
              <span class="text-[10px] px-1 py-px bg-slate-800 text-slate-400 rounded uppercase">{log.level}</span>
              <span class="text-[10px] text-slate-600 ml-auto">{new Date(log.timestamp).toLocaleTimeString()}</span>
            </div>
            <p class="text-slate-400 leading-snug">{log.message}</p>
          </div>
        </div>
        {/each}
      </div>
    </div>

  </div>
</div>
