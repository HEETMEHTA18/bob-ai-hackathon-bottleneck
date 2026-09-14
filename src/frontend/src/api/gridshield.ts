import type { AxiosResponse } from 'axios'
import gs, {
  gsGetAssets as gsGetAssetsBase,
  gsGetRiskRanking as gsGetRiskRankingBase,
  gsGetCrews as gsGetCrewsBase,
  type GSAsset,
  type GSCrew as BaseGSCrew,
  type GSRankingEntry as BaseGSRankingEntry,
} from './bottleneck'

export type { GSAsset }

export interface GSCrew extends BaseGSCrew {
  lat?: number
  lon?: number
}

export interface GSRankingEntry extends BaseGSRankingEntry {
  asset_lat: number
  asset_lon: number
}

export interface GSNearbyCrew {
  crew: GSCrew
  distance_km: number
  eta_hours: number
  specialty_match: boolean
}

export interface GSModelFileInfo {
  size_bytes: number
  modified: string
}

export interface GSMLStatus {
  mode: 'real_ml' | 'mock'
  use_real_ml: boolean
  models_available: boolean
  model_version?: string
  trained_at?: string
  models_directory: string
  model_files?: Record<string, GSModelFileInfo>
  metrics?: Record<string, number | string | boolean | null>
}

export interface GSHardwareRegister {
  telemetry_field: string
  address: number
  scale: number
}

export interface GSHardwareConnection {
  host?: string
  port?: number
  unit_id?: number
  serial_port?: string
  baud_rate?: number
  topic?: string
  endpoint?: string
}

export interface GSHardwareConfig {
  asset_id: string
  device_type: string
  protocol: string
  status: 'connected' | 'disconnected' | 'error'
  enabled: boolean
  poll_interval_seconds: number
  registers: GSHardwareRegister[]
  connection: GSHardwareConnection
  last_sync?: string
}

export const gsGetAssets = gsGetAssetsBase

export const gsGetRiskRanking = (scenario?: string) =>
  gsGetRiskRankingBase(scenario) as Promise<AxiosResponse<{ ranking: GSRankingEntry[]; total: number; scenario: string | null }>>

export const gsGetCrews = (availability?: string) =>
  gsGetCrewsBase(availability) as Promise<AxiosResponse<{ crews: GSCrew[]; count: number }>>

export const gsGetMLStatus = () =>
  gs.get<GSMLStatus>('/api/bottleneck/model/status')

export const gsGetAllHardwareConfigs = () =>
  gs.get<{ configs: GSHardwareConfig[] }>('/api/gs/hardware/configs')

export const gsTestHardwareConnection = (assetId: string) =>
  gs.post<{ success: boolean; message: string }>(`/api/gs/assets/${assetId}/hardware/test`, {})

export const gsSyncHardwareData = (assetId: string) =>
  gs.post<{ synced: number }>(`/api/gs/assets/${assetId}/hardware/sync`, {})
