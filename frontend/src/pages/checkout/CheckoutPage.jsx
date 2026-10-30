import React, { useEffect, useState } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { billingApi } from '../../services/api'
import { useToast } from '../../context/ToastContext'
import { Button } from '../../components/common/Button'
import { Card } from '../../components/common/Card'
import { Logo } from '../../components/common/Logo'

export const CheckoutPage = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { showToast } = useToast()
  const [plans, setPlans] = useState([])
  const [interval, setInterval] = useState(searchParams.get('interval') === 'yearly' ? 'yearly' : 'monthly')
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState('')
  const planId = searchParams.get('plan') || 'pro'
  const plan = plans.find((item) => item.id === planId)

  useEffect(() => {
    billingApi.plans().then(setPlans).catch((err) => setError(err.message)).finally(() => setLoading(false))
  }, [])

  const amount = plan ? (interval === 'yearly' ? plan.pricing.yearlyCents : plan.pricing.monthlyCents) : 0
  const handleCheckout = async () => {
    setProcessing(true)
    setError('')
    try {
      const session = await billingApi.checkout({
        planId, interval,
        successUrl: `${window.location.origin}/checkout/success`,
        cancelUrl: `${window.location.origin}/checkout/cancelled`
      })
      window.location.assign(session.checkoutUrl)
    } catch (err) {
      setError(err.message)
      showToast(err.message, 'error')
    } finally { setProcessing(false) }
  }

  return <div className="checkout-page-view">
    <div className="checkout-top-header"><div className="flex items-center gap-3"><Logo size="md" href="/home" /><span className="checkout-pill-badge">Plan checkout</span></div><button type="button" className="cancel-checkout-link" onClick={() => navigate('/pricing')}>Back to plans</button></div>
    <div className="checkout-container-grid"><div className="checkout-left-col"><Card className="checkout-section-card"><h2 className="section-heading">Billing interval</h2><div className="interval-selector-row mt-4">{['monthly', 'yearly'].map((value) => <label key={value} className={`interval-radio-card ${interval === value ? 'selected' : ''}`}><input type="radio" name="interval" checked={interval === value} onChange={() => setInterval(value)} /><div className="radio-text-wrap"><span className="radio-title">{value === 'monthly' ? 'Monthly' : 'Annual'}</span><span className="radio-price">{plan ? new Intl.NumberFormat(undefined, { style: 'currency', currency: plan.pricing.currency }).format((value === 'monthly' ? plan.pricing.monthlyCents : plan.pricing.yearlyCents) / 100) : '—'} / {value === 'monthly' ? 'month' : 'year'}</span></div></label>)}</div></Card>
      <Card className="checkout-section-card mt-6"><h2 className="section-heading">Secure payment</h2><p className="text-muted">Payment details are collected by our hosted payment provider. Sangram AI never receives your card number.</p>{error && <p className="auth-alert error-alert" role="alert">{error}</p>}<Button type="button" variant="primary" size="lg" className="w-full mt-6" loading={processing || loading} disabled={!plan || loading} onClick={handleCheckout}>Continue to secure checkout</Button></Card></div>
      <div className="checkout-right-col"><Card className="order-summary-card"><h3 className="summary-card-title">Plan summary</h3>{loading ? <p>Loading plans…</p> : plan ? <><div className="summary-plan-row mt-4"><div><span className="summary-plan-name">{plan.name}</span><span className="summary-plan-tagline block text-muted text-xs">{plan.description}</span></div><span className="summary-plan-price font-bold">{new Intl.NumberFormat(undefined, { style: 'currency', currency: plan.pricing.currency }).format(amount / 100)}</span></div></> : <p className="auth-alert error-alert">{error || 'That plan is not available.'}</p>}<Link to="/terms" className="text-link-sm mt-4 block">Terms of Service</Link></Card></div></div>
  </div>
}
