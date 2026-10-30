import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { billingApi } from '../../services/api'
import { Button } from '../../components/common/Button'
import { Card } from '../../components/common/Card'

export const BillingUpgradePage = () => {
  const [plans, setPlans] = useState([])
  const [error, setError] = useState('')
  useEffect(() => { billingApi.plans().then(setPlans).catch((e) => setError(e.message)) }, [])
  return <div className="billing-upgrade-view"><div className="page-header-row"><div><h1 className="page-title">Plans</h1><p className="page-sub">Compare the plan catalog available from Sangram AI.</p></div><Link to="/app/billing"><Button variant="outline">Back to billing</Button></Link></div>
    {error && <p className="auth-alert error-alert mt-6" role="alert">{error}</p>}
    <p className="auth-alert error-alert mt-6" role="status">Paid plans are catalog entries only. Checkout and plan entitlements are not enabled yet.</p>
    <div className="upgrade-cards-grid mt-6">{plans.filter((plan) => plan.id !== 'free').map((plan) => <Card key={plan.id} className="upgrade-tier-card"><h2 className="tier-title">{plan.name}</h2><p className="tier-tagline">{plan.description}</p><div className="tier-price mt-4"><span className="price-big">{new Intl.NumberFormat(undefined, { style: 'currency', currency: plan.pricing.currency }).format(plan.pricing.monthlyCents / 100)}</span><span className="price-cadence">/ month</span></div><ul className="tier-perks-list mt-6">{plan.features.map((feature) => <li key={feature} className="included"><span>✓</span><span>{feature}</span></li>)}</ul><div className="tier-action mt-6"><Button variant="outline" className="w-full" disabled>Payments unavailable</Button></div></Card>)}</div>
  </div>
}
