"use client"

import { TenantConfigPage } from "@/components/tenant-config-page"
import { TenantGuard } from "@/components/TenantGuard"

export default function TenantConfigurationPage() {
  return (
    <TenantGuard>
      <TenantConfigPage />
    </TenantGuard>
  )
}