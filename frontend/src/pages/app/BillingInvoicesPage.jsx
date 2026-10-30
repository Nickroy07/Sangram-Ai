import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { billingApi } from '../../services/api'
import { Button } from '../../components/common/Button'
import { Card } from '../../components/common/Card'

export const BillingInvoicesPage = () => {
  const [invoices, setInvoices] = useState([])
  const [error, setError] = useState('')
  useEffect(() => { billingApi.invoices().then(setInvoices).catch((e) => setError(e.message)) }, [])
  return <div className="billing-invoices-view"><div className="page-header-row"><div><h1 className="page-title">Invoices & Receipts</h1><p className="page-sub">Invoices issued to your account.</p></div><Link to="/app/billing"><Button variant="outline">Back to billing</Button></Link></div>
    {error && <p className="auth-alert error-alert mt-6" role="alert">{error}</p>}
    <Card className="invoices-list-card mt-6">{invoices.length ? <div className="table-responsive"><table className="invoices-full-table"><thead><tr><th>Invoice</th><th>Date</th><th>Amount</th><th>Status</th><th>Receipt</th></tr></thead><tbody>{invoices.map((invoice) => <tr key={invoice.id}><td>{invoice.number}</td><td>{new Date(invoice.date).toLocaleDateString()}</td><td>{new Intl.NumberFormat(undefined, { style: 'currency', currency: invoice.currency }).format(invoice.amountCents / 100)}</td><td>{invoice.status}</td><td>{invoice.pdfUrl ? <a href={invoice.pdfUrl} target="_blank" rel="noreferrer">Download</a> : '—'}</td></tr>)}</tbody></table></div> : !error && <p className="text-muted">No invoices are available.</p>}</Card>
  </div>
}
