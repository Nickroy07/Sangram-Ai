import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { billingApi } from '../../services/api'
import { useAuth } from '../../context/AuthContext'
import { Button } from '../../components/common/Button'

export const BillingPage = () => {
  const { user } = useAuth()
  const [invoices, setInvoices] = useState([])
  const [subscription, setSubscription] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => {
    Promise.all([billingApi.invoices(), billingApi.subscription()]).then(([items, current]) => {
      setInvoices(items); setSubscription(current)
    }).catch((err) => setError(err.message))
  }, [])
  return <div className="billing-page-view">
    <div className="page-header-row"><div><h1 className="page-title">Billing & Subscriptions</h1><p className="page-sub">Review your account plan and payment history.</p></div><Link to="/pricing"><Button variant="primary">View plans</Button></Link></div>
    <div className="current-plan-box mt-6"><div className="plan-header-row"><div><span className="clean-tag-active">ACCOUNT PLAN</span><h2 className="plan-title-lg mt-2">{subscription?.planId || user?.tier || 'Free'}</h2><p className="plan-sub-text">{subscription ? `Status: ${subscription.status} · Renews ${new Date(subscription.currentPeriodEnd).toLocaleDateString()}` : 'No paid subscription is active on this account.'}</p></div></div></div>
    {error && <p className="auth-alert error-alert mt-6" role="alert">{error}</p>}
    <div className="clean-card-box mt-6"><div className="box-title-row"><h3 className="box-title">Invoice history</h3><span className="text-muted text-xs">{invoices.length} records</span></div>
      {invoices.length ? <div className="invoices-table-container mt-4"><table className="clean-invoices-table"><thead><tr><th>Invoice</th><th>Date</th><th>Amount</th><th>Status</th><th>Receipt</th></tr></thead><tbody>{invoices.map((invoice) => <tr key={invoice.id}><td className="font-mono text-cyan">{invoice.number}</td><td>{new Date(invoice.date).toLocaleDateString()}</td><td>{new Intl.NumberFormat(undefined, { style: 'currency', currency: invoice.currency }).format(invoice.amountCents / 100)}</td><td>{invoice.status}</td><td>{invoice.pdfUrl ? <a href={invoice.pdfUrl} target="_blank" rel="noreferrer">Download</a> : '—'}</td></tr>)}</tbody></table></div> : !error && <p className="text-muted mt-4">No invoices are available.</p>}
    </div>
  </div>
}
