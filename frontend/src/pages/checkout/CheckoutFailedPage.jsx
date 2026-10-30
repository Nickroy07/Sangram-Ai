import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';

export const CheckoutFailedPage = () => {
  return (
    <div className="checkout-status-page-view">
      <div className="status-container max-w-lg mx-auto py-16">
        <Card className="status-card text-center p-8 animate-scale-in">
          <div className="status-badge-circle error-circle">!</div>
          <h1 className="status-title mt-4">Checkout is unavailable</h1>
          <p className="status-sub text-muted mt-2">
            Sangram AI cannot start a payment session because billing provider integration is not configured yet.
          </p>

          <div className="status-actions mt-8 flex flex-col gap-3">
            <Link to="/pricing" className="w-full">
              <Button variant="primary" size="lg" className="w-full">
                View Plans
              </Button>
            </Link>
            <Link to="/contact" className="w-full">
              <Button variant="outline" className="w-full">
                Contact Support
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
};
