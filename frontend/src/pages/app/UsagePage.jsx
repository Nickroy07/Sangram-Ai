import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { billingApi } from '../../services/api'
import { Button } from '../../components/common/Button'

export const UsagePage = () => {
  const [usage, setUsage] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => { billingApi.usage().then(setUsage).catch((e) => setError(e.message)) }, [])
  return <div className="usage-page-view"><div className="page-header-row"><div><h1 className="page-title">Usage & Compute</h1><p className="page-sub">Usage appears here when account metering is enabled.</p></div><Link to="/app/billing"><Button variant="primary">Manage quota</Button></Link></div>
    {error ? <p className="auth-alert error-alert mt-6" role="alert">{error}</p> : usage && <div className="usage-meter-box mt-6"><span className="clean-label-sm">BILLING PERIOD · {usage.billingPeriod}</span><h2 className="meter-heading mt-1">{usage.quotaUsed} of {usage.quotaTotal} battles used</h2><div className="clean-progress-bar mt-4"><div className="clean-progress-fill" style={{ width: `${usage.quotaTotal ? Math.min(100, usage.quotaUsed / usage.quotaTotal * 100) : 0}%` }} /></div><p className="meter-footer-info mt-3">{usage.quotaRemaining} remaining · Updated {new Date(usage.lastUpdated).toLocaleString()}</p><ul>{Object.entries(usage.modelBreakdown || {}).map(([id, amount]) => <li key={id}>{id}: {amount}</li>)}</ul></div>}
  </div>
}
