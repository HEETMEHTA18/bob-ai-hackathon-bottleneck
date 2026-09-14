/**
 * GridShield — Hardware Integration Settings
 * Documents how to connect physical hardware (sensors, RTUs, DTCs) to GridShield.
 */
import React, { useState, useEffect } from 'react'
import {
  gsGetAllHardwareConfigs,
  gsGetHardwareConfig,
  gsTestHardwareConnection,
  gsSyncHardwareData,
  type GSHardwareConfig,
} from '../../api/gridshield'
import { RED, MUTED } from './utils'
import {
  Loader2, RefreshCw, Wifi, WifiOff, Zap, Settings as SettingsIcon,
  ChevronRight, ChevronDown, Cpu, Radio, Server, Shield,
  AlertTriangle, CheckCircle2, XCircle, Info, ArrowRight,
} from 'lucide-react'

const PROTOCOL_DOCS: Record<string, { label: string; port: string; description: string; wiring: string }> = {
  modbus_tcp: {
    label: 'Modbus TCP/IP',
    port: '502',
    description: 'Standard Ethernet-based industrial protocol. Each asset gets its own IP address on the SCADA LAN.',
    wiring: 'Connect RJ45 to asset switch/router. Set IP via asset front panel or serial console.',
  },
  modbus: {
    label: 'Modbus RTU (Serial)',
    port: 'COM / USB',
    description: 'Serial RS-485 bus. Multiple assets share the bus with unique slave IDs (1–247).',
    wiring: 'RS-485 A/B wires to terminal block. Set unit_id (1–247) on each device.',
  },
  dnp3: {
    label: 'DNP3',
    port: '20000',
    description: 'Distributed Network Protocol — used by utilities for SCADA. Supports unsolicited responses.',
    wiring: 'Serial RS-232/RS-485 or TCP/IP. Configure DNP3 address per asset.',
  },
  iec61850: {
    label: 'IEC 61850 (MMS)',
    port: '102',
    description: 'Substation communication standard. GOOSE for fast peer-to-peer, MMS for monitoring.',
    wiring: 'Ethernet LAN. Configure IED IP and GOOSE virtual LAN tags.',
  },
  mqtt: {
    label: 'MQTT',
    port: '1883 / 8883',
    description: 'Lightweight pub/sub messaging. Ideal for battery-powered or low-bandwidth sensors.',
    wiring: 'Wi-Fi or cellular. Set broker IP, topic, and QoS. TLS on port 8883.',
  },
  opcua: {
    label: 'OPC UA',
    port: '4840',
    description: 'Unified Architecture for secure industrial data exchange.',
    wiring: 'Ethernet. Set server endpoint URL and node IDs per register.',
  },
  http: {
    label: 'HTTP/REST',
    port: '80 / 443',
    description: 'RESTful JSON API. Common for smart sensors and IoT gateways.',
    wiring: 'Wi-Fi or Ethernet. Set endpoint URL and polling interval.',
  },
}

const DEVICE_TYPE_DOCS: Record<string, { label: string; description: string; icon: React.ReactNode }> = {
  dtc: { label: 'DTC (Distribution Transformer Controller)', description: 'Monitors transformer oil temp, load, vibration. Usually Modbus TCP.', icon: <Zap className="h-4 w-4 text-blue-500" /> },
  smart_sensor: { label: 'Smart Sensor', description: 'IoT vibration/temperature sensors attached to bushings, cables, or busbars.', icon: <Radio className="h-4 w-4 text-green-500" /> },
  pmcu: { label: 'PMCU (Protection & Monitoring Control Unit)', description: 'Benchmarks current/voltage and detects imbalance. DNP3 or IEC 61850.', icon: <Shield className="h-4 w-4 text-purple-500" /> },
  rtu: { label: 'RTU (Remote Terminal Unit)', description: 'General-purpose I/O for substations. Multiple register groups.', icon: <Server className="h-4 w-4 text-orange-500" /> },
  custom: { label: 'Custom / Third-Party', description: 'Any device with HTTP/REST, MQTT, or OPC UA interface.', icon: <Cpu className="h-4 w-4 text-gray-500" /> },
}

const COMMON_REGISTER_MAP = [
  { modbus_address: '100–101', telemetry_field: 'oil_temperature', unit: '°C', description: 'Top-oil temperature (float32, scale 0.1)' },
  { modbus_address: '102–103', telemetry_field: 'load_percentage', unit: '%', description: 'Current load as % of rated MVA (float32, scale 0.1)' },
  { modbus_address: '104–105', telemetry_field: 'vibration', unit: 'mm/s', description: 'Peak vibration on core/tank (float32, scale 0.01)' },
  { modbus_address: '106–107', telemetry_field: 'partial_discharge', unit: 'pC', description: 'Partial discharge magnitude (float32, scale 0.001)' },
  { modbus_address: '108–109', telemetry_field: 'current_unbalance', unit: '%', description: 'Phase current unbalance (float32)' },
  { modbus_address: '110–111', telemetry_field: 'voltage_deviation', unit: '%', description: 'Voltage deviation from nominal (float32)' },
]

interface HardwareConfigCardProps {
  config: GSHardwareConfig
  onTest: (assetId: string) => void
  onSync: (assetId: string) => void
  testResults: Record<string, { success: boolean; message: string } | null>
  syncResults: Record<string, { synced: number } | null>
}

function HardwareConfigCard({ config, onTest, onSync, testResults, syncResults }: HardwareConfigCardProps) {
  const [expanded, setExpanded] = useState(false)
  const testResult = testResults[config.asset_id]
  const syncResult = syncResults[config.asset_id]

  return (
    <div className="card" style={{ marginBottom: 12, borderLeft: `4px solid ${config.status === 'connected' ? '#0d904f' : '#e8710a'}` }}>
      <div
        style={{ display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer', padding: '12px 16px' }}
        onClick={() => setExpanded(!expanded)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1, minWidth: 0 }}>
          {config.status === 'connected'
            ? <Wifi className="h-4 w-4 text-green-600" style={{ flexShrink: 0 }} />
            : <WifiOff className="h-4 w-4 text-orange-500" style={{ flexShrink: 0 }} />
          }
          <div style={{ minWidth: 0 }}>
            <div style={{ fontWeight: 700, fontSize: 14, color: '#202124' }}>{config.asset_id}</div>
            <div style={{ fontSize: 12, color: MUTED, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <span>{config.device_type.replace('_', ' ').toUpperCase()}</span>
              <span>{config.protocol.toUpperCase()}</span>
              <span>{config.status}</span>
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
          {testResult && (
            testResult.success
              ? <CheckCircle2 className="h-4 w-4 text-green-600" />
              : <XCircle className="h-4 w-4 text-red-500" />
          )}
          {expanded ? <ChevronDown className="h-4 w-4 text-gray-400" /> : <ChevronRight className="h-4 w-4 text-gray-400" />}
        </div>
      </div>

      {expanded && (
        <div style={{ padding: '0 16px 16px', borderTop: '1px solid #e0e0e0' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 12 }}>
            <div>
              <div style={{ fontSize: 11, fontWeight: 600, color: MUTED, textTransform: 'uppercase', marginBottom: 4 }}>Connection</div>
              <div style={{ fontSize: 13, color: '#202124' }}>
                {config.connection.host && <div>Host: {config.connection.host}</div>}
                {config.connection.port && <div>Port: {config.connection.port}</div>}
                {config.connection.unit_id !== undefined && <div>Unit ID: {config.connection.unit_id}</div>}
                {config.connection.serial_port && <div>Serial: {config.connection.serial_port}</div>}
                {config.connection.baud_rate && <div>Baud: {config.connection.baud_rate}</div>}
                {config.connection.topic && <div>Topic: {config.connection.topic}</div>}
                {config.connection.endpoint && <div>Endpoint: {config.connection.endpoint}</div>}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 11, fontWeight: 600, color: MUTED, textTransform: 'uppercase', marginBottom: 4 }}>Polling</div>
              <div style={{ fontSize: 13, color: '#202124' }}>
                <div>Interval: {config.poll_interval_seconds}s</div>
                <div>Enabled: {config.enabled ? 'Yes' : 'No'}</div>
              </div>
              <div style={{ fontSize: 11, fontWeight: 600, color: MUTED, textTransform: 'uppercase', marginTop: 12, marginBottom: 4 }}>Registers ({config.registers?.length || 0})</div>
              <div style={{ fontSize: 12 }}>
                {config.registers?.map((r, i) => (
                  <div key={i} style={{ color: '#202124', marginBottom: 2 }}>
                    {r.telemetry_field}: addr {r.address} ({r.scale !== 1 ? `×${r.scale}` : 'raw'})
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 8, marginTop: 12, paddingTop: 12, borderTop: '1px solid #f0f0f0' }}>
            <button
              className="btn btn-outline btn-sm"
              onClick={(e) => { e.stopPropagation(); onTest(config.asset_id) }}
            >
              <Wifi className="h-3 w-3 mr-1" /> Test Connection
            </button>
            <button
              className="btn btn-outline btn-sm"
              onClick={(e) => { e.stopPropagation(); onSync(config.asset_id) }}
            >
              <RefreshCw className="h-3 w-3 mr-1" /> Sync Data
            </button>
          </div>

          {testResult && (
            <div
              className="text-xs"
              style={{
                marginTop: 8, padding: 8, borderRadius: 6,
                background: testResult.success ? '#e6f4ea' : '#fce8e6',
                color: testResult.success ? '#0d904f' : RED,
              }}
            >
              {testResult.success
                ? <CheckCircle2 className="h-3.5 w-3.5 inline-block align-middle mr-1" />
                : <XCircle className="h-3.5 w-3.5 inline-block align-middle mr-1" />}
              {testResult.message}
            </div>
          )}
          {syncResult && (
            <div className="text-xs" style={{ marginTop: 8, padding: 8, borderRadius: 6, background: '#e6f4ea', color: '#0d904f', display: 'flex', alignItems: 'center', gap: 6 }}>
              <CheckCircle2 className="h-3.5 w-3.5" /> Synced {syncResult.synced} reading(s)
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function Settings() {
  const [configs, setConfigs] = useState<GSHardwareConfig[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [testResults, setTestResults] = useState<Record<string, { success: boolean; message: string } | null>>({})
  const [syncResults, setSyncResults] = useState<Record<string, { synced: number } | null>>({})
  const [docsOpen, setDocsOpen] = useState(true)

  useEffect(() => { load() }, [])

  const load = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await gsGetAllHardwareConfigs()
      setConfigs(res.data.configs)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleTest = async (assetId: string) => {
    try {
      const res = await gsTestHardwareConnection(assetId)
      setTestResults(prev => ({ ...prev, [assetId]: res.data }))
    } catch (e: any) {
      setTestResults(prev => ({ ...prev, [assetId]: { success: false, message: e.message } }))
    }
  }

  const handleSync = async (assetId: string) => {
    try {
      const res = await gsSyncHardwareData(assetId)
      setSyncResults(prev => ({ ...prev, [assetId]: res.data }))
    } catch (e: any) {
      setSyncResults(prev => ({ ...prev, [assetId]: null }))
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="card" style={{ borderLeft: `4px solid ${RED}` }}>
        <div className="card-title" style={{ color: RED }}>Error</div>
        <p className="text-sm">{error}</p>
        <button className="btn btn-outline btn-sm" style={{ marginTop: 8 }} onClick={load}>Retry</button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 style={{ fontSize: 22, fontWeight: 800, color: '#202124', display: 'flex', alignItems: 'center', gap: 10 }}>
          <SettingsIcon className="h-5 w-5" /> Hardware Integration Settings
        </h1>
        <p style={{ fontSize: 14, color: MUTED, marginTop: 4 }}>
          Connect physical sensors, RTUs, and DTCs to feed live telemetry into GridShield's risk engine.
        </p>
      </div>

      {/* Quick Stats */}
      <div style={{ display: 'flex', gap: 12 }}>
        <div className="kpi-card" style={{ flex: 1 }}>
          <div className="kpi-value" style={{ color: '#0d904f' }}>{configs.filter(c => c.status === 'connected').length}</div>
          <div className="kpi-label">Connected</div>
        </div>
        <div className="kpi-card" style={{ flex: 1 }}>
          <div className="kpi-value" style={{ color: '#e8710a' }}>{configs.filter(c => c.status !== 'connected').length}</div>
          <div className="kpi-label">Disconnected</div>
        </div>
        <div className="kpi-card" style={{ flex: 1 }}>
          <div className="kpi-value">{configs.length}</div>
          <div className="kpi-label">Total Devices</div>
        </div>
      </div>

      {/* Integration Guide */}
      <div className="card" style={{ borderLeft: '4px solid #2563eb' }}>
        <div
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}
          onClick={() => setDocsOpen(!docsOpen)}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Info className="h-4 w-4 text-blue-600" />
            <span style={{ fontWeight: 700, fontSize: 14 }}>Integration Guide — How to Connect Hardware</span>
          </div>
          {docsOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </div>

        {docsOpen && (
          <div style={{ marginTop: 16, fontSize: 13, lineHeight: 1.7, color: '#3c4043' }}>
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontWeight: 700, marginBottom: 6, color: '#202124' }}>1. Supported Protocols</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                {Object.entries(PROTOCOL_DOCS).map(([key, doc]) => (
                  <div key={key} style={{ padding: 10, background: '#f8f9fa', borderRadius: 8, border: '1px solid #e0e0e0' }}>
                    <div style={{ fontWeight: 600, color: '#202124', fontSize: 12 }}>{doc.label}</div>
                    <div style={{ fontSize: 11, color: MUTED, marginTop: 2 }}>Port: {doc.port}</div>
                    <div style={{ fontSize: 11, color: '#3c4043', marginTop: 4 }}>{doc.description}</div>
                    <div style={{ fontSize: 11, color: '#3c4043', marginTop: 4, fontStyle: 'italic' }}>Wiring: {doc.wiring}</div>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ marginBottom: 20 }}>
              <div style={{ fontWeight: 700, marginBottom: 6, color: '#202124' }}>2. Device Types</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                {Object.entries(DEVICE_TYPE_DOCS).map(([key, doc]) => (
                  <div key={key} style={{ padding: 10, background: '#f8f9fa', borderRadius: 8, border: '1px solid #e0e0e0', display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                    {doc.icon}
                    <div>
                      <div style={{ fontWeight: 600, color: '#202124', fontSize: 12 }}>{doc.label}</div>
                      <div style={{ fontSize: 11, color: '#3c4043', marginTop: 2 }}>{doc.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ marginBottom: 20 }}>
              <div style={{ fontWeight: 700, marginBottom: 6, color: '#202124' }}>3. Register Map (Modbus DTC Default)</div>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid #e0e0e0', textAlign: 'left' }}>
                      <th style={{ padding: '6px 10px', fontWeight: 700, color: '#202124' }}>Modbus Address</th>
                      <th style={{ padding: '6px 10px', fontWeight: 700, color: '#202124' }}>Telemetry Field</th>
                      <th style={{ padding: '6px 10px', fontWeight: 700, color: '#202124' }}>Unit</th>
                      <th style={{ padding: '6px 10px', fontWeight: 700, color: '#202124' }}>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {COMMON_REGISTER_MAP.map((r, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid #f0f0f0' }}>
                        <td style={{ padding: '6px 10px', fontFamily: 'monospace' }}>{r.modbus_address}</td>
                        <td style={{ padding: '6px 10px' }}>{r.telemetry_field}</td>
                        <td style={{ padding: '6px 10px' }}>{r.unit}</td>
                        <td style={{ padding: '6px 10px', color: MUTED }}>{r.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div style={{ padding: 12, background: '#e8f0fe', borderRadius: 8, border: '1px solid #c6dafc' }}>
              <div style={{ fontWeight: 700, color: '#1a56db', fontSize: 12, display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                <Info className="h-3 w-3" /> How to Add a New Asset Device
              </div>
              <ol style={{ fontSize: 12, color: '#3c4043', paddingLeft: 18, margin: 0, lineHeight: 1.8 }}>
                <li>Wire the sensor/RTU to the asset's SCADA network (see wiring notes per protocol above).</li>
                <li>Note the device's IP address, Modbus unit ID (or serial port + slave ID), and register addresses.</li>
                <li>In GridShield, navigate to <strong>Asset Intelligence</strong> → select your asset → <strong>Hardware Integration</strong>.</li>
                <li>Enter the connection fields (host, port, unit_id, poll interval) and register mappings.</li>
                <li>Click <strong>Test Connection</strong> to verify the device is reachable and responding.</li>
                <li>Click <strong>Sync Data</strong> to pull a live reading. Confirm values appear in the Telemetry tab.</li>
                <li>GridShield will now automatically poll and factor live telemetry into the risk score.</li>
              </ol>
            </div>
          </div>
        )}
      </div>

      {/* Configured Devices */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <h2 style={{ fontSize: 16, fontWeight: 700, color: '#202124' }}>Configured Devices</h2>
          <button className="btn btn-outline btn-sm" onClick={load}>
            <RefreshCw className="h-3 w-3 mr-1" /> Refresh
          </button>
        </div>
        {configs.map(config => (
          <HardwareConfigCard
            key={config.asset_id}
            config={config}
            onTest={handleTest}
            onSync={handleSync}
            testResults={testResults}
            syncResults={syncResults}
          />
        ))}
        {configs.length === 0 && (
          <div className="empty-state">
            <Cpu className="empty-icon h-8 w-8" style={{ color: MUTED }} />
            <div className="empty-title">No hardware devices configured</div>
            <div className="empty-desc">Follow the integration guide above to connect your first device.</div>
          </div>
        )}
      </div>
    </div>
  )
}
