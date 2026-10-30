import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { billingApi } from '../../services/api'
import { Button } from '../../components/common/Button'
import { Card } from '../../components/common/Card'

export const BillingManagePage = () => {
  const [subscription, setSubscription] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => { billingApi.subscription().then(setSubscription).catch((e) => setError(e.message)) }, [])
  return <div className="billing-manage-view"><div className="page-header-row"><div><h1 className="page-title">Subscription</h1><p className="page-sub">Manage subscription details and payment methods.</p></div><Link to="/app/billing"><Button variant="outline">Back to billing</Button></Link></div>
    {error && <p className="auth-alert error-alert mt-6" role="alert">{error}</p>}
    <Card className="manage-card mt-6">{subscription ? <><h2 className="manage-title">{subscription.planId}</h2><p>Status: {subscription.status} · {subscription.interval}</p><p>Current period ends {new Date(subscription.currentPeriodEnd).toLocaleDateString()}</p></> : !error && <p className="text-muted">No active subscription is linked to this account.</p>}<p className="text-muted mt-4">Payment method changes and subscription cancellation are not available until the billing provider is configured.</p></Card>
  </div>
}
