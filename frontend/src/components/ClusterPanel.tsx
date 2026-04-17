import { useState, useEffect } from 'react'
import { Cpu, MemoryStick, MonitorDot, HardDrive, Wifi, WifiOff, ArrowLeftRight } from 'lucide-react'
import { useNotebookStore, ClusterNode } from '../stores/notebookStore'
import { useThemeStore } from '../stores/themeStore'

export function ClusterPanel() {
  const { clusterNodes } = useNotebookStore()
  const { clusterPosition, setClusterPosition } = useThemeStore()

  const togglePosition = () => {
    setClusterPosition(clusterPosition === 'right' ? 'left' : 'right')
  }

  const demoNodes: ClusterNode[] = clusterNodes.length > 0 ? clusterNodes : [
    { id: '1', hostname: 'mbm-lab-01 (Head)', ipAddress: '10.10.13.242', status: 'online', cpuCores: 20, ramTotalGb: 32, gpuName: 'RTX 3060', gpuVramGb: 12, activeKernels: 2 },
    { id: '2', hostname: 'mbm-lab-02', ipAddress: '10.10.13.100', status: 'online', cpuCores: 20, ramTotalGb: 32, gpuName: 'RTX 3060', gpuVramGb: 12, activeKernels: 1 },
    { id: '3', hostname: 'mbm-lab-03', ipAddress: '10.10.13.101', status: 'offline', cpuCores: 20, ramTotalGb: 32, gpuName: 'RTX 3060', gpuVramGb: 12, activeKernels: 0 },
  ]

  const onlineNodes = demoNodes.filter(n => n.status === 'online')
  const totalCores = onlineNodes.reduce((sum, n) => sum + n.cpuCores, 0)
  const totalRam = onlineNodes.reduce((sum, n) => sum + n.ramTotalGb, 0)
  const totalGpu = onlineNodes.reduce((sum, n) => sum + n.gpuVramGb, 0)

  return (
    <aside className="h-full bg-surface-secondary border-l border-line overflow-y-auto transition-theme">
      <div className="px-4 py-3 border-b border-line flex items-center justify-between">
        <h2 className="text-xs font-semibold text-content-muted uppercase tracking-wider">Cluster Dashboard</h2>
        <button
          onClick={togglePosition}
          className="p-1 rounded hover:bg-surface-tertiary text-content-muted hover:text-content-primary transition-colors"
          title={`Move to ${clusterPosition === 'right' ? 'left' : 'right'}`}
        >
          <ArrowLeftRight size={12} />
        </button>
      </div>

      <div className="px-3 py-3 border-b border-line">
        <div className="grid grid-cols-2 gap-2">
          <StatCard label="Nodes" value={`${onlineNodes.length}/${demoNodes.length}`} color="accent" />
          <StatCard label="CPU Cores" value={`${totalCores}`} color="success" />
          <StatCard label="RAM" value={`${totalRam} GB`} color="purple" />
          <StatCard label="GPU VRAM" value={`${totalGpu} GB`} color="warning" />
        </div>
      </div>

      <div className="px-3 py-3">
        <h3 className="text-[11px] font-semibold text-content-muted uppercase mb-2 tracking-wide">Nodes</h3>
        <div className="space-y-2">
          {demoNodes.map((node) => (
            <NodeCard key={node.id} node={node} />
          ))}
        </div>
      </div>
    </aside>
  )
}

function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  const colorMap: Record<string, string> = {
    accent: 'text-accent',
    success: 'text-success',
    purple: 'text-purple-400',
    warning: 'text-warning',
  }
  return (
    <div className="bg-surface-tertiary rounded-lg px-3 py-2 border border-line/50">
      <p className="text-[10px] text-content-muted uppercase">{label}</p>
      <p className={`text-lg font-bold ${colorMap[color] || 'text-accent'}`}>{value}</p>
    </div>
  )
}

function NodeCard({ node }: { node: ClusterNode }) {
  const isOnline = node.status === 'online'
  return (
    <div className={`rounded-lg border p-3 transition-colors ${
      isOnline
        ? 'border-line bg-surface-tertiary/50'
        : 'border-line/50 bg-surface-primary/30 opacity-60'
    }`}>
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-success' : 'bg-danger'}`} />
        <span className="text-xs font-medium text-content-primary truncate">{node.hostname}</span>
        {isOnline
          ? <Wifi size={12} className="text-success ml-auto shrink-0" />
          : <WifiOff size={12} className="text-danger ml-auto shrink-0" />
        }
      </div>
      <div className="text-[10px] text-content-muted mb-2">{node.ipAddress}</div>
      <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[11px]">
        <div className="flex items-center gap-1 text-content-secondary"><Cpu size={10} /> {node.cpuCores} cores</div>
        <div className="flex items-center gap-1 text-content-secondary"><MemoryStick size={10} /> {node.ramTotalGb} GB</div>
        <div className="flex items-center gap-1 text-content-secondary"><MonitorDot size={10} /> {node.gpuName}</div>
        <div className="flex items-center gap-1 text-content-secondary"><HardDrive size={10} /> {node.gpuVramGb} GB VRAM</div>
      </div>
      {node.activeKernels > 0 && (
        <div className="mt-2 text-[10px] text-accent">{node.activeKernels} active kernel{node.activeKernels > 1 ? 's' : ''}</div>
      )}
    </div>
  )
}
