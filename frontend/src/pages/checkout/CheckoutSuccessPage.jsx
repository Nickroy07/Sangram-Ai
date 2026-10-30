import React from 'react'
import { Link } from 'react-router-dom'
import { Button } from '../../components/common/Button'
import { Card } from '../../components/common/Card'

export const CheckoutSuccessPage = () => <div className="checkout-status-page-view"><div className="status-container max-w-lg mx-auto py-16"><Card className="status-card text-center p-8"><div className="status-badge-circle">…</div><h1 className="status-title mt-4">Payment status unavailable</h1><p className="status-sub text-muted mt-2">Sangram AI could not verify a payment for this account. Billing confirmation is not available until payment processing is connected.</p><div className="status-actions mt-8"><Link to="/app/billing"><Button variant="outline">View billing</Button></Link><Link to="/app/arena/new"><Button variant="primary">Open the Arena</Button></Link></div></Card></div></div>
